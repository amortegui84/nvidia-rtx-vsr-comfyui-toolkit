# Troubleshooting Guide

---

## nvidia-vfx Install Failure

**Symptom**: `pip install nvidia-vfx` returns "No matching distribution found"
or a build error.

**Fix A** — Use the correct index URL:
```bash
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

**Fix B** — If Fix A fails, try the python -m variant:
```bash
python -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

**Fix C** — If build isolation is the issue, ensure build tools are installed:
```bash
pip install setuptools wheel
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

**Fix D** — Check Python version. `nvidia-vfx` may require Python 3.10 or 3.11.
Try: `python --version` and use a compatible version.

---

## Driver Mismatch

**Symptom**: `nvvfx.VideoSuperRes()` raises `RuntimeError: CUDA driver version
is insufficient` or similar.

**Fix**: Update your NVIDIA driver.
- RTX VSR requires driver **≥ 531** on Windows.
- For RTX 5090 (Blackwell): driver **≥ 570** recommended.
- Download from: https://www.nvidia.com/Download/index.aspx

Check current driver:
```bash
nvidia-smi --query-gpu=driver_version --format=csv,noheader
```

---

## CUDA Unavailable

**Symptom**: `torch.cuda.is_available()` returns `False`.

**Causes & Fixes**:

1. PyTorch CPU build installed:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
   ```
   (Replace `cu124` with your CUDA version, e.g. `cu121`, `cu128`)

2. NVIDIA driver not installed or too old → update driver.

3. Running in a virtualenv that does not see the GPU:
   Activate your venv and re-run `python -c "import torch; print(torch.cuda.is_available())"`.

4. WDDM vs TCC mode (Windows): RTX GPUs default to WDDM which supports CUDA.
   No change needed on desktop Windows.

---

## FFmpeg Missing

**Symptom**: `FileNotFoundError: ffmpeg not found` or
`shutil.which("ffmpeg")` returns `None`.

**Fix — Windows**:

Option A (winget):
```powershell
winget install Gyan.FFmpeg
```
Then restart terminal so PATH is updated.

Option B (manual):
1. Download from https://ffmpeg.org/download.html (Windows builds → gyan.dev)
2. Extract to `C:\ffmpeg\`
3. Add `C:\ffmpeg\bin` to your system PATH.
4. Verify: `ffmpeg -version`

---

## Unsupported Image Format

**Symptom**: `[ERROR] Unsupported format '.tiff'`

**Fix**: Convert your image to JPG, PNG, or WEBP before passing to the scripts:
```python
from PIL import Image
Image.open("input.tiff").convert("RGB").save("input.png")
```

---

## ComfyUI Custom Node Not Appearing

**Symptom**: The "RTX VSR Single Frame Upscale" node is not visible in ComfyUI.

**Checklist**:
1. Confirm the folder `rtx_vsr_single_frame_node/` is inside
   `ComfyUI/custom_nodes/` (not nested an extra level deeper).
2. Confirm `__init__.py` exists in that folder.
3. Check ComfyUI startup console for import errors.
4. Ensure `nvidia-vfx` is installed in the **same Python environment** that
   runs ComfyUI (not a different venv).
5. Restart ComfyUI completely.

If there is an import error in `__init__.py`, ComfyUI may silently skip the
node. Check `ComfyUI/comfy.log` or the terminal output for traceback lines
mentioning `rtx_vsr_single_frame_node`.

---

## DLPack / Tensor Copy Issues

**Symptom**: Second frame comes out identical to the first, or corrupted.

**Cause**: The DLPack buffer backing `vsr.output` was overwritten before it
was copied.

**Fix**: Always call `.clone()` immediately after `vsr.run()`:
```python
vsr.run()
output = vsr.output.clone()  # DO NOT skip this
```

---

## Out of Memory (OOM)

**Symptom**: `torch.cuda.OutOfMemoryError` or `RuntimeError: CUDA out of memory`.

**Fixes**:
1. Use `--scale 2` instead of `--scale 4`.
2. Reduce input resolution before upscaling.
3. For video: process shorter clips or lower-resolution clips first.
4. Check what else is using VRAM:
   ```bash
   nvidia-smi
   ```
   Close other GPU-intensive applications (games, other AI tools).
5. On RTX 5090 (32 GB VRAM), OOM during 4x upscaling is unlikely unless
   input frames are very large (e.g. > 8K).

---

## RTX Node Not Available in ComfyUI (Official NVIDIA Node)

**Symptom**: NVIDIA RTX Nodes are not visible after installing.

**Fix**:
1. Clone into the correct location:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI
   ```
2. Install requirements:
   ```bash
   cd Nvidia_RTX_Nodes_ComfyUI
   pip install -r requirements.txt
   ```
3. Follow any additional setup in the repo's own README.
4. Restart ComfyUI.

---

## Blackwell / RTX 5090 Driver Compatibility

**Symptom**: Scripts work on older RTX cards but not on the RTX 5090.

**Cause**: Blackwell requires newer CUDA (12.8+) and driver (570+).

**Fix**:
1. Ensure driver ≥ 570 is installed.
2. Reinstall PyTorch with CUDA 12.8 support:
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
   ```
3. Reinstall `nvidia-vfx` after updating driver and CUDA.
4. Check CUDA compute capability: Blackwell is `10.0`.
   If your torch build does not support it, you may get
   "no kernel image available for execution on device" errors.

---

## "VideoSuperRes" Symbol Not Found in nvvfx

**Symptom**: `AttributeError: module 'nvvfx' has no attribute 'VideoSuperRes'`

**Fix**: Check your installed version with `python -c "import nvvfx; print(dir(nvvfx))"`.
The class name may differ in older builds. Common variants:
- `nvvfx.VideoSuperRes`
- `nvvfx.VideoSuperResolution`
- `nvvfx.UpscaleEffect`

Update the import in `scripts/` and `comfyui/custom_nodes/` accordingly, and
check the NVIDIA Video Effects SDK release notes for your version.

---

## Slow Performance / Low FPS

**Expected throughput on RTX 5090 at 4x**:
- 1080p → 4K: roughly 30–60+ frames/s (real-time or faster)
- 4K → 16K: significantly slower

**If performance is unexpectedly low**:
1. Confirm GPU is being used (not CPU fallback).
2. Check GPU clock speed: `nvidia-smi dmon`.
3. Ensure no power limit is applied: `nvidia-smi -q -d POWER`.
4. Profile with `torch.cuda.synchronize()` around the `vsr.run()` call
   for accurate timing.
