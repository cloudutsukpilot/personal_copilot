# Personal_Copilot

## Installation

### Learnings

1. Warning Message: "FP16 is not supported on CPU; using FP32 instead"

🧠 What It Means

- FP16 (16-bit floating point) is a lower-precision number format that is faster and uses less memory than FP32 (32-bit).
- Some deep learning models (like Whisper, Stable Diffusion, etc.) support FP16 for faster inference and lower memory usage, but only on GPUs that support it (e.g., NVIDIA RTX series with Tensor Cores).
- CPUs do not support FP16 arithmetic efficiently — they are designed for FP32 and sometimes FP64.
- So when a model like Whisper tries to use FP16 but detects it's running on a CPU, it automatically falls back to FP32, which is fully supported by all CPUs.