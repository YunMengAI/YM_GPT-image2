"""YM GPT Image 2.0 ComfyUI custom node."""

from .ym_gpt_image2 import YM_GPT_image2_0
from .ym_settings import YM_RH_API_Settings

NODE_CLASS_MAPPINGS = {
    "YM_GPT_image2_0": YM_GPT_image2_0,
    "YM_RH_API_Settings": YM_RH_API_Settings,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "YM_GPT_image2_0": "YM_GPT_image2.0",
    "YM_RH_API_Settings": "YM RH API Settings",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
