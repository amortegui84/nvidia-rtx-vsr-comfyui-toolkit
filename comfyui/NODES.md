# ComfyUI Node Installation Guide

---

## How ComfyUI nodes work

ComfyUI loads nodes from a specific folder inside **your ComfyUI installation**:

```
C:\ComfyUI\
  custom_nodes\        ← ComfyUI reads every folder here at startup
    some_node\
    another_node\
  models\
  output\
  main.py
```

To install a node you either:
- **`git clone` a repository** directly into `C:\ComfyUI\custom_nodes\`
- **Copy a folder** into `C:\ComfyUI\custom_nodes\`

**This project** (`nvidia-rtx-vsr-comfyui-toolkit`) is separate from ComfyUI.
It contains the source code for our custom node and the install scripts.
It is **not** where ComfyUI loads nodes from.

```
nvidia-rtx-vsr-comfyui-toolkit\     ← THIS project (source code)
  comfyui\
    custom_nodes\
      rtx_vsr_single_frame_node\    ← source of our node (not loaded by ComfyUI)
    install_nodes.ps1               ← copies/clones everything into real ComfyUI

C:\ComfyUI\                         ← your REAL ComfyUI installation
  custom_nodes\
    rtx_vsr_single_frame_node\      ← copied here by the installer
    Nvidia_RTX_Nodes_ComfyUI\       ← cloned here by the installer
    ComfyUI-VideoHelperSuite\       ← cloned here by the installer
```

---

## Automatic installation (recommended)

Run this from the root of this project. It does everything below automatically.

**Windows:**
```powershell
.\comfyui\install_nodes.ps1
```

**Linux / macOS:**
```bash
bash comfyui/install_nodes.sh
```

The script:
1. Finds your ComfyUI installation (or asks you for the path)
2. Clones `Nvidia_RTX_Nodes_ComfyUI` into `C:\ComfyUI\custom_nodes\`
3. Clones `ComfyUI-VideoHelperSuite` into `C:\ComfyUI\custom_nodes\`
4. Copies `rtx_vsr_single_frame_node` into `C:\ComfyUI\custom_nodes\`
5. Installs `nvidia-vfx`

---

## Manual installation — step by step

### Step 1 — Find your ComfyUI `custom_nodes` folder

Open your ComfyUI installation folder. You should see a `custom_nodes` subfolder:

```
C:\ComfyUI\custom_nodes\
```

Common locations:
```
C:\ComfyUI\custom_nodes\
C:\Users\YourName\ComfyUI\custom_nodes\
D:\ComfyUI\custom_nodes\
```

All `git clone` commands below go **inside this folder**.

---

### Step 2 — Install NVIDIA RTX Nodes (official)

This is the official NVIDIA node package published by Comfy-Org.

```powershell
cd C:\ComfyUI\custom_nodes

git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git

cd Nvidia_RTX_Nodes_ComfyUI
pip install -r requirements.txt
```

Result:
```
C:\ComfyUI\custom_nodes\
  Nvidia_RTX_Nodes_ComfyUI\    ← cloned here
    __init__.py
    requirements.txt
    nodes\
```

Nodes it adds to ComfyUI:
- `RTX Video Super Resolution` — upscales video
- `RTX Denoise` — removes noise before upscaling
- `RTX Artifact Reduction` — reduces compression artifacts

Where they appear in ComfyUI:
> Double-click canvas → search `RTX` → category **NVIDIA RTX**

---

### Step 3 — Install ComfyUI-VideoHelperSuite (VHS)

Required for any workflow that loads or exports video.

```powershell
cd C:\ComfyUI\custom_nodes

git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git

cd ComfyUI-VideoHelperSuite
pip install -r requirements.txt
```

Result:
```
C:\ComfyUI\custom_nodes\
  ComfyUI-VideoHelperSuite\    ← cloned here
    __init__.py
    requirements.txt
```

Nodes it adds:
- `VHS_LoadVideo` — loads a video file, outputs IMAGE batch
- `VHS_VideoCombine` — saves IMAGE batch back to video

---

### Step 4 — Install our custom node: RTX VSR Single Frame

This node lives in **this project** under `comfyui/custom_nodes/rtx_vsr_single_frame_node/`.
It needs to be **copied** into your ComfyUI `custom_nodes` folder.

```powershell
# Run from the root of this project
Copy-Item -Recurse `
  ".\comfyui\custom_nodes\rtx_vsr_single_frame_node" `
  "C:\ComfyUI\custom_nodes\rtx_vsr_single_frame_node"
```

Result:
```
C:\ComfyUI\custom_nodes\
  rtx_vsr_single_frame_node\    ← copied here
    __init__.py
    rtx_vsr_single_frame_node.py
    README.md
