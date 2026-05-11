# Model Files Guide

This toolkit uses two categories of models:

1. **NVIDIA RTX VSR models** — required by the `nvidia-vfx` SDK for all upscaling.
2. **Stable Diffusion checkpoint** — required only for workflow 07 (AI generation + VSR).

---

## 1. NVIDIA RTX VSR Models

### How the models are distributed

The NVIDIA Video Effects SDK ships its neural network model files as part of
the SDK installation. They are **not** inside `nvidia-vfx` itself — they are
installed separately, either:

- **Automatically** when the NVIDIA driver is installed (some versions include them).
- **Manually** by downloading and extracting the NVIDIA Video Effects SDK.

### Where the models live on disk

Default path on Windows:
```
C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\
```

The SDK looks for this path at runtime. If the models are missing, `vsr.load()`
will raise a `RuntimeError` with a message about missing model files.

### How to get the models

**Option A — NVIDIA Video Effects SDK download (recommended)**

1. Go to: https://developer.nvidia.com/rtx-video-sdk
2. Click **Download SDK**.
3. Run the installer — it places the model files in the default path above.
4. No further action needed; `nvidia-vfx` finds them automatically.

**Option B — Set a custom model path via environment variable**

If your models are in a different location, set `NVVFX_SDK_PATH` before
running any script or launching ComfyUI:

```powershell
# PowerShell — set for the current session
$env:NVVFX_SDK_PATH = "D:\NvVFX\models"

# Or set it permanently in Windows system environment variables
[System.Environment]::SetEnvironmentVariable("NVVFX_SDK_PATH", "D:\NvVFX\models", "User")
```

Then pass the path in Python if the API requires it:
```python
import os
import nvvfx

vsr = nvvfx.VideoSuperRes()
# Some builds accept a model_dir parameter:
# vsr.model_dir = os.environ.get("NVVFX_SDK_PATH", r"C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models")
vsr.load()
```

**Option C — Auto-download on first `load()` call**

Some builds of `nvidia-vfx` automatically download the model files the first
time `vsr.load()` is called. This requires an internet connection. A progress
message is printed to the console. If download fails, you will see a
`RuntimeError` — fall back to Option A.

### Verifying the models are present

```powershell
python scripts/check_environment.py
```

The environment check reports whether the NVVFX model directory is found.

---

## 2. Stable Diffusion Checkpoint (workflow 07 only)

Workflow `07_ai_gen_image_enhance.json` uses a standard ComfyUI KSampler to
generate an image before passing it to RTX VSR. It requires a Stable Diffusion
checkpoint model.

### Where to place it

```
ComfyUI\
  models\
    checkpoints\       ← place your .safetensors or .ckpt file here
      my_model.safetensors
```

### Where to download checkpoints

| Source | URL | Notes |
|--------|-----|-------|
| HuggingFace | https://huggingface.co/models | Filter by "text-to-image" |
| CivitAI | https://civitai.com | Large community model library |
| Stability AI | https://stability.ai/stable-image | Official SD models |

**Recommended starting points:**

| Model | Type | Size | Download |
|-------|------|------|---------|
| SD 1.5 (pruned) | SD 1.5 | ~4 GB | [HuggingFace](https://huggingface.co/runwayml/stable-diffusion-v1-5) |
| SDXL Base 1.0 | SDXL | ~7 GB | [HuggingFace](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) |
| Flux.1 Dev | Flux | ~24 GB | [HuggingFace](https://huggingface.co/black-forest-labs/FLUX.1-dev) |

### Connecting the model in workflow 07

After placing the file in `ComfyUI/models/checkpoints/`:

1. Open `07_ai_gen_image_enhance.json` in ComfyUI.
2. Click the `CheckpointLoaderSimple` node.
3. In the dropdown, select your model filename.
4. Queue Prompt.

---

## Model directory structure (complete reference)

```
ComfyUI\
  models\
    checkpoints\           ← SD / SDXL / Flux models (workflow 07)
    clip\                  ← CLIP text encoders (auto-loaded by checkpoint)
    vae\                   ← VAE models (optional override)
    upscale_models\        ← ESRGAN / 4x models (not used by RTX VSR)

C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\
  models\                  ← NVIDIA RTX VSR model files (auto-detected)
    SuperRes_CG_2x.nvmdl   ← 2x super resolution model (example filename)
    SuperRes_CG_4x.nvmdl   ← 4x super resolution model (example filename)
```

> **Note:** The exact NVIDIA model filenames depend on the SDK version installed.
> You do not need to know the filenames — `nvvfx` finds them automatically
> from the SDK path.

---

## Troubleshooting model issues

| Symptom | Fix |
|---------|-----|
| `RuntimeError: model file not found` | Download the NVIDIA Video Effects SDK from https://developer.nvidia.com/rtx-video-sdk |
| `RuntimeError: NVVFX_SDK_PATH not set` | Set `NVVFX_SDK_PATH` to the folder containing the model files |
| Checkpoint not visible in ComfyUI dropdown | Refresh the model list or restart ComfyUI; confirm file is in `models/checkpoints/` |
| `load()` hangs on first run | Models may be downloading; wait for completion and check console |
| Wrong model filename in workflow 07 | Click `CheckpointLoaderSimple` and select the correct file from the dropdown |
