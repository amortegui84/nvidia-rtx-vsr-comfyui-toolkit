"""
benchmark_rtx_vsr.py
--------------------
Run a small benchmark across:
  - one short video
  - one still image
  - one extracted frame (from the same video)

Generates a Markdown report at:
  outputs/benchmarks/benchmark_results.md

Usage:
    python scripts/benchmark_rtx_vsr.py

Optionally specify custom inputs:
    python scripts/benchmark_rtx_vsr.py \\
        --video  inputs/videos/test_video.mp4 \\
        --image  inputs/images/test_image.jpg \\
        --scale  4

Run from the project root directory.
"""

import argparse
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

try:
    import nvvfx
    NVVFX_AVAILABLE = True
    NVVFX_VERSION = getattr(nvvfx, "__version__", "unknown")
except ImportError:
    NVVFX_AVAILABLE = False
    NVVFX_VERSION = "not installed"

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from upscale_image_rtx_vsr import upscale_image
from upscale_video_rtx_vsr import upscale_video
from extract_frame_test import extract_frame


# ── System info ───────────────────────────────────────────────────────────────

def _gpu_name() -> str:
    if TORCH_AVAILABLE and torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    return "N/A (CUDA unavailable)"


def _driver_version() -> str:
    smi = shutil.which("nvidia-smi")
    if smi is None:
        return "N/A"
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip().splitlines()[0] if result.returncode == 0 else "N/A"
    except Exception:
        return "N/A"


def _image_resolution(path: Path) -> str:
    try:
        from PIL import Image
        with Image.open(path) as img:
            return f"{img.width}x{img.height}"
    except Exception:
        return "?"


def _video_resolution(path: Path) -> str:
    if not CV2_AVAILABLE:
        return "?"
    try:
        cap = cv2.VideoCapture(str(path))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        duration = frames / fps if fps > 0 else 0
        return f"{w}x{h}  {fps:.2f}fps  {frames} frames  {duration:.1f}s"
    except Exception:
        return "?"


# ── Timed runs ────────────────────────────────────────────────────────────────

BenchResult = dict  # {label, input, input_res, output, output_res, scale, time_s, fps, notes}


def _bench_image(image_path: Path, output_dir: Path, scale: int) -> BenchResult:
    out_path = output_dir / f"bench_image_{scale}x.png"
    in_res   = _image_resolution(image_path)

    if not NVVFX_AVAILABLE:
        return {
            "label":      "Still Image",
            "input":      str(image_path),
            "input_res":  in_res,
            "output":     "—",
            "output_res": "—",
            "scale":      scale,
            "time_s":     None,
            "fps":        None,
            "notes":      "SKIPPED — nvidia-vfx not installed",
        }

    t0 = time.perf_counter()
    try:
        upscale_image(str(image_path), str(out_path), scale)
        elapsed = time.perf_counter() - t0
        out_res = _image_resolution(out_path)
        return {
            "label": "Still Image", "input": str(image_path),
            "input_res": in_res, "output": str(out_path),
            "output_res": out_res, "scale": scale,
            "time_s": round(elapsed, 3), "fps": None, "notes": "OK",
        }
    except Exception as exc:
        return {
            "label": "Still Image", "input": str(image_path),
            "input_res": in_res, "output": "—", "output_res": "—",
            "scale": scale, "time_s": None, "fps": None,
            "notes": f"ERROR: {exc}",
        }


def _bench_frame(video_path: Path, frame_idx: int, output_dir: Path, scale: int) -> BenchResult:
    frames_in_dir = PROJECT_ROOT / "inputs" / "frames"
    extracted = extract_frame(video_path, frame_idx, frames_in_dir)
    in_res = _image_resolution(extracted)
    out_path = output_dir / f"bench_frame_{scale}x.png"

    if not NVVFX_AVAILABLE:
        return {
            "label": "Extracted Frame", "input": str(extracted),
            "input_res": in_res, "output": "—", "output_res": "—",
            "scale": scale, "time_s": None, "fps": None,
            "notes": "SKIPPED — nvidia-vfx not installed",
        }

    t0 = time.perf_counter()
    try:
        upscale_image(str(extracted), str(out_path), scale)
        elapsed = time.perf_counter() - t0
        out_res = _image_resolution(out_path)
        return {
            "label": "Extracted Frame", "input": str(extracted),
            "input_res": in_res, "output": str(out_path),
            "output_res": out_res, "scale": scale,
            "time_s": round(elapsed, 3), "fps": None, "notes": "OK",
        }
    except Exception as exc:
        return {
            "label": "Extracted Frame", "input": str(extracted),
            "input_res": in_res, "output": "—", "output_res": "—",
            "scale": scale, "time_s": None, "fps": None,
            "notes": f"ERROR: {exc}",
        }


