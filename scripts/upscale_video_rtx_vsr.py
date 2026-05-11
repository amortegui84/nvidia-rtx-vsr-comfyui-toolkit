"""
upscale_video_rtx_vsr.py
------------------------
Upscale a video using NVIDIA RTX Video Super Resolution via the
nvidia-vfx Python package.

Workflow:
  1. Extract frames from input video (via OpenCV or ffmpeg).
  2. Convert each frame to a CUDA float32 tensor (3, H, W) in [0, 1].
  3. Run NVIDIA VideoSuperRes on each frame.
  4. Reassemble upscaled frames into a video with ffmpeg (preserving FPS).
  5. Merge original audio track back in with ffmpeg.

Usage:
    python scripts/upscale_video_rtx_vsr.py \\
        --input  inputs/videos/test_video.mp4 \\
        --output outputs/videos/test_video_rtx_vsr_4x.mp4 \\
        --scale  4

Run from the project root directory.
"""

import argparse
import os
import sys
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

try:
    import nvvfx
    NVVFX_AVAILABLE = True
except ImportError:
    NVVFX_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import cv2
import numpy as np
from tqdm import tqdm


# ── Constants ─────────────────────────────────────────────────────────────────
SUPPORTED_SCALES = {2, 4}
PROJECT_ROOT     = Path(__file__).resolve().parent.parent


# ── Tensor helpers ────────────────────────────────────────────────────────────

def bgr_frame_to_tensor(frame_bgr: np.ndarray) -> "torch.Tensor":
    """OpenCV BGR uint8 frame → CUDA float32 tensor (3, H, W) in [0, 1]."""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    arr = frame_rgb.astype(np.float32) / 255.0             # (H, W, 3)
    tensor = torch.from_numpy(arr).permute(2, 0, 1)        # (3, H, W)
    return tensor.cuda().contiguous()


def tensor_to_bgr_frame(tensor: "torch.Tensor") -> np.ndarray:
    """CUDA float32 tensor (3, H, W) in [0, 1] → OpenCV BGR uint8 frame."""
    arr = tensor.detach().cpu().permute(1, 2, 0).numpy()   # (H, W, 3)
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


# ── nvidia-vfx VSR effect ─────────────────────────────────────────────────────

class RTXVideoSuperRes:
    """
    Wrapper around nvvfx.VideoSuperRes that manages the effect lifecycle.

    The effect instance is created once per session; load() is called once.
    Input tensors are fed frame-by-frame via run(). Output is cloned
    immediately to avoid DLPack buffer reuse issues.
    """

    def __init__(self, scale: int, in_w: int, in_h: int):
        if not NVVFX_AVAILABLE:
            raise RuntimeError(
                "nvidia-vfx not installed.\n"
                "Run: pip install -U --no-build-isolation nvidia-vfx "
                "--index-url https://pypi.nvidia.com"
            )
        self.scale = scale
        self.out_w = in_w * scale
        self.out_h = in_h * scale
        self._vsr  = None

    def load(self) -> None:
        """Initialise the effect and download model weights."""
        self._vsr = nvvfx.VideoSuperRes()

        # Set scale factor.
        # TODO: Verify the constant name for your installed nvidia-vfx version.
        # Options (uncomment the one that works):
        #   self._vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_4X   (named constant)
        #   self._vsr.upscaleFactor = 1                          (integer, 4x)
        #   self._vsr.upscaleFactor = 0                          (integer, 2x)
        if self.scale == 4:
            if hasattr(nvvfx, "UPSCALE_FACTOR_4X"):
                self._vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_4X
            else:
                self._vsr.upscaleFactor = 1
        elif self.scale == 2:
            if hasattr(nvvfx, "UPSCALE_FACTOR_2X"):
                self._vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_2X
            else:
                self._vsr.upscaleFactor = 0

        self._vsr.output_width  = self.out_w
        self._vsr.output_height = self.out_h
        self._vsr.load()

        print(f"[INFO] RTXVideoSuperRes loaded: {self.scale}x → {self.out_w}x{self.out_h}")

    def run_frame(self, frame_tensor: "torch.Tensor") -> "torch.Tensor":
        """
        Process one frame tensor through VideoSuperRes.

        Args:
            frame_tensor: CUDA float32 tensor, shape (3, H, W), values in [0, 1].

        Returns:
            Cloned output CUDA float32 tensor, shape (3, out_H, out_W).
        """
        self._vsr.input = frame_tensor
        self._vsr.run()
        # Clone immediately — the DLPack buffer backing vsr.output
        # will be overwritten on the next call to run().
        return self._vsr.output.clone()


# ── ffmpeg helpers ────────────────────────────────────────────────────────────

def _check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        print("[ERROR] ffmpeg not found in PATH.")
        print("        Windows: winget install ffmpeg  |  or download from https://ffmpeg.org")
        sys.exit(1)


