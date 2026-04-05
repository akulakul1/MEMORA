"""
Run Memora Pipeline with .env Loading
This script ensures .env file is loaded before processing
"""

import sys
import os
from pathlib import Path

# Load .env file FIRST
try:
    from dotenv import load_dotenv
    
    # Load from current directory
    env_path = Path('.env')
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded .env from: {env_path.absolute()}")
    else:
        print(f"⚠️  Warning: .env file not found at {env_path.absolute()}")
    
except ImportError:
    print("⚠️  Warning: python-dotenv not installed")
    print("Install it: pip install python-dotenv")

# Check if keys are loaded
hf_token = os.getenv("HUGGINGFACE_TOKEN")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

print("\nAPI Key Status:")
print(f"  HUGGINGFACE_TOKEN: {'✓ Loaded' if hf_token else '✗ Not found'}")
print(f"  ANTHROPIC_API_KEY: {'✓ Loaded' if anthropic_key else '✗ Not found'}")
print(f"  OPENAI_API_KEY: {'✓ Loaded' if openai_key else '✗ Not found'}")

if not hf_token:
    print("\n⚠️  Note: Speaker diarization will be disabled without HUGGINGFACE_TOKEN")

if not anthropic_key and not openai_key:
    print("\n⚠️  Note: AI-powered summaries will be disabled without LLM API key")

print("\n" + "="*60)

# Now import and run the pipeline
if __name__ == "__main__":
    from memora_pipeline import main
    main()
