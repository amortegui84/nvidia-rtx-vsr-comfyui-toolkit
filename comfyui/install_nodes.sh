#!/usr/bin/env bash
# install_nodes.sh
# ----------------
# Automatically installs all ComfyUI nodes required for the
# NVIDIA RTX VSR toolkit (Linux / macOS).
#
# Usage:
#   bash comfyui/install_nodes.sh
#   bash comfyui/install_nodes.sh /path/to/ComfyUI

set -e

GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; RESET='\033[0m'
pass() { echo -e "${GREEN}[PASS]${RESET} $1"; }
warn() { echo -e "${YELLOW}[WARN]${RESET} $1"; }
fail() { echo -e "${RED}[FAIL]${RESET} $1"; exit 1; }
info() { echo -e "${CYAN}[INFO]${RESET} $1"; }
step() { echo -e "\n-- $1"; }

echo ""
echo -e "${CYAN}==========================================${RESET}"
echo -e "${CYAN}  NVIDIA RTX VSR -- ComfyUI Node Installer${RESET}"
echo -e "${CYAN}==========================================${RESET}"
echo ""

# ── Locate ComfyUI ────────────────────────────────────────────────────────────
step "Locating ComfyUI installation"

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
            pass "ComfyUI found at: $COMFYUI_PATH"
            break
        fi
    done
fi

if [ -z "$COMFYUI_PATH" ] || [ ! -d "$COMFYUI_PATH/custom_nodes" ]; then
    warn "Could not auto-detect ComfyUI."
    read -rp "Enter the full path to your ComfyUI installation: " COMFYUI_PATH
    [ -d "$COMFYUI_PATH/custom_nodes" ] || fail "custom_nodes not found at: $COMFYUI_PATH"
fi

CUSTOM_NODES="$COMFYUI_PATH/custom_nodes"
info "custom_nodes path: $CUSTOM_NODES"

# ── Check dependencies ────────────────────────────────────────────────────────
step "Checking dependencies"
command -v git    >/dev/null 2>&1 || fail "git not installed. Run: sudo apt install git"
command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 || fail "python not found"
PYTHON=$(command -v python3 || command -v python)
pass "git: $(git --version)"
pass "python: $($PYTHON --version)"

# ── Clone or update a node repo ───────────────────────────────────────────────
install_node() {
    local name="$1" url="$2" folder="$3" requirements="${4:-}"
    local dest="$CUSTOM_NODES/$folder"

    step "Node: $name"

    if [ -d "$dest/.git" ]; then
        info "Already installed. Updating..."
        git -C "$dest" pull --ff-only
        pass "$name updated."
    else
        [ -d "$dest" ] && rm -rf "$dest"
        info "Cloning from $url ..."
        git clone "$url" "$dest"
        pass "$name cloned to: $dest"
    fi

    if [ -n "$requirements" ] && [ -f "$dest/$requirements" ]; then
        info "Installing requirements..."
        $PYTHON -m pip install -r "$dest/$requirements" --quiet
        pass "Requirements installed."
    fi
}

# ── Copy our local custom node ────────────────────────────────────────────────
install_local_node() {
    local name="$1" src_folder="$2" dest_folder="$3"
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local src="$script_dir/custom_nodes/$src_folder"
    local dest="$CUSTOM_NODES/$dest_folder"

    step "Local node: $name"
    [ -d "$src" ] || { warn "Source not found: $src"; return; }
    [ -d "$dest" ] && rm -rf "$dest"
    cp -r "$src" "$dest"
    pass "$name copied to: $dest"
}

# ── Install nodes ─────────────────────────────────────────────────────────────

install_node \
    "NVIDIA RTX Nodes for ComfyUI (official)" \
    "https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git" \
    "Nvidia_RTX_Nodes_ComfyUI" \
    "requirements.txt"

install_node \
    "ComfyUI-VideoHelperSuite (VHS)" \
    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git" \
    "ComfyUI-VideoHelperSuite" \
    "requirements.txt"

install_local_node \
    "RTX VSR Single Frame Node (this toolkit)" \
    "rtx_vsr_single_frame_node" \
    "rtx_vsr_single_frame_node"

# ── Install nvidia-vfx ────────────────────────────────────────────────────────
step "Installing nvidia-vfx"
if $PYTHON -c "import nvvfx" 2>/dev/null; then
    pass "nvidia-vfx is already installed."
else
    info "Installing from pypi.nvidia.com ..."
    $PYTHON -m pip install -U --no-build-isolation nvidia-vfx \
        --index-url https://pypi.nvidia.com
    $PYTHON -c "import nvvfx" 2>/dev/null && pass "nvidia-vfx installed." \
        || warn "Verify installation manually."
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}==========================================${RESET}"
echo -e "${CYAN}  Installation complete${RESET}"
echo -e "${CYAN}==========================================${RESET}"
echo ""
echo "Nodes installed in: $CUSTOM_NODES"
echo ""
echo -e "${GREEN}  Nvidia_RTX_Nodes_ComfyUI/     (official NVIDIA nodes)${RESET}"
echo -e "${GREEN}  ComfyUI-VideoHelperSuite/     (load / save video)${RESET}"
echo -e "${GREEN}  rtx_vsr_single_frame_node/    (our custom node)${RESET}"
echo ""
echo -e "${YELLOW}Next step: restart ComfyUI and search for:${RESET}"
echo -e "${YELLOW}  NVIDIA RTX / Super Resolution -> RTX VSR Single Frame Upscale${RESET}"
echo ""
