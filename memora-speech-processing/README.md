# Memora Speech Processing Pipeline

AI-powered speech-to-text processing pipeline for the Memora assistive memory system. This pipeline processes audio recordings to generate structured memory summaries for individuals with cognitive challenges.

## Features

- 🎙️ **Speech-to-Text**: Powered by OpenAI Whisper with multi-language support
- 👥 **Speaker Diarization**: Identify and separate different speakers using pyannote.audio
- 🔑 **Keyword Extraction**: Extract important keywords using KeyBERT and YAKE
- 📝 **Summarization**: Multiple summarization algorithms (LSA, TextRank, LexRank)
- 🤖 **LLM Integration**: Generate user-friendly summaries with Claude or GPT-4
- 💾 **Structured Output**: JSON format ready for app integration

## System Requirements

- Python 3.8 or higher
- CUDA-capable GPU (optional but recommended for faster processing)
- 4GB+ RAM
- Internet connection (for initial model downloads)

## Installation

### 1. Clone or download this repository

```bash
cd memora-speech-processing
```

### 2. Run the installation script

```bash
chmod +x install.sh
./install.sh
```

This will:
- Create a Python virtual environment
- Install PyTorch (with CUDA if available)
- Install all dependencies
- Download required models
- Create output directory

### 3. Configure API Keys

Edit the `.env` file and add your API keys:

```bash
nano .env
```

