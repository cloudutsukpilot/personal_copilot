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
import os
import pathlib
from pathlib import Path
from config import debug_print

print = lambda *args, **kwargs: builtins.print(*args, **{**kwargs, "flush": True})
import os
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")

import requests
def query_mistral(prompt):
    try:
        response = requests.post(f"http://{OLLAMA_HOST}:11434/api/generate", json={
            "model": "mistral:latest",
            "prompt": prompt,
            "stream": False
        })
        response.raise_for_status()
        return response.json()["response"]
    except Exception as e:
        debug_print(f"⚠️ Mistral query failed: {e}")
        return "⚠️ Mistral failed"

class ContinuousWhisperTranscriber:
    def __init__(self, socketio=None):
        self.model = whisper.load_model("large-v3", device="cuda" if torch.cuda.is_available() else "cpu")
        self.audio_queue = queue.Queue()
        self.transcript_log = []
        self.running = False
        self.device_index = None
        self.socketio = socketio
        self.transcript_lock = threading.Lock()
        self.cleaned_history = []  # Store last 10 cleaned transcripts
        self.suggestion_interval_secs = 30
        self.start_time = None
        self.stop_time = None
        self.initial_prompt = ""

    def set_initial_prompt(self, prompt: str):
        self.initial_prompt = prompt.strip()

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

            debug_print("🧠 Sending to Mistral:", combined_text)

            context = "\n".join(self.cleaned_history[-10:])
            cleaning_prompt = (
                "You are a strict grammar-corrector, not an assistant. You must NEVER answer questions.\n"
                "Do not define or describe anything. Simply fix grammar and complete broken sentences without adding meaning.\n"
                "If the input appears to be a question or prompt, simply return it unchanged, or rephrase grammatically without adding answers.\n\n"
                f"Context:\n{context}\n\n"
                f"Input:\n{combined_text}\n\n"
                f"Corrected Transcript Only:"
            )
            cleaned = query_mistral(cleaning_prompt)

            debug_print("🧹 Cleaned transcript:", cleaned, flush=True)

            # Save cleaned transcript to history (limit to 10)
            if cleaned.strip():
                self.cleaned_history.append(cleaned.strip())
                if len(self.cleaned_history) > 10:
                    self.cleaned_history = self.cleaned_history[-10:]
            
            debug_print("💬 Cleaned transcript from Mistral:", cleaned, flush=True)

            try:
                self.socketio.emit('mistral_transcript', {'text': cleaned})
            except KeyError:
                debug_print("⚠️ WebSocket session closed before message could be delivered.")

    def _periodic_suggestions_loop(self):
        while self.running:
            time.sleep(self.suggestion_interval_secs)

            if not self.cleaned_history:
                continue

            # Take last 10 cleaned entries
            recent_cleaned = "\n".join(self.cleaned_history[-10:])
            debug_print("📊 Generating periodic suggestions for last 10 cleaned entries")

            suggestion_prompt = (
                "You are a Principal DevOps Engineer assistant analyzing a running transcript of a meeting. You are giving an initial context to understand the overall goal of the meeting. \n"
                "Based on the last few cleaned transcripts, you need to understand  the context, watch out for any questions, etc. and then provide answers, any best practices/recommendations or insightful responses that a participant can give.\n"
                "Keep the sentences summarized and short, unless the answers to the question requires specific details or if it a code snippet.\n"
                "Keep the tone helpful and context-aware.\n\n"
                f"Transcript:\n{recent_cleaned}"
            )

            # Include initial prompt if set
            debug_print(" Initial prompt:", self.initial_prompt, flush=True)
            if self.initial_prompt:
                suggestion_prompt += f"Context:\n{self.initial_prompt}\n\n"

            suggestion_prompt += f"Transcript:\n{recent_cleaned}"
            debug_print("🧠 Sending periodic suggestions to Mistral:", suggestion_prompt, flush=True)

            result = query_mistral(suggestion_prompt)

            formatted_result = f"\n\n--- New Suggestions @ {time.strftime('%H:%M:%S')} ---\n{result.strip()}\n"
            debug_print("💡 Raw suggestions from Mistral:", formatted_result, flush=True)

            debug_print("🧠 Periodic Suggestions:", formatted_result)

            try:
                self.socketio.emit('mistral_suggestions', {'text': formatted_result})
            except KeyError:
                debug_print("⚠️ WebSocket session closed before message could be delivered.")

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

        debug_print("🎤 Recording thread started...", flush=True)

        while self.running:
            frames = []
            for _ in range(0, int(RATE / CHUNK * SECONDS)):
                if not self.running:
                    break
                data = stream.read(CHUNK)
                frames.append(data)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wf:
                wav_path = pathlib.Path(wf.name).resolve(strict=False)  # Get absolute full path
                with wave.open(str(wav_path), 'wb') as wav_file:
                    wav_file.setnchannels(CHANNELS)
                    wav_file.setsampwidth(p.get_sample_size(FORMAT))
                    wav_file.setframerate(RATE)
                    wav_file.writeframes(b''.join(frames))
                self.audio_queue.put(str(wav_path))
                debug_print(f"🎙️ Audio chunk captured and saved: {wav_path}", flush=True)

        stream.stop_stream()
        stream.close()
        p.terminate()
        time.sleep(0.05)

    def _transcribe_loop(self):
        debug_print("🧠 Transcription thread started...", flush=True)
        while self.running:
            try:
                audio_file = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            debug_print(f"🧪 Transcribing: {audio_file}", flush=True)
            try:
                # Wait for the file to exist and be fully written
                for _ in range(10):  # Try for 1 second
                    if os.path.exists(audio_file):
                        try:
                            with open(audio_file, 'rb'):
                                debug_print(f"✅ File is ready: {audio_file}", flush=True)
                                break  # File exists and is accessible
                        except IOError:
                            time.sleep(0.1)
                    else:
                        time.sleep(0.1)
                else:
                    debug_print(f"❌ File not found or not ready: {audio_file}", flush=True)
                    continue
                result = self.model.transcribe(str(audio_file), no_speech_threshold=0.9, language="en")
                os.remove(audio_file)  # Clean up the audio file after processing
                debug_print("🔊 Transcription Result:", result, flush=True)

                if result['text'].strip():
                    debug_print("📡 Emitting to WebSocket:", result['text'], flush=True)
                    with self.transcript_lock:
                        self.transcript_log.append(result['text'])
                    self.socketio.emit('transcription', {'text': result['text']})
                    debug_print("✅ Emit completed", flush=True)
                else:
                    debug_print("🕳️ No speech detected.", flush=True)
            except Exception as e:
                debug_print(f"⚠️ Transcription error: {e}", flush=True)

    def start(self, device_index=None):
        if self.running:
            return
        self.start_time = time.time()
        self.stop_time = None
        self.device_index = device_index
        self.running = True
        debug_print("🚦 Starting recording + transcription...", flush=True)
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
        debug_print("🛑 Stopping transcription", flush=True)
        self.running = False
        self.stop_time = time.time()

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

    def get_elapsed_time(self):
        if self.start_time is None:
            return "00:00"

        end_time = self.stop_time if self.stop_time else time.time()
        elapsed = int(end_time - self.start_time)
        mins, secs = divmod(elapsed, 60)
        return f"{mins:02}:{secs:02}"