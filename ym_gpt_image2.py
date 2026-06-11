"""Standalone RunningHub GPT Image 2.0 text/image-to-image node."""

import json
import os
import time
from io import BytesIO

DEFAULT_BASE_URL = "https://www.runninghub.cn/openapi/v2"
LOW_PRICE_TEXT_ENDPOINT = "rhart-image-g-2/text-to-image"
LOW_PRICE_IMAGE_ENDPOINT = "rhart-image-g-2/image-to-image"
OFFICIAL_TEXT_ENDPOINT = "rhart-image-g-2-official/text-to-image"
OFFICIAL_IMAGE_ENDPOINT = "rhart-image-g-2-official/image-to-image"
MAX_IMAGES = 10
LOW_PRICE_MAX_IMAGE_BYTES = 30 * 1024 * 1024
OFFICIAL_MAX_IMAGE_BYTES = 10 * 1024 * 1024

ASPECT_RATIOS = [
    "empty", "3:2", "1:1", "2:3", "5:4", "4:5", "16:9", "9:16",
    "21:9", "3:4", "4:3", "9:21", "1:2", "2:1", "1:3", "3:1",
]

ASPECT_PREFIX_ZH = {
    "3:2": "横版 3:2，", "1:1": "方图 1:1，", "2:3": "竖版 2:3，",
    "5:4": "横版 5:4，", "4:5": "竖版 4:5，", "16:9": "横版 16:9，",
    "9:16": "竖版 9:16，", "21:9": "横幅 21:9，", "3:4": "竖版 3:4，",
    "4:3": "横版 4:3，", "9:21": "竖幅 9:21，", "1:2": "竖版 1:2，",
    "2:1": "横版 2:1，", "1:3": "竖版 1:3，", "3:1": "横版 3:1，",
}

ASPECT_PREFIX_EN = {
    "3:2": "landscape 3:2, ", "1:1": "square 1:1, ",
    "2:3": "portrait 2:3, ", "5:4": "landscape 5:4, ",
    "4:5": "portrait 4:5, ", "16:9": "landscape 16:9, ",
    "9:16": "portrait 9:16, ", "21:9": "banner 21:9, ",
    "3:4": "portrait 3:4, ", "4:3": "landscape 4:3, ",
    "9:21": "vertical banner 9:21, ", "1:2": "portrait 1:2, ",
    "2:1": "landscape 2:1, ", "1:3": "portrait 1:3, ",
    "3:1": "landscape 3:1, ",
}


def _shared_api_key():
    try:
        from server import PromptServer

        value = getattr(PromptServer.instance, "shared_api_key", None)
        if isinstance(value, str) and value.strip() and value != "unknown":
            return value.strip()
    except Exception:
        pass
    return ""


def _extract_api_config(api_config):
    if isinstance(api_config, list) and api_config:
        api_config = api_config[0]
    return api_config if isinstance(api_config, dict) else {}


