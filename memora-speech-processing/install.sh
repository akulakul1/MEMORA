#!/bin/bash

# Memora Installation Script
# This script sets up the Memora speech processing pipeline

set -e

echo "=========================================="
echo "Memora Installation Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv memora_env
source memora_env/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch (with CUDA support if available)
echo ""
echo "Installing PyTorch..."
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected. Installing CUDA-enabled PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    echo "No NVIDIA GPU detected. Installing CPU-only PyTorch..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install requirements
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo ""
echo "Downloading spaCy language model..."
python -m spacy download en_core_web_sm

# Download NLTK data
echo ""
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Create output directory
echo ""
echo "Creating output directory..."
mkdir -p output

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo ""
    echo ".env file already exists, skipping..."
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - HUGGINGFACE_TOKEN (for speaker diarization)"
echo "   - ANTHROPIC_API_KEY or OPENAI_API_KEY (for LLM)"
echo ""
echo "2. Activate the virtual environment:"
echo "   source memora_env/bin/activate"
echo ""
echo "3. Run the pipeline:"
echo "   python memora_pipeline.py <audio_file>"
echo ""
echo "For help:"
echo "   python memora_pipeline.py --help"
echo ""
