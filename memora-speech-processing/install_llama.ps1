# Llama 3.2 3B Installation Script for Windows
# Run this in PowerShell with virtual environment activated

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Llama 3.2 3B Setup for Memora" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check CUDA
Write-Host "Checking CUDA availability..." -ForegroundColor Yellow
try {
    $cudaVersion = nvidia-smi --query-gpu=driver_version --format=csv, noheader 2>&1
    if ($LASTEXITCODE -eq 0 -and $cudaVersion) {
        Write-Host "✓ CUDA Driver: $cudaVersion" -ForegroundColor Green
    }
    else {
        throw "No CUDA"
    }
}
catch {
    Write-Host "⚠ CUDA not detected. This will be very slow on CPU!" -ForegroundColor Red
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 1
    }
}

# Check Python
Write-Host ""
Write-Host "Checking Python..." -ForegroundColor Yellow
$pythonVersion = python --version
Write-Host "✓ $pythonVersion" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install PyTorch with CUDA
Write-Host ""
Write-Host "Installing PyTorch with CUDA 12.1..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other requirements
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements_llama.txt

# Install Unsloth (special installation)
Write-Host ""
Write-Host "Installing Unsloth for fast training..." -ForegroundColor Yellow
pip install "unsloth[cu121-ampere-torch230] @ git+https://github.com/unslothai/unsloth.git"

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}')"

# Test model loading
Write-Host ""
Write-Host "Testing Llama 3.2 3B model loading..." -ForegroundColor Yellow
python test_llama_setup.py

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Generate training data: python generate_training_data.py" -ForegroundColor White
Write-Host "2. Fine-tune model: python finetune_llama.py" -ForegroundColor White
Write-Host "3. Test model: python test_finetuned_model.py" -ForegroundColor White
Write-Host ""