Required keys:
- `HUGGINGFACE_TOKEN`: For speaker diarization (get from [HuggingFace](https://huggingface.co/settings/tokens))
  - You must also accept the license at: https://huggingface.co/pyannote/speaker-diarization-3.1
- `ANTHROPIC_API_KEY`: For Claude LLM (get from [Anthropic Console](https://console.anthropic.com/))
  - OR `OPENAI_API_KEY`: For GPT-4 (get from [OpenAI](https://platform.openai.com/api-keys))

### 4. Activate the virtual environment

```bash
source memora_env/bin/activate
```

## Usage

### Basic Usage

Process an audio file with all features enabled:

```bash
python memora_pipeline.py audio_recording.mp3
```

### Advanced Options

```bash
python memora_pipeline.py audio_file.wav \
  --language en \              # Specify language (en, es, fr, etc.)
  --speakers 2 \               # Expected number of speakers
  --output ./my_output \       # Custom output directory
  --whisper-model medium \     # Whisper model size
  --llm-provider anthropic     # LLM provider (anthropic/openai)
```

### Whisper Model Sizes

Choose based on your hardware and accuracy needs:

| Model  | Parameters | VRAM  | Speed    | Accuracy |
|--------|-----------|-------|----------|----------|
| tiny   | 39M       | ~1GB  | Fastest  | Basic    |
| base   | 74M       | ~1GB  | Fast     | Good     |
| small  | 244M      | ~2GB  | Medium   | Better   |
| medium | 769M      | ~5GB  | Slow     | Great    |
| large  | 1550M     | ~10GB | Slowest  | Best     |

**Recommendation**: Start with `base` for testing, use `medium` or `large` for production.

### Disable Speaker Diarization

If you don't have a HuggingFace token or don't need speaker identification:

```bash
python memora_pipeline.py audio_file.wav --no-diarization
```

## Output Format

The pipeline generates two JSON files:

### 1. Complete Results (`*_complete.json`)

Contains all processing stages:

```json
{
  "metadata": {
    "audio_file": "recording.mp3",
    "processed_at": "2024-01-18T10:30:00",
    "language": "en",
    "has_diarization": true
  },
  "transcription": {
    "full_text": "Complete transcription...",
    "segments": [
      {
        "start": 0.0,
        "end": 5.2,
        "text": "Hello, this is Dr. Johnson.",
        "speaker": "SPEAKER_00"
      }
    ]
  },
  "keywords": {
    "entities": {
      "persons": ["Dr. Johnson"],
      "locations": ["Memorial Hospital"],
      "dates": ["next Tuesday"],
      "times": ["2 PM"]
    },
    "combined_keywords": ["medication", "appointment", "treatment"]
  },
  "summary": {
    "overall_summary": "...",
    "speaker_summaries": {...}
  },
  "memory_summary": {...}
}
```

### 2. Memory Summary (`*_memory.json`)

App-ready format optimized for display:

```json
{
  "title": "Doctor's Appointment - Medication Review",
  "quick_summary": "Discussion about ADHD medication adjustment with Dr. Johnson.",
  "key_points": [
    "Medication dosage increased from 10mg to 15mg",
    "Follow-up appointment scheduled for next Tuesday at 2 PM",
    "Patient to maintain sleep journal"
  ],
  "people": [
    {
      "name": "Dr. Johnson",
      "context": "Primary physician"
    }
  ],
  "action_items": [
    "Take medication at 8 AM daily",
    "Bring test results to next appointment",
    "Start keeping sleep journal"
  ],
  "tags": ["medical", "appointment", "medication", "ADHD"],
  "generated_at": "2024-01-18T10:30:45",
  "model_used": "claude-sonnet-4-20250514"
}
```

## Module Usage

You can also use individual modules programmatically:

### Speech Processing Only

```python
from speech_processor import SpeechProcessor

processor = SpeechProcessor(whisper_model_size="base")
result = processor.process_audio("audio.mp3")
print(result["full_text"])
```

### Keyword Extraction Only

```python
from keyword_extractor import KeywordExtractor

extractor = KeywordExtractor()
keywords = extractor.extract_all("Your text here")
print(keywords["combined_keywords"])
```

### Summarization Only

```python
from summarizer import TextSummarizer

summarizer = TextSummarizer()
summary = summarizer.summarize_textrank("Your text here", sentences_count=3)
print(summary)
```

### LLM Processing Only

```python
from llm_processor import LLMProcessor

processor = LLMProcessor(provider="anthropic")
memory = processor.generate_memory_summary(transcription, keywords, summary)
print(memory["title"])
```

## Project Structure

```
memora-speech-processing/
├── memora_pipeline.py      # Main integration pipeline
├── speech_processor.py     # Whisper transcription + diarization
├── keyword_extractor.py    # Keyword and entity extraction
├── summarizer.py          # Text summarization
├── llm_processor.py       # LLM integration (Claude/GPT)
├── requirements.txt       # Python dependencies
├── install.sh            # Installation script
├── .env.template         # Environment variables template
├── .env                  # Your API keys (git-ignored)
└── output/               # Processing results
```

## Supported Audio Formats

The pipeline supports all formats that FFmpeg can decode:
- MP3
- WAV
- M4A
- FLAC
- OGG
- WMA
- AAC

## Troubleshooting

### CUDA Out of Memory

If you get CUDA OOM errors:
1. Use a smaller Whisper model (`tiny` or `base`)
2. Process shorter audio segments
3. Disable diarization with `--no-diarization`

### Speaker Diarization Not Working

1. Ensure you have a valid HuggingFace token in `.env`
2. Accept the pyannote model license: https://huggingface.co/pyannote/speaker-diarization-3.1
3. Check your token has read permissions

### LLM Errors

1. Verify your API key is correct in `.env`
2. Check you have API credits/quota
3. Try the alternative provider (Anthropic ↔ OpenAI)

### Slow Processing

- Use GPU if available (check with `nvidia-smi`)
- Use smaller Whisper model
- Process shorter audio files
- Disable features you don't need

## Performance Benchmarks

Approximate processing times on different hardware:

| Hardware | Model | 1 min audio | 10 min audio |
|----------|-------|-------------|--------------|
| CPU (i7) | base  | ~30s        | ~5min        |
| CPU (i7) | medium| ~2min       | ~20min       |
| GPU (RTX 3060) | base | ~5s   | ~45s         |
| GPU (RTX 3060) | medium | ~15s | ~2.5min     |

*Times include transcription + diarization + keyword extraction + summarization + LLM*

## Integration with Firebase

To upload results to Firebase:

```python
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Initialize Firebase
cred = credentials.Certificate("path/to/firebase-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load memory summary
with open("output/recording_memory.json") as f:
    memory = json.load(f)

# Upload to Firestore
doc_ref = db.collection("memories").document()
doc_ref.set(memory)
print(f"Uploaded memory with ID: {doc_ref.id}")
```

## Future Enhancements

- [ ] Real-time streaming transcription
- [ ] Multi-language detection and mixed-language support
- [ ] Emotion detection in speech
- [ ] Custom entity recognition for medical/personal terms
- [ ] Integration with calendar APIs for automatic reminders
- [ ] Web interface for processing
- [ ] Mobile app SDK

## Contributing

This is part of the Memora project. For contributions or issues, please refer to the main project repository.

## License

[Your License Here]

## Acknowledgments

- OpenAI Whisper for speech recognition
- pyannote.audio for speaker diarization
- Anthropic Claude for intelligent summarization
- The open-source NLP community

## Contact

For questions or support, contact [your contact info]
