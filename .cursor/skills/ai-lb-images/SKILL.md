---
name: ai-lb-images
description: Use when the user asks to generate, redraw, vary, or download an image, or to pick a Cloudflare image model on lb.bonnate.com.
---

# AI LB Images

Generate images with `https://lb.bonnate.com/v1` and the image-only key in `api-key` next to `image_generation_mcp.py`. Save files under `images/` unless the user names another folder.

Use the MCP tools `list_image_models` and `generate_image` when they are available. Otherwise run:

```text
python image_generation_mcp.py models
python image_generation_mcp.py generate "prompt" --size 512x512
python image_generation_mcp.py generate "prompt" --image ref.jpg
```

Repeat `--image` for more references. Other flags are `--model`, `--steps`, `--strength`, `--seed`, and `--out-dir`.

Default model is `cloudflare/@cf/black-forest-labs/flux-2-klein-4b`.

| Model | References |
|---|---|
| flux-2-dev, flux-2-klein-4b, flux-2-klein-9b | up to 4 |
| stable-diffusion-xl-lightning, stable-diffusion-xl-base-1.0, dreamshaper-8-lcm | 1, with `strength` |
| flux-1-schnell, lucid-origin, phoenix-1.0 | none |

Do not send an image generation through `/v1/chat/completions`. That route returns 400. If models, arguments, or the base URL change, follow `AGENTS.md` and update every agent config in the same change.
