"""
extract_frame_test.py
---------------------
Extract a single frame from a video, save it to inputs/frames/,
then run the NVIDIA RTX VSR image upscaling path on that frame and
save the result to outputs/frames/.

This validates that the video upscaler can be used as a still-frame enhancer.

Usage:
    python scripts/extract_frame_test.py \\
        --input inputs/videos/test_video.mp4 \\
        --frame 10 \\
        --scale 4

Run from the project root directory.
"""

import argparse
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Import our image upscaler (handles nvvfx availability internally)
from upscale_image_rtx_vsr import upscale_image, NVVFX_AVAILABLE


def extract_frame(video_path: Path, frame_index: int, out_dir: Path) -> Path:
    """
    Extract a single frame from a video file and save as PNG.

    Returns the path to the saved frame.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        sys.exit(1)

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_index >= total:
        print(f"[ERROR] Frame {frame_index} out of range. Video has {total} frames.")
        cap.release()
        sys.exit(1)

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print(f"[ERROR] Could not read frame {frame_index}.")
        sys.exit(1)

    stem = video_path.stem
    out_path = out_dir / f"{stem}_frame{frame_index:06d}.png"
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), frame)

    h, w = frame.shape[:2]
    print(f"[INFO] Extracted frame {frame_index}: {w}x{h} → {out_path}")
    return out_path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extract a frame from video, then upscale it via NVIDIA RTX VSR."
    )
    p.add_argument("--input", required=True, help="Path to input video")
    p.add_argument("--frame", type=int, default=0,
                   help="Frame index to extract (0-based, default: 0)")
    p.add_argument("--scale", type=int, default=4, choices=[2, 4],
                   help="Upscale factor (default: 4)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    video_path  = Path(args.input)
    frame_index = args.frame
    scale       = args.scale

    if not video_path.exists():
        print(f"[ERROR] Video not found: {video_path}")
        sys.exit(1)

    frames_in_dir  = PROJECT_ROOT / "inputs"  / "frames"
    frames_out_dir = PROJECT_ROOT / "outputs" / "frames"

    # Step 1: Extract the frame
    print(f"\n[STEP 1] Extracting frame {frame_index} from: {video_path}")
    extracted_frame = extract_frame(video_path, frame_index, frames_in_dir)

    # Step 2: Upscale the extracted frame
    out_stem = extracted_frame.stem + f"_rtx_vsr_{scale}x.png"
    out_path = frames_out_dir / out_stem
    frames_out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[STEP 2] Upscaling extracted frame via RTX VSR ({scale}x) ...")

    if not NVVFX_AVAILABLE:
        print("[ERROR] nvidia-vfx is not installed. Cannot run VSR.")
        print("  Extracted frame saved at:", extracted_frame)
        print("  Install nvidia-vfx and re-run to upscale.")
        sys.exit(1)

    upscale_image(
        input_path  = str(extracted_frame),
        output_path = str(out_path),
        scale       = scale,
    )

    print(f"\n[DONE]")
    print(f"  Source frame : {extracted_frame}")
    print(f"  Enhanced     : {out_path}")


if __name__ == "__main__":
    main()