def _resolve_config(api_config=None):
    config = _extract_api_config(api_config)
    config_key = str(config.get("apiKey") or config.get("api_key") or "").strip()
    config_url = str(config.get("base_url") or "").strip()
    if config and (not config_key or not config_url):
        raise RuntimeError("Settings: both base_url and apiKey are required")

    key = config_key or _shared_api_key()
    if not key:
        key = str(os.environ.get("RH_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "RunningHub API Key not found. Connect RH OpenAPI Settings, or set RH_API_KEY. "
            "On RunningHub the shared API Key should be supplied automatically."
        )
    base_url = config_url or str(os.environ.get("RH_API_BASE_URL") or DEFAULT_BASE_URL).strip()
    return key, base_url.rstrip("/")


def _is_mostly_chinese(text):
    cjk = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    latin = sum(1 for char in text if char.isascii() and char.isalpha())
    return cjk + latin > 0 and cjk / (cjk + latin) >= 0.3


def _apply_aspect_prefix(prompt, aspect_ratio):
    if not aspect_ratio or aspect_ratio == "empty":
        return prompt
    mapping = ASPECT_PREFIX_ZH if _is_mostly_chinese(prompt) else ASPECT_PREFIX_EN
    fallback = f"画面比例 {aspect_ratio}，" if _is_mostly_chinese(prompt) else f"aspect ratio {aspect_ratio}, "
    return mapping.get(aspect_ratio, fallback) + prompt


def _tensor_to_png(image):
    import numpy as np
    from PIL import Image

    if image is None:
        raise ValueError("Empty image")
    value = image.detach().cpu().numpy() if hasattr(image, "detach") else np.asarray(image)
    if value.ndim == 4:
        value = value[0]
    if value.ndim != 3:
        raise ValueError(f"Unsupported IMAGE shape: {value.shape}")
    if value.shape[0] in (1, 3, 4) and value.shape[-1] not in (1, 3, 4):
        value = np.transpose(value, (1, 2, 0))
    value = np.clip(value * 255.0 if value.max() <= 1.0 else value, 0, 255).astype(np.uint8)
    if value.shape[-1] == 1:
        value = np.repeat(value, 3, axis=-1)
    mode = "RGBA" if value.shape[-1] == 4 else "RGB"
    buffer = BytesIO()
    Image.fromarray(value, mode=mode).save(buffer, format="PNG")
    return buffer.getvalue()


def _upload_image(image, index, api_key, base_url, max_image_bytes):
    import requests

    content = _tensor_to_png(image)
    if len(content) > max_image_bytes:
        max_mb = max_image_bytes // (1024 * 1024)
        raise RuntimeError(f"image{index} exceeds the RH {max_mb} MB limit for this channel")
    response = requests.post(
        f"{base_url}/media/upload/binary",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": (f"ym_gpt_image2_{index}.png", content, "image/png")},
        timeout=120,
    )
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Upload returned invalid JSON: HTTP {response.status_code}") from exc
    if response.status_code != 200 or data.get("code") != 0:
        message = data.get("message") or data.get("msg") or response.text[:300]
        raise RuntimeError(f"Image upload failed: {message}")
    url = (data.get("data") or {}).get("download_url")
    if not url:
        raise RuntimeError("Image upload response has no download_url")
    return url


def _submit(endpoint, payload, api_key, base_url):
    import requests

    response = requests.post(
        f"{base_url}/{endpoint}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Submit returned invalid JSON: HTTP {response.status_code}") from exc
    error_code = data.get("errorCode") or data.get("error_code") or ""
    error_message = data.get("errorMessage") or data.get("error_message") or ""
    if response.status_code != 200 or error_code or error_message:
        message = error_message or data.get("message") or response.text[:300]
        raise RuntimeError(f"Submit failed: {message} [errorCode: {error_code}]")
    task_id = data.get("taskId") or data.get("task_id")
    if not task_id:
        raise RuntimeError(f"Submit response has no taskId: {json.dumps(data, ensure_ascii=False)[:500]}")
    return str(task_id)


def _poll(task_id, api_key, base_url, interval=5.0, timeout=1800):
    import requests

    started = time.time()
    while time.time() - started <= timeout:
        time.sleep(interval)
        response = requests.post(
            f"{base_url}/query",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"taskId": task_id},
            timeout=60,
        )
        try:
            data = response.json()
        except ValueError:
            continue
        if response.status_code != 200:
            continue
        error_code = data.get("errorCode") or data.get("error_code") or ""
        error_message = data.get("errorMessage") or data.get("error_message") or ""
        if error_code or error_message:
            raise RuntimeError(f"Task failed: {error_message} [errorCode: {error_code}]")
        status = str(data.get("status") or "").upper()
        if status == "SUCCESS":
            urls = []
            for result in data.get("results") or []:
                url = result.get("url") or result.get("outputUrl")
                if url:
                    urls.append(url)
            if not urls:
                raise RuntimeError("Task succeeded but returned no image URL")
            return urls, data
        if status in ("FAILED", "CANCEL"):
            raise RuntimeError(f"Task status is {status}: {error_message or 'no message'}")
    raise RuntimeError(f"Task polling timed out after {timeout} seconds [taskId: {task_id}]")


