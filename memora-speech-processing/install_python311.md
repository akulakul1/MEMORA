# Installing Python 3.11 for Llama Fine-Tuning

## Current Status
- ❌ Python 3.11: Not installed
- ✅ Python 3.13: Installed (but no CUDA PyTorch)
- ✅ Training data: Ready (100 examples)

## Step 1: Download Python 3.11

1. **Visit:** https://www.python.org/downloads/release/python-31110/
2. **Scroll down** to "Files"
3. **Download:** "Windows installer (64-bit)"
   - File: `python-3.11.10-amd64.exe`

## Step 2: Install Python 3.11

1. **Run the installer**
2. ✅ **CHECK:** "Add python.exe to PATH"
3. ✅ **CHECK:** "Install launcher for all users"
4. **Click:** "Install Now"
5. **Wait** for installation (~2-3 minutes)

> [!IMPORTANT]
> This will install Python 3.11 **alongside** Python 3.13 - you'll have both!

## Step 3: Verify Installation

After installation, **close and reopen PowerShell**, then run:
```powershell
py -3.11 --version
```

You should see: `Python 3.11.10`

## Step 4: Return Here

Once Python 3.11 is installed and verified, let me know and I'll:
1. Delete the broken `llama_env`
2. Create new `llama_env_311` with Python 3.11
3. Install PyTorch with CUDA support
4. Run fine-tuning

---

## Alternative: Skip This

If you change your mind, just say "use Gemini instead" and we'll switch back to the working solution.

**Estimated total time after Python 3.11 install:**
- Setup: 30 minutes
- Training: 1-2 hours
- Total: 1.5-2.5 hours
