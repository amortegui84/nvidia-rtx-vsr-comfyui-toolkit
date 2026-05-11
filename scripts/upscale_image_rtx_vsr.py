"""
upscale_image_rtx_vsr.py
------------------------
Upscale a single still image (JPG, PNG, WEBP, BMP) using NVIDIA RTX
Video Super Resolution via the nvidia-vfx Python package.

Usage:
    python scripts/upscale_image_rtx_vsr.py \\
        --input  inputs/images/test_image.jpg \\
        --output outputs/images/test_image_rtx_vsr_4x.png \\
        --scale  4

Run from the project root directory.
"""

import argparse
import os
import sys
import time
from pathlib import Path


# ── nvidia-vfx import (graceful fallback) ─────────────────────────────────────
try:
    import nvvfx
    NVVFX_AVAILABLE = True
except ImportError:
    NVVFX_AVAILABLE = False

# ── PyTorch ───────────────────────────────────────────────────────────────────
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import numpy as np
from PIL import Image


# ── Constants ─────────────────────────────────────────────────────────────────
SUPPORTED_INPUTS  = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SUPPORTED_SCALES  = {2, 4}
PROJECT_ROOT      = Path(__file__).resolve().parent.parent


# ── Tensor helpers ────────────────────────────────────────────────────────────

def image_to_tensor(img: Image.Image) -> "torch.Tensor":
    """Convert a PIL RGB image → CUDA float32 tensor (3, H, W) in [0, 1]."""
    arr = np.array(img.convert("RGB"), dtype=np.float32) / 255.0   # (H, W, 3)
    tensor = torch.from_numpy(arr).permute(2, 0, 1)                 # (3, H, W)
    return tensor.cuda().contiguous()


def tensor_to_image(tensor: "torch.Tensor") -> Image.Image:
    """Convert a CUDA float32 tensor (3, H, W) in [0, 1] → PIL RGB image."""
    arr = tensor.detach().cpu().permute(1, 2, 0).numpy()            # (H, W, 3)
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGB")


# ── VSR core ──────────────────────────────────────────────────────────────────

def _run_nvvfx_vsr(input_tensor: "torch.Tensor", scale: int) -> "torch.Tensor":
    """
    Run NVIDIA VideoSuperRes on a single (3, H, W) float32 CUDA tensor.

    The nvidia-vfx API uses GPU tensors directly (or DLPack capsules).
    This function wraps the API and clones the output immediately to avoid
    the DLPack buffer being overwritten on the next call.

    TODO: If the nvvfx API version on your system differs, check:
          - The exact constant for upscale factor (upscaleFactor vs UPSCALE_FACTOR_*)
          - Whether load() must be called once per session or per frame
          - Whether the tensor must be passed via __dlpack__() explicitly
    """
    if not NVVFX_AVAILABLE:
        raise RuntimeError(
            "nvidia-vfx is not installed.\n"
            "Run: pip install -U --no-build-isolation nvidia-vfx "
            "--index-url https://pypi.nvidia.com"
        )
    if not TORCH_AVAILABLE or not torch.cuda.is_available():
        raise RuntimeError("CUDA is required. Ensure a CUDA-enabled GPU and PyTorch are installed.")

    _, h, w = input_tensor.shape
    out_h = h * scale
    out_w = w * scale

    vsr = nvvfx.VideoSuperRes()

    # Set scale factor.
    # TODO: The exact API constant depends on your nvidia-vfx version.
    # Common patterns (try in order if one fails):
    #   vsr.upscaleFactor = 1        → often means 4x
    #   vsr.upscaleFactor = 0        → often means 2x
    #   nvvfx.UPSCALE_FACTOR_4X      → named constant if available
    #   nvvfx.UPSCALE_FACTOR_2X
    if scale == 4:
        if hasattr(nvvfx, "UPSCALE_FACTOR_4X"):
            vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_4X
        else:
            vsr.upscaleFactor = 1  # 1 = strong / 4x in most builds
    elif scale == 2:
        if hasattr(nvvfx, "UPSCALE_FACTOR_2X"):
            vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_2X
        else:
            vsr.upscaleFactor = 0  # 0 = 2x in most builds

    # Set expected output resolution before load()
    vsr.output_width  = out_w
    vsr.output_height = out_h

    # load() downloads/initialises the model weights. Call once per effect instance.
    vsr.load()

    # Assign input tensor. The tensor must be:
    #   - On CUDA (device='cuda')
    #   - channels-first RGB: shape (3, H, W)
    #   - dtype: float32
    #   - values in [0.0, 1.0]
    vsr.input = input_tensor

    # Run inference
    vsr.run()

    # IMPORTANT: Clone the output immediately. The internal DLPack buffer
    # backing vsr.output may be overwritten on the next vsr.run() call.
    output_tensor = vsr.output.clone()

    return output_tensor


