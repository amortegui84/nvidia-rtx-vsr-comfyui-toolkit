# Workflow Examples

Load any of these JSON files in ComfyUI by dragging them onto the canvas
or using **Load** in the workflow menu.

---

## Workflow Index

| # | File | Use Case | Requires |
|---|------|----------|---------|
| 01 | `01_quick_4x_upscale.json` | Simplest upscale: load → RTX VSR 4x → save | Custom node only |
| 02 | `02_before_after_preview.json` | Side-by-side original vs upscaled preview | Custom node only |
| 03 | `03_2x_vs_4x_comparison.json` | Both scale factors in parallel, two saved outputs | Custom node only |
| 04 | `04_denoise_then_upscale.json` | Denoise first, then upscale (recommended for noisy sources) | Custom node + official NVIDIA RTX Nodes |
| 05 | `05_video_frame_sampler.json` | Sample frames from a video and upscale each one | Custom node + VHS (VideoHelperSuite) |
| 06 | `06_upscale_then_crop_tile.json` | Upscale 4x, then crop a detail region for close inspection | Custom node only |
| 07 | `07_ai_gen_image_enhance.json` | Generate with KSampler → upscale with RTX VSR 4x | Custom node + any SD checkpoint |

---

## Required Nodes per Workflow

### Always required

**RTXVSRSingleFrameNode** — our custom node.

Install by copying:
```
comfyui/custom_nodes/rtx_vsr_single_frame_node/
  → ComfyUI/custom_nodes/rtx_vsr_single_frame_node/
```

Then install `nvidia-vfx`:
```bash
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

---

### Workflow 04 — also requires NVIDIA RTX Nodes

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI
cd Nvidia_RTX_Nodes_ComfyUI && pip install -r requirements.txt
```

If the RTX Denoise node is not available, delete node 2 in that workflow
and connect `LoadImage` directly to `RTXVSRSingleFrameNode`.

---

### Workflow 05 — also requires ComfyUI-VideoHelperSuite (VHS)

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
cd ComfyUI-VideoHelperSuite && pip install -r requirements.txt
```

---

### Workflow 07 — requires a Stable Diffusion checkpoint

Place your `.ckpt` or `.safetensors` model in `ComfyUI/models/checkpoints/`
and update the `CheckpointLoaderSimple` widget to match the filename.

---

## Quick Decision Guide

```
Just want to upscale one image fast?
  → 01_quick_4x_upscale.json

Want to compare before and after visually?
  → 02_before_after_preview.json

Not sure whether 2x or 4x looks better?
  → 03_2x_vs_4x_comparison.json

Source has noise or compression artifacts?
  → 04_denoise_then_upscale.json  (denoise first, then upscale)

Working with video, want to spot-check quality?
  → 05_video_frame_sampler.json

Want to inspect fine details after upscaling?
  → 06_upscale_then_crop_tile.json

Using AI-generated images (SD/SDXL)?
  → 07_ai_gen_image_enhance.json
```

---

## Notes on Workflow JSON Format

These workflow files are written for ComfyUI's standard JSON format (version 0.4).
They include a `_name` and `_description` field at the root level for
documentation — ComfyUI ignores unknown top-level keys, so they load cleanly.

Node types that reference our custom node (`RTXVSRSingleFrameNode`) will show
as **red/missing** in ComfyUI if the custom node is not installed.
Install the node first, then reload the workflow.
