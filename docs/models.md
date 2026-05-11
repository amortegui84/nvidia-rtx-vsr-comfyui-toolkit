# Model Files Guide

Everything stays inside your ComfyUI installation.
No need to touch system directories or Program Files.

---

## NVIDIA RTX VSR Model Files

### Where they go

```
ComfyUI_windows_portable\
  ComfyUI\
    models\
      nvidia_vsr\          ← place the NVIDIA VSR model files here
        SuperRes_CG_2x.nvmdl
        SuperRes_CG_4x.nvmdl
        (other .nvmdl / .bin files from the SDK)
```

Our custom node registers `nvidia_vsr` as a model type inside ComfyUI
and looks there first — before checking any system path.

---

### How to get the model files

**Step 1 — Download the NVIDIA Video Effects SDK:**
```
https://developer.nvidia.com/rtx-video-sdk
```

**Step 2 — Run the installer.**
The installer places the model files at:
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

Or copy manually — open the folder and drag the files across.

**Step 4 — Verify:**
```powershell
python scripts\check_environment.py
```
Look for: `[PASS] NVVFX model directory`

---

### How the node finds the models

The node checks these locations in order and uses the first one that
contains model files:

| Priority | Path | When to use |
|----------|------|-------------|
| 1st | `ComfyUI\models\nvidia_vsr\` | Recommended — everything in ComfyUI |
| 2nd | `NVVFX_SDK_PATH` env var | Custom/override path |
| 3rd | `C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\` | SDK default fallback |

If models are found in `ComfyUI\models\nvidia_vsr\`, the node uses them
directly and the Program Files path is never touched.

---

### Custom model path (optional)

If you keep your models somewhere else, set the environment variable
before launching ComfyUI:

```powershell
$env:NVVFX_SDK_PATH = "D:\MyModels\nvidia_vsr"
```

---

## Stable Diffusion Checkpoint (workflow 07 only)

Workflow `07_ai_gen_image_enhance.json` uses a KSampler node and requires
a Stable Diffusion checkpoint.

**Where it goes:**
```
ComfyUI_windows_portable\
  ComfyUI\
    models\
      checkpoints\
        your_model.safetensors    ← place it here
```

**Where to download:**

| Source | URL |
|--------|-----|
| HuggingFace | https://huggingface.co/models |
| CivitAI | https://civitai.com |

Recommended models:

| Model | Size | Link |
|-------|------|------|
| SD 1.5 pruned emaonly | ~4 GB | https://huggingface.co/runwayml/stable-diffusion-v1-5 |
| SDXL Base 1.0 | ~7 GB | https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 |
| Flux.1 Dev | ~24 GB | https://huggingface.co/black-forest-labs/FLUX.1-dev |

**After downloading:**
1. Restart ComfyUI (or refresh model list).
2. Open workflow 07, click `CheckpointLoaderSimple`, select your model.

---

## Complete models folder structure

```
ComfyUI_windows_portable\ComfyUI\models\
  nvidia_vsr\               ← NVIDIA RTX VSR model files (all workflows)
    SuperRes_CG_2x.nvmdl
    SuperRes_CG_4x.nvmdl
  checkpoints\              ← SD / SDXL / Flux (workflow 07 only)
    your_model.safetensors
  vae\                      ← optional VAE override
  loras\                    ← LoRA files
  upscale_models\           ← ESRGAN models (not used by RTX VSR)
```
