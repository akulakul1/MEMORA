# Memora Quick Start Guide

Get up and running with Memora speech processing in 5 minutes!

## Prerequisites

- Windows/Mac/Linux with Python 3.8+
- GPU with CUDA support (optional but recommended)
- Internet connection

## Step 1: Installation (2 minutes)

```bash
# Clone/download the project
cd memora-speech-processing

# Run installation script
chmod +x install.sh
./install.sh

# Activate virtual environment
source memora_env/bin/activate  # Linux/Mac
# OR
memora_env\Scripts\activate     # Windows
```

## Step 2: Configure API Keys (1 minute)

Edit `.env` file:

```bash
nano .env  # or use any text editor
```

Add your keys:
```
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### Where to get keys:

1. **HuggingFace Token** (FREE):
   - Go to: https://huggingface.co/settings/tokens
   - Create new token with read access
   - Accept license: https://huggingface.co/pyannote/speaker-diarization-3.1

2. **Anthropic API Key** (Requires credits):
   - Go to: https://console.anthropic.com/
   - Create API key
   - Add credits to account

## Step 3: Test Installation (30 seconds)

```bash
python test_installation.py
```

You should see all ✓ checkmarks.

## Step 4: Process Your First Audio (1 minute)

```bash
# Basic usage
python memora_pipeline.py your_audio.mp3

# With all options
python memora_pipeline.py recording.wav \
  --language en \
  --speakers 2 \
  --output ./my_results \
  --whisper-model base
```

## Step 5: Check Results

Find outputs in `output/` folder:
- `*_complete.json` - Full processing results
- `*_memory.json` - App-ready memory summary

## VS Code Users

1. Open workspace:
   ```bash
   code memora.code-workspace
   ```

2. Select Python interpreter:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type "Python: Select Interpreter"
   - Choose `./memora_env/bin/python`

3. Run with F5 or use tasks:
   - `Ctrl+Shift+B` → "Process Sample Audio"

## Common Issues

### "No module named 'whisper'"
- Make sure virtual environment is activated
- Run: `source memora_env/bin/activate`

### "CUDA out of memory"
- Use smaller model: `--whisper-model tiny`
- Or disable GPU: `export CUDA_VISIBLE_DEVICES=-1`

### "Invalid API key"
- Check `.env` file has correct keys
- Verify no extra spaces or quotes

### Diarization not working
- Ensure HuggingFace token is valid
- Accept model license (see link above)
- Or disable: `--no-diarization`

## Next Steps

- Read full [README.md](README.md) for detailed documentation
- Integrate with Firebase (see Firebase section in README)
- Customize for your use case
- Build mobile app interface

## Example Output

When you process an audio file, you'll get:

```
==========================================
Processing: doctor_visit.mp3
==========================================

Step 1: Transcribing audio...
✓ Transcription complete (en)

Step 2: Extracting keywords and entities...
✓ Found 12 keywords
✓ Found 8 entities

Step 3: Generating summaries...
✓ Summaries generated

Step 4: Generating AI-powered memory summary...
✓ Memory summary generated

✓ Complete results saved to: output/doctor_visit_complete.json
✓ Memory summary saved to: output/doctor_visit_memory.json

==========================================
PROCESSING SUMMARY
==========================================

Language: en
Speaker Diarization: Enabled

Full Transcription:
Hello, this is Dr. Johnson. We're reviewing your medication today...

KEY ENTITIES:
  Persons: Dr. Johnson, Sarah
  Locations: Memorial Hospital
  Dates: next Tuesday
  Times: 2 PM, 8 AM

KEYWORDS:
  medication, appointment, treatment, dosage, symptoms...

AI-GENERATED MEMORY SUMMARY:

Title: Doctor's Appointment - Medication Review

Quick Summary:
  Discussion about ADHD medication adjustment...

Key Points:
  1. Medication dosage increased from 10mg to 15mg
  2. Follow-up appointment scheduled
  3. Patient to maintain sleep journal

Action Items:
  • Take medication at 8 AM daily
  • Bring test results to next appointment

Tags: medical, appointment, medication, ADHD
```

## Support

For issues or questions:
- Check the full README.md
- Review troubleshooting section
- Test with `test_installation.py`

Happy processing! 🎙️🧠
