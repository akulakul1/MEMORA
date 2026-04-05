"""
Quick test to download Llama model
"""
import torch
from transformers import AutoTokenizer

print("Testing HuggingFace download...")
print("This will download the tokenizer first (~1MB)")

model_id = "unsloth/Llama-3.2-3B-Instruct"

try:
    print(f"\nDownloading tokenizer from: {model_id}")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    print("✓ Tokenizer downloaded successfully!")
    print("\nIf this worked, the full model download should work too.")
    print("Run: python test_llama_setup.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Check internet connection")
    print("2. Login to HuggingFace: huggingface-cli login")
    print("3. Check firewall/proxy settings")
