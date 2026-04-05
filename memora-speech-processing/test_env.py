"""
Test .env File Loading
Checks if your API keys are being loaded correctly
"""

import os
from pathlib import Path


def test_env_file():
    """Test if .env file exists and is readable"""
    print("\n" + "="*60)
    print("Testing .env File Configuration")
    print("="*60 + "\n")
    
    # Check if .env exists
    env_path = Path(".env")
    if not env_path.exists():
        print("✗ .env file not found in current directory")
        print(f"  Current directory: {os.getcwd()}")
        print("\nCreate .env file from template:")
        print("  copy .env.template .env")
        return False
    
    print(f"✓ .env file found at: {env_path.absolute()}")
    
    # Read .env file
    print("\n" + "-"*60)
    print("Contents of .env file:")
    print("-"*60)
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    keys_found = {}
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line and not line.startswith('#'):
            # Check if it looks like a key=value pair
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Mask the value for security
                if value and value != 'your_huggingface_token_here' and value != 'your_anthropic_api_key_here':
                    masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                    print(f"Line {i}: {key} = {masked_value}")
                    keys_found[key] = True
                else:
                    print(f"Line {i}: {key} = [NOT SET]")
                    keys_found[key] = False
            else:
                print(f"Line {i}: {line[:50]}")
    
    # Check environment variables
    print("\n" + "-"*60)
    print("Environment Variables (what Python sees):")
    print("-"*60)
    
    required_keys = ['HUGGINGFACE_TOKEN', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
    env_status = {}
    
    for key in required_keys:
        value = os.getenv(key)
        if value:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✓ {key} = {masked}")
            env_status[key] = True
        else:
            print(f"✗ {key} = NOT FOUND")
            env_status[key] = False
    
    # Summary
    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    
    issues = []
    
    if not any(env_status.values()):
        issues.append("❌ No API keys are loaded into environment")
        issues.append("   The .env file is not being loaded by python-dotenv")
    
    if keys_found.get('HUGGINGFACE_TOKEN') == False:
        issues.append("⚠️  HUGGINGFACE_TOKEN not set in .env file")
    
    if keys_found.get('ANTHROPIC_API_KEY') == False and keys_found.get('OPENAI_API_KEY') == False:
        issues.append("⚠️  No LLM API key (ANTHROPIC_API_KEY or OPENAI_API_KEY) set")
    
    if issues:
        print("\nIssues Found:")
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✓ All API keys configured correctly!")
        return True


def show_fix_instructions():
    """Show how to fix the issues"""
    print("\n" + "="*60)
    print("How to Fix:")
    print("="*60)
    
    print("\n1. Make sure .env file is in the SAME directory as your scripts")
    print(f"   Current directory: {os.getcwd()}")
    
    print("\n2. Edit .env file with a text editor:")
    print("   notepad .env")
    
    print("\n3. Your .env file should look like this:")
    print("-"*60)
    print("HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxx")
    print("ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx")
    print("OPENAI_API_KEY=sk-xxxxxxxxxxxxx")
    print("-"*60)
    
    print("\n4. IMPORTANT - No spaces, quotes, or extra characters:")
    print("   ✓ CORRECT:   ANTHROPIC_API_KEY=sk-ant-12345")
    print("   ✗ WRONG:     ANTHROPIC_API_KEY = sk-ant-12345")
    print("   ✗ WRONG:     ANTHROPIC_API_KEY=\"sk-ant-12345\"")
    print("   ✗ WRONG:     ANTHROPIC_API_KEY='sk-ant-12345'")
    
    print("\n5. Save the file and try again")
    
    print("\n" + "="*60)
    print("Where to Get API Keys:")
    print("="*60)
    print("\nHuggingFace Token (FREE):")
    print("  1. Go to: https://huggingface.co/settings/tokens")
    print("  2. Create new token with 'read' access")
    print("  3. Accept license: https://huggingface.co/pyannote/speaker-diarization-3.1")
    
    print("\nAnthropic API Key (Paid):")
    print("  1. Go to: https://console.anthropic.com/")
    print("  2. Create API key")
    print("  3. Add credits to account")
    
    print("\nOpenAI API Key (Paid - Alternative):")
    print("  1. Go to: https://platform.openai.com/api-keys")
    print("  2. Create new secret key")
    print("  3. Add credits to account")


def test_loading_with_dotenv():
    """Test loading with python-dotenv"""
    print("\n" + "="*60)
    print("Testing python-dotenv Loading")
    print("="*60 + "\n")
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv is installed")
        
        # Try to load
        result = load_dotenv()
        if result:
            print("✓ .env file loaded successfully")
            
            # Check again
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            
            if hf_token:
                print(f"✓ HUGGINGFACE_TOKEN loaded: {hf_token[:8]}...")
            if anthropic_key:
                print(f"✓ ANTHROPIC_API_KEY loaded: {anthropic_key[:12]}...")
            
            if not hf_token and not anthropic_key:
                print("✗ Keys still not loaded. Check .env file format")
                return False
            
            return True
        else:
            print("✗ .env file not found or couldn't be loaded")
            return False
    
    except ImportError:
        print("✗ python-dotenv not installed")
        print("  Install it: pip install python-dotenv")
        return False


if __name__ == "__main__":
    # Test .env file
    success = test_env_file()
    
    # Test dotenv loading
    dotenv_success = test_loading_with_dotenv()
    
    if not success or not dotenv_success:
        show_fix_instructions()
    else:
        print("\n✅ Everything is configured correctly!")
        print("\nYou can now run:")
        print("  python memora_pipeline.py your_audio.mp3")
    
    print("\n")
