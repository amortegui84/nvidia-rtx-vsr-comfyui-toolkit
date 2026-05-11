#!/usr/bin/env bash
# install_nodes.sh
# ----------------
# Instala automaticamente todos los nodos de ComfyUI necesarios
# para el toolkit NVIDIA RTX VSR (Linux / macOS).
#
# Uso:
#   bash comfyui/install_nodes.sh
#   bash comfyui/install_nodes.sh /ruta/a/ComfyUI

set -e

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; RESET='\033[0m'
pass() { echo -e "${GREEN}[PASS]${RESET} $1"; }
warn() { echo -e "${YELLOW}[WARN]${RESET} $1"; }
fail() { echo -e "${RED}[FAIL]${RESET} $1"; exit 1; }
info() { echo -e "${CYAN}[INFO]${RESET} $1"; }
step() { echo -e "\n── $1"; }

echo ""
echo -e "${CYAN}===========================================${RESET}"
echo -e "${CYAN}  NVIDIA RTX VSR — ComfyUI Node Installer ${RESET}"
echo -e "${CYAN}===========================================${RESET}"
echo ""

# ── Localizar ComfyUI ─────────────────────────────────────────────────────────
step "Localizando ComfyUI"

COMFYUI_PATH="${1:-}"
COMMON_PATHS=(
    "$HOME/ComfyUI"
    "$HOME/Desktop/ComfyUI"
    "/opt/ComfyUI"
    "/workspace/ComfyUI"
)

if [ -z "$COMFYUI_PATH" ]; then
    for p in "${COMMON_PATHS[@]}"; do
        if [ -d "$p/custom_nodes" ]; then
            COMFYUI_PATH="$p"
            pass "ComfyUI encontrado en: $COMFYUI_PATH"
            break
        fi
    done
fi

if [ -z "$COMFYUI_PATH" ] || [ ! -d "$COMFYUI_PATH/custom_nodes" ]; then
    warn "No se pudo detectar ComfyUI automaticamente."
    read -rp "Ingresa la ruta a ComfyUI: " COMFYUI_PATH
    [ -d "$COMFYUI_PATH/custom_nodes" ] || fail "custom_nodes no existe en: $COMFYUI_PATH"
fi

CUSTOM_NODES="$COMFYUI_PATH/custom_nodes"
info "custom_nodes: $CUSTOM_NODES"

# ── Verificar dependencias ────────────────────────────────────────────────────
step "Verificando dependencias"
command -v git    >/dev/null 2>&1 || fail "git no instalado. Instala con: sudo apt install git"
command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 || fail "python no encontrado"
PYTHON=$(command -v python3 || command -v python)
pass "git: $(git --version)"
pass "python: $($PYTHON --version)"

# ── Clonar o actualizar un nodo ───────────────────────────────────────────────
install_node() {
    local name="$1" url="$2" folder="$3" requirements="${4:-}"
    local dest="$CUSTOM_NODES/$folder"

    step "Nodo: $name"

    if [ -d "$dest/.git" ]; then
        info "Ya existe. Actualizando..."
        git -C "$dest" pull --ff-only
        pass "$name actualizado."
    else
        [ -d "$dest" ] && rm -rf "$dest"
        info "Clonando desde $url ..."
        git clone "$url" "$dest"
        pass "$name clonado en: $dest"
    fi

    if [ -n "$requirements" ] && [ -f "$dest/$requirements" ]; then
        info "Instalando requirements..."
        $PYTHON -m pip install -r "$dest/$requirements" --quiet
        pass "Requirements instalados."
    fi
}

# ── Copiar nuestro nodo local ─────────────────────────────────────────────────
install_local_node() {
    local name="$1" src_folder="$2" dest_folder="$3"
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local src="$script_dir/custom_nodes/$src_folder"
    local dest="$CUSTOM_NODES/$dest_folder"

    step "Nodo local: $name"
    [ -d "$src" ] || { warn "No se encuentra: $src"; return; }
    [ -d "$dest" ] && rm -rf "$dest"
    cp -r "$src" "$dest"
    pass "$name copiado en: $dest"
}

# ── Instalacion ───────────────────────────────────────────────────────────────
install_node \
    "NVIDIA RTX Nodes for ComfyUI (oficial)" \
    "https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git" \
    "Nvidia_RTX_Nodes_ComfyUI" \
    "requirements.txt"

install_node \
    "ComfyUI-VideoHelperSuite (VHS)" \
    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" \
    "ComfyUI-VideoHelperSuite" \
    "requirements.txt"

install_local_node \
    "RTX VSR Single Frame Node (este toolkit)" \
    "rtx_vsr_single_frame_node" \
    "rtx_vsr_single_frame_node"

# ── nvidia-vfx ────────────────────────────────────────────────────────────────
step "Instalando nvidia-vfx"
if $PYTHON -c "import nvvfx" 2>/dev/null; then
    pass "nvidia-vfx ya esta instalado."
else
    info "Instalando desde pypi.nvidia.com ..."
    $PYTHON -m pip install -U --no-build-isolation nvidia-vfx \
        --index-url https://pypi.nvidia.com
    $PYTHON -c "import nvvfx" 2>/dev/null && pass "nvidia-vfx instalado." \
        || warn "Verifica la instalacion manualmente."
fi

# ── Resumen ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}==========================================${RESET}"
echo -e "${CYAN}  Instalacion completa${RESET}"
echo -e "${CYAN}==========================================${RESET}"
echo ""
echo "Nodos instalados en: $CUSTOM_NODES"
echo ""
echo -e "${GREEN}  Nvidia_RTX_Nodes_ComfyUI/       (nodos oficiales NVIDIA)${RESET}"
echo -e "${GREEN}  ComfyUI-VideoHelperSuite/        (carga/guarda video)${RESET}"
echo -e "${GREEN}  rtx_vsr_single_frame_node/       (nuestro nodo custom)${RESET}"
echo ""
echo -e "${YELLOW}Reinicia ComfyUI y busca:${RESET}"
echo -e "${YELLOW}  NVIDIA RTX / Super Resolution -> RTX VSR Single Frame Upscale${RESET}"
echo ""