def _bench_video(video_path: Path, output_dir: Path, scale: int) -> BenchResult:
    in_res   = _video_resolution(video_path)
    out_path = output_dir / f"bench_video_{scale}x.mp4"

    if not NVVFX_AVAILABLE:
        return {
            "label": "Video", "input": str(video_path),
            "input_res": in_res, "output": "—", "output_res": "—",
            "scale": scale, "time_s": None, "fps": None,
            "notes": "SKIPPED — nvidia-vfx not installed",
        }

    t0 = time.perf_counter()
    try:
        upscale_video(str(video_path), str(out_path), scale)
        elapsed = time.perf_counter() - t0
        out_res = _video_resolution(out_path)
        # Compute avg fps from elapsed and frame count
        cap = cv2.VideoCapture(str(video_path))
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        avg_fps = round(frames / elapsed, 2) if elapsed > 0 else None
        return {
            "label": "Video", "input": str(video_path),
            "input_res": in_res, "output": str(out_path),
            "output_res": out_res, "scale": scale,
            "time_s": round(elapsed, 2), "fps": avg_fps, "notes": "OK",
        }
    except Exception as exc:
        return {
            "label": "Video", "input": str(video_path),
            "input_res": in_res, "output": "—", "output_res": "—",
            "scale": scale, "time_s": None, "fps": None,
            "notes": f"ERROR: {exc}",
        }


# ── Markdown report ───────────────────────────────────────────────────────────

def _write_report(results: list[BenchResult], scale: int, report_path: Path) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    gpu = _gpu_name()
    driver = _driver_version()
    py_ver = sys.version.split()[0]

    lines = [
        "# NVIDIA RTX VSR Benchmark Results",
        "",
        "## Environment",
        "",
        f"| Key | Value |",
        f"|-----|-------|",
        f"| Date / Time | {now} |",
        f"| GPU | {gpu} |",
        f"| NVIDIA Driver | {driver} |",
        f"| Python | {py_ver} |",
        f"| nvidia-vfx version | {NVVFX_VERSION} |",
        f"| Platform | {platform.system()} {platform.release()} |",
        "",
        "## Results",
        "",
        "| Test | Input | Input Res | Output | Scale | Time (s) | Avg FPS | Notes |",
        "|------|-------|-----------|--------|-------|----------|---------|-------|",
    ]
    for r in results:
        time_str = f"{r['time_s']:.3f}" if r["time_s"] is not None else "—"
        fps_str  = str(r["fps"]) if r["fps"] is not None else "—"
        lines.append(
            f"| {r['label']} | `{Path(r['input']).name}` | {r['input_res']} "
            f"| `{Path(r['output']).name if r['output'] != '—' else '—'}` "
            f"| {r['scale']}x | {time_str} | {fps_str} | {r['notes']} |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- All processing performed on the GPU listed above.",
        "- Video benchmark time includes frame extraction, VSR, and reassembly.",
        "- Image benchmark time covers tensor conversion, VSR inference, and save.",
        "- VRAM usage is not tracked per-test in this report; "
          "run individual scripts for peak VRAM detail.",
        "",
        "---",
        f"*Generated by nvidia-rtx-vsr-comfyui-toolkit benchmark script.*",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[DONE] Report saved: {report_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Benchmark NVIDIA RTX VSR on video, image, and frame.")
    p.add_argument("--video",  default=str(PROJECT_ROOT / "inputs" / "videos" / "test_video.mp4"),
                   help="Input video path (default: inputs/videos/test_video.mp4)")
    p.add_argument("--image",  default=str(PROJECT_ROOT / "inputs" / "images" / "test_image.jpg"),
                   help="Input image path (default: inputs/images/test_image.jpg)")
    p.add_argument("--frame",  type=int, default=0,
                   help="Frame index to extract for frame benchmark (default: 0)")
    p.add_argument("--scale",  type=int, default=4, choices=[2, 4],
                   help="Upscale factor (default: 4)")
    return p.parse_args()


def main() -> None:
    args   = parse_args()
    scale  = args.scale
    video  = Path(args.video)
    image  = Path(args.image)
    out_dir = PROJECT_ROOT / "outputs" / "benchmarks"
    report  = out_dir / "benchmark_results.md"

    results: list[BenchResult] = []

    if image.exists():
        print(f"\n[BENCH] Still image: {image}")
        results.append(_bench_image(image, out_dir, scale))
    else:
        print(f"[SKIP] Image not found: {image}")
        results.append({
            "label": "Still Image", "input": str(image), "input_res": "—",
            "output": "—", "output_res": "—", "scale": scale,
            "time_s": None, "fps": None, "notes": "INPUT FILE NOT FOUND",
        })

    if video.exists():
        print(f"\n[BENCH] Extracted frame from: {video}")
        results.append(_bench_frame(video, args.frame, out_dir, scale))

        print(f"\n[BENCH] Video: {video}")
        results.append(_bench_video(video, out_dir, scale))
    else:
        print(f"[SKIP] Video not found: {video}")
        for label in ("Extracted Frame", "Video"):
            results.append({
                "label": label, "input": str(video), "input_res": "—",
                "output": "—", "output_res": "—", "scale": scale,
                "time_s": None, "fps": None, "notes": "INPUT FILE NOT FOUND",
            })

    _write_report(results, scale, report)


if __name__ == "__main__":
    main()
