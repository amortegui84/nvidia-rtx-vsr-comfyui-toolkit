# nvidia-rtx-vsr-comfyui-toolkit

Toolkit for using **NVIDIA RTX Video Super Resolution (RTX VSR)** inside
ComfyUI and standalone Python scripts. Designed for RTX 5090 (Blackwell).
Supports video upscaling, still images, and individual AI-generated frames.

---

## Quick Start — ComfyUI

### 1. Install the nodes

All nodes go inside your ComfyUI `custom_nodes` folder.
With the **Windows portable** this is:

```
ComfyUI_windows_portable\ComfyUI\custom_nodes\
```

---

#### Option A — ComfyUI Manager (easiest, no terminal needed)

1. Launch ComfyUI.
2. Click **Manager** in the top menu.
3. Click **Install Custom Nodes**.
4. Search **`RTX`** → install **Nvidia RTX Nodes**.
5. Search **`VHS`** → install **ComfyUI-VideoHelperSuite**.
6. Restart ComfyUI.

Then copy our custom node manually (see Option B, step 3 only).

---

#### Option B — Manual git clone

Open PowerShell and navigate to your `custom_nodes` folder:

```powershell
cd ComfyUI_windows_portable\ComfyUI\custom_nodes
```

**Clone the official NVIDIA RTX nodes:**
```powershell
git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git
..\..\..\python_embeded\python.exe -m pip install -r Nvidia_RTX_Nodes_ComfyUI\requirements.txt
```

**Clone ComfyUI-VideoHelperSuite (for video workflows):**
```powershell
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
..\..\..\python_embeded\python.exe -m pip install -r ComfyUI-VideoHelperSuite\requirements.txt
```

