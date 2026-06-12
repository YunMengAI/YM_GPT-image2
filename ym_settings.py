"""RunningHub API configuration node for YM GPT Image 2.0."""


class YM_RH_API_Settings:
    """Collect a user's RunningHub API settings for connected YM nodes."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_url": (
                    "STRING",
                    {"default": "https://www.runninghub.cn/openapi/v2"},
                ),
                "apiKey": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("RH_OPENAPI_CONFIG",)
    RETURN_NAMES = ("api_config",)
    CATEGORY = "RunningHub/RHArt Image"
    FUNCTION = "process"

    def process(self, base_url, apiKey):
        base_url = str(base_url or "").strip().rstrip("/")
        api_key = str(apiKey or "").strip()
        if not base_url:
            raise ValueError("base_url is required")
        if not api_key:
            raise ValueError("apiKey is required")
        return [{"base_url": base_url, "apiKey": api_key}]
