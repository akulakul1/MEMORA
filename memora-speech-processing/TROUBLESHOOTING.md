# Memora Troubleshooting Guide

## Quick Fix for Your Current Issues

You have 3 failed tests. Here's how to fix them:

### Step 1: Run the Fix Script

```powershell
# Make sure virtual environment is activated
.\memora_env\Scripts\Activate.ps1

# Run the fix script
python fix_installation.py
```

This will automatically:
1. Install the spaCy model
2. Upgrade huggingface_hub
3. Fix sentence-transformers compatibility

### Step 2: Verify the Fixes

```powershell
python test_installation.py
```

You should now see 19/19 tests passing!

---

## Manual Fixes (If Script Doesn't Work)

### Issue 1: spaCy Model Not Found

**Error:**
```
✗ spaCy model: [E050] Can't find model 'en_core_web_sm'
```

**Fix:**
```powershell
# Download the model directly
python -m spacy download en_core_web_sm

# If that fails, try with full path
python -m spacy download en_core_web_sm --no-deps

# Alternative: Download and install manually
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0-py3-none-any.whl
```

**Verify:**
```powershell
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✓ spaCy model loaded')"
```

### Issue 2: huggingface_hub ImportError

**Error:**
```
cannot import name 'cached_download' from 'huggingface_hub'
```

**Cause:** Older version of huggingface_hub using deprecated API

**Fix:**
```powershell
# Upgrade huggingface_hub
pip install --upgrade huggingface_hub

# If still failing, reinstall
pip uninstall -y huggingface_hub
pip install huggingface_hub>=0.20.0

# Also upgrade sentence-transformers
pip install --upgrade sentence-transformers
```

**Verify:**
```powershell
python -c "from huggingface_hub import hf_hub_download; print('✓ huggingface_hub working')"
```

### Issue 3: keyword_extractor ImportError

**Error:**
```
keyword_extractor: cannot import name 'cached_download'
```

**Fix:**
This is related to Issue 2. After fixing huggingface_hub:

```powershell
# Reinstall KeyBERT
pip uninstall -y keybert
pip install keybert

# Reinstall sentence-transformers
pip uninstall -y sentence-transformers
pip install sentence-transformers>=2.3.0
```

**Verify:**
```powershell
python -c "from keyword_extractor import KeywordExtractor; print('✓ keyword_extractor working')"
```

---

## Common Installation Issues

### Issue: "Python is not recognized"

**Fix:**
1. Add Python to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" in User Variables
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX`
   - Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX\Scripts`
2. Restart terminal
3. Verify: `python --version`

### Issue: "pip is not recognized"

**Fix:**
Use `python -m pip` instead:
```powershell
python -m pip install -r requirements.txt
```

### Issue: Virtual Environment Not Activating

**Symptoms:**
- Commands fail with "module not found"
- No `(memora_env)` prefix in terminal

**Fix:**
```powershell
# PowerShell
.\memora_env\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again
.\memora_env\Scripts\Activate.ps1

# Verify activation (should show virtual env path):
where python
```

### Issue: CUDA Out of Memory

**Error:**
```
RuntimeError: CUDA out of memory
```

**Fix:**
```powershell
# Use smaller Whisper model
python memora_pipeline.py audio.mp3 --whisper-model tiny

# Or force CPU usage
$env:CUDA_VISIBLE_DEVICES="-1"
python memora_pipeline.py audio.mp3
```

### Issue: Torch Not Finding CUDA

**Symptoms:**
```
Testing hardware...
⚠ CUDA not available (CPU mode will be used)
```

**Fix:**
```powershell
# Check if NVIDIA driver is installed
nvidia-smi

# If driver is installed but CUDA not detected:
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify CUDA:
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Issue: FFmpeg Not Found

**Error:**
```
FileNotFoundError: ffmpeg not found
```

**Fix:**
```powershell
# Install using chocolatey (if you have it):
choco install ffmpeg

