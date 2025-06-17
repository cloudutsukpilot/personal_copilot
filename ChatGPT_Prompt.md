
I am trying to create an python web based app which will listen to the audio calls and transcribe it into text using whisper openai model running locally (ref: https://github.com/openai/whisper ). The web ui should have a start button and a box to show transcribed output as processed.

Next Step is to send the transcribed output to a local mistral model as input, understand the conversation and add points during the call as if it is part of the call. Also, once i stop the transcription, it should use all the transcribe text and generate a summary, next action items and update to a database.

The web app should also provide a interface/text block to add the prompt/memory context before the start of the call, so that mistral model is aware and accordingly provide suggestions or recommendations during the call. 

✅ Project Goals

 - Web UI with a Start button
   - Add microphone selector or upload audio file option - Completed
 - Stream audio input from the mic (or other source) - Completed
 - Continuously transcribe using OpenAI Whisper (local model) - Completed
   - Add speaker diarization or timestamping - Pending
   - Use WebSockets for live updates - Pending
 - Stream the transcribed text to the browser live - Completed
   - Save transcripts to Database - Pending
- Package as desktop app
- Add "record session" + save transcript to file?

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


- Please scan the files for the python code written for this app and provide steps to change the polling to websockets for live updates. Please keep this context in memery as the following questions will be related to this project.