```

Node it adds:
- `RTX VSR Single Frame Upscale` — upscales a single image or frame

Where it appears in ComfyUI:
> Double-click canvas → search `RTX VSR` → category **NVIDIA RTX / Super Resolution**

Input / Output:

| Port | Type | Description |
|------|------|-------------|
| `image` (input) | IMAGE | Any ComfyUI image — photo, render, KSampler output |
| `scale_factor` | Widget | `4x` or `2x` |
| `upscaled_image` (output) | IMAGE | Upscaled result at the same tensor format |

---

### Step 5 — Install nvidia-vfx

This is the Python package that provides the RTX VSR engine.
It must be installed in the same Python environment that runs ComfyUI.

```powershell
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

If that fails:
```powershell
python -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

Verify:
```powershell
python -c "import nvvfx; print('OK')"
```

---

### Step 6 — Download the NVIDIA RTX VSR model files

`nvidia-vfx` provides the engine, but **the neural network model files are separate**.
They are distributed as part of the **NVIDIA Video Effects SDK**.

**Download the SDK:**
```
https://developer.nvidia.com/rtx-video-sdk
```

Run the installer. The model files are placed automatically at:
```
C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\
```

ComfyUI and the Python scripts find them there automatically.

**Custom location:** if you install to a different path, set this before launching ComfyUI:
```powershell
$env:NVVFX_SDK_PATH = "D:\NvVFX\models"
```

**Verify models are found:**
```powershell
python scripts/check_environment.py
```
Look for: `[PASS] NVVFX model directory`

---

### Step 7 — Restart ComfyUI

After installing nodes, **restart ComfyUI completely**. Nodes are only loaded at startup.

If a node appears **red** in the canvas after restarting, it means ComfyUI could
not import it. Check the ComfyUI terminal for the error message, then see
[docs/troubleshooting.md](../docs/troubleshooting.md).

---

## Final structure: what `custom_nodes` should look like

```
C:\ComfyUI\custom_nodes\
  Nvidia_RTX_Nodes_ComfyUI\          ← git clone (Step 2)
    __init__.py
    requirements.txt
    nodes\

  ComfyUI-VideoHelperSuite\          ← git clone (Step 3)
    __init__.py
    requirements.txt

  rtx_vsr_single_frame_node\         ← copied from this project (Step 4)
    __init__.py
    rtx_vsr_single_frame_node.py
    README.md
```

---

## Stable Diffusion checkpoint (workflow 07 only)

Workflow `07_ai_gen_image_enhance.json` generates an image with KSampler
before passing it to RTX VSR. It needs a Stable Diffusion checkpoint model.

**Where it goes** — inside your ComfyUI installation, NOT this project:
```
C:\ComfyUI\models\checkpoints\
  your_model.safetensors    ← place it here
```

**Where to download:**

| Source | URL |
|--------|-----|
| HuggingFace | https://huggingface.co/models |
| CivitAI | https://civitai.com |

Recommended starting models:

| Model | Size | Link |
|-------|------|------|
| SD 1.5 (pruned emaonly) | ~4 GB | https://huggingface.co/runwayml/stable-diffusion-v1-5 |
| SDXL Base 1.0 | ~7 GB | https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 |
| Flux.1 Dev | ~24 GB | https://huggingface.co/black-forest-labs/FLUX.1-dev |

**After downloading:**
1. Restart ComfyUI (or refresh model list).
2. Open workflow 07 and click `CheckpointLoaderSimple`.
3. Select your model filename from the dropdown.

---

## Node requirements per workflow

| Workflow | Required nodes | Required models |
|----------|---------------|-----------------|
| `01_quick_4x_upscale` | `rtx_vsr_single_frame_node` | NVIDIA VSR SDK |
| `02_before_after_preview` | `rtx_vsr_single_frame_node` | NVIDIA VSR SDK |
| `03_2x_vs_4x_comparison` | `rtx_vsr_single_frame_node` | NVIDIA VSR SDK |
| `04_denoise_then_upscale` | `rtx_vsr_single_frame_node` + `Nvidia_RTX_Nodes_ComfyUI` | NVIDIA VSR SDK |
| `05_video_frame_sampler` | `rtx_vsr_single_frame_node` + `ComfyUI-VideoHelperSuite` | NVIDIA VSR SDK |
| `06_upscale_then_crop` | `rtx_vsr_single_frame_node` | NVIDIA VSR SDK |
| `07_ai_gen_image_enhance` | `rtx_vsr_single_frame_node` | NVIDIA VSR SDK + SD checkpoint |

---

## Updating nodes

```powershell
cd C:\ComfyUI\custom_nodes\Nvidia_RTX_Nodes_ComfyUI
git pull

cd C:\ComfyUI\custom_nodes\ComfyUI-VideoHelperSuite
git pull
```

To update our custom node, re-run the installer or re-copy the folder
from this project.

---

## Verifying everything is working

At ComfyUI startup, the terminal should show:

```
Import success: Nvidia_RTX_Nodes_ComfyUI
Import success: ComfyUI-VideoHelperSuite
Import success: rtx_vsr_single_frame_node
```

If you see an import error for any node, check
[docs/troubleshooting.md](../docs/troubleshooting.md).