def _get_video_info(video_path: str) -> dict:
    """Return basic video metadata via ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
        "-of", "default=noprint_wrappers=1:nokey=0",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info: dict = {}
    for line in result.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k.strip()] = v.strip()

    # Parse frame rate (may be "30000/1001" format)
    fps_raw = info.get("r_frame_rate", "30/1")
    try:
        num, den = fps_raw.split("/")
        info["fps"] = float(num) / float(den)
    except Exception:
        info["fps"] = 30.0

    info["width"]  = int(info.get("width",  "0") or 0)
    info["height"] = int(info.get("height", "0") or 0)
    return info


def _extract_audio(video_path: Path, audio_path: Path) -> bool:
    """Extract audio stream from video. Returns True if audio exists."""
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "copy", str(audio_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0 and audio_path.exists()


def _frames_to_video(
    frames_dir: Path,
    output_path: Path,
    fps: float,
    audio_path: Path | None,
) -> None:
    """Reassemble frame PNGs into a video with ffmpeg, merging audio if available."""
    frame_pattern = str(frames_dir / "%06d.png")
    if audio_path and audio_path.exists():
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", frame_pattern,
            "-i", str(audio_path),
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", frame_pattern,
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
    print(f"[INFO] Assembling output video: {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] ffmpeg assembly failed:\n{result.stderr}")
        sys.exit(1)


# ── Main processing function ──────────────────────────────────────────────────

def upscale_video(
    input_path: str,
    output_path: str,
    scale: int = 4,
) -> None:
    _check_ffmpeg()

    input_path  = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        print(f"[ERROR] Input video not found: {input_path}")
        sys.exit(1)
    if scale not in SUPPORTED_SCALES:
        print(f"[ERROR] Unsupported scale {scale}x. Choose from: {SUPPORTED_SCALES}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Video metadata ────────────────────────────────────────────────────────
    info = _get_video_info(str(input_path))
    in_w   = info["width"]
    in_h   = info["height"]
    fps    = info["fps"]
    out_w  = in_w * scale
    out_h  = in_h * scale
    gpu    = torch.cuda.get_device_name(0) if (TORCH_AVAILABLE and torch.cuda.is_available()) else "N/A"

    print(f"\n[INFO] Input  : {input_path}")
    print(f"[INFO] Output : {output_path}")
    print(f"[INFO] In res : {in_w}x{in_h}")
    print(f"[INFO] Out res: {out_w}x{out_h}  ({scale}x)")
    print(f"[INFO] FPS    : {fps:.3f}")
    print(f"[INFO] GPU    : {gpu}")

    # ── Open video capture ────────────────────────────────────────────────────
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {input_path}")
        sys.exit(1)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[INFO] Frames : {total_frames}")

    # ── Initialise RTX VSR ────────────────────────────────────────────────────
    vsr = RTXVideoSuperRes(scale=scale, in_w=in_w, in_h=in_h)
    vsr.load()

    # ── Temporary workspace ───────────────────────────────────────────────────
    with tempfile.TemporaryDirectory(prefix="rtx_vsr_frames_") as tmp_dir:
        tmp_path    = Path(tmp_dir)
        audio_path  = tmp_path / "audio.aac"

        # Extract audio track
        has_audio = _extract_audio(input_path, audio_path)
        if has_audio:
            print(f"[INFO] Audio extracted to: {audio_path}")
        else:
            print(f"[INFO] No audio track found or extraction failed.")

        # ── Process frames ────────────────────────────────────────────────────
        t_start     = time.perf_counter()
        frame_idx   = 0
        vram_peak   = 0.0

        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        pbar = tqdm(total=total_frames, unit="frame", desc="RTX VSR")
        while True:
            ret, frame_bgr = cap.read()
            if not ret:
                break

            input_tensor   = bgr_frame_to_tensor(frame_bgr)
            output_tensor  = vsr.run_frame(input_tensor)
            out_frame      = tensor_to_bgr_frame(output_tensor)

            frame_name = tmp_path / f"{frame_idx:06d}.png"
            cv2.imwrite(str(frame_name), out_frame)
            frame_idx += 1
            pbar.update(1)

        pbar.close()
        cap.release()

        if TORCH_AVAILABLE and torch.cuda.is_available():
            vram_peak = torch.cuda.max_memory_allocated() / (1024 ** 2)

        t_end     = time.perf_counter()
        elapsed   = t_end - t_start
        avg_fps   = frame_idx / elapsed if elapsed > 0 else 0

        # ── Reassemble video ──────────────────────────────────────────────────
        _frames_to_video(
            frames_dir  = tmp_path,
            output_path = output_path,
            fps         = fps,
            audio_path  = audio_path if has_audio else None,
        )

    # ── Report ────────────────────────────────────────────────────────────────
    duration = frame_idx / fps if fps > 0 else 0
    print(f"\n[DONE] Results")
    print(f"  Input      : {input_path}  ({in_w}x{in_h})")
    print(f"  Output     : {output_path}  ({out_w}x{out_h})")
    print(f"  Scale      : {scale}x")
    print(f"  Frames     : {frame_idx}")
    print(f"  Duration   : {duration:.2f}s")
    print(f"  Total time : {elapsed:.2f}s")
    print(f"  Avg fps    : {avg_fps:.2f} frames/s")
    print(f"  Peak VRAM  : {vram_peak:.1f} MB")
    print(f"  GPU        : {gpu}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Upscale a video using NVIDIA RTX Video Super Resolution."
    )
    p.add_argument("--input",  required=True, help="Path to input video")
    p.add_argument("--output", required=True, help="Path to output video")
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
        print("[ERROR] PyTorch not installed.")
        sys.exit(1)

    if not torch.cuda.is_available():
        print("[ERROR] CUDA not available. RTX GPU required.")
        sys.exit(1)

    upscale_video(
        input_path  = args.input,
        output_path = args.output,
        scale       = args.scale,
    )


if __name__ == "__main__":
    main()
