# install_nodes.ps1
# -----------------
# Automatically installs all ComfyUI nodes required for the
# NVIDIA RTX VSR toolkit.
#
# Usage:
#   .\comfyui\install_nodes.ps1
#   .\comfyui\install_nodes.ps1 -ComfyUIPath "D:\ComfyUI"
#
# Run from the project root.

param(
    [string]$ComfyUIPath = ""
)

$ErrorActionPreference = "Stop"

function Write-Pass { param($msg) Write-Host "[PASS] $msg" -ForegroundColor Green  }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red    }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan   }
function Write-Step { param($msg) Write-Host "`n-- $msg" -ForegroundColor White    }

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  NVIDIA RTX VSR -- ComfyUI Node Installer" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ── Locate ComfyUI ────────────────────────────────────────────────────────────
Write-Step "Locating ComfyUI installation"

$commonPaths = @(
    # Windows portable (most common)
    "C:\ComfyUI_windows_portable\ComfyUI",
    "D:\ComfyUI_windows_portable\ComfyUI",
    "E:\ComfyUI_windows_portable\ComfyUI",
    "$env:USERPROFILE\Desktop\ComfyUI_windows_portable\ComfyUI",
    "$env:USERPROFILE\Downloads\ComfyUI_windows_portable\ComfyUI",
    # Standalone installs
    "C:\ComfyUI",
    "D:\ComfyUI",
    "C:\Users\$env:USERNAME\ComfyUI",
    "C:\Users\$env:USERNAME\Desktop\ComfyUI"
)

if ($ComfyUIPath -eq "") {
    foreach ($p in $commonPaths) {
        if (Test-Path "$p\custom_nodes") {
            $ComfyUIPath = $p
            Write-Pass "ComfyUI found at: $ComfyUIPath"
            break
        }
    }
}

if ($ComfyUIPath -eq "" -or !(Test-Path "$ComfyUIPath\custom_nodes")) {
    Write-Warn "Could not auto-detect ComfyUI."
    $ComfyUIPath = Read-Host "Enter the full path to your ComfyUI installation (e.g. C:\ComfyUI)"
    if (!(Test-Path "$ComfyUIPath\custom_nodes")) {
        Write-Fail "custom_nodes folder not found at: $ComfyUIPath"
        Write-Host "Make sure ComfyUI is installed correctly."
        exit 1
    }
}

$customNodes = "$ComfyUIPath\custom_nodes"
Write-Info "custom_nodes path: $customNodes"

# ── Detect Python (embedded portable vs system) ───────────────────────────────
$embeddedPython = "$ComfyUIPath\..\python_embeded\python.exe"
if (Test-Path $embeddedPython) {
    $PythonExe = (Resolve-Path $embeddedPython).Path
    Write-Pass "Embedded Python found: $PythonExe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = "python"
    Write-Pass "System Python: $(python --version)"
} else {
    Write-Fail "Python not found. Install Python or use the ComfyUI Windows portable."
    exit 1
}

# ── Check dependencies ────────────────────────────────────────────────────────
Write-Step "Checking dependencies"

if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Fail "git is not installed or not in PATH."
    Write-Host "Download from: https://git-scm.com/download/win"
    exit 1
}
Write-Pass "git: $(git --version)"
Write-Info "Python: $PythonExe"

Write-Host ""
Write-Warn "NOTE: For official nodes (NVIDIA RTX, VHS), you can also use"
Write-Warn "      ComfyUI Manager inside ComfyUI — search 'RTX' or 'VHS'."
Write-Host "      This script installs via git clone as an alternative." -ForegroundColor Gray

# ── Clone or update a repo ────────────────────────────────────────────────────
function Install-Node {
    param(
        [string]$Name,
        [string]$RepoUrl,
        [string]$DestFolder,
        [string]$RequirementsTxt = ""
    )

    $destPath = "$customNodes\$DestFolder"

    Write-Step "Node: $Name"

    if (Test-Path "$destPath\.git") {
        Write-Info "Already installed. Updating with git pull..."
        Push-Location $destPath
        git pull --ff-only 2>&1 | ForEach-Object { Write-Host "  $_" }
        Pop-Location
        Write-Pass "$Name updated."
    } else {
        if (Test-Path $destPath) {
            Write-Warn "Folder exists but is not a git repo. Removing to clone fresh..."
            Remove-Item -Recurse -Force $destPath
        }
        Write-Info "Cloning from $RepoUrl ..."
        git clone $RepoUrl $destPath 2>&1 | ForEach-Object { Write-Host "  $_" }
        Write-Pass "$Name cloned to: $destPath"
    }

    if ($RequirementsTxt -ne "" -and (Test-Path "$destPath\$RequirementsTxt")) {
        Write-Info "Installing requirements ($RequirementsTxt)..."
        & $PythonExe -m pip install -r "$destPath\$RequirementsTxt" --quiet
        Write-Pass "Requirements installed."
    }
}

