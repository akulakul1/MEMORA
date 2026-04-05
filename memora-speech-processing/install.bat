@echo off
REM Memora Installation Script for Windows (Batch)
REM Run this if PowerShell script doesn't work

echo ==========================================
echo Memora Installation Script for Windows
echo ==========================================
echo.

REM Check Python
echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv memora_env

REM Activate virtual environment
echo.
echo Activating virtual environment...
call memora_env\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Check for GPU
echo.
echo Checking for NVIDIA GPU...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo NVIDIA GPU detected. Installing CUDA-enabled PyTorch...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
) else (
    echo No NVIDIA GPU detected. Installing CPU-only PyTorch...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

REM Install requirements
echo.
echo Installing Python dependencies...
pip install -r requirements.txt

REM Download spaCy model
echo.
echo Downloading spaCy language model...
python -m spacy download en_core_web_sm

REM Download NLTK data
echo.
echo Downloading NLTK data...
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

REM Create output directory
echo.
echo Creating output directory...
if not exist output mkdir output

REM Create .env file
if not exist .env (
    echo.
    echo Creating .env file from template...
    copy .env.template .env
    echo.
    echo WARNING: Please edit .env and add your API keys!
) else (
    echo.
    echo .env file already exists, skipping...
)

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Activate virtual environment: memora_env\Scripts\activate.bat
echo 3. Run pipeline: python memora_pipeline.py audio_file.mp3
echo.
pause
