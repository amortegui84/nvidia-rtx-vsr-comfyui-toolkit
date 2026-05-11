# install_nodes.ps1
# -----------------
# Instala automaticamente todos los nodos de ComfyUI necesarios para
# el toolkit NVIDIA RTX VSR.
#
# Uso:
#   .\comfyui\install_nodes.ps1
#   .\comfyui\install_nodes.ps1 -ComfyUIPath "D:\ComfyUI"
#
# Ejecutar desde la raiz del proyecto.

param(
    [string]$ComfyUIPath = ""
)

$ErrorActionPreference = "Stop"

# ── Colores ────────────────────────────────────────────────────────────────────
function Write-Pass  { param($msg) Write-Host "[PASS] $msg" -ForegroundColor Green  }
function Write-Fail  { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red    }
function Write-Warn  { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Info  { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan   }
function Write-Step  { param($msg) Write-Host "`n── $msg" -ForegroundColor White   }

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  NVIDIA RTX VSR — ComfyUI Node Installer " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# ── Localizar ComfyUI ─────────────────────────────────────────────────────────
Write-Step "Localizando ComfyUI"

$commonPaths = @(
    "C:\ComfyUI",
    "C:\Users\$env:USERNAME\ComfyUI",
    "C:\Users\$env:USERNAME\Desktop\ComfyUI",
    "C:\Users\$env:USERNAME\Documents\ComfyUI",
    "D:\ComfyUI",
    "E:\ComfyUI"
)

if ($ComfyUIPath -eq "") {
    foreach ($p in $commonPaths) {
        if (Test-Path "$p\custom_nodes") {
            $ComfyUIPath = $p
            Write-Pass "ComfyUI encontrado en: $ComfyUIPath"
            break
        }
    }
}

if ($ComfyUIPath -eq "" -or !(Test-Path "$ComfyUIPath\custom_nodes")) {
    Write-Warn "No se pudo detectar ComfyUI automaticamente."
    $ComfyUIPath = Read-Host "Ingresa la ruta completa a tu instalacion de ComfyUI (ej: C:\ComfyUI)"
    if (!(Test-Path "$ComfyUIPath\custom_nodes")) {
        Write-Fail "La carpeta custom_nodes no existe en: $ComfyUIPath"
        Write-Host "Verifica que ComfyUI este instalado correctamente."
        exit 1
    }
}

$customNodes = "$ComfyUIPath\custom_nodes"
Write-Info "custom_nodes: $customNodes"

# ── Verificar git ─────────────────────────────────────────────────────────────
Write-Step "Verificando dependencias"

if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Fail "git no esta instalado o no esta en PATH."
    Write-Host "Descarga git desde: https://git-scm.com/download/win"
    exit 1
}
Write-Pass "git: $(git --version)"

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Fail "python no encontrado en PATH."
    exit 1
}
Write-Pass "python: $(python --version)"

# ── Funcion para clonar o actualizar un repo ──────────────────────────────────
function Install-Node {
    param(
        [string]$Name,
        [string]$RepoUrl,
        [string]$DestFolder,
        [string]$RequirementsTxt = ""
    )

    $destPath = "$customNodes\$DestFolder"

    Write-Step "Nodo: $Name"

    if (Test-Path "$destPath\.git") {
        Write-Info "Ya existe. Actualizando con git pull..."
        Push-Location $destPath
        git pull --ff-only 2>&1 | ForEach-Object { Write-Host "  $_" }
        Pop-Location
        Write-Pass "$Name actualizado."
    } else {
        if (Test-Path $destPath) {
            Write-Warn "La carpeta existe pero no es un repo git. Eliminando para clonar limpio..."
            Remove-Item -Recurse -Force $destPath
        }
        Write-Info "Clonando desde $RepoUrl ..."
        git clone $RepoUrl $destPath 2>&1 | ForEach-Object { Write-Host "  $_" }
        Write-Pass "$Name clonado en: $destPath"
    }

    if ($RequirementsTxt -ne "" -and (Test-Path "$destPath\$RequirementsTxt")) {
        Write-Info "Instalando requirements ($RequirementsTxt)..."
        python -m pip install -r "$destPath\$RequirementsTxt" --quiet
        Write-Pass "Requirements instalados."
    }
}

