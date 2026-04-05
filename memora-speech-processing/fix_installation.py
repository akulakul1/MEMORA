"""
Memora Installation Fix Script
Fixes common installation issues on Windows
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and print status"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✓ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False


def main():
    print("\n" + "="*60)
    print("Memora Installation Fix Script")
    print("="*60)
    
    fixes_applied = []
    
    # Fix 1: Install spaCy model
    print("\n[Fix 1/3] Installing spaCy model...")
    if run_command(
        "python -m spacy download en_core_web_sm",
        "Downloading spaCy model"
    ):
        fixes_applied.append("spaCy model installed")
    
    # Fix 2: Upgrade huggingface_hub to fix cached_download issue
    print("\n[Fix 2/3] Fixing huggingface_hub compatibility...")
    if run_command(
        "pip install --upgrade huggingface_hub",
        "Upgrading huggingface_hub"
    ):
        fixes_applied.append("huggingface_hub upgraded")
    
    # Fix 3: Reinstall sentence-transformers with compatible version
    print("\n[Fix 3/3] Fixing sentence-transformers...")
    commands = [
        ("pip uninstall -y sentence-transformers", "Removing old sentence-transformers"),
        ("pip install sentence-transformers>=2.3.0", "Installing compatible sentence-transformers")
    ]
    
    success = True
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            success = False
    
    if success:
        fixes_applied.append("sentence-transformers fixed")
    
    # Summary
    print("\n" + "="*60)
    print("Fix Summary")
    print("="*60)
    
    if fixes_applied:
        print("\n✓ Fixes applied:")
        for fix in fixes_applied:
            print(f"  • {fix}")
        
        print("\n" + "="*60)
        print("Next Step: Run the test again")
        print("="*60)
        print("\nRun: python test_installation.py")
    else:
        print("\n✗ No fixes were successfully applied")
        print("\nPlease try manual fixes:")
        print("1. python -m spacy download en_core_web_sm")
        print("2. pip install --upgrade huggingface_hub")
        print("3. pip install --upgrade sentence-transformers")
    
    print("")


if __name__ == "__main__":
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        print("\n⚠️  WARNING: Virtual environment may not be activated!")
        print("Please activate it first:")
        print("  PowerShell: .\\memora_env\\Scripts\\Activate.ps1")
        print("  CMD: memora_env\\Scripts\\activate.bat")
        print("")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(0)
    
    main()
