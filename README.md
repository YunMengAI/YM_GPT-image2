# YM_GPT_image2.0

RunningHub GPT Image 2.0 ComfyUI nodes, supporting both low-price and official-stable channels.

## Installation

Place the entire plugin folder in `ComfyUI/custom_nodes/`, then fully restart ComfyUI.

Search under `RunningHub/RHArt Image` for:

- `YM RH API Settings`
- `YM_GPT_image2.0`

## API Key

1. Add `YM RH API Settings`.
2. Keep `base_url` as `https://www.runninghub.cn/openapi/v2`.
3. Enter the current user's own RunningHub OpenAPI Key in `apiKey`.
4. Connect its `api_config` output to the `api_config` input on `YM_GPT_image2.0`.

The plugin contains no built-in API Key. The endpoint paths identify the API but are not credentials. Each user supplies their own Key and pays for their own API usage.

ComfyUI may save widget values in workflow JSON. Clear the Key before publishing or sharing a workflow.

## Routes

- `channel=low_price`, without images: `rhart-image-g-2/text-to-image`
- `channel=low_price`, with images: `rhart-image-g-2/image-to-image`
- `channel=official_stable`, without images: `rhart-image-g-2-official/text-to-image`
- `channel=official_stable`, with images: `rhart-image-g-2-official/image-to-image`

`quality` is sent only to the official-stable endpoints. Low-price images allow up to 30 MB each; official-stable images allow up to 10 MB each.

For server deployments, the generation node also supports a platform-injected shared API Key or the `RH_API_KEY` and `RH_API_BASE_URL` environment variables.
