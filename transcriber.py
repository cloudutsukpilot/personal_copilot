import whisper
import threading
import time
import queue
import pyaudio
import wave
import tempfile

class ContinuousWhisperTranscriber:
    def __init__(self):
        self.model = whisper.load_model("base")
        self.audio_queue = queue.Queue()
        self.transcript_log = []
        self.running = False
        self.device_index = None

    def _record_loop(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        SECONDS = 2

        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, input_device_index=self.device_index,
                    frames_per_buffer=CHUNK)

        while self.running:
            frames = []
            for _ in range(0, int(RATE / CHUNK * SECONDS)):
                if not self.running:
                    break
                data = stream.read(CHUNK)
                frames.append(data)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wf:
                with wave.open(wf.name, 'wb') as wav_file:
                    wav_file.setnchannels(CHANNELS)
                    wav_file.setsampwidth(p.get_sample_size(FORMAT))
                    wav_file.setframerate(RATE)
                    wav_file.writeframes(b''.join(frames))
                self.audio_queue.put(wf.name)

        stream.stop_stream()
        stream.close()
        p.terminate()

    def _transcribe_loop(self):
        while self.running:
            try:
                audio_file = self.audio_queue.get(timeout=1)
                result = self.model.transcribe(audio_file)
                text = result['text'].strip()
                if text:
                    self.transcript_log.append(text)
            except queue.Empty:
                continue

    def start(self, device_index=None):
        if self.running:
            return
        self.device_index = device_index
        self.running = True
        threading.Thread(target=self._record_loop, daemon=True).start()
        threading.Thread(target=self._transcribe_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def get_transcript(self):
        return "\n".join(self.transcript_log)
    
    def list_input_devices(self):
        p = pyaudio.PyAudio()
        devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                devices.append({
                    "index": i,
                    "name": info["name"]
                })
        p.terminate()
        return devices
