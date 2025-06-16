from flask import Flask, render_template, jsonify, request, Response
from transcriber import ContinuousWhisperTranscriber


app = Flask(__name__)
transcriber = ContinuousWhisperTranscriber()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start')
def start():
    device = request.args.get('device', default=None, type=int)
    transcriber.start(device_index=device)
    return jsonify({"status": "started", "device": device})

@app.route('/stop')
def stop():
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

if __name__ == '__main__':
    app.run(debug=True)


