
I am trying to create an python web based app which will listen to the audio calls, transcribe it into text using whisper openai model running locally (ref: https://github.com/openai/whisper ) and provide realtime suggestions as a intelligent human who is part of that call. 

✅ Project Goals

 - Web UI with a Start button
   - Add microphone selector or upload audio file option - Completed
   - Add start, stop button to start and stop recording/transcribing - Completed
   - Add option to download the transcript - Completed
   - Add exit button to stop the transcribing and flask server - Completed
   - Add 3 output boxes - raw whisper transcribed text, transcribe text from mistral model and suggestions from mistral model - Completed
   - Button to refresh the audio devices - Pending
 - Streaming
   - Stream audio input from the mic (or other source) - Completed
   - Continuously transcribe using OpenAI Whisper (local model) - Completed
   - Use WebSockets for live updates - Completed
   - Add speaker diarization or timestamping - Pending
   - Stream the transcribed text to the browser live - Completed
   
- Query Mistral API endpoint to
  - Transcribe the text into gramatically correct and complete sentences - Completed
  - Based on the transcribed text, provide promt + transcribe text to mistral to provide realtime suggestions - Pending
  - Generate summary, action items and next plan by sending all the transcript text to mistral model.  - Pending
- Local Database:
  - Create tables which will contains the notes from meetings grouped by a specific topic/project - Pending
  - Create tables which will contains the projects goals and task and their status - Pending
  - Save transcripts to Database - Pending


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


- Please keep this context in memery as the following questions will be related to this project. 
- Question: The transcribed text from mistral model is being passed to mistral model and suggestion are returned. Suggestions are also being printed to the console output, but not to the web UI

