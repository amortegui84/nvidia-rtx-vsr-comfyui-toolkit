# Guía de Nodos ComfyUI — NVIDIA RTX VSR Toolkit

Esta guía explica qué nodos se necesitan, cómo instalarlos, y dónde
aparecen en ComfyUI.

---

## Instalación automática (recomendado)

Ejecuta el script instalador desde la raíz del proyecto:

**Windows (PowerShell):**
```powershell
.\comfyui\install_nodes.ps1
```

**Linux / macOS:**
```bash
bash comfyui/install_nodes.sh
```

El script detecta tu instalación de ComfyUI, clona los repos necesarios,
copia nuestro nodo custom, e instala `nvidia-vfx`.

---

## Instalación manual paso a paso

### Paso 1 — Localiza tu carpeta `custom_nodes`

Es la carpeta donde ComfyUI carga todos los nodos adicionales.
Está dentro de tu instalación de ComfyUI:

```
ComfyUI/
  custom_nodes/    ← aquí van todos los nodos
  models/
  output/
  ...
```

Rutas comunes en Windows:
```
C:\ComfyUI\custom_nodes\
C:\Users\TuUsuario\ComfyUI\custom_nodes\
```

---

### Paso 2 — Nodo oficial NVIDIA RTX Nodes for ComfyUI

**Repositorio:** https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI

**Qué incluye:**
- `RTX Video Super Resolution` — upscaling de video completo
- `RTX Denoise` — eliminación de ruido con hardware RTX
- `RTX Artifact Reduction` — reduce artefactos de compresión

**Instalar:**
```powershell
cd C:\ComfyUI\custom_nodes
git clone https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI.git
cd Nvidia_RTX_Nodes_ComfyUI
pip install -r requirements.txt
```

**Dónde aparece en ComfyUI:**
> Doble clic en el canvas → busca `RTX` → categoría `NVIDIA RTX`

---

### Paso 3 — Nuestro nodo custom: RTX VSR Single Frame

**Qué hace:** Upscaling de imágenes y frames individuales con RTX VSR.
Pensado para imágenes estáticas y salidas de generación AI (SD, SDXL, Flux).

**Instalar (copia la carpeta):**

```powershell
# Desde la raiz del proyecto
Copy-Item -Recurse `
  ".\comfyui\custom_nodes\rtx_vsr_single_frame_node" `
  "C:\ComfyUI\custom_nodes\rtx_vsr_single_frame_node"
```

O manualmente: copia la carpeta entera aquí:
```
comfyui/custom_nodes/rtx_vsr_single_frame_node/
  → C:\ComfyUI\custom_nodes\rtx_vsr_single_frame_node\
```

**Estructura que debe quedar:**
```
C:\ComfyUI\custom_nodes\rtx_vsr_single_frame_node\
  __init__.py
  rtx_vsr_single_frame_node.py
  README.md
```

**Dónde aparece en ComfyUI:**
> Doble clic en el canvas → busca `RTX VSR` → categoría `NVIDIA RTX / Super Resolution`
> Nombre del nodo: **RTX VSR Single Frame Upscale**

**Inputs / Outputs:**

| Puerto | Tipo | Descripción |
|--------|------|-------------|
| `image` (entrada) | IMAGE | Imagen ComfyUI estándar `(B, H, W, C)` |
| `scale_factor` | Widget | `4x` o `2x` |
| `upscaled_image` (salida) | IMAGE | Imagen upscaleada `(1, H*scale, W*scale, C)` |

---

### Paso 4 — ComfyUI-VideoHelperSuite (VHS)

Necesario para los workflows que cargan o guardan video.

**Repositorio:** https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite

**Instalar:**
```powershell
cd C:\ComfyUI\custom_nodes
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
cd ComfyUI-VideoHelperSuite
pip install -r requirements.txt
```

**Nodos que agrega:**
- `VHS_LoadVideo` — carga video desde archivo
- `VHS_VideoCombine` — guarda frames como video
- `VHS_GetLatentCount` — info del batch

---

### Paso 5 — Instalar nvidia-vfx

```powershell
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

Si falla:
```powershell
python -m pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
```

Verificar:
```powershell
python -c "import nvvfx; print('OK:', dir(nvvfx))"
```

---

### Paso 6 — Reiniciar ComfyUI

Después de cualquier instalación de nodos, **siempre reinicia ComfyUI**.
Los nodos se cargan solo al arrancar.

Si un nodo aparece en **rojo** después de reiniciar:
→ Ve a [docs/troubleshooting.md](../docs/troubleshooting.md) sección "ComfyUI custom node not appearing".

---

## Resumen: estado esperado de `custom_nodes/`

```
C:\ComfyUI\custom_nodes\
  Nvidia_RTX_Nodes_ComfyUI\          ← nodos NVIDIA oficiales
    __init__.py
    requirements.txt
    nodes\
      ...
  ComfyUI-VideoHelperSuite\          ← carga y guarda video
    __init__.py
    requirements.txt
    ...
  rtx_vsr_single_frame_node\         ← nuestro nodo custom
    __init__.py
    rtx_vsr_single_frame_node.py
    README.md
```

---

## Nodos por workflow

| Workflow | Nodos necesarios |
|----------|-----------------|
| `01_quick_4x_upscale` | `rtx_vsr_single_frame_node` |
| `02_before_after_preview` | `rtx_vsr_single_frame_node` |
| `03_2x_vs_4x_comparison` | `rtx_vsr_single_frame_node` |
| `04_denoise_then_upscale` | `rtx_vsr_single_frame_node` + `Nvidia_RTX_Nodes_ComfyUI` |
| `05_video_frame_sampler` | `rtx_vsr_single_frame_node` + `ComfyUI-VideoHelperSuite` |
| `06_upscale_then_crop` | `rtx_vsr_single_frame_node` |
| `07_ai_gen_image_enhance` | `rtx_vsr_single_frame_node` + cualquier checkpoint SD |

---

## Actualizar nodos

Para actualizar un nodo clonado con git:

```powershell
cd C:\ComfyUI\custom_nodes\Nvidia_RTX_Nodes_ComfyUI
git pull

cd C:\ComfyUI\custom_nodes\ComfyUI-VideoHelperSuite
git pull
```

Para actualizar nuestro nodo custom, vuelve a copiar la carpeta
`rtx_vsr_single_frame_node` desde este repositorio.

---

## Verificar que los nodos están activos

En el terminal donde corre ComfyUI, al arrancar deberías ver líneas como:

```
[RTX VSR Node] Loading RTX VSR Single Frame Node...
Import success: Nvidia_RTX_Nodes_ComfyUI
Import success: ComfyUI-VideoHelperSuite
```

Si ves un error de importación, revisa [docs/troubleshooting.md](../docs/troubleshooting.md).
