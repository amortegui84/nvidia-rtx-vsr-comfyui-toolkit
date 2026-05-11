# ComfyUI Node Guide — NVIDIA RTX VSR Toolkit

This guide covers every node required by this toolkit: what it does,
how to install it, and where it appears in ComfyUI.

---

## Automatic installation (recommended)

Run the installer script from the project root:

**Windows (PowerShell):**
```powershell
.\comfyui\install_nodes.ps1
```

**Linux / macOS:**
```bash
bash comfyui/install_nodes.sh
```

The script auto-detects your ComfyUI installation, clones all required
repos, copies our custom node, and installs `nvidia-vfx`.

---

## Manual installation — step by step

### Step 1 — Find your `custom_nodes` folder

This is where ComfyUI loads all additional nodes.
It lives inside your ComfyUI installation:

```
ComfyUI/
  custom_nodes/    ← all nodes go here
  models/
  output/
  ...
```

Common paths on Windows:
```
C:\ComfyUI\custom_nodes\
C:\Users\YourName\ComfyUI\custom_nodes\
```

---

### Step 2 — Official NVIDIA RTX Nodes for ComfyUI

**Repository:** https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI

**What it includes:**
- `RTX Video Super Resolution` — full video upscaling
- `RTX Denoise` — hardware-accelerated noise removal
- `RTX Artifact Reduction` — reduces compression artifacts

**Install:**
```powershell
cd C:\ComfyUI\custom_nodes
git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git
cd Nvidia_RTX_Nodes_ComfyUI
pip install -r requirements.txt
```

**Where it appears in ComfyUI:**
> Double-click canvas → search `RTX` → category **NVIDIA RTX**

---

### Step 3 — Our custom node: RTX VSR Single Frame

**What it does:** Upscales individual images and frames with RTX VSR.
Designed for static images and AI-generated outputs (SD, SDXL, Flux).

**Install — copy the folder:**

```powershell
# From the project root
Copy-Item -Recurse `
  ".\comfyui\custom_nodes\rtx_vsr_single_frame_node" `
  "C:\ComfyUI\custom_nodes\rtx_vsr_single_frame_node"
```

Or copy manually — the destination must look like this:
```
C:\ComfyUI\custom_nodes\rtx_vsr_single_frame_node\
  __init__.py
  rtx_vsr_single_frame_node.py
  README.md
```

**Where it appears in ComfyUI:**
> Double-click canvas → search `RTX VSR`
> Category: **NVIDIA RTX / Super Resolution**
> Node name: **RTX VSR Single Frame Upscale**

**Inputs / Outputs:**

| Port | Type | Description |
|------|------|-------------|
| `image` (input) | IMAGE | Standard ComfyUI image tensor `(B, H, W, C)` |
| `scale_factor` | Widget | `4x` or `2x` |
| `upscaled_image` (output) | IMAGE | Upscaled image `(1, H×scale, W×scale, C)` |

---

### Step 4 — ComfyUI-VideoHelperSuite (VHS)

Required for any workflow that loads or saves video.

**Repository:** https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite

**Install:**
```powershell
cd C:\ComfyUI\custom_nodes
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
cd ComfyUI-VideoHelperSuite
pip install -r requirements.txt
```

**Nodes it adds:**
- `VHS_LoadVideo` — load video from file, outputs IMAGE batch
- `VHS_VideoCombine` — save IMAGE batch as video file
- `VHS_GetLatentCount` — batch info

---

### Step 5 — Install nvidia-vfx

```powershell
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

If that fails:
```powershell
python -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

Verify:
```powershell
python -c "import nvvfx; print('OK:', dir(nvvfx))"
```

---

### Step 6 — Restart ComfyUI

After installing any node, **always restart ComfyUI fully**.
Nodes are only loaded at startup.

If a node appears **red** after restarting:
→ See [docs/troubleshooting.md](../docs/troubleshooting.md) — "ComfyUI custom node not appearing".

---

## Expected `custom_nodes/` structure

```
C:\ComfyUI\custom_nodes\
  Nvidia_RTX_Nodes_ComfyUI\          ← official NVIDIA nodes
    __init__.py
    requirements.txt
    nodes\
      ...
  ComfyUI-VideoHelperSuite\          ← video load / save
    __init__.py
    requirements.txt
    ...
  rtx_vsr_single_frame_node\         ← our custom node
    __init__.py
    rtx_vsr_single_frame_node.py
    README.md
```

---

## Node requirements per workflow

| Workflow | Required nodes |
|----------|---------------|
| `01_quick_4x_upscale` | `rtx_vsr_single_frame_node` |
| `02_before_after_preview` | `rtx_vsr_single_frame_node` |
| `03_2x_vs_4x_comparison` | `rtx_vsr_single_frame_node` |
| `04_denoise_then_upscale` | `rtx_vsr_single_frame_node` + `Nvidia_RTX_Nodes_ComfyUI` |
| `05_video_frame_sampler` | `rtx_vsr_single_frame_node` + `ComfyUI-VideoHelperSuite` |
| `06_upscale_then_crop` | `rtx_vsr_single_frame_node` |
| `07_ai_gen_image_enhance` | `rtx_vsr_single_frame_node` + any SD checkpoint |

---

## Updating nodes

To update a cloned node:

```powershell
cd C:\ComfyUI\custom_nodes\Nvidia_RTX_Nodes_ComfyUI
git pull

cd C:\ComfyUI\custom_nodes\ComfyUI-VideoHelperSuite
git pull
```

To update our custom node, re-copy the `rtx_vsr_single_frame_node` folder
from this repository, or re-run `install_nodes.ps1`.

---

## Verifying nodes loaded correctly

In the terminal where ComfyUI runs, at startup you should see lines like:

```
[RTX VSR Node] Loading RTX VSR Single Frame Node...
Import success: Nvidia_RTX_Nodes_ComfyUI
Import success: ComfyUI-VideoHelperSuite
```

If you see an import error, check [docs/troubleshooting.md](../docs/troubleshooting.md).
