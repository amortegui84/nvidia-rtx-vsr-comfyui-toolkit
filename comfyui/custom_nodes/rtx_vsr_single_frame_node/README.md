# RTX VSR Single Frame Node

A ComfyUI custom node that upscales a single image frame using
**NVIDIA RTX Video Super Resolution** via the `nvidia-vfx` Python package.

## Node Details

| Property | Value |
|----------|-------|
| Name | RTX VSR Single Frame Upscale |
| Category | NVIDIA RTX / Super Resolution |
| Input | IMAGE (ComfyUI standard tensor) |
| Output | IMAGE (ComfyUI standard tensor, upscaled) |
| Scale options | 2x, 4x |

## Installation

### 1. Install this node

Copy or symlink the `rtx_vsr_single_frame_node` folder into your ComfyUI
`custom_nodes` directory:

```
ComfyUI/
  custom_nodes/
    rtx_vsr_single_frame_node/   ← place here
      __init__.py
      rtx_vsr_single_frame_node.py
      README.md
```

### 2. Install nvidia-vfx

The node requires the `nvidia-vfx` package from NVIDIA's private PyPI index.
Run inside your ComfyUI Python environment:

```bash
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

If that fails:

```bash
python -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

### 3. Restart ComfyUI

After placing the folder and installing `nvidia-vfx`, restart ComfyUI.

The node will appear in the node browser under:
**NVIDIA RTX / Super Resolution → RTX VSR Single Frame Upscale**

## How It Works

ComfyUI passes images as `(B, H, W, C)` float32 tensors in `[0, 1]`.

This node:
1. Takes the first frame from the batch `(B=0)`.
2. Converts to nvvfx format: `(C, H, W)` float32 on CUDA.
3. Runs `nvvfx.VideoSuperRes` at the selected scale factor.
4. Clones the DLPack output (required to avoid buffer reuse).
5. Converts back to ComfyUI format: `(1, H, W, C)` float32 on CPU.

## Graceful Degradation

- If `nvidia-vfx` is not installed: node loads but returns the original
  image unchanged with a console warning.
- If CUDA is unavailable: same graceful fallback.
- If an unexpected error occurs during inference: falls back to original
  image and prints the traceback to the console.

## Known Limitations

- Processes **one frame at a time** (no temporal consistency across frames).
  For video upscaling with temporal consistency, use the official NVIDIA RTX
  Nodes for ComfyUI or the `upscale_video_rtx_vsr.py` script.
- The exact `upscaleFactor` constant name may vary by `nvidia-vfx` version.
  See the TODO comment in `rtx_vsr_single_frame_node.py` if upscaling fails.
- Very large images may exceed VRAM. Try 2x before 4x if you hit OOM errors.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Node not visible in ComfyUI | Check `__init__.py` exports; restart ComfyUI |
| `nvidia-vfx` import error | Re-run the pip install command above |
| CUDA not available | Ensure CUDA PyTorch and correct driver are installed |
| `AttributeError: upscaleFactor` | Edit the constant in the node file per the TODO comment |
| Out of memory | Use 2x instead of 4x, or reduce input resolution |
