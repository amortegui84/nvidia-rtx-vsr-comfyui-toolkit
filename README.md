# nvidia-rtx-vsr-comfyui-toolkit

A proof-of-concept toolkit for testing **NVIDIA RTX Video Super Resolution (RTX VSR)**
on a local NVIDIA RTX 5090. Supports video upscaling, still-image enhancement,
single-frame extraction workflows, benchmarking, and ComfyUI integration.

---

## What This Project Does

- Upscale videos at 2x or 4x using NVIDIA's RTX VSR SDK (`nvidia-vfx`)
- Upscale still images and single extracted video frames using the same SDK
- Integrate RTX VSR into ComfyUI via a custom node
- Benchmark RTX VSR throughput and VRAM usage
- Provide a structured comparison platform against tools like SeedVR2 and Topaz Video AI

## Why It Exists

NVIDIA RTX Video Super Resolution is a hardware-accelerated upscaler built
into the RTX SDK. It can run at near-real-time speeds on RTX GPUs. This toolkit
makes it accessible as:

1. Standalone Python CLI scripts (for batch processing and automation)
2. A ComfyUI custom node (for visual workflow integration)
3. A benchmark harness (for comparison against other upscalers)

---

## Requirements

### Hardware

- NVIDIA RTX GPU (RTX 20-series or newer)
- **RTX 5090 (Blackwell)**: fully supported, 32 GB VRAM allows very large inputs

### Software / Drivers

| Requirement | Version |
|-------------|---------|
| NVIDIA Driver (Windows) | ≥ 531 (≥ 570 recommended for Blackwell / RTX 5090) |
| CUDA | 12.x (bundled with driver) |
| Python | 3.10, 3.11, or 3.12 |
| PyTorch | 2.1.0+ (CUDA build) |
| nvidia-vfx | Latest from pypi.nvidia.com |
| FFmpeg | Any recent version |

---

## Installation

### Windows (Primary)

See [setup_instructions.md](setup_instructions.md) for the full step-by-step guide.

**Quick start:**

```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install PyTorch (CUDA 12.4 build — adjust cu124 to match your CUDA version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install nvidia-vfx from NVIDIA's index
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com

# 5. Verify FFmpeg is installed
ffmpeg -version

# 6. Run environment check
python scripts/check_environment.py
```

---

## ComfyUI Installation

### Option A — Official NVIDIA RTX Nodes (for video)

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI
cd Nvidia_RTX_Nodes_ComfyUI
pip install -r requirements.txt
```

Restart ComfyUI. Look for nodes in the **NVIDIA RTX** category.

### Option B — Our custom node (for still images / single frames)

Copy the node folder into your ComfyUI custom nodes:

```
comfyui/custom_nodes/rtx_vsr_single_frame_node/
  → ComfyUI/custom_nodes/rtx_vsr_single_frame_node/
```

Then restart ComfyUI. The node appears as:
**NVIDIA RTX / Super Resolution → RTX VSR Single Frame Upscale**

Load the workflow files from `comfyui/workflows/` in ComfyUI.

---

## Python Script Usage

### Environment Check

```bash
python scripts/check_environment.py
```

Checks GPU, CUDA, driver, nvidia-vfx, ffmpeg, and directory structure.

---

### Image Upscaling

```bash
python scripts/upscale_image_rtx_vsr.py \
  --input  inputs/images/test_image.jpg \
  --output outputs/images/test_image_rtx_vsr_4x.png \
  --scale  4
```

Supported input formats: JPG, JPEG, PNG, WEBP, BMP
Supported scale factors: 2, 4
Default output format: PNG

---

### Video Upscaling

```bash
python scripts/upscale_video_rtx_vsr.py \
  --input  inputs/videos/test_video.mp4 \
  --output outputs/videos/test_video_rtx_vsr_4x.mp4 \
  --scale  4
```

Audio is preserved. FPS is preserved. Output is H.264 MP4.

---

### Single Frame Extraction + Enhancement

```bash
python scripts/extract_frame_test.py \
  --input inputs/videos/test_video.mp4 \
  --frame 10 \
  --scale 4
```

Extracts frame 10 (0-based index), saves it to `inputs/frames/`,
upscales via RTX VSR, saves to `outputs/frames/`.

---

### Benchmark

```bash
python scripts/benchmark_rtx_vsr.py --scale 4
```

Runs image, frame, and video benchmarks and generates:
```
outputs/benchmarks/benchmark_results.md
```

---

### Smoke Test (creates synthetic inputs automatically)

```bash
python scripts/test_rtx_vsr.py
```

Creates a synthetic test image and video if none exist, then runs all
pipeline stages and prints a pass/fail summary.

---

## RTX 5090 / Blackwell Notes

The RTX 5090 uses the Blackwell (GB202) architecture.

- Compute capability: 10.0
- VRAM: 32 GB GDDR7
- CUDA minimum: 12.8
- Driver minimum: 570 (recommended)

At 4x scale on the RTX 5090, expect:
- **1080p → 4K**: real-time or faster (30–60+ FPS depending on model)
- **4K → 16K**: slower, but VRAM headroom is not a bottleneck

If `nvidia-vfx` was installed before your driver was updated to 570+,
reinstall it after updating the driver.

---

## Testing Sequence

```bash
# Step 1: Environment
python scripts/check_environment.py

# Step 2: Still image
python scripts/upscale_image_rtx_vsr.py \
  --input inputs/images/test_image.jpg \
  --output outputs/images/test_image_rtx_vsr_2x.png \
  --scale 2

# Step 3: Frame extraction
python scripts/extract_frame_test.py \
  --input inputs/videos/test_video.mp4 \
  --frame 10

# Step 4: Full video
python scripts/upscale_video_rtx_vsr.py \
  --input inputs/videos/test_video.mp4 \
  --output outputs/videos/test_video_rtx_vsr_2x.mp4 \
  --scale 2

# Step 5: Benchmark
python scripts/benchmark_rtx_vsr.py
```

---

## Project Structure

```
nvidia-rtx-vsr-comfyui-toolkit/
  README.md                          ← this file
  setup_instructions.md              ← detailed setup steps
  requirements.txt
  pyproject.toml
  .gitignore

  scripts/
    check_environment.py             ← GPU, driver, nvvfx, ffmpeg checks
    test_rtx_vsr.py                  ← end-to-end smoke test
    upscale_image_rtx_vsr.py        ← still image upscaler
    upscale_video_rtx_vsr.py        ← video upscaler
    extract_frame_test.py            ← extract + upscale one video frame
    benchmark_rtx_vsr.py             ← benchmark + markdown report

  comfyui/
    custom_nodes/
      rtx_vsr_single_frame_node/    ← ComfyUI node for still images
    workflows/
      rtx_vsr_video_workflow.json
      rtx_vsr_image_workflow.json
      rtx_vsr_single_frame_workflow.json

  inputs/                            ← place your test media here
    videos/
    images/
    frames/

  outputs/                           ← results land here
    videos/
    images/
    frames/
    benchmarks/

  docs/
    implementation_notes.md
    troubleshooting.md
    comparison_methodology.md
```

---

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for detailed fixes for:

- `nvidia-vfx` install failure
- Driver mismatch / CUDA unavailable
- FFmpeg missing
- ComfyUI node not appearing
- DLPack / tensor clone issues
- Out-of-memory errors
- RTX 5090 / Blackwell compatibility

---

## References

- [NVIDIA RTX Video SDK](https://developer.nvidia.com/rtx-video-sdk)
- [nvidia-vfx on PyPI (NVIDIA index)](https://pypi.org/project/nvidia-vfx/)
- [NVIDIA RTX Nodes for ComfyUI](https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI)
- [Comparison methodology](docs/comparison_methodology.md)

---

## License

MIT — see LICENSE file if added. Dependencies (PyTorch, nvidia-vfx) have their own licenses.
