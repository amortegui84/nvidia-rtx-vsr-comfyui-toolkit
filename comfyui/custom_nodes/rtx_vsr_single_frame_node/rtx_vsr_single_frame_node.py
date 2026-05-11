"""
rtx_vsr_single_frame_node.py
-----------------------------
ComfyUI custom node: RTX VSR Single Frame Upscale

Model resolution order (first match wins):
  1. ComfyUI models folder:  ComfyUI/models/nvidia_vsr/
  2. NVVFX_SDK_PATH env var (user-defined custom path)
  3. NVIDIA SDK default:     C:/Program Files/NVIDIA Corporation/NVIDIA Video Effects/models/

Place model files in ComfyUI/models/nvidia_vsr/ to keep everything
inside ComfyUI without touching system directories.

ComfyUI IMAGE tensor format:  (B, H, W, C)  float32  [0, 1]  RGB
nvidia-vfx expected format:   (C, H, W)     float32  [0, 1]  RGB  on CUDA
"""

import os
import sys
import traceback

import torch
import numpy as np

# ── ComfyUI folder_paths integration ─────────────────────────────────────────
try:
    import folder_paths

    # Register nvidia_vsr as a recognised model type inside ComfyUI.
    # This makes ComfyUI/models/nvidia_vsr/ appear in the UI model list
    # and lets folder_paths.get_folder_paths("nvidia_vsr") resolve it.
    COMFYUI_MODELS_DIR = folder_paths.models_dir
    NVIDIA_VSR_MODEL_DIR = os.path.join(COMFYUI_MODELS_DIR, "nvidia_vsr")
    os.makedirs(NVIDIA_VSR_MODEL_DIR, exist_ok=True)

    if "nvidia_vsr" not in folder_paths.folder_names_and_paths:
        folder_paths.folder_names_and_paths["nvidia_vsr"] = (
            [NVIDIA_VSR_MODEL_DIR],
            {".nvmdl", ".bin", ".onnx", ".trt"},
        )

    FOLDER_PATHS_AVAILABLE = True
except ImportError:
    # Running outside ComfyUI (e.g. standalone testing)
    FOLDER_PATHS_AVAILABLE = False
    NVIDIA_VSR_MODEL_DIR = ""

# ── nvidia-vfx availability ───────────────────────────────────────────────────
try:
    import nvvfx
    NVVFX_AVAILABLE = True
except ImportError:
    NVVFX_AVAILABLE = False
    print("[RTX VSR Node] WARNING: nvidia-vfx (nvvfx) is not installed.")
    print("[RTX VSR Node] Install: pip install -U --no-build-isolation nvidia-vfx"
          " --index-url https://pypi.nvidia.com")


# ── Model path resolution ─────────────────────────────────────────────────────

_MODEL_FILE_EXTENSIONS = {".nvmdl", ".bin", ".onnx", ".trt"}

def _has_model_files(directory: str) -> bool:
    """Return True if the directory exists and contains at least one model file."""
    if not os.path.isdir(directory):
        return False
    return any(
        f.endswith(tuple(_MODEL_FILE_EXTENSIONS))
        for f in os.listdir(directory)
    )


def resolve_model_path() -> str | None:
    """
    Find the NVIDIA VSR model directory.

    Search order:
      1. ComfyUI/models/nvidia_vsr/            (recommended — everything in ComfyUI)
      2. NVVFX_SDK_PATH environment variable   (user override)
      3. NVIDIA SDK default system path        (fallback)

    Returns the first valid directory that contains model files, or None.
    """
    candidates = []

    # 1 — ComfyUI models folder (highest priority)
    if NVIDIA_VSR_MODEL_DIR:
        candidates.append(NVIDIA_VSR_MODEL_DIR)

    # 2 — User-defined env var
    env_path = os.environ.get("NVVFX_SDK_PATH", "").strip()
    if env_path:
        candidates.append(env_path)

    # 3 — NVIDIA SDK default paths
    candidates += [
        r"C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models",
        r"C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects",
    ]

    for path in candidates:
        if _has_model_files(path):
            return path

    return None


def _set_model_path(path: str) -> None:
    """
    Tell nvvfx where to find model files.

    The NVVFX_SDK_PATH environment variable is the most portable way to
    override the default search path across nvvfx versions. Some builds
    also expose vsr.model_dir — that is tried in run_rtx_vsr() directly.
    """
    os.environ["NVVFX_SDK_PATH"] = path


# ── Tensor conversion helpers ─────────────────────────────────────────────────

def comfyui_to_nvvfx(image_tensor: torch.Tensor) -> torch.Tensor:
    """
    ComfyUI IMAGE (B, H, W, C) float32 [0,1]
      → nvvfx tensor (C, H, W) float32 [0,1] on CUDA
    Takes only the first item from the batch.
    """
    frame = image_tensor[0]               # (H, W, C)
    frame = frame.permute(2, 0, 1)        # (C, H, W)
    frame = frame.float().contiguous()
    if torch.cuda.is_available():
        frame = frame.cuda()
    return frame


