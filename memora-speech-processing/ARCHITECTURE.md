# Memora Speech Processing - Architecture & Integration Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Audio Input                              │
│                    (MP3, WAV, M4A, etc.)                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SPEECH PROCESSOR                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Whisper Transcription                                    │  │
│  │  - Multi-language support                                 │  │
│  │  - Word-level timestamps                                  │  │
│  │  - Auto language detection                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                       │                                          │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Speaker Diarization (pyannote.audio)                     │  │
│  │  - Identify different speakers                            │  │
│  │  - Timestamp speaker changes                              │  │
│  │  - Label speaker segments                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    KEYWORD EXTRACTOR                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Named Entity Recognition (spaCy)                         │  │
│  │  - People, Places, Organizations                          │  │
│  │  - Dates, Times, Events                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  KeyBERT - Semantic Keywords                              │  │
│  │  - Context-aware keyword extraction                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  YAKE - Statistical Keywords                              │  │
│  │  - Frequency-based extraction                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SUMMARIZER                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LSA (Latent Semantic Analysis)                           │  │
│  │  TextRank Algorithm                                       │  │
│  │  LexRank Algorithm                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Per-Speaker Summaries                                    │  │
│  │  Conversation Overview                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LLM PROCESSOR                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Claude / GPT-4                                           │  │
│  │  - Generate user-friendly summary                         │  │
│  │  - Extract action items                                   │  │
│  │  - Identify key people & context                          │  │
│  │  - Create relevant tags                                   │  │
│  │  - Format for app display                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT GENERATION                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Complete Results JSON                                    │  │
│  │  - Full transcription with timestamps                     │  │
│  │  - All extracted data                                     │  │
│  │  - Intermediate processing results                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Memory Summary JSON (App-Ready)                          │  │
│  │  - Title, quick summary                                   │  │
│  │  - Key points, action items                               │  │
│  │  - People, tags, metadata                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Mobile App /  │
              │  Firebase DB   │
              └────────────────┘
```

## Data Flow

### 1. Input Stage
- **Format**: Audio files (MP3, WAV, M4A, FLAC, etc.)
- **Source**: Microphone recordings, uploaded files
- **Size**: Any duration (chunked for processing if needed)

### 2. Processing Stages

#### Stage A: Speech-to-Text
```python
{
  "full_text": "Complete transcription...",
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Hello, this is a test.",
      "speaker": "SPEAKER_00"  # If diarization enabled
    }
  ],
  "language": "en"
}
```

#### Stage B: Keyword & Entity Extraction
```python
{
  "entities": {
    "persons": ["Dr. Smith", "John"],
    "locations": ["Memorial Hospital"],
    "dates": ["next Tuesday"],
    "times": ["2 PM"]
  },
  "keybert_keywords": [
    {"keyword": "medication", "score": 0.85},
    {"keyword": "appointment", "score": 0.78}
  ],
  "combined_keywords": ["medication", "appointment", "treatment"]
}
```

#### Stage C: Summarization
```python
{
  "overall_summary": "Discussion about medication...",
  "speaker_summaries": {
    "SPEAKER_00": "Doctor discussed treatment plan...",
    "SPEAKER_01": "Patient asked about side effects..."
  }
}
```

#### Stage D: LLM Enhancement
```python
{
  "title": "Doctor's Appointment - Medication Review",
  "quick_summary": "Brief summary...",
  "key_points": ["Point 1", "Point 2"],
  "people": [{"name": "Dr. Smith", "context": "Primary physician"}],
  "action_items": ["Take medication at 8 AM"],
  "tags": ["medical", "appointment"]
}
```

### 3. Output Stage
- **Complete JSON**: All processing data
- **Memory JSON**: App-ready summary
- **Firebase Upload**: Optional cloud storage

## Integration Patterns

### Pattern 1: Real-time Recording

```python
from memora_pipeline import MemoraProcessor
import sounddevice as sd
import soundfile as sf

# Initialize processor
processor = MemoraProcessor()

# Record audio
duration = 60  # seconds
sample_rate = 16000
audio = sd.rec(int(duration * sample_rate), 
               samplerate=sample_rate, 
               channels=1)
sd.wait()

# Save to file
sf.write("recording.wav", audio, sample_rate)

# Process
results = processor.process_audio_file("recording.wav")
```

### Pattern 2: Batch Processing

```python
import os
from memora_pipeline import MemoraProcessor

processor = MemoraProcessor()

# Process all audio files in directory
audio_dir = "./recordings"
for filename in os.listdir(audio_dir):
    if filename.endswith(('.mp3', '.wav', '.m4a')):
        filepath = os.path.join(audio_dir, filename)
        print(f"Processing {filename}...")
        results = processor.process_audio_file(filepath)
```

### Pattern 3: Firebase Integration

```python
from memora_pipeline import MemoraProcessor
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Initialize Firebase
cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Process audio
processor = MemoraProcessor()
results = processor.process_audio_file("audio.mp3")

# Upload to Firebase
memory = results['memory_summary']
doc_ref = db.collection("memories").add(memory)
print(f"Uploaded with ID: {doc_ref[1].id}")
```

### Pattern 4: REST API Endpoint

```python
from flask import Flask, request, jsonify
from memora_pipeline import MemoraProcessor
import os

app = Flask(__name__)
processor = MemoraProcessor()