**Copy our custom RTX VSR Single Frame node** (run from this project's root):
```powershell
Copy-Item -Recurse `
  ".\comfyui\custom_nodes\rtx_vsr_single_frame_node" `
  "ComfyUI_windows_portable\ComfyUI\custom_nodes\rtx_vsr_single_frame_node"
```

**Install nvidia-vfx:**
```powershell
ComfyUI_windows_portable\python_embeded\python.exe -m pip install `
  -U --no-build-isolation nvidia-vfx `
  --index-url https://pypi.nvidia.com
```

After all steps, `custom_nodes` should look like this:

```
ComfyUI_windows_portable\ComfyUI\custom_nodes\
  Nvidia_RTX_Nodes_ComfyUI\          ← official NVIDIA RTX nodes
  ComfyUI-VideoHelperSuite\          ← video load / save
  rtx_vsr_single_frame_node\         ← our custom node (single image upscale)
```

---

#### Option C — Automatic installer script

Run from this project's root — detects ComfyUI and does all the steps above:

```powershell
.\comfyui\install_nodes.ps1
```

→ Full node guide with troubleshooting: [comfyui/NODES.md](comfyui/NODES.md)

---

### 2. Download the NVIDIA RTX VSR model files

The nodes need the NVIDIA Video Effects SDK model files to run.
**These are separate from `nvidia-vfx` and must be downloaded once.**

All model files live **inside your ComfyUI folder** — nothing in Program Files:

```
ComfyUI_windows_portable\ComfyUI\models\
  nvidia_vsr\              ← NVIDIA VSR model files go here
    SuperRes_CG_2x.nvmdl
    SuperRes_CG_4x.nvmdl
```

**Steps:**

1. Download the SDK: **https://developer.nvidia.com/rtx-video-sdk**
2. Run the installer — models land at `C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\`
3. Copy them into ComfyUI:
   ```powershell
   Copy-Item `
     "C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\*" `
     "ComfyUI_windows_portable\ComfyUI\models\nvidia_vsr\" `
     -Recurse
   ```
4. Verify:
   ```powershell
   python scripts\check_environment.py
   ```
   Look for: `[PASS] NVVFX model directory`

The node checks `ComfyUI\models\nvidia_vsr\` first — if models are there,
the Program Files path is never used.

→ Full model guide: [docs/models.md](docs/models.md)

---

### 3. Restart ComfyUI

After installing nodes, restart ComfyUI completely.

---

### 3. Load a workflow

Drag any of these JSON files onto the ComfyUI canvas:

| File | Description |
|------|-------------|
| `comfyui/workflows/examples/01_quick_4x_upscale.json` | Simplest 4x upscale |
| `comfyui/workflows/examples/02_before_after_preview.json` | Original vs upscaled side-by-side |
| `comfyui/workflows/examples/03_2x_vs_4x_comparison.json` | Compare both scale factors |
| `comfyui/workflows/examples/04_denoise_then_upscale.json` | Denoise → VSR 4x |
| `comfyui/workflows/examples/05_video_frame_sampler.json` | Sample video frames → VSR |
| `comfyui/workflows/examples/06_upscale_then_crop_tile.json` | Upscale + crop detail region |
| `comfyui/workflows/examples/07_ai_gen_image_enhance.json` | SD/SDXL generation → RTX VSR 4x |

→ Workflow descriptions: [comfyui/workflows/examples/README.md](comfyui/workflows/examples/README.md)

---

## Available Nodes After Installation

### RTX VSR Single Frame Upscale *(our custom node)*

> ComfyUI category: **NVIDIA RTX / Super Resolution**

Upscales a single image or frame using NVIDIA RTX VSR.

```
[IMAGE] ──► RTX VSR Single Frame Upscale ──► [IMAGE upscaled]
                     │
               scale_factor: 4x / 2x
```

- Input: standard ComfyUI IMAGE tensor `(B, H, W, C)`
- Output: upscaled IMAGE at the same format
- Works with any image: photos, renders, KSampler outputs, etc.

---

### RTX Video Super Resolution *(official NVIDIA)*

> ComfyUI category: **NVIDIA RTX**

Official Comfy-Org node for full video upscaling.
Requires: [Nvidia_RTX_Nodes_ComfyUI](https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI)

---

### RTX Denoise *(official NVIDIA)*

> ComfyUI category: **NVIDIA RTX**

Removes noise and compression artifacts before upscaling.
Always use **before** the upscale node for best results.

---

### VHS LoadVideo / VHS VideoCombine *(VideoHelperSuite)*

Load and save video inside ComfyUI.
Requires: [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)

---

## Recommended Pipelines

### AI-generated image (SD / SDXL / Flux output)

```
[CheckpointLoader] ──► [KSampler] ──► [VAEDecode] ──► [RTX VSR 4x] ──► [SaveImage]
```

Generate at 768×768 → RTX VSR outputs 3072×3072 instantly.
Ready workflow: `07_ai_gen_image_enhance.json`

---

### Noisy or compressed source image

```
[LoadImage] ──► [RTX Denoise] ──► [RTX VSR 4x] ──► [SaveImage]
```

Clean first, then scale. Upscaling amplifies noise if not removed first.
Ready workflow: `04_denoise_then_upscale.json`

---

### Video quality check before full upscale

```
[VHS_LoadVideo] ──► [VHS_GetImageBatch (frame N)] ──► [RTX VSR 4x] ──► [SaveImage]
```

Sample individual frames to verify quality before processing the full clip.
Ready workflow: `05_video_frame_sampler.json`

---

## Python Scripts (standalone, no ComfyUI needed)

```powershell
# Verify environment
python scripts/check_environment.py

# Upscale a still image
python scripts/upscale_image_rtx_vsr.py --input inputs/images/photo.jpg --output outputs/images/photo_4x.png --scale 4

# Upscale a video
python scripts/upscale_video_rtx_vsr.py --input inputs/videos/clip.mp4 --output outputs/videos/clip_4x.mp4 --scale 4

# Extract one frame and upscale it
python scripts/extract_frame_test.py --input inputs/videos/clip.mp4 --frame 10 --scale 4

# Run benchmark and generate report
python scripts/benchmark_rtx_vsr.py --scale 4
```

---

## Requirements

| Component | Minimum version |
|-----------|----------------|
| GPU | NVIDIA RTX (RTX 5090 recommended) |
| NVIDIA Driver (Windows) | ≥ 531 (≥ 570 for RTX 5090 / Blackwell) |
| Python | 3.10 / 3.11 / 3.12 |
| PyTorch | 2.1+ (CUDA build) |
| nvidia-vfx | Latest from pypi.nvidia.com |
| FFmpeg | Any recent version |

---

## Python Environment Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
python scripts/check_environment.py
```

→ Full setup guide: [setup_instructions.md](setup_instructions.md)

---

## Project Structure

```
nvidia-rtx-vsr-comfyui-toolkit/
  comfyui/
    install_nodes.ps1              ← auto-installer (Windows)
    install_nodes.sh               ← auto-installer (Linux / macOS)
    NODES.md                       ← complete node guide
    custom_nodes/
      rtx_vsr_single_frame_node/  ← our custom node
    workflows/
      examples/                    ← 7 ready-to-use workflows
        01_quick_4x_upscale.json
        02_before_after_preview.json
        03_2x_vs_4x_comparison.json
        04_denoise_then_upscale.json
        05_video_frame_sampler.json
        06_upscale_then_crop_tile.json
        07_ai_gen_image_enhance.json
        README.md

  scripts/                         ← standalone Python CLI
    check_environment.py
    upscale_image_rtx_vsr.py
    upscale_video_rtx_vsr.py
    extract_frame_test.py
    benchmark_rtx_vsr.py
    test_rtx_vsr.py

  inputs/   outputs/   docs/
```

---

## References

- [NVIDIA RTX Video SDK](https://developer.nvidia.com/rtx-video-sdk)
- [nvidia-vfx on PyPI (NVIDIA index)](https://pypi.org/project/nvidia-vfx/)
- [Nvidia_RTX_Nodes_ComfyUI (official)](https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI)
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)
- [Node guide](comfyui/NODES.md)
- [Troubleshooting](docs/troubleshooting.md)
