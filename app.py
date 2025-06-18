import requests
OLLAMA_URL = "http://localhost:11434/api/generate" 

from transcriber import query_mistral
from threading import Thread
from flask import Flask, render_template, jsonify, request, Response, redirect, url_for
from flask_socketio import SocketIO, emit
from transcriber import ContinuousWhisperTranscriber
import os
import signal
import sys
import tempfile
import threading
import time
from flask import request

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
transcriber = ContinuousWhisperTranscriber(socketio)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start():
    device_index = request.args.get('device', default=0, type=int)
    print("🚦 Starting recording + transcription...")

    # ✅ Start transcriber.start() in its own thread to avoid blocking
    Thread(target=transcriber.start, args=(device_index,), daemon=True).start()

    return jsonify({"status": "started"})

@app.route('/stop')
def stop():
    if not transcriber.running:
        print("⚠️ Transcriber is not running.")
        return jsonify({"status": "already stopped"})

    print("🛑 Request received: stopping transcription")
    transcriber.stop()
    return jsonify({"status": "stopped"})

@app.route('/get_transcript')
def get_transcript():
    return jsonify({"text": transcriber.get_transcript()})

@app.route('/devices')
def list_devices():
    return jsonify(transcriber.list_input_devices())

@app.route('/download')
def download():
    content = transcriber.get_transcript()
    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=transcript.txt"}
    )

@app.route('/exit')
def exit_app():
    print("🛑 Exit requested by user.", flush=True)
    transcriber.stop()
    return jsonify({"status": "stopped"})


@app.route('/goodbye')
def goodbye():
    def shutdown_server():
        time.sleep(5)  # Wait longer to ensure browser renders the page
        pid = os.getpid()
        print(f"💥 Shutting down Flask app. PID: {pid}")
        os.kill(pid, signal.SIGINT)

    threading.Thread(target=shutdown_server, daemon=True).start()

    return """
    <html>
        <head><title>Goodbye</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h1>👋 Transcription Ended</h1>
            <p>You may now close this tab.</p>
        </body>
    </html>
    """


def shutdown_handler(signum, frame):
    print("\n🛑 Shutting down gracefully...", flush=True)
    transcriber.stop()
    sys.exit(0)

# Register Ctrl+C handler
signal.signal(signal.SIGINT, shutdown_handler)

@app.route('/duration')
def get_duration():
    return jsonify({"duration": transcriber.get_elapsed_time()})


@app.route('/generate-summary', methods=['POST'])
def generate_summary():
    data = request.get_json()
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    print(f"📝 Generating summary for prompt: {prompt}", flush=True)
    result = query_mistral(prompt)
    return jsonify({"summary": result})

if __name__ == '__main__':
    print("🚀 Starting Whisper WebSocket Server at http://localhost:5000", flush=True)
    socketio.run(app, host='0.0.0.0', port=5000)


