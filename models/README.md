# models/

This folder is a reference placeholder. Model files are not stored here.

---

## NVIDIA RTX VSR Models

The NVIDIA RTX VSR model files are installed by the **NVIDIA Video Effects SDK**,
not placed here manually.

**Download the SDK:**
https://developer.nvidia.com/rtx-video-sdk

After installing, the models are placed automatically at:
```
C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\
```

The `nvidia-vfx` Python package finds them there automatically.
If your models are in a different location, set the environment variable:

```powershell
$env:NVVFX_SDK_PATH = "D:\path\to\your\models"
```

---

## Stable Diffusion Checkpoints (workflow 07 only)

SD/SDXL/Flux checkpoints go into your **ComfyUI** installation, not here:

```
ComfyUI\models\checkpoints\your_model.safetensors
```

Download from:
- https://huggingface.co/models
- https://civitai.com

---

See [docs/models.md](../docs/models.md) for the complete model guide.
