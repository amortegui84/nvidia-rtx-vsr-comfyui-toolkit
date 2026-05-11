# Setup Instructions

## Windows (Primary Platform)

Tested on Windows 11 with RTX 5090 (Blackwell) and driver 570+.

---

### Prerequisites

Before starting, ensure:

- [ ] NVIDIA driver ≥ 570 installed (for RTX 5090 / Blackwell)
  - Verify: `nvidia-smi` → check driver version in output
  - Download: https://www.nvidia.com/Download/index.aspx
- [ ] Python 3.10, 3.11, or 3.12 installed
  - Verify: `python --version`
  - Download: https://www.python.org/downloads/
- [ ] Git installed (for cloning ComfyUI nodes)
  - Verify: `git --version`
  - Download: https://git-scm.com/download/win
- [ ] FFmpeg installed and on PATH
  - Verify: `ffmpeg -version`
  - Install via winget: `winget install Gyan.FFmpeg`
  - Or download from: https://ffmpeg.org/download.html → Windows builds (gyan.dev)

---

### Step 1 — Clone or copy the project

If you have this project as a folder already, navigate to it:

```powershell
cd C:\path\to\nvidia-rtx-vsr-comfyui-toolkit
```

If you are setting up from a fresh clone:

```powershell
git clone https://github.com/amortegui84/nvidia-rtx-vsr-comfyui-toolkit
cd nvidia-rtx-vsr-comfyui-toolkit
```

---

### Step 2 — Create a Python virtual environment

```powershell
python -m venv .venv
```

---

### Step 3 — Activate the virtual environment

**PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

If you get a script execution policy error:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

**Command Prompt (alternative):**
```cmd
.venv\Scripts\activate.bat
```

You should see `(.venv)` at the start of your prompt.

---

### Step 4 — Install PyTorch (CUDA build)

Find your CUDA version:
```powershell
nvidia-smi | Select-String "CUDA Version"
```

Install the matching PyTorch build:

```powershell
# CUDA 12.8 (RTX 5090 / Blackwell)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# CUDA 12.4 (older RTX GPUs)
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# CUDA 12.1
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Verify CUDA is available:
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0))"
```

---

### Step 5 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

---

### Step 6 — Install nvidia-vfx

```powershell
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

**If the above fails**, try:
```powershell
python -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

**If build errors occur**, install build tools first:
```powershell
pip install setuptools wheel
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

Verify installation:
```powershell
python -c "import nvvfx; print('nvvfx available:', dir(nvvfx))"
```

---

### Step 7 — Verify FFmpeg

```powershell
ffmpeg -version
ffprobe -version
```

Both commands should print version information. If not, revisit the FFmpeg
installation in Prerequisites.

---

### Step 8 — Run environment check

```powershell
python scripts/check_environment.py
```

Expected output: all critical checks should show `[PASS]`.

If any check fails, see [docs/troubleshooting.md](docs/troubleshooting.md).

---

### Step 9 — First image test

Place a test image in `inputs/images/`. Any JPG, PNG, or WEBP will work.

```powershell
python scripts/upscale_image_rtx_vsr.py `
  --input  inputs/images/test_image.jpg `
  --output outputs/images/test_image_rtx_vsr_4x.png `
  --scale  4
```

Check `outputs/images/` for the result.

If you don't have a test image, the smoke test script creates one:
```powershell
python scripts/test_rtx_vsr.py
```

---

### Step 10 — First video test

Place a short test video (a few seconds is enough) in `inputs/videos/`.

```powershell
python scripts/upscale_video_rtx_vsr.py `
  --input  inputs/videos/test_video.mp4 `
  --output outputs/videos/test_video_rtx_vsr_4x.mp4 `
  --scale  4
```

Check `outputs/videos/` for the result.

---

### Step 11 — ComfyUI Setup (optional)

#### Install official NVIDIA RTX Nodes

```powershell
cd C:\path\to\ComfyUI\custom_nodes
git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI
cd Nvidia_RTX_Nodes_ComfyUI
pip install -r requirements.txt
```

#### Install our custom single-frame node

Copy:
```
nvidia-rtx-vsr-comfyui-toolkit\comfyui\custom_nodes\rtx_vsr_single_frame_node\
```
→ into →
```
ComfyUI\custom_nodes\rtx_vsr_single_frame_node\
```

Restart ComfyUI. Open one of the workflow JSONs from `comfyui/workflows/`.

---

### Step 12 — Run benchmark

```powershell
python scripts/benchmark_rtx_vsr.py --scale 4
```

Results: `outputs/benchmarks/benchmark_results.md`

---

## Linux (Secondary Platform)

The scripts are cross-platform. Linux setup follows the same steps with
minor command differences.

### Prerequisites

```bash
# NVIDIA driver >= 525 (>= 570 for Blackwell)
nvidia-smi

# FFmpeg
sudo apt install ffmpeg        # Debian/Ubuntu
sudo dnf install ffmpeg        # Fedora

# Python 3.10+
python3 --version
```

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate

# CUDA 12.8 build
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

pip install -r requirements.txt

pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com

python scripts/check_environment.py
```

Script invocations are identical to Windows (use `\` instead of `` ` ``
for line continuation in bash).

---

## Environment Deactivation

When done:

```powershell
deactivate
```

---

## Keeping Dependencies Updated

```powershell
pip install -U -r requirements.txt
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

After any NVIDIA driver update, reinstall `nvidia-vfx` to ensure
the correct CUDA runtime bindings are used.