@app.route('/process', methods=['POST'])
def process_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file"}), 400
    
    audio_file = request.files['audio']
    filepath = f"/tmp/{audio_file.filename}"
    audio_file.save(filepath)
    
    try:
        results = processor.process_audio_file(filepath)
        return jsonify(results['memory_summary'])
    finally:
        os.remove(filepath)

if __name__ == '__main__':
    app.run(port=5000)
```

## Mobile App Integration

### Recommended Architecture

```
Mobile App (React Native / Flutter)
    │
    ├── Audio Recorder Component
    │   └── Captures audio from device microphone
    │
    ├── Upload Manager
    │   ├── Firebase Storage (audio files)
    │   └── Cloud Function Trigger
    │
    ├── Processing Backend
    │   ├── Google Cloud Function / AWS Lambda
    │   │   └── Runs Memora Pipeline
    │   └── Returns memory summary
    │
    └── Memory Display Component
        ├── Firestore Database (memories)
        └── Real-time updates
```

### Sample Mobile App Flow

1. **User records conversation**
   - App uses native audio recorder
   - Saves locally with timestamp

2. **Upload to Firebase Storage**
   ```javascript
   const uploadAudio = async (audioUri) => {
     const filename = `recordings/${Date.now()}.m4a`;
     const ref = storage().ref(filename);
     await ref.putFile(audioUri);
     return filename;
   }
   ```

3. **Trigger Cloud Function**
   ```javascript
   // Cloud Function (Node.js)
   exports.processAudio = functions.storage
     .object()
     .onFinalize(async (object) => {
       // Download audio
       // Run Python Memora pipeline
       // Save results to Firestore
     });
   ```

4. **Display in App**
   ```javascript
   const [memories, setMemories] = useState([]);
   
   useEffect(() => {
     const unsubscribe = firestore()
       .collection('memories')
       .orderBy('generated_at', 'desc')
       .onSnapshot(snapshot => {
         const mems = snapshot.docs.map(doc => ({
           id: doc.id,
           ...doc.data()
         }));
         setMemories(mems);
       });
     
     return unsubscribe;
   }, []);
   ```

## Performance Optimization

### GPU Acceleration

```python
# Check GPU availability
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0)}")

# Process with GPU
processor = MemoraProcessor(
    whisper_model="medium"  # Larger model with GPU
)
```

### Batch Processing Tips

1. **Process multiple files in parallel**
   ```python
   from concurrent.futures import ProcessPoolExecutor
   
   def process_file(filepath):
       processor = MemoraProcessor()
       return processor.process_audio_file(filepath)
   
   with ProcessPoolExecutor(max_workers=4) as executor:
       results = list(executor.map(process_file, audio_files))
   ```

2. **Use smaller models for draft processing**
   ```python
   # Quick draft
   draft = MemoraProcessor(whisper_model="tiny")
   
   # High-quality final
   final = MemoraProcessor(whisper_model="large")
   ```

## Security Considerations

### 1. API Key Management
- Never commit `.env` to version control
- Use environment variables in production
- Rotate keys regularly

### 2. Audio Privacy
- Encrypt audio files at rest
- Delete processed audio after extraction
- Use secure transmission (HTTPS)

### 3. Data Storage
- Implement user authentication
- Use Firebase Security Rules
- Enable audit logging

### Firebase Security Rules Example
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /memories/{memoryId} {
      allow read, write: if request.auth != null 
                         && request.auth.uid == resource.data.userId;
    }
  }
}
```

## Testing

### Unit Tests
```python
# test_speech_processor.py
import pytest
from speech_processor import SpeechProcessor

def test_transcription():
    processor = SpeechProcessor(whisper_model_size="tiny")
    result = processor.transcribe_audio("test_audio.wav")
    assert "text" in result
    assert len(result["text"]) > 0
```

### Integration Tests
```python
# test_pipeline.py
from memora_pipeline import MemoraProcessor

def test_full_pipeline():
    processor = MemoraProcessor(
        whisper_model="tiny",
        enable_diarization=False
    )
    results = processor.process_audio_file("test.mp3")
    assert results["memory_summary"] is not None
```

## Deployment

### Docker Container
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "api_server.py"]
```

### Cloud Deployment (Google Cloud Run)
```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/memora

# Deploy
gcloud run deploy memora \
  --image gcr.io/PROJECT_ID/memora \
  --platform managed \
  --memory 4Gi \
  --timeout 300s
```

## Monitoring & Analytics

### Log Processing Results
```python
import logging

logging.basicConfig(
    filename='memora.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# In processing
logging.info(f"Processed {filename}: {len(results['transcription']['text'])} chars")
```

### Track Metrics
```python
from datetime import datetime

metrics = {
    "timestamp": datetime.now(),
    "duration": audio_duration,
    "processing_time": end_time - start_time,
    "word_count": len(transcription.split()),
    "speakers": num_speakers,
    "language": detected_language
}
```

## Future Enhancements

1. **Emotion Detection**
   - Analyze tone and sentiment
   - Flag concerning patterns

2. **Custom Entity Recognition**
   - Train on medical/personal terms
   - Domain-specific extraction

3. **Multi-modal Processing**
   - Combine with image recognition
   - Context from visual cues

4. **Adaptive Learning**
   - User feedback loop
   - Personalized summaries

5. **Real-time Streaming**
   - Live transcription
   - Immediate memory creation
