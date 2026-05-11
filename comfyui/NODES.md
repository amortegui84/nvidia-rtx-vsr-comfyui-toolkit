# ComfyUI Node Installation Guide

---

## How ComfyUI loads nodes

ComfyUI loads every subfolder inside its `custom_nodes` directory at startup.

**Windows portable path** (most common setup):
```
ComfyUI_windows_portable\
  ComfyUI\
    custom_nodes\    ← all nodes go here
    models\
      checkpoints\
      vae\
      loras\
    output\
    main.py
  python_embeded\
  run_nvidia_gpu.bat
```

There are two ways to install a node:
1. **ComfyUI Manager** — the built-in GUI installer (recommended for official nodes)
2. **Manual git clone** — paste a command, node is ready immediately

---

## Method 1 — ComfyUI Manager (recommended for official nodes)

ComfyUI Manager is bundled with ComfyUI. It lets you search, install, and
update nodes without touching the terminal.

### Install NVIDIA RTX Nodes via Manager

1. Launch ComfyUI.
2. Click **Manager** in the top menu bar.
3. Click **Install Custom Nodes**.
4. Search: `RTX`
5. Find **Nvidia RTX Nodes** → click **Install**.
6. Restart ComfyUI when prompted.

### Install ComfyUI-VideoHelperSuite via Manager

1. Open Manager → **Install Custom Nodes**.
2. Search: `VideoHelperSuite` or `VHS`.
3. Click **Install** → restart ComfyUI.

> If ComfyUI Manager is not available, install it first:
> ```powershell
> cd ComfyUI_windows_portable\ComfyUI\custom_nodes
> git clone https://github.com/ltdrdata/ComfyUI-Manager.git
> ```
> Then restart ComfyUI.

---

## Method 2 — Manual git clone

Open a terminal and navigate to your `custom_nodes` folder first:

```powershell
cd ComfyUI_windows_portable\ComfyUI\custom_nodes
```

### Clone NVIDIA RTX Nodes

```powershell
git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git
```

Install its requirements using the **embedded Python** that comes with the portable:

```powershell
..\..\..\python_embeded\python.exe -m pip install -r Nvidia_RTX_Nodes_ComfyUI\requirements.txt
```

Result:
```
ComfyUI_windows_portable\ComfyUI\custom_nodes\
  Nvidia_RTX_Nodes_ComfyUI\    ← cloned here
    __init__.py
    requirements.txt
    nodes\
```

---

### Clone ComfyUI-VideoHelperSuite

```powershell
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
```

```powershell
..\..\..\python_embeded\python.exe -m pip install -r ComfyUI-VideoHelperSuite\requirements.txt
```

Result:
```
ComfyUI_windows_portable\ComfyUI\custom_nodes\
  ComfyUI-VideoHelperSuite\    ← cloned here
    __init__.py
    requirements.txt
```

---

### Install our custom node: RTX VSR Single Frame

This node is included in this project under `comfyui/custom_nodes/rtx_vsr_single_frame_node/`.
Copy it into your ComfyUI `custom_nodes` folder:

```powershell
# Run from the root of this project
Copy-Item -Recurse `
  ".\comfyui\custom_nodes\rtx_vsr_single_frame_node" `
  "ComfyUI_windows_portable\ComfyUI\custom_nodes\rtx_vsr_single_frame_node"
```

Result:
```
ComfyUI_windows_portable\ComfyUI\custom_nodes\
  rtx_vsr_single_frame_node\    ← copied here
    __init__.py
    rtx_vsr_single_frame_node.py
    README.md
```

> **Note:** This node is not on ComfyUI Manager. It must be copied manually
> or installed via the `install_nodes.ps1` script.

---

### Install nvidia-vfx

Install into the **embedded Python** that comes with the ComfyUI portable:

```powershell
ComfyUI_windows_portable\python_embeded\python.exe -m pip install `
  -U --no-build-isolation nvidia-vfx `
  --index-url https://pypi.nvidia.com
```

Verify:
```powershell
ComfyUI_windows_portable\python_embeded\python.exe -c "import nvvfx; print('OK')"
```

---

## After installation — restart ComfyUI

Always restart ComfyUI after installing nodes.
Nodes only load at startup.

If a node appears **red** on the canvas after restarting, ComfyUI could not
import it. Read the error in the terminal and check
[docs/troubleshooting.md](../docs/troubleshooting.md).

---

## Final custom_nodes structure

```
ComfyUI_windows_portable\ComfyUI\custom_nodes\
  Nvidia_RTX_Nodes_ComfyUI\          ← via Manager or git clone
  ComfyUI-VideoHelperSuite\          ← via Manager or git clone
  rtx_vsr_single_frame_node\         ← copied from this project
```

