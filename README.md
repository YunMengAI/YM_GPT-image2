# YM_GPT_image2.0

Standalone ComfyUI node for RunningHub GPT Image 2.0, with both channel-low-price
and official-stable routing.

Verified against `HM-RunningHub/ComfyUI_RH_OpenAPI` model registry on 2026-06-11.

## Install

Place the entire `YM_GPT_image2_0` folder in `ComfyUI/custom_nodes/`, then fully restart ComfyUI.

Search for `YM_GPT_image2.0` under `RunningHub/RHArt Image`.

- `channel=low_price`, without images: `rhart-image-g-2/text-to-image`
- `channel=low_price`, with images: `rhart-image-g-2/image-to-image`
- `channel=official_stable`, without images: `rhart-image-g-2-official/text-to-image`
- `channel=official_stable`, with images: `rhart-image-g-2-official/image-to-image`

`quality` is sent only to the official-stable endpoints. Low-price images allow
up to 30 MB each; official-stable images allow up to 10 MB each.

On RunningHub, the API key is read from the platform automatically. Locally, connect
`RH OpenAPI Settings` or set `RH_API_KEY` and `RH_API_BASE_URL`.

