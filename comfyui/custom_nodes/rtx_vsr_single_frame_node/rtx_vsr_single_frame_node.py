"""
rtx_vsr_single_frame_node.py
-----------------------------
ComfyUI custom node: RTX VSR Single Frame Upscale

Accepts a ComfyUI IMAGE tensor, processes it through NVIDIA RTX Video
Super Resolution (nvidia-vfx / nvvfx), and returns an upscaled IMAGE tensor.

ComfyUI IMAGE tensor format:  (B, H, W, C)  float32  [0, 1]  RGB
nvidia-vfx expected format:   (C, H, W)     float32  [0, 1]  RGB  on CUDA

This node handles the format conversion in both directions.

If nvidia-vfx is unavailable, the node returns the original image and
displays a warning — it will NOT crash ComfyUI.
"""

import sys
import traceback

import torch
import numpy as np

# ── nvidia-vfx availability ───────────────────────────────────────────────────
try:
    import nvvfx
    NVVFX_AVAILABLE = True
except ImportError:
    NVVFX_AVAILABLE = False
    print("[RTX VSR Node] WARNING: nvidia-vfx (nvvfx) is not installed.")
    print("[RTX VSR Node] Node will load but upscaling will be unavailable.")
    print("[RTX VSR Node] Install: pip install -U --no-build-isolation nvidia-vfx"
          " --index-url https://pypi.nvidia.com")


# ── Tensor conversion helpers ─────────────────────────────────────────────────

def comfyui_to_nvvfx(image_tensor: torch.Tensor) -> torch.Tensor:
    """
    Convert a ComfyUI image batch to an nvvfx-compatible single frame tensor.

    ComfyUI format: (B, H, W, C)  float32  [0, 1]
    nvvfx format  : (C, H, W)     float32  [0, 1]  on CUDA

    Takes the first batch item only (B=0).
    """
    # Take the first image from the batch
    frame = image_tensor[0]                    # (H, W, C)
    frame = frame.permute(2, 0, 1)             # (C, H, W)
    frame = frame.float().contiguous()
    if torch.cuda.is_available():
        frame = frame.cuda()
    return frame


def nvvfx_to_comfyui(tensor: torch.Tensor) -> torch.Tensor:
    """
    Convert nvvfx output tensor back to ComfyUI IMAGE format.

    nvvfx format  : (C, H, W)     float32  [0, 1]  on CUDA
    ComfyUI format: (B, H, W, C)  float32  [0, 1]  on CPU

    Adds a batch dimension (B=1).
    """
    frame = tensor.detach().cpu()              # (C, H, W)
    frame = frame.permute(1, 2, 0)            # (H, W, C)
    frame = frame.clamp(0.0, 1.0)
    frame = frame.unsqueeze(0)                # (1, H, W, C)
    return frame


# ── VSR effect wrapper ────────────────────────────────────────────────────────

def run_rtx_vsr(input_tensor: torch.Tensor, scale: int) -> torch.Tensor:
    """
    Run NVIDIA RTX VideoSuperRes on a single (C, H, W) CUDA float32 tensor.

    Args:
        input_tensor: CUDA float32 tensor, shape (3, H, W), values in [0, 1].
        scale: Upscale factor — 2 or 4.

    Returns:
        CUDA float32 tensor, shape (3, out_H, out_W).

    TODO: Verify the exact attribute name for scale factor in your
          installed version of nvidia-vfx:
          - Try: vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_4X  (named constant)
          - Or:  vsr.upscaleFactor = 1  (integer, often = 4x)
          - Or:  vsr.upscaleFactor = 0  (integer, often = 2x)
    """
    _, h, w = input_tensor.shape
    out_h = h * scale
    out_w = w * scale

    vsr = nvvfx.VideoSuperRes()

    if scale == 4:
        if hasattr(nvvfx, "UPSCALE_FACTOR_4X"):
            vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_4X
        else:
            vsr.upscaleFactor = 1
    elif scale == 2:
        if hasattr(nvvfx, "UPSCALE_FACTOR_2X"):
            vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_2X
        else:
            vsr.upscaleFactor = 0

    vsr.output_width  = out_w
    vsr.output_height = out_h

    # load() must be called before the first run()
    vsr.load()

    # Assign the input tensor.
    # The tensor must be: CUDA device, (3, H, W), float32, [0, 1].
    vsr.input = input_tensor
    vsr.run()

    # Clone output immediately to prevent DLPack buffer reuse issues
    return vsr.output.clone()


# ── ComfyUI node class ────────────────────────────────────────────────────────

class RTXVSRSingleFrameNode:
    """
    ComfyUI node: RTX VSR Single Frame Upscale

    Uses NVIDIA RTX Video Super Resolution to upscale a single image.
    Input/output: standard ComfyUI IMAGE tensor (B, H, W, C).
    """

    CATEGORY = "NVIDIA RTX / Super Resolution"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_factor": (["4x", "2x"],),
            }
        }

    RETURN_TYPES  = ("IMAGE",)
    RETURN_NAMES  = ("upscaled_image",)
    FUNCTION      = "upscale"

    def upscale(
        self,
        image: torch.Tensor,
        scale_factor: str,
    ) -> tuple[torch.Tensor]:
        scale = int(scale_factor[0])  # "4x" → 4, "2x" → 2

        # ── Guard: CUDA required ──────────────────────────────────────────────
        if not torch.cuda.is_available():
            print("[RTX VSR Node] WARNING: CUDA not available. Returning original image.")
            return (image,)

        # ── Guard: nvvfx required ─────────────────────────────────────────────
        if not NVVFX_AVAILABLE:
            print("[RTX VSR Node] WARNING: nvidia-vfx not installed. Returning original image.")
            print("[RTX VSR Node] Install: pip install -U --no-build-isolation nvidia-vfx"
                  " --index-url https://pypi.nvidia.com")
            return (image,)

        # ── Convert ComfyUI IMAGE → nvvfx tensor ──────────────────────────────
        b, h, w, c = image.shape
        print(f"[RTX VSR Node] Input : batch={b}  {w}x{h}  channels={c}")

        try:
            nvvfx_input = comfyui_to_nvvfx(image)

            # ── Run VSR ───────────────────────────────────────────────────────
            print(f"[RTX VSR Node] Running RTX VSR ({scale}x) ...")
            nvvfx_output = run_rtx_vsr(nvvfx_input, scale)

            # ── Convert nvvfx output → ComfyUI IMAGE ──────────────────────────
            output_image = nvvfx_to_comfyui(nvvfx_output)
            _, out_h, out_w, _ = output_image.shape
            print(f"[RTX VSR Node] Output: {out_w}x{out_h}")

            return (output_image,)

        except Exception:
            print("[RTX VSR Node] ERROR during VSR processing:")
            traceback.print_exc()
            print("[RTX VSR Node] Returning original image as fallback.")
            return (image,)


# ── Node registration ─────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "RTXVSRSingleFrameNode": RTXVSRSingleFrameNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RTXVSRSingleFrameNode": "RTX VSR Single Frame Upscale",
}