def _download_images(urls):
    import numpy as np
    import requests
    import torch
    from PIL import Image

    tensors = []
    target_size = None
    for url in urls[:5]:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        if target_size is None:
            target_size = image.size
        elif image.size != target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        array = np.asarray(image).astype(np.float32) / 255.0
        tensors.append(torch.from_numpy(array))
    if not tensors:
        raise RuntimeError("No images downloaded")
    return torch.stack(tensors)


class YM_GPT_image2_0:
    CATEGORY = "RunningHub/RHArt Image"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "url", "response")
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        optional = {f"image{i}": ("IMAGE",) for i in range(1, MAX_IMAGES + 1)}
        optional.update({
            "api_config": ("RH_OPENAPI_CONFIG",),
            "channel": (["low_price", "official_stable"], {"default": "low_price"}),
            "aspectRatio": (ASPECT_RATIOS, {"default": "empty"}),
            "quality": (["low", "medium", "high"], {"default": "medium"}),
            "skip_error": ("BOOLEAN", {"default": False}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            "resolution": (["1k", "2k", "4k"], {"default": "1k"}),
        })
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "", "maxLength": 20000}),
            },
            "optional": optional,
        }

    @staticmethod
    def _error_image(message):
        import numpy as np
        import torch

        image = np.zeros((512, 512, 3), dtype=np.float32)
        image[:, :, 0] = 0.3
        return torch.from_numpy(image).unsqueeze(0)

    def generate(
        self,
        prompt,
        channel="low_price",
        aspectRatio="empty",
        quality="medium",
        resolution="1k",
        api_config=None,
        skip_error=False,
        seed=0,
        **kwargs,
    ):
        try:
            return self._generate_inner(
                prompt,
                channel,
                aspectRatio,
                quality,
                resolution,
                api_config,
                **kwargs,
            )
        except Exception as exc:
            if not skip_error:
                raise
            response_text = json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)
            return {
                "ui": {"text": ["", response_text]},
                "result": (self._error_image(str(exc)), "", response_text),
            }

    def _generate_inner(
        self,
        prompt,
        channel,
        aspectRatio,
        quality,
        resolution,
        api_config,
        **kwargs,
    ):
        prompt = str(prompt or "").strip()
        if not prompt:
            raise ValueError("prompt is required")
        key, root = _resolve_config(api_config)
        images = [kwargs[f"image{i}"] for i in range(1, MAX_IMAGES + 1) if kwargs.get(f"image{i}") is not None]
        official = channel == "official_stable"

        payload_prompt = prompt if official else _apply_aspect_prefix(prompt, aspectRatio)
        payload = {"prompt": payload_prompt, "appCode": "comfyui_rh_openapi"}
        if aspectRatio and aspectRatio != "empty":
            payload["aspectRatio"] = aspectRatio
        if resolution:
            payload["resolution"] = resolution
        if official:
            payload["quality"] = quality

        endpoint = OFFICIAL_TEXT_ENDPOINT if official else LOW_PRICE_TEXT_ENDPOINT
        max_image_bytes = OFFICIAL_MAX_IMAGE_BYTES if official else LOW_PRICE_MAX_IMAGE_BYTES
        if images:
            endpoint = OFFICIAL_IMAGE_ENDPOINT if official else LOW_PRICE_IMAGE_ENDPOINT
            payload["imageUrls"] = [
                _upload_image(image, index, key, root, max_image_bytes)
                for index, image in enumerate(images, 1)
            ]

        task_id = _submit(endpoint, payload, key, root)
        urls, full_response = _poll(task_id, key, root)
        image_batch = _download_images(urls)
        url_text = "\n".join(urls)
        response_text = json.dumps(full_response, ensure_ascii=False, indent=2)
        return {"ui": {"text": [url_text, response_text]}, "result": (image_batch, url_text, response_text)}

