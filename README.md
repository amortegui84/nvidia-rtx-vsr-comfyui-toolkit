# nvidia-rtx-vsr-comfyui-toolkit

Toolkit para usar **NVIDIA RTX Video Super Resolution (RTX VSR)** en ComfyUI
y scripts Python. Diseñado para RTX 5090 (Blackwell). Soporta upscaling de
video, imágenes estáticas, y frames individuales de AI generativa.

---

## Inicio rápido — ComfyUI

### 1. Instala los nodos (un solo comando)

**Windows (PowerShell) — desde la raíz del proyecto:**
```powershell
.\comfyui\install_nodes.ps1
```

**Linux / macOS:**
```bash
bash comfyui/install_nodes.sh
```

El script hace todo automáticamente:
- Detecta tu instalación de ComfyUI
- Clona los nodos oficiales de NVIDIA
- Clona ComfyUI-VideoHelperSuite (para video)
- Copia nuestro nodo custom `RTX VSR Single Frame`
- Instala `nvidia-vfx`

→ Ver guía completa de nodos: [comfyui/NODES.md](comfyui/NODES.md)

---

### 2. Reinicia ComfyUI

Después de instalar los nodos, reinicia ComfyUI completamente.

---

### 3. Carga un workflow de ejemplo

Arrastra cualquiera de estos JSON al canvas de ComfyUI:

| Archivo | Descripción |
|---------|-------------|
| `comfyui/workflows/examples/01_quick_4x_upscale.json` | Upscale 4x rápido |
| `comfyui/workflows/examples/02_before_after_preview.json` | Original vs upscaleado |
| `comfyui/workflows/examples/03_2x_vs_4x_comparison.json` | Compara 2x y 4x |
| `comfyui/workflows/examples/04_denoise_then_upscale.json` | Denoise → VSR 4x |
| `comfyui/workflows/examples/05_video_frame_sampler.json` | Frames de video → VSR |
| `comfyui/workflows/examples/06_upscale_then_crop_tile.json` | Upscale + recorte de detalle |
| `comfyui/workflows/examples/07_ai_gen_image_enhance.json` | SD/SDXL → RTX VSR 4x |

→ Ver descripción de cada workflow: [comfyui/workflows/examples/README.md](comfyui/workflows/examples/README.md)

---

## Nodos disponibles tras la instalación

### RTX VSR Single Frame Upscale *(nuestro nodo custom)*

> Categoría en ComfyUI: **NVIDIA RTX / Super Resolution**

Upscalea una imagen o frame individual con NVIDIA RTX VSR.

```
[IMAGE] ──► RTX VSR Single Frame Upscale ──► [IMAGE upscaleada]
                    │
              scale_factor: 4x / 2x
```

- Entrada: IMAGE estándar de ComfyUI `(B, H, W, C)`
- Salida: IMAGE upscaleada al mismo formato
- Funciona con cualquier imagen: fotos, renders, salidas de KSampler, etc.

---

### RTX Video Super Resolution *(NVIDIA oficial)*

> Categoría en ComfyUI: **NVIDIA RTX**

Nodo oficial de Comfy-Org para upscaling de video completo.
Requiere: [Nvidia_RTX_Nodes_ComfyUI](https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI)

---

### RTX Denoise *(NVIDIA oficial)*

> Categoría en ComfyUI: **NVIDIA RTX**

Elimina ruido y artefactos de compresión antes del upscaling.
Úsalo siempre **antes** del nodo de upscaling para mejores resultados.

---

### VHS LoadVideo / VHS VideoCombine *(VideoHelperSuite)*

Carga y guarda video en ComfyUI. Necesario para los workflows de video.
Requiere: [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)

---

## Pipeline recomendado para imagen AI generada

```
[CheckpointLoader] ──► [KSampler] ──► [VAEDecode] ──► [RTX VSR 4x] ──► [SaveImage]
```

Genera a 768×768 con tu modelo → RTX VSR sube a 3072×3072 instantáneamente.
Workflow listo: `07_ai_gen_image_enhance.json`

---

## Pipeline recomendado para imagen con ruido / compresión

```
[LoadImage] ──► [RTX Denoise] ──► [RTX VSR 4x] ──► [SaveImage]
```

Limpia primero, luego escala. El upscaling amplifica el ruido si no se hace primero.
Workflow listo: `04_denoise_then_upscale.json`

---

## Pipeline recomendado para video

```
[VHS_LoadVideo] ──► [RTX VSR Single Frame] ──► [VHS_VideoCombine]
```

Para verificar calidad antes del video completo:
```
[VHS_LoadVideo] ──► [VHS_GetImageBatch (frame N)] ──► [RTX VSR 4x] ──► [SaveImage]
```

Workflow listo: `05_video_frame_sampler.json`

---

## Scripts Python (alternativa sin ComfyUI)

Para procesamiento en batch o sin interfaz:

```powershell
# Verificar entorno
python scripts/check_environment.py

# Upscale de imagen
python scripts/upscale_image_rtx_vsr.py --input inputs/images/foto.jpg --output outputs/images/foto_4x.png --scale 4

# Upscale de video
python scripts/upscale_video_rtx_vsr.py --input inputs/videos/clip.mp4 --output outputs/videos/clip_4x.mp4 --scale 4

# Frame de video → upscale
python scripts/extract_frame_test.py --input inputs/videos/clip.mp4 --frame 10 --scale 4

# Benchmark completo
python scripts/benchmark_rtx_vsr.py --scale 4
```

---

## Requisitos

| Componente | Versión mínima |
|------------|---------------|
| GPU | NVIDIA RTX (recomendado RTX 5090) |
| Driver Windows | ≥ 531 (≥ 570 para RTX 5090 / Blackwell) |
| Python | 3.10 / 3.11 / 3.12 |
| PyTorch | 2.1+ (build CUDA) |
| nvidia-vfx | Última desde pypi.nvidia.com |
| FFmpeg | Cualquier versión reciente |

---

## Instalación del entorno Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
pip install -U --no-build-isolation nvidia-vfx --index-url https://pypi.nvidia.com
python scripts/check_environment.py
```

→ Guía detallada: [setup_instructions.md](setup_instructions.md)

---

## Estructura del proyecto

```
nvidia-rtx-vsr-comfyui-toolkit/
  comfyui/
    install_nodes.ps1              ← instalador automático (Windows)
    install_nodes.sh               ← instalador automático (Linux/Mac)
    NODES.md                       ← guía completa de nodos
    custom_nodes/
      rtx_vsr_single_frame_node/  ← nuestro nodo custom
    workflows/
      examples/                    ← 7 workflows listos para usar
        01_quick_4x_upscale.json
        02_before_after_preview.json
        03_2x_vs_4x_comparison.json
        04_denoise_then_upscale.json
        05_video_frame_sampler.json
        06_upscale_then_crop_tile.json
        07_ai_gen_image_enhance.json
        README.md

  scripts/                         ← scripts Python CLI
    check_environment.py
    upscale_image_rtx_vsr.py
    upscale_video_rtx_vsr.py
    extract_frame_test.py
    benchmark_rtx_vsr.py
    test_rtx_vsr.py

  inputs/  outputs/  docs/
```

---

## Referencias

- [NVIDIA RTX Video SDK](https://developer.nvidia.com/rtx-video-sdk)
- [nvidia-vfx en PyPI NVIDIA](https://pypi.org/project/nvidia-vfx/)
- [Nvidia_RTX_Nodes_ComfyUI (oficial)](https://github.com/Comfy-Org/Nvidia_RTX_Nodes_ComfyUI)
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)
- [Guía de nodos](comfyui/NODES.md)
- [Troubleshooting](docs/troubleshooting.md)
