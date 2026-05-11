# Implementation Notes

## nvidia-vfx API Notes

### Tensor Format Contract

The `nvidia-vfx` (imported as `nvvfx`) SDK expects:

- **Device**: CUDA (GPU)
- **Shape**: `(C, H, W)` — channels-first
- **Channels**: RGB order (not BGR)
- **dtype**: `float32`
- **Value range**: `[0.0, 1.0]`
- **Memory layout**: contiguous (call `.contiguous()` if unsure)

This is different from:
- OpenCV: `(H, W, C)` BGR uint8
- PIL: `(H, W, C)` RGB uint8
- ComfyUI: `(B, H, W, C)` RGB float32

### DLPack Output Buffer

After calling `vsr.run()`, the output tensor `vsr.output` is backed by
an internal DLPack buffer. **This buffer is overwritten on the next
`vsr.run()` call.** Always `.clone()` or `.copy()` the output immediately:

```python
vsr.run()
output = vsr.output.clone()  # safe copy — do this before the next frame
```

### Scale Factor Constants

The API for `upscaleFactor` may vary by `nvidia-vfx` version. Known patterns:

```python
# Pattern A — named constants (preferred if available)
vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_4X
vsr.upscaleFactor = nvvfx.UPSCALE_FACTOR_2X

# Pattern B — integer (common fallback)
vsr.upscaleFactor = 1  # 4x in most builds
vsr.upscaleFactor = 0  # 2x in most builds
```

Check available symbols with: `print([x for x in dir(nvvfx) if 'UPSCALE' in x])`

### load() Lifecycle

- `vsr.load()` downloads/initialises model weights. It is expensive.
- Call it **once per effect instance**, not per frame.
- `output_width` and `output_height` must be set **before** `load()`.
- Do not change these after `load()`. Create a new instance if resolution changes.

---

## Video Processing Architecture

Frames are extracted with OpenCV (`cv2.VideoCapture`), not decoded directly
by nvvfx. This is intentional:

- Gives frame-by-frame control
- Allows saving intermediate PNGs for debugging
- Works with any video format that OpenCV supports

Audio is extracted separately with `ffmpeg -vn -acodec copy` and merged back
after frame reassembly. If extraction fails, the output video is silent.

### Frame Rate Preservation

FPS is read from `ffprobe` (more accurate than OpenCV's `CAP_PROP_FPS` for
variable-framerate content) and passed to the `ffmpeg` reassembly command via
`-framerate`.

---

## ComfyUI Integration Notes

### Tensor Direction

ComfyUI's IMAGE type is always `(B, H, W, C)` CPU float32. Our node converts:

```
ComfyUI IMAGE  →  (B, H, W, C)  →  frame[0]  →  permute(2,0,1)  →  (C, H, W).cuda()
nvvfx output   →  (C, H, W).cuda()  →  .cpu()  →  permute(1,2,0)  →  (H,W,C)  →  unsqueeze(0)  →  (1,H,W,C)
```

### Batch Limitation

The custom node processes **only the first item** from the batch (`image[0]`).
Multi-frame batch processing is not supported in the single-frame node by
design. For video, use the standalone script or the official NVIDIA RTX Nodes.

---

## RTX 5090 / Blackwell Notes

The RTX 5090 uses the Blackwell architecture (GB202 die).
- Compute capability: 10.0
- Requires CUDA 12.8+ (bundled with driver 570+)
- VRAM: 32 GB GDDR7

RTX VSR on the 5090 should support:
- 4x upscaling
- Very high throughput due to increased tensor core count
- Large frame sizes without OOM (32 GB VRAM)

Driver requirement for RTX VSR: **≥ 531** on Windows, **≥ 525** on Linux.
For Blackwell: driver **≥ 570** recommended.

---

## Known API Unknowns (verify locally)

| Item | Status | How to verify |
|------|--------|---------------|
| `upscaleFactor` constant names | Unverified | `print(dir(nvvfx))` |
| Whether `load()` must be called per-session or per-resolution change | Unverified | Test with changing input res |
| DLPack format: is `.clone()` sufficient or is `.cpu()` needed first? | Unverified | Check output on second frame |
| Maximum supported input resolution | Unverified | Try 4K input |
| Whether 4x is supported at all inputs (may have min size) | Unverified | Test with small test image |

---

## Comparison Pipeline Notes

When comparing RTX VSR to other tools:
- **SeedVR2**: diffusion-based, temporal consistency for video, higher quality
  but much slower.
- **Topaz Video AI**: commercial, uses proprietary models, frame-accurate.
- **ESRGAN / RealESRGAN**: general-purpose image SR, not video-aware.
- **RTX VSR**: real-time capable, driver-level when used in media players,
  SDK access via nvidia-vfx, best for throughput benchmarks.

For fair comparison: use the same source, same scale factor, and measure
both PSNR/SSIM (if you have a reference) and wall-clock time.
