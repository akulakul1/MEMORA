# Creating Fresh Llama Environment

## Steps

1. **Deactivate current environment**
   ```powershell
   deactivate
   ```

2. **Create new environment**
   ```powershell
   cd C:\Users\VIJAY\Downloads\memora-speech-processing
   python -m venv llama_env
   ```

3. **Activate new environment**
   ```powershell
   .\llama_env\Scripts\Activate.ps1
   ```

4. **Install PyTorch (compatible version)**
   ```powershell
   pip install torch==2.3.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

5. **Install transformers & dependencies**
   ```powershell
   pip install transformers==4.44.0 peft==0.12.0 bitsandbytes==0.43.1 datasets accelerate jsonlines tqdm
   ```

6. **Run fine-tuning**
   ```powershell
   python finetune_llama_simple.py
   ```

## Current Status
- [/] Step 1: Deactivating environment