# ── VRAM reporting ────────────────────────────────────────────────────────────

def vram_used_mb() -> float:
    if TORCH_AVAILABLE and torch.cuda.is_available():
        return torch.cuda.memory_allocated() / (1024 ** 2)
    return 0.0


def gpu_name() -> str:
    if TORCH_AVAILABLE and torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    return "N/A"


# ── Main processing function ──────────────────────────────────────────────────

def upscale_image(
    input_path: str,
    output_path: str,
    scale: int = 4,
) -> None:
    input_path  = Path(input_path)
    output_path = Path(output_path)

    # ── Validate input ────────────────────────────────────────────────────────
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)
    if input_path.suffix.lower() not in SUPPORTED_INPUTS:
        print(f"[ERROR] Unsupported format '{input_path.suffix}'. Supported: {SUPPORTED_INPUTS}")
        sys.exit(1)
    if scale not in SUPPORTED_SCALES:
        print(f"[ERROR] Unsupported scale factor {scale}x. Supported: {SUPPORTED_SCALES}")
        sys.exit(1)

    # ── Create output directory ───────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Load image ────────────────────────────────────────────────────────────
    print(f"\n[INFO] Loading image: {input_path}")
    img = Image.open(input_path).convert("RGB")
    in_w, in_h = img.size
    out_w = in_w * scale
    out_h = in_h * scale
    print(f"[INFO] Input  resolution : {in_w} x {in_h}")
    print(f"[INFO] Output resolution : {out_w} x {out_h}  ({scale}x)")
    print(f"[INFO] GPU               : {gpu_name()}")

    # ── Convert to tensor ─────────────────────────────────────────────────────
    if TORCH_AVAILABLE and torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    print(f"[INFO] Converting image to CUDA tensor ...")
    input_tensor = image_to_tensor(img)

    # ── Run VSR ───────────────────────────────────────────────────────────────
    print(f"[INFO] Running NVIDIA RTX VideoSuperRes ({scale}x) ...")
    t0 = time.perf_counter()

    output_tensor = _run_nvvfx_vsr(input_tensor, scale)

    elapsed = time.perf_counter() - t0

    # ── VRAM ──────────────────────────────────────────────────────────────────
    vram_mb = 0.0
    if TORCH_AVAILABLE and torch.cuda.is_available():
        vram_mb = torch.cuda.max_memory_allocated() / (1024 ** 2)

    # ── Convert back to PIL and save ──────────────────────────────────────────
    out_img = tensor_to_image(output_tensor)

    # Default: save as PNG. Honour .jpg/.jpeg explicitly.
    if output_path.suffix.lower() in {".jpg", ".jpeg"}:
        out_img.save(output_path, "JPEG", quality=95)
    else:
        # Force .png extension if not already set
        if output_path.suffix.lower() != ".png":
            output_path = output_path.with_suffix(".png")
        out_img.save(output_path, "PNG")

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n[DONE] Results")
    print(f"  Input      : {input_path}  ({in_w}x{in_h})")
    print(f"  Output     : {output_path}  ({out_w}x{out_h})")
    print(f"  Scale      : {scale}x")
    print(f"  Time       : {elapsed:.3f}s")
    print(f"  Peak VRAM  : {vram_mb:.1f} MB")
    print(f"  GPU        : {gpu_name()}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Upscale a still image using NVIDIA RTX Video Super Resolution."
    )
    p.add_argument("--input",  required=True,  help="Path to input image")
    p.add_argument("--output", required=True,  help="Path to output image (PNG by default)")
    p.add_argument("--scale",  type=int, default=4, choices=[2, 4],
                   help="Upscale factor: 2 or 4 (default: 4)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not NVVFX_AVAILABLE:
        print("[ERROR] nvidia-vfx is not installed.")
        print("  Run: pip install -U --no-build-isolation nvidia-vfx"
              " --index-url https://pypi.nvidia.com")
        sys.exit(1)

    if not TORCH_AVAILABLE:
        print("[ERROR] PyTorch is not installed.")
        print("  Run: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124")
        sys.exit(1)

    if not torch.cuda.is_available():
        print("[ERROR] CUDA is not available. An RTX GPU with CUDA is required.")
        sys.exit(1)

    upscale_image(
        input_path  = args.input,
        output_path = args.output,
        scale       = args.scale,
    )


if __name__ == "__main__":
    main()
