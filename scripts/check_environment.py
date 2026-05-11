"""
check_environment.py
--------------------
Validates that the local environment meets all requirements for
NVIDIA RTX Video Super Resolution workflows.

Run from the project root:
    python scripts/check_environment.py
"""

import sys
import os
import platform
import subprocess
import shutil
import textwrap


# ── ANSI colours (Windows 10+ supports these) ─────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

PASS = f"{GREEN}[PASS]{RESET}"
WARN = f"{YELLOW}[WARN]{RESET}"
FAIL = f"{RED}[FAIL]{RESET}"
INFO = f"[INFO]"


def section(title: str) -> None:
    print(f"\n{BOLD}{'─' * 60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'─' * 60}{RESET}")


# ── Individual checks ─────────────────────────────────────────────────────────

def check_python() -> bool:
    v = sys.version_info
    ok = v >= (3, 10)
    tag = PASS if ok else FAIL
    print(f"{tag}  Python {sys.version}")
    if not ok:
        print(f"       Python 3.10+ required.")
    return ok


def check_platform() -> None:
    print(f"{INFO}  OS      : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"{INFO}  Arch    : {platform.processor() or 'unknown'}")


def check_torch() -> bool:
    try:
        import torch
        print(f"{PASS}  PyTorch {torch.__version__}")
        return True
    except ImportError:
        print(f"{FAIL}  PyTorch not installed.")
        print(f"       Fix: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124")
        return False


def check_cuda() -> bool:
    try:
        import torch
        if torch.cuda.is_available():
            count = torch.cuda.device_count()
            for i in range(count):
                name = torch.cuda.get_device_name(i)
                props = torch.cuda.get_device_properties(i)
                vram_gb = props.total_memory / (1024 ** 3)
                print(f"{PASS}  CUDA GPU {i}: {name} ({vram_gb:.1f} GB VRAM)")
                if "5090" in name:
                    print(f"       RTX 5090 (Blackwell) detected — full VSR support expected.")
                elif "RTX" not in name:
                    print(f"{WARN}  GPU does not appear to be an RTX card. RTX VSR requires an RTX-series GPU.")
            cap = torch.cuda.get_device_capability(0)
            print(f"{INFO}  Compute capability: {cap[0]}.{cap[1]}")
            return True
        else:
            print(f"{FAIL}  CUDA is not available to PyTorch.")
            print(f"       Ensure the CUDA-enabled PyTorch build is installed and your driver is up to date.")
            return False
    except ImportError:
        print(f"{FAIL}  Cannot check CUDA — PyTorch not installed.")
        return False


def check_nvidia_smi() -> bool:
    smi = shutil.which("nvidia-smi")
    if smi is None:
        print(f"{FAIL}  nvidia-smi not found in PATH.")
        return False
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                gpu_name    = parts[0] if len(parts) > 0 else "unknown"
                driver_ver  = parts[1] if len(parts) > 1 else "unknown"
                vram        = parts[2] if len(parts) > 2 else "unknown"
                print(f"{PASS}  nvidia-smi: {gpu_name} | Driver {driver_ver} | VRAM {vram}")
                # NVIDIA RTX VSR requires driver >= 531 on Windows
                try:
                    major = int(driver_ver.split(".")[0])
                    if major < 531:
                        print(f"{WARN}  Driver {driver_ver} may be too old. RTX VSR typically requires driver >= 531.")
                    else:
                        print(f"       Driver version looks sufficient (>= 531).")
                except ValueError:
                    pass
            return True
        else:
            print(f"{FAIL}  nvidia-smi returned error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"{FAIL}  nvidia-smi error: {e}")
        return False


def check_nvvfx() -> bool:
    try:
        import nvvfx  # noqa: F401
        version = getattr(nvvfx, "__version__", "unknown")
        print(f"{PASS}  nvidia-vfx (nvvfx) installed — version: {version}")
        # Try to list available effects
        try:
            effects = dir(nvvfx)
            vsr_names = [e for e in effects if "Super" in e or "VSR" in e or "VideoSuperRes" in e]
            if vsr_names:
                print(f"       VideoSuperRes symbols found: {vsr_names}")
            else:
                print(f"{WARN}  VideoSuperRes symbol not found in nvvfx — check API version.")
        except Exception:
            pass
        return True
    except ImportError:
        print(f"{FAIL}  nvidia-vfx (nvvfx) is NOT installed.")
        print(textwrap.dedent("""\
               Fix:
                 pip install -U --no-build-isolation nvidia-vfx \\
                   --index-url https://pypi.nvidia.com

               Or (if above fails):
                 python -m pip install -U --no-build-isolation nvidia-vfx \\
                   --index-url https://pypi.nvidia.com"""))
        return False
    except Exception as e:
        print(f"{FAIL}  nvidia-vfx import error: {e}")
        return False


def check_ffmpeg() -> bool:
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    ok = True
    if ffmpeg_path:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
            )
            ver_line = result.stdout.splitlines()[0] if result.stdout else "?"
            print(f"{PASS}  ffmpeg: {ver_line}")
        except Exception as e:
            print(f"{WARN}  ffmpeg found but could not get version: {e}")
    else:
        print(f"{FAIL}  ffmpeg not found in PATH.")
        print(f"       Windows: download from https://ffmpeg.org/download.html and add to PATH")
        print(f"       Or use: winget install ffmpeg")
        ok = False

    if ffprobe_path:
        print(f"{PASS}  ffprobe: found at {ffprobe_path}")
    else:
        print(f"{WARN}  ffprobe not found — some video metadata features may fail.")
    return ok


def check_packages() -> None:
    packages = [
        ("PIL",        "Pillow"),
        ("cv2",        "opencv-python"),
        ("numpy",      "numpy"),
        ("tqdm",       "tqdm"),
        ("ffmpeg",     "ffmpeg-python"),
    ]
    for import_name, pkg_name in packages:
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", "?")
            print(f"{PASS}  {pkg_name}: {ver}")
        except ImportError:
            print(f"{FAIL}  {pkg_name} not installed — run: pip install {pkg_name}")


def check_nvvfx_models() -> bool:
    """Check that the NVIDIA Video Effects SDK model files are present."""
    default_paths = [
        r"C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models",
        r"C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects",
    ]
    env_path = os.environ.get("NVVFX_SDK_PATH", "")
    if env_path:
        default_paths.insert(0, env_path)

    found_path = None
    for p in default_paths:
        if os.path.isdir(p):
            found_path = p
            break

    if found_path:
        # Look for any .nvmdl or model-like files
        model_files = [
            f for f in os.listdir(found_path)
            if f.endswith((".nvmdl", ".bin", ".onnx", ".trt"))
        ]
        if model_files:
            print(f"{PASS}  NVVFX model directory: {found_path}")
            print(f"       Model files found: {len(model_files)}")
            return True
        else:
            print(f"{WARN}  NVVFX model directory exists but appears empty: {found_path}")
            print(f"       Download the SDK at: https://developer.nvidia.com/rtx-video-sdk")
            return False
    else:
        print(f"{FAIL}  NVVFX model directory not found.")
        print(f"       Download the NVIDIA Video Effects SDK:")
        print(f"       https://developer.nvidia.com/rtx-video-sdk")
        print(f"       After installing, models land at:")
        print(f"       C:\\Program Files\\NVIDIA Corporation\\NVIDIA Video Effects\\models\\")
        print(f"       Or set NVVFX_SDK_PATH to a custom model directory.")
        return False


def check_output_dirs() -> None:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required = [
        "inputs/videos", "inputs/images", "inputs/frames",
        "outputs/videos", "outputs/images", "outputs/frames", "outputs/benchmarks",
    ]
    for rel in required:
        full = os.path.join(base, rel.replace("/", os.sep))
        if os.path.isdir(full):
            print(f"{PASS}  Directory: {rel}")
        else:
            os.makedirs(full, exist_ok=True)
            print(f"{WARN}  Created missing directory: {rel}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"\n{BOLD}NVIDIA RTX VSR Toolkit — Environment Check{RESET}")
    print(f"{'=' * 60}")

    results: dict[str, bool] = {}

    section("System")
    check_platform()
    results["python"] = check_python()

    section("NVIDIA GPU & Driver")
    results["nvidia_smi"] = check_nvidia_smi()
    results["cuda"] = check_cuda()

    section("Python Packages")
    results["torch"] = check_torch()
    check_packages()

    section("NVIDIA nvidia-vfx")
    results["nvvfx"] = check_nvvfx()

    section("NVIDIA VSR Model Files")
    results["nvvfx_models"] = check_nvvfx_models()

    section("FFmpeg")
    results["ffmpeg"] = check_ffmpeg()

    section("Project Directory Structure")
    check_output_dirs()

    # ── Summary ──────────────────────────────────────────────────────────────
    section("Summary")
    critical = ["python", "cuda", "torch", "nvvfx", "nvvfx_models", "ffmpeg"]
    all_ok = True
    for key in critical:
        val = results.get(key, False)
        tag = PASS if val else FAIL
        label = key.replace("_", "-").upper()
        print(f"  {tag}  {label}")
        if not val:
            all_ok = False

    print()
    if all_ok:
        print(f"{GREEN}{BOLD}All critical checks passed. You are ready to run RTX VSR scripts.{RESET}")
    else:
        print(f"{RED}{BOLD}One or more critical checks failed. See messages above for fixes.{RESET}")

    print()


if __name__ == "__main__":
    main()