# ── Copy our local custom node ────────────────────────────────────────────────
function Install-LocalNode {
    param(
        [string]$Name,
        [string]$SourceFolder,
        [string]$DestFolder
    )

    Write-Step "Local node: $Name"

    $scriptDir   = Split-Path -Parent $MyInvocation.ScriptName
    $projectRoot = Split-Path -Parent $scriptDir
    $sourcePath  = "$projectRoot\comfyui\custom_nodes\$SourceFolder"
    $destPath    = "$customNodes\$DestFolder"

    if (!(Test-Path $sourcePath)) {
        $sourcePath = "$scriptDir\custom_nodes\$SourceFolder"
    }

    if (!(Test-Path $sourcePath)) {
        Write-Fail "Source node not found at: $sourcePath"
        return
    }

    if (Test-Path $destPath) {
        Write-Info "Already exists. Overwriting..."
        Remove-Item -Recurse -Force $destPath
    }

    Copy-Item -Recurse -Force $sourcePath $destPath
    Write-Pass "$Name copied to: $destPath"
}

# ── Install nodes ─────────────────────────────────────────────────────────────

# 1. Official NVIDIA RTX Nodes for ComfyUI
Install-Node `
    -Name            "NVIDIA RTX Nodes for ComfyUI (official)" `
    -RepoUrl         "https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git" `
    -DestFolder      "Nvidia_RTX_Nodes_ComfyUI" `
    -RequirementsTxt "requirements.txt"

# 2. ComfyUI-VideoHelperSuite — required for video workflows
Install-Node `
    -Name            "ComfyUI-VideoHelperSuite (VHS)" `
    -RepoUrl         "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" `
    -DestFolder      "ComfyUI-VideoHelperSuite" `
    -RequirementsTxt "requirements.txt"

# 3. Our custom RTX VSR Single Frame node
Install-LocalNode `
    -Name         "RTX VSR Single Frame Node (this toolkit)" `
    -SourceFolder "rtx_vsr_single_frame_node" `
    -DestFolder   "rtx_vsr_single_frame_node"

# ── Install nvidia-vfx ────────────────────────────────────────────────────────
Write-Step "Installing nvidia-vfx"

$nvvfxCheck = & $PythonExe -c "import nvvfx; print('ok')" 2>&1
if ($nvvfxCheck -eq "ok") {
    Write-Pass "nvidia-vfx is already installed."
} else {
    Write-Info "Installing nvidia-vfx from pypi.nvidia.com ..."
    & $PythonExe -m pip install -U --no-build-isolation nvidia-vfx `
        --index-url https://pypi.nvidia.com 2>&1 | ForEach-Object { Write-Host "  $_" }

    $nvvfxCheck2 = & $PythonExe -c "import nvvfx; print('ok')" 2>&1
    if ($nvvfxCheck2 -eq "ok") {
        Write-Pass "nvidia-vfx installed successfully."
    } else {
        Write-Warn "Could not verify nvidia-vfx. Try manually:"
        Write-Host "  $PythonExe -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com"
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Installation complete" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Nodes installed in:" -ForegroundColor White
Write-Host "  $customNodes" -ForegroundColor White
Write-Host ""
Write-Host "  Nvidia_RTX_Nodes_ComfyUI\     (official NVIDIA nodes)" -ForegroundColor Green
Write-Host "  ComfyUI-VideoHelperSuite\     (load / save video)" -ForegroundColor Green
Write-Host "  rtx_vsr_single_frame_node\    (our custom node)" -ForegroundColor Green
Write-Host ""
Write-Host "NVIDIA VSR model files — still need to be downloaded separately:" -ForegroundColor Yellow
Write-Host "  https://developer.nvidia.com/rtx-video-sdk" -ForegroundColor Yellow
Write-Host "  Installer places models at:" -ForegroundColor Yellow
Write-Host "  C:\Program Files\NVIDIA Corporation\NVIDIA Video Effects\models\" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next step: restart ComfyUI and search for:" -ForegroundColor Cyan
Write-Host "  NVIDIA RTX / Super Resolution -> RTX VSR Single Frame Upscale" -ForegroundColor Cyan
Write-Host ""
