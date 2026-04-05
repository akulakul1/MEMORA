# Memora Installation Script for Windows
# Run this script in PowerShell

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Memora Installation Script for Windows" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv memora_env

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\memora_env\Scripts\Activate.ps1

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Detect GPU
Write-Host ""
Write-Host "Checking for NVIDIA GPU..." -ForegroundColor Yellow
try {
    $gpu = nvidia-smi --query-gpu=name --format=csv,noheader 2>$null
    if ($gpu) {
        Write-Host "NVIDIA GPU detected: $gpu" -ForegroundColor Green
        Write-Host "Installing CUDA-enabled PyTorch..." -ForegroundColor Yellow
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    } else {
        throw "No GPU"
    }
} catch {
    Write-Host "No NVIDIA GPU detected. Installing CPU-only PyTorch..." -ForegroundColor Yellow
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
}

# Install requirements
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Download spaCy model
Write-Host ""
Write-Host "Downloading spaCy language model..." -ForegroundColor Yellow
python -m spacy download en_core_web_sm

# Download NLTK data
Write-Host ""
Write-Host "Downloading NLTK data..." -ForegroundColor Yellow
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create output directory
Write-Host ""
Write-Host "Creating output directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path output | Out-Null

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host ""
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.template .env
    Write-Host "WARNING: Please edit .env and add your API keys!" -ForegroundColor Red
} else {
    Write-Host ""
    Write-Host ".env file already exists, skipping..." -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file and add your API keys:" -ForegroundColor White
Write-Host "   - HUGGINGFACE_TOKEN (for speaker diarization)" -ForegroundColor White
Write-Host "   - ANTHROPIC_API_KEY or OPENAI_API_KEY (for LLM)" -ForegroundColor White
Write-Host ""
Write-Host "2. Activate the virtual environment:" -ForegroundColor White
Write-Host "   .\memora_env\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Run the pipeline:" -ForegroundColor White
Write-Host "   python memora_pipeline.py <audio_file>" -ForegroundColor Cyan
Write-Host ""
Write-Host "For help:" -ForegroundColor White
Write-Host "   python memora_pipeline.py --help" -ForegroundColor Cyan
Write-Host ""
