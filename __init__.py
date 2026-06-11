"""YM GPT Image 2.0 ComfyUI custom node."""

from .ym_gpt_image2 import YM_GPT_image2_0

NODE_CLASS_MAPPINGS = {
    "YM_GPT_image2_0": YM_GPT_image2_0,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "YM_GPT_image2_0": "YM_GPT_image2.0",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

