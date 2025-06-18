import whisper
import threading
import time
import queue
import pyaudio
import wave
import tempfile
import socketio
import builtins
import torch
print = lambda *args, **kwargs: builtins.print(*args, **{**kwargs, "flush": True})

import requests
def query_mistral(prompt):
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral:latest",
            "prompt": prompt,
            "stream": False
        })
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        print(f"⚠️ Mistral query failed: {e}")
        return "⚠️ Mistral failed"

class ContinuousWhisperTranscriber:
    def __init__(self, socketio=None):
        #self.model = whisper.load_model("large-v3", device="cuda" if whisper.is_cuda_available() else "cpu")
        self.model = whisper.load_model("large-v3", device="cuda" if torch.cuda.is_available() else "cpu")
        self.audio_queue = queue.Queue()
        self.transcript_log = []
        self.running = False
        self.device_index = None
        self.socketio = socketio
        self.transcript_lock = threading.Lock()
        self.cleaned_history = []  # Store last 10 cleaned transcripts
        self.suggestion_interval_secs = 60
        
    def _mistral_loop(self):
        last_processed = 0
        while self.running:
            time.sleep(5)  # Run every 5 seconds

            with self.transcript_lock:
                new_transcripts = self.transcript_log[last_processed:]
                last_processed = len(self.transcript_log)

            if not new_transcripts:
                continue

            combined_text = " ".join(new_transcripts).strip()
            if not combined_text:
                continue

            print("🧠 Sending to Mistral:", combined_text)

            context = "\n".join(self.cleaned_history[-10:])
            cleaning_prompt = (
                "You are not a participant in the conversation.\n"
                "You are not allowed to answer questions or add any content.\n"
                "You are an assistant that receives partial, streaming transcripts of a live meeting.\n"
                "Your task is to:\n"
                "1. Fix grammatical errors only.\n"
                "2. Complete incomplete sentences using ONLY the context provided.\n"
                "3. Do NOT answer any questions.\n"
                "4. Do NOT rephrase or change meaning.\n"
                "5. Return only the corrected and completed transcript.\n\n"
                f"Context:\n{context}\n\n"
                f"New Transcript:\n{combined_text}"
            )
            cleaned = query_mistral(cleaning_prompt)

            # Save cleaned transcript to history (limit to 10)
            if cleaned.strip():
                self.cleaned_history.append(cleaned.strip())
                if len(self.cleaned_history) > 10:
                    self.cleaned_history = self.cleaned_history[-10:]
            
            print("💬 Cleaned transcript from Mistral:", cleaned, flush=True)

            try:
                self.socketio.emit('mistral_transcript', {'text': cleaned})
            except KeyError:
                print("⚠️ WebSocket session closed before message could be delivered.")

    def _periodic_suggestions_loop(self):
        while self.running:
            time.sleep(self.suggestion_interval_secs)

            if not self.cleaned_history:
                continue

            # Take last 10 cleaned entries
            recent_cleaned = "\n".join(self.cleaned_history[-10:])
            print("📊 Generating periodic suggestions for last 10 cleaned entries")

            suggestion_prompt = (
                "You are a Principal DevOps Engineer assistant analyzing a running transcript of a meeting.\n"
                "Based on the last few cleaned transcripts, you need to understand  the context, watch out for any questions, etc. and then provide answers, any best practices/recommendations or insightful responses that a participant can give.\n"
                "Keep the sentences summarized and short, unless the answers to the question requires specific details or if it a code snippet.\n"
                "Keep the tone helpful and context-aware.\n\n"
                f"Transcript:\n{recent_cleaned}"
            )

            result = query_mistral(suggestion_prompt)

            formatted_result = f"\n\n--- New Suggestions @ {time.strftime('%H:%M:%S')} ---\n{result.strip()}\n"
            print("💡 Raw suggestions from Mistral:", formatted_result, flush=True)

            print("🧠 Periodic Suggestions:", formatted_result)

            try:
                self.socketio.emit('mistral_suggestions', {'text': formatted_result})
            except KeyError:
                print("⚠️ WebSocket session closed before message could be delivered.")

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
                result = self.model.transcribe(audio_file, no_speech_threshold=0.8)
                #result = self.model.transcribe(audio_file)
                print("🔊 Transcription Result:", result, flush=True)

                if result['text'].strip():
                    print("📡 Emitting to WebSocket:", result['text'], flush=True)
                    with self.transcript_lock:
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
        
        # Start Mistral processing thread
        threading.Thread(target=self._mistral_loop, daemon=True).start()

        # Start periodic suggestions thread
        threading.Thread(target=self._periodic_suggestions_loop, daemon=True).start()

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
