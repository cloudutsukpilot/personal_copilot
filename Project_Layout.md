✅ Project Goals

 - Web UI with a Start button
 - Stream audio input from the mic (or other source)
 - Continuously transcribe using OpenAI Whisper (local model)
 - Show transcription output live


📁 Folder Structure

```php
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

🚀 To Run the App

```bash
cd whisper_transcriber
pip install -r requirements.txt
python app.py
```

Open browser: http://127.0.0.1:5000


Improvements:
----------------------
🔁 Make it continuous without pressing the button repeatedly?

💬 Add speaker diarization or timestamping?

🪄 Add microphone selector or upload audio file option?


Installation for GPU Support:

1. Install Whisper
- pip install git+https://github.com/openai/whisper.git

2. Install Pytorch
- Check for the version compatibilty - https://pytorch.org/get-started/locally/
- pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

3. Download CUDA Toolkit for Windows
https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local

4. Test if GPU is used

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

- Inside the container, check if CUDA is available:

```sh
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```