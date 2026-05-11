# Comparison Methodology

## Goal

Compare NVIDIA RTX Video Super Resolution (RTX VSR) against other
upscaling/enhancement tools in terms of:

1. **Output quality** — visual sharpness, artifact level, detail recovery
2. **Throughput** — frames per second at given scale factor
3. **VRAM usage** — peak GPU memory during processing
4. **Ease of use** — integration complexity

---

## Tools to Compare

| Tool | Type | Scale | Method | License |
|------|------|-------|--------|---------|
| NVIDIA RTX VSR | Real-time SDK | 2x, 4x | CNN-based SR | NVIDIA SDK (free) |
| SeedVR2 | Diffusion | 2x–8x | Video diffusion | Open source |
| Topaz Video AI | GUI / CLI | 2x–8x | Proprietary DNN | Commercial |
| RealESRGAN | Image SR | 2x, 4x | GAN | Open source |
| ESRGAN | Image SR | 4x | GAN | Open source |
| Waifu2x | Image SR | 2x | CNN | Open source |

---

## Test Media

Use consistent test clips and images across all tools for fair comparison.

### Recommended Test Sources

| Name | Resolution | Duration | Content |
|------|-----------|----------|---------|
| `test_video_1080p.mp4` | 1920×1080 | 5s | Mixed live-action |
| `test_video_720p.mp4`  | 1280×720  | 5s | Same clip, downscaled |
| `test_image_hd.jpg`    | 1920×1080 | — | Single still frame |
| `test_image_sd.jpg`    | 960×540   | — | Same image, downscaled |

For a ground-truth comparison: start from a high-resolution source,
downscale it to the input resolution, upscale with each tool, then
compare against the original.

---

## Metrics

### Perceptual Quality (if reference is available)

- **PSNR** (Peak Signal-to-Noise Ratio) — higher is better
- **SSIM** (Structural Similarity Index) — higher is better, max 1.0
- **LPIPS** (Learned Perceptual Image Patch Similarity) — lower is better

Python tools:
```bash
pip install scikit-image lpips
```

```python
from skimage.metrics import peak_signal_noise_ratio, structural_similarity
psnr = peak_signal_noise_ratio(reference_np, upscaled_np)
ssim = structural_similarity(reference_np, upscaled_np, channel_axis=2)
```

### Throughput

- **Frames per second (FPS)**: measured by the benchmark script
- **Total processing time**: wall-clock time for the full clip

### VRAM

- **Peak VRAM (MB)**: `torch.cuda.max_memory_allocated() / 1024**2`

---

## Benchmark Procedure

### Step 1: Set up test inputs

Place test files in:
```
inputs/videos/test_video.mp4
inputs/images/test_image.jpg
```

### Step 2: Run RTX VSR benchmark

```bash
python scripts/benchmark_rtx_vsr.py --scale 4
```

Results: `outputs/benchmarks/benchmark_results.md`

### Step 3: Run comparison tools

For each competitor tool, process the same input at the same scale factor
and record:
- Output file path
- Total processing time
- FPS (for video)
- Peak VRAM

### Step 4: Compare quality

Use a side-by-side viewer (e.g. DiffImg, Pixelmator, or the browser)
to compare outputs visually. For objective metrics, compare upscaled
outputs against the ground-truth high-res source using PSNR/SSIM/LPIPS.

---

## Notes on RTX VSR vs Diffusion-Based Tools

RTX VSR is designed for real-time or near-real-time throughput. It will
generally be faster than diffusion-based tools (e.g. SeedVR2) but may
produce less detail in textures with complex high-frequency content.

Diffusion tools like SeedVR2 hallucinate plausible detail, which can look
better perceptually but may differ from the true ground truth.

RTX VSR is best suited for:
- Broadcast/live scenarios where speed matters
- Gaming video content (textures are grid-aligned)
- Quick batch upscaling of large libraries

Diffusion tools are better suited for:
- Single hero shots where quality trumps speed
- AI-generated content where the "ground truth" is ambiguous
- Very low-resolution inputs (below 360p) where CNN-based SR degrades

---

## Recording Results

After each comparison run, document in `outputs/benchmarks/`:
- The tool used
- The input and output resolution
- Scale factor
- FPS / processing time
- Any visual quality observations

The benchmark script generates `benchmark_results.md` automatically for
RTX VSR. Add rows for other tools manually.