---

## Where to find nodes in ComfyUI

After installation and restart:

| Node | Search term | Category |
|------|-------------|----------|
| RTX VSR Single Frame Upscale | `RTX VSR` | NVIDIA RTX / Super Resolution |
| RTX Video Super Resolution | `RTX Video` | NVIDIA RTX |
| RTX Denoise | `RTX Denoise` | NVIDIA RTX |
| VHS Load Video | `VHS` or `Load Video` | Video Helper Suite 🎥 |
| VHS Video Combine | `VHS` or `Video Combine` | Video Helper Suite 🎥 |

---

## Models

### NVIDIA RTX VSR model files

All model files live **inside your ComfyUI folder** — no system directories needed:

```
ComfyUI_windows_portable\ComfyUI\models\
  nvidia_vsr\              ← NVIDIA VSR model files go here
    SuperRes_CG_2x.nvmdl
    SuperRes_CG_4x.nvmdl
    (other .nvmdl / .bin files from the SDK)
```

Our node registers `nvidia_vsr` as a model type inside ComfyUI and checks
that folder first automatically.

**Step 1 — Download the NVIDIA Video Effects SDK:**
```
https://developer.nvidia.com/rtx-video-sdk
```

**Step 2 — Run the SDK installer.**
Models land at:
```
C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\
```

**Step 3 — Copy the model files into ComfyUI:**
```powershell
Copy-Item `
  "C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\*" `
  "ComfyUI_windows_portable\ComfyUI\models\nvidia_vsr\" `
  -Recurse
```

**Step 4 — Verify:**
```powershell
ComfyUI_windows_portable\python_embeded\python.exe scripts\check_environment.py
```
Look for: `[PASS] NVVFX model directory`

The node searches in this order:
| Priority | Path |
|----------|------|
| 1st | `ComfyUI\models\nvidia_vsr\` — everything inside ComfyUI |
| 2nd | `NVVFX_SDK_PATH` env var — custom override |
| 3rd | `C:\Program Files\NVIDIA Corporation\...` — SDK fallback |

---

### Stable Diffusion checkpoint (workflow 07 only)

```
ComfyUI_windows_portable\ComfyUI\models\checkpoints\
  your_model.safetensors    ← place it here
```

Download from [HuggingFace](https://huggingface.co/models) or [CivitAI](https://civitai.com).

| Model | Size | Link |
|-------|------|------|
| SD 1.5 pruned emaonly | ~4 GB | https://huggingface.co/runwayml/stable-diffusion-v1-5 |
| SDXL Base 1.0 | ~7 GB | https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 |
| Flux.1 Dev | ~24 GB | https://huggingface.co/black-forest-labs/FLUX.1-dev |

After placing the file: restart ComfyUI → click `CheckpointLoaderSimple` → select your model.

→ Full model guide: [docs/models.md](../docs/models.md)

---

## Node + model requirements per workflow

| Workflow | Nodes needed | Models needed |
|----------|-------------|---------------|
| `01_quick_4x_upscale` | `rtx_vsr_single_frame_node` | `ComfyUI\models\nvidia_vsr\` |
| `02_before_after_preview` | `rtx_vsr_single_frame_node` | `ComfyUI\models\nvidia_vsr\` |
| `03_2x_vs_4x_comparison` | `rtx_vsr_single_frame_node` | `ComfyUI\models\nvidia_vsr\` |
| `04_denoise_then_upscale` | `rtx_vsr_single_frame_node` + `Nvidia_RTX_Nodes_ComfyUI` | `ComfyUI\models\nvidia_vsr\` |
| `05_video_frame_sampler` | `rtx_vsr_single_frame_node` + `ComfyUI-VideoHelperSuite` | `ComfyUI\models\nvidia_vsr\` |
| `06_upscale_then_crop` | `rtx_vsr_single_frame_node` | `ComfyUI\models\nvidia_vsr\` |
| `07_ai_gen_image_enhance` | `rtx_vsr_single_frame_node` | `ComfyUI\models\nvidia_vsr\` + SD checkpoint |

---

## Updating nodes

**Via ComfyUI Manager:**
Open Manager → **Update All** or update each node individually.

**Via git:**
```powershell
cd ComfyUI_windows_portable\ComfyUI\custom_nodes\Nvidia_RTX_Nodes_ComfyUI
git pull

cd ..\ComfyUI-VideoHelperSuite
git pull
```

To update our custom node, re-copy `rtx_vsr_single_frame_node` from this project
or re-run `.\comfyui\install_nodes.ps1`.
