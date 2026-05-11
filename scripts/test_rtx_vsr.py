"""
test_rtx_vsr.py
---------------
Quick end-to-end smoke test for the RTX VSR pipeline.

Creates a synthetic test image and a synthetic short video in inputs/,
runs them through the upscalers, and confirms outputs are written.

Useful when you don't yet have real test media.

Usage:
    python scripts/test_rtx_vsr.py

Run from the project root.
"""

import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _make_test_image(path: Path, width: int = 512, height: int = 288) -> None:
    """Create a synthetic gradient test image with text overlay."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for x in range(width):
        r = int(255 * x / width)
        for y in range(height):
            g = int(255 * y / height)
            b = 128
            draw.point((x, y), fill=(r, g, b))

    # Text overlay
    draw.rectangle([10, 10, width - 10, 50], fill=(0, 0, 0, 180))
    draw.text((15, 15), f"RTX VSR Test Image  {width}x{height}", fill=(255, 255, 255))

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(path), "JPEG", quality=90)
    print(f"[INFO] Created test image: {path}  ({width}x{height})")


def _make_test_video(path: Path, width: int = 512, height: int = 288, fps: int = 24,
                     duration_s: int = 3) -> None:
    """Create a synthetic test video using ffmpeg (colour-sweep)."""
    if shutil.which("ffmpeg") is None:
        print("[WARN] ffmpeg not in PATH — cannot create synthetic test video.")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration_s}:size={width}x{height}:rate={fps}",
        "-c:v", "libx264", "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[INFO] Created test video: {path}  ({width}x{height} @ {fps}fps, {duration_s}s)")
    else:
        print(f"[WARN] Could not create test video: {result.stderr.strip()[:200]}")


def _run_script(script: str, args: list[str]) -> bool:
    """Run a project script via subprocess and stream output."""
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / script)] + args
    print(f"\n{'─'*60}")
    print(f"[RUN] {' '.join(cmd)}")
    print(f"{'─'*60}")
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode == 0


def main() -> None:
    print("\n" + "="*60)
    print("  RTX VSR Toolkit — Quick Smoke Test")
    print("="*60)

    image_path = PROJECT_ROOT / "inputs" / "images" / "test_image.jpg"
    video_path = PROJECT_ROOT / "inputs" / "videos" / "test_video.mp4"
    img_out    = PROJECT_ROOT / "outputs" / "images" / "test_image_rtx_vsr_4x.png"
    vid_out    = PROJECT_ROOT / "outputs" / "videos" / "test_video_rtx_vsr_4x.mp4"

    # Create test inputs if they don't exist
    if not image_path.exists():
        _make_test_image(image_path)
    else:
        print(f"[INFO] Using existing test image: {image_path}")

    if not video_path.exists():
        _make_test_video(video_path)
    else:
        print(f"[INFO] Using existing test video: {video_path}")

    # Step 1: environment check
    ok1 = _run_script("check_environment.py", [])

    # Step 2: image upscale
    if image_path.exists():
        ok2 = _run_script("upscale_image_rtx_vsr.py", [
            "--input",  str(image_path),
            "--output", str(img_out),
            "--scale",  "4",
        ])
    else:
        print("[SKIP] No test image — skipping image upscale test.")
        ok2 = False

    # Step 3: frame extraction + upscale
    if video_path.exists():
        ok3 = _run_script("extract_frame_test.py", [
            "--input", str(video_path),
            "--frame", "0",
            "--scale", "4",
        ])
    else:
        print("[SKIP] No test video — skipping frame test.")
        ok3 = False

    # Step 4: video upscale
    if video_path.exists():
        ok4 = _run_script("upscale_video_rtx_vsr.py", [
            "--input",  str(video_path),
            "--output", str(vid_out),
            "--scale",  "4",
        ])
    else:
        ok4 = False

    # Summary
    print(f"\n{'='*60}")
    print("  Smoke Test Summary")
    print(f"{'='*60}")
    for label, result in [
        ("Environment check",  ok1),
        ("Image upscale",      ok2),
        ("Frame extraction",   ok3),
        ("Video upscale",      ok4),
    ]:
        status = "\033[92m[PASS]\033[0m" if result else "\033[91m[FAIL]\033[0m"
        print(f"  {status}  {label}")
    print()


if __name__ == "__main__":
    main()