# Or download manually:
# 1. Go to: https://github.com/BtbN/FFmpeg-Builds/releases
# 2. Download ffmpeg-master-latest-win64-gpl.zip
# 3. Extract to C:\ffmpeg
# 4. Add C:\ffmpeg\bin to PATH
```

### Issue: SSL Certificate Error

**Error:**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**Fix:**
```powershell
# Temporary fix (testing only):
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Permanent fix: Update certificates
pip install --upgrade certifi
```

### Issue: Permission Denied

**Error:**
```
PermissionError: [WinError 5] Access is denied
```

**Fix:**
```powershell
# Run PowerShell as Administrator

# Or install in user space:
pip install --user -r requirements.txt
```

---

## Verification Commands

After fixing issues, run these to verify:

```powershell
# 1. Check Python
python --version

# 2. Check virtual environment
where python  # Should point to memora_env

# 3. Check PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"

# 4. Check Whisper
python -c "import whisper; print('✓ Whisper installed')"

# 5. Check spaCy
python -c "import spacy; spacy.load('en_core_web_sm'); print('✓ spaCy model loaded')"

# 6. Check KeyBERT
python -c "from keybert import KeyBERT; print('✓ KeyBERT installed')"

# 7. Check pyannote
python -c "from pyannote.audio import Pipeline; print('✓ pyannote installed')"

# 8. Run full test
python test_installation.py
```

---

## Still Having Issues?

### Collect Diagnostic Information

```powershell
# Create a diagnostic report
python -c "
import sys
import torch
print('Python:', sys.version)
print('Python path:', sys.executable)
print('PyTorch:', torch.__version__)
print('CUDA:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU:', torch.cuda.get_device_name(0))
" > diagnostic.txt

# Check installed packages
pip list > installed_packages.txt

# Share these files when asking for help
```

### Clean Reinstall

If all else fails:

```powershell
# 1. Delete virtual environment
Remove-Item -Recurse -Force memora_env

# 2. Delete cache
pip cache purge

# 3. Reinstall from scratch
python -m venv memora_env
.\memora_env\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 4. Test
python test_installation.py
```

---

## Component-Specific Issues

### Whisper Issues

```powershell
# Test Whisper separately
python -c "
import whisper
model = whisper.load_model('tiny')
print('✓ Whisper working')
"
```

### Pyannote Issues

```powershell
# Pyannote requires accepting license
# Go to: https://huggingface.co/pyannote/speaker-diarization-3.1
# Click "Agree and access repository"

# Test pyannote
python -c "
from pyannote.audio import Pipeline
print('✓ pyannote imported')
"
```

### LLM Integration Issues

```powershell
# Test Anthropic
python -c "
from anthropic import Anthropic
print('✓ Anthropic SDK installed')
"

# Test OpenAI
python -c "
from openai import OpenAI
print('✓ OpenAI SDK installed')
"
```

---

## Performance Optimization

### Speed Up Processing

```powershell
# Use smaller models for faster processing
python memora_pipeline.py audio.mp3 --whisper-model tiny --no-diarization

# Process shorter clips
# Split long audio into 5-minute chunks before processing
```

### Reduce Memory Usage

```powershell
# Set memory limits
$env:PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
python memora_pipeline.py audio.mp3
```

---

## Getting Help

1. **Check the logs**: Look for error messages in terminal output
2. **Run diagnostics**: `python test_installation.py`
3. **Try the fix script**: `python fix_installation.py`
4. **Check Python version**: Must be 3.8+
5. **Verify virtual environment**: Should see `(memora_env)` in prompt
6. **Update all packages**: `pip install --upgrade -r requirements.txt`

---

## Success Checklist

- [ ] Virtual environment activated
- [ ] All packages installed without errors
- [ ] spaCy model downloaded
- [ ] Test script shows 19/19 passing
- [ ] Can import all modules
- [ ] Sample audio processes successfully

When all items are checked, you're ready to use Memora! 🎉
