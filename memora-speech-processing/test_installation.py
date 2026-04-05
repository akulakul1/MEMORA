"""
Test script to verify Memora installation
"""

import sys
import importlib


def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✓ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"✗ {package_name or module_name}: {e}")
        return False


def test_cuda():
    """Test CUDA availability"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✓ CUDA available (Device: {torch.cuda.get_device_name(0)})")
            return True
        else:
            print("⚠ CUDA not available (CPU mode will be used)")
            return False
    except Exception as e:
        print(f"✗ CUDA test failed: {e}")
        return False


def test_models():
    """Test if models can be loaded"""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✓ spaCy model (en_core_web_sm)")
        return True
    except Exception as e:
        print(f"✗ spaCy model: {e}")
        return False


def main():
    print("="*60)
    print("Memora Installation Test")
    print("="*60)
    
    print("\nTesting Python version...")
    print(f"✓ Python {sys.version.split()[0]}")
    
    print("\nTesting core dependencies...")
    results = []
    
    # Core packages
    results.append(test_import("whisper", "openai-whisper"))
    results.append(test_import("torch", "PyTorch"))
    results.append(test_import("pyannote.audio", "pyannote.audio"))
    results.append(test_import("transformers"))
    results.append(test_import("keybert"))
    results.append(test_import("yake"))
    results.append(test_import("spacy"))
    results.append(test_import("sumy"))
    results.append(test_import("nltk"))
    
    print("\nTesting LLM clients...")
    results.append(test_import("anthropic"))
    results.append(test_import("openai"))
    
    print("\nTesting utilities...")
    results.append(test_import("dotenv", "python-dotenv"))
    results.append(test_import("numpy"))
    results.append(test_import("pandas"))
    
    print("\nTesting hardware...")
    test_cuda()
    
    print("\nTesting models...")
    test_models()
    
    print("\nTesting Memora modules...")
    results.append(test_import("speech_processor"))
    results.append(test_import("keyword_extractor"))
    results.append(test_import("summarizer"))
    results.append(test_import("llm_processor"))
    results.append(test_import("memora_pipeline"))
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All tests passed ({passed}/{total})")
        print("\nMemora is ready to use!")
        print("Run: python memora_pipeline.py --help")
    else:
        print(f"⚠ Some tests failed ({passed}/{total} passed)")
        print("\nPlease check the installation:")
        print("1. Run ./install.sh again")
        print("2. Activate virtual environment: source memora_env/bin/activate")
        print("3. Check for error messages above")
    
    print("="*60)


if __name__ == "__main__":
    main()