def nvvfx_to_comfyui(tensor: torch.Tensor) -> torch.Tensor:
    """
    nvvfx tensor (C, H, W) float32 [0,1] on CUDA
      → ComfyUI IMAGE (1, H, W, C) float32 [0,1] on CPU
    """
    frame = tensor.detach().cpu()         # (C, H, W)
    frame = frame.permute(1, 2, 0)        # (H, W, C)
    frame = frame.clamp(0.0, 1.0)
    return frame.unsqueeze(0)             # (1, H, W, C)


# ── VSR inference ─────────────────────────────────────────────────────────────

def run_rtx_vsr(input_tensor: torch.Tensor, scale: int, model_path: str) -> torch.Tensor:
    """
    Run NVIDIA RTX VideoSuperRes on a single (C, H, W) CUDA float32 tensor.

    Args:
        input_tensor: CUDA float32, shape (3, H, W), values in [0, 1].
        scale:        2 or 4.
        model_path:   Directory that contains the NVIDIA VSR model files.

    Returns:
        CUDA float32 tensor, shape (3, out_H, out_W).
    """
    _, h, w = input_tensor.shape
    out_h = h * scale
    out_w = w * scale

    vsr = nvvfx.VideoSuperRes()

    # Point nvvfx to our model directory before load()
    # Try attribute first (some builds), fall back to env var set earlier.
    if hasattr(vsr, "model_dir"):
        vsr.model_dir = model_path

    # Scale factor — try named constants first, fall back to integers
    if scale == 4:
        vsr.upscaleFactor = getattr(nvvfx, "UPSCALE_FACTOR_4X", 1)
    elif scale == 2:
        vsr.upscaleFactor = getattr(nvvfx, "UPSCALE_FACTOR_2X", 0)

    vsr.output_width  = out_w
    vsr.output_height = out_h

    # load() reads model weights from model_path / NVVFX_SDK_PATH
    try:
        vsr.load()
    except Exception as e:
        raise RuntimeError(
            f"nvvfx load() failed: {e}\n\n"
            "Model files not found or invalid.\n"
            "Place the NVIDIA VSR model files in:\n"
            f"  {NVIDIA_VSR_MODEL_DIR}\n\n"
            "Download the NVIDIA Video Effects SDK:\n"
            "  https://developer.nvidia.com/rtx-video-sdk\n"
            "Then copy the model files from the SDK into the folder above."
        ) from e

    vsr.input = input_tensor
    vsr.run()

    # Clone immediately — DLPack buffer is overwritten on the next run()
    return vsr.output.clone()


# ── ComfyUI node class ────────────────────────────────────────────────────────

class RTXVSRSingleFrameNode:
    """
    ComfyUI node: RTX VSR Single Frame Upscale

    Looks for NVIDIA VSR model files in (priority order):
      1. ComfyUI/models/nvidia_vsr/
      2. NVVFX_SDK_PATH environment variable
      3. C:/Program Files/NVIDIA Corporation/NVIDIA Video Effects/models/
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

    def upscale(self, image: torch.Tensor, scale_factor: str) -> tuple:
        scale = int(scale_factor[0])  # "4x" → 4

        # ── Guards ────────────────────────────────────────────────────────────
        if not torch.cuda.is_available():
            print("[RTX VSR Node] WARNING: CUDA not available. Returning original image.")
            return (image,)

        if not NVVFX_AVAILABLE:
            print("[RTX VSR Node] WARNING: nvidia-vfx not installed. Returning original image.")
            print("[RTX VSR Node] Install: pip install -U --no-build-isolation nvidia-vfx"
                  " --index-url https://pypi.nvidia.com")
            return (image,)

        # ── Resolve model path ────────────────────────────────────────────────
        model_path = resolve_model_path()

        if model_path is None:
            print("[RTX VSR Node] ERROR: No NVIDIA VSR model files found.")
            print(f"[RTX VSR Node] Place model files in: {NVIDIA_VSR_MODEL_DIR}")
            print("[RTX VSR Node] Download SDK: https://developer.nvidia.com/rtx-video-sdk")
            return (image,)

        print(f"[RTX VSR Node] Using model path: {model_path}")

        # Set env var so nvvfx finds models regardless of which API path works
        _set_model_path(model_path)

        # ── Run VSR ───────────────────────────────────────────────────────────
        b, h, w, c = image.shape
        print(f"[RTX VSR Node] Input : {w}x{h}  scale={scale}x")

        try:
            nvvfx_input  = comfyui_to_nvvfx(image)
            nvvfx_output = run_rtx_vsr(nvvfx_input, scale, model_path)
            output_image = nvvfx_to_comfyui(nvvfx_output)
            _, oh, ow, _ = output_image.shape
            print(f"[RTX VSR Node] Output: {ow}x{oh}")
            return (output_image,)

        except Exception:
            print("[RTX VSR Node] ERROR during VSR — returning original image.")
            traceback.print_exc()
            return (image,)


# ── Node registration ─────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "RTXVSRSingleFrameNode": RTXVSRSingleFrameNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RTXVSRSingleFrameNode": "RTX VSR Single Frame Upscale",
}