# ── Funcion para copiar nuestro custom node ───────────────────────────────────
function Install-LocalNode {
    param(
        [string]$Name,
        [string]$SourceFolder,
        [string]$DestFolder
    )

    Write-Step "Nodo local: $Name"

    $projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    # Si se ejecuta desde la raiz, ajustar
    if (!(Test-Path "$projectRoot\comfyui")) {
        $projectRoot = Get-Location
    }

    $sourcePath = "$projectRoot\comfyui\custom_nodes\$SourceFolder"
    $destPath   = "$customNodes\$DestFolder"

    if (!(Test-Path $sourcePath)) {
        # Intentar relativo al script
        $sourcePath = "$PSScriptRoot\custom_nodes\$SourceFolder"
    }

    if (!(Test-Path $sourcePath)) {
        Write-Fail "No se encuentra el nodo fuente en: $sourcePath"
        return
    }

    if (Test-Path $destPath) {
        Write-Info "Ya existe. Sobreescribiendo archivos..."
        Remove-Item -Recurse -Force $destPath
    }

    Copy-Item -Recurse -Force $sourcePath $destPath
    Write-Pass "$Name copiado en: $destPath"
}

# ── Instalacion de nodos ──────────────────────────────────────────────────────

# 1. NVIDIA RTX Nodes (oficial de Comfy-Org)
Install-Node `
    -Name        "NVIDIA RTX Nodes for ComfyUI (oficial)" `
    -RepoUrl     "https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git" `
    -DestFolder  "Nvidia_RTX_Nodes_ComfyUI" `
    -RequirementsTxt "requirements.txt"

# 2. ComfyUI-VideoHelperSuite (VHS) — necesario para workflows de video
Install-Node `
    -Name        "ComfyUI-VideoHelperSuite (VHS)" `
    -RepoUrl     "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" `
    -DestFolder  "ComfyUI-VideoHelperSuite" `
    -RequirementsTxt "requirements.txt"

# 3. Nuestro nodo custom RTX VSR Single Frame
Install-LocalNode `
    -Name        "RTX VSR Single Frame Node (este toolkit)" `
    -SourceFolder "rtx_vsr_single_frame_node" `
    -DestFolder   "rtx_vsr_single_frame_node"

# ── Instalar nvidia-vfx ───────────────────────────────────────────────────────
Write-Step "Instalando nvidia-vfx"

$nvvfxCheck = python -c "import nvvfx; print('ok')" 2>&1
if ($nvvfxCheck -eq "ok") {
    Write-Pass "nvidia-vfx ya esta instalado."
} else {
    Write-Info "Instalando nvidia-vfx desde pypi.nvidia.com ..."
    python -m pip install -U --no-build-isolation nvidia-vfx `
        --index-url https://pypi.nvidia.com 2>&1 | ForEach-Object { Write-Host "  $_" }

    $nvvfxCheck2 = python -c "import nvvfx; print('ok')" 2>&1
    if ($nvvfxCheck2 -eq "ok") {
        Write-Pass "nvidia-vfx instalado correctamente."
    } else {
        Write-Warn "nvidia-vfx no se pudo verificar. Intenta manualmente:"
        Write-Host "  python -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com"
    }
}

# ── Resumen ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Instalacion completa" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Nodos instalados en: $customNodes" -ForegroundColor White
Write-Host ""
Write-Host "  Nvidia_RTX_Nodes_ComfyUI\        (nodos oficiales NVIDIA)" -ForegroundColor Green
Write-Host "  ComfyUI-VideoHelperSuite\         (carga/guarda video)" -ForegroundColor Green
Write-Host "  rtx_vsr_single_frame_node\        (nuestro nodo custom)" -ForegroundColor Green
Write-Host ""
Write-Host "Siguiente paso: reinicia ComfyUI y busca los nodos en:" -ForegroundColor Yellow
Write-Host "  NVIDIA RTX / Super Resolution -> RTX VSR Single Frame Upscale" -ForegroundColor Yellow
Write-Host ""
