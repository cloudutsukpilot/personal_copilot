# ✅ Project Goals

- Web UI with a Start button
- Stream audio input from the mic (or other source)
- Continuously transcribe using OpenAI Whisper (local model)
- Show transcription output live

## 📁 Folder Structure

```sh
    whisper_transcriber/
    ├── app.py                  # Main backend app (Flask)
    ├── transcriber.py          # Whisper logic (transcription pipeline)
    ├── templates/
    │   └── index.html          # Web UI
    ├── static/
    │   └── style.css           # Optional styles
    ├── requirements.txt        # Dependencies
    └── README.md               # Instructions (optional)
```

### 🚀 To Run the App

- Execute the code

  ```bash
  cd personal_copilot
  pip install -r requirements.txt
  python app.py
  ```

- Open browser: http://127.0.0.1:5000

### Improvements

- 🔁 Make it continuous without pressing the button repeatedly?
- 💬 Add speaker diarization or timestamping?
- 🪄 Add microphone selector or upload audio file option?

### Setup Host

1. Install FFmpeg

    ```sh
    choco install ffmpeg
    ```

2. Install Whisper OpenAI Model

    ```sh
    pip install git+https://github.com/openai/whisper.git
    ```

3. Download Ollama

- https://ollama.com/download/windows
- Run the below command to serve Ollama for remote access

```powershell
$env:OLLAMA_HOST='0.0.0.0'; ollama serve
```

### Installation for GPU Support

1. Install NVIDIA Drivers(If required)

    - https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local

2. Check the CUDA Version

    - Check from NVIDIA System Info (Windows)
      - Right-click on desktop → NVIDIA Control Panel
      - Go to System Information (bottom-left)
      - Look under Components for CUDA version

3. Check CUDA Compatible pytorch version

    - Check for the version compatibilty based on the CUDA version on NVIDIA graphics card.
    - FP16 (16-bit floating point) is a lower-precision number format
    - Ref: https://pytorch.org/get-started/locally/

4. Install PythonTorch

    ```sh
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
    ```

5. Test if GPU is used

    ```python
    import torch
    print("CUDA available:", torch.cuda.is_available())
    print("GPU device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
    ```

### Containerization

1. Create a docker file

    ```dockerfile
    FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-runtime

    RUN pip install git+https://github.com/openai/whisper.git
    RUN apt-get update && apt-get install -y ffmpeg
    COPY . /app
    WORKDIR /app

    CMD ["python", "app.py"]
    ```

2. Enable GPU in Docker

    ```sh
    docker run --gpus all -p 5000:5000 your-image-name
    ```

3. Inside the container, check if CUDA is available:

    ```sh
    python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
    ```
