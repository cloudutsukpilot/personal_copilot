import whisper
import threading
import time
import queue
import pyaudio
import wave
import tempfile
import socketio
import builtins
print = lambda *args, **kwargs: builtins.print(*args, **{**kwargs, "flush": True})

class ContinuousWhisperTranscriber:
    def __init__(self, socketio=None):
        self.model = whisper.load_model("large-v3")
        self.audio_queue = queue.Queue()
        self.transcript_log = []
        self.running = False
        self.device_index = None
        self.socketio = socketio

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

        print("🎤 Recording thread started...", flush=True)

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
                print(f"🎙️ Audio chunk captured and saved: {wf.name}", flush=True)

        stream.stop_stream()
        stream.close()
        p.terminate()
        time.sleep(0.05)

    def _transcribe_loop(self):
        print("🧠 Transcription thread started...", flush=True)
        while self.running:
            try:
                audio_file = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            print(f"🧪 Transcribing: {audio_file}", flush=True)
            try:
                #result = self.model.transcribe(audio_file, no_speech_threshold=0.8)
                result = self.model.transcribe(audio_file)
                print("🔊 Transcription Result:", result, flush=True)

                if result['text'].strip():
                    print("📡 Emitting to WebSocket:", result['text'], flush=True)
                    self.transcript_log.append(result['text'])
                    self.socketio.emit('transcription', {'text': result['text']})
                    print("✅ Emit completed", flush=True)
                else:
                    print("🕳️ No speech detected.", flush=True)
            except Exception as e:
                print(f"⚠️ Transcription error: {e}", flush=True)

    def start(self, device_index=None):
        if self.running:
            return
        self.device_index = device_index
        self.running = True
        print("🚦 Starting recording + transcription...", flush=True)
        # Start transcribe thread FIRST to ensure it runs
        threading.Thread(target=self._transcribe_loop, daemon=True).start()

        # Start recording shortly after
        time.sleep(0.5)
        threading.Thread(target=self._record_loop, daemon=True).start()

    def stop(self):
        print("🛑 Stopping transcription", flush=True)
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
