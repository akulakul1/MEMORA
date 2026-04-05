"""
Test Llama 3.2 3B Setup
Verifies the model can load on your RTX 4050
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import sys

def test_gpu():
    """Test GPU availability"""
    print("\n" + "="*60)
    print("GPU Information")
    print("="*60)
    
    if not torch.cuda.is_available():
        print("❌ CUDA not available!")
        print("This script requires a CUDA-capable GPU.")
        return False
    
    print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✓ CUDA Version: {torch.version.cuda}")
    print(f"✓ Total VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print(f"✓ Available VRAM: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3:.2f} GB")
    
    return True


def test_model_loading():
    """Test loading Llama 3.2 3B with 4-bit quantization"""
    print("\n" + "="*60)
    print("Testing Llama 3.2 3B Model Loading")
    print("="*60)
    
    model_id = "unsloth/Llama-3.2-3B-Instruct"  # Using Unsloth's version (no approval needed)
    
    print(f"\nLoading model: {model_id}")
    print("This may take a few minutes on first run...")
    
    try:
        # Configure 4-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        # Load model
        print("\nLoading model with 4-bit quantization...")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
        )
        
        print("✓ Model loaded successfully!")
        
        # Load tokenizer
        print("\nLoading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        print("✓ Tokenizer loaded successfully!")
        
        # Check VRAM usage
        vram_used = torch.cuda.memory_allocated(0) / 1024**3
        vram_reserved = torch.cuda.memory_reserved(0) / 1024**3
        
        print(f"\n✓ VRAM Used: {vram_used:.2f} GB")
        print(f"✓ VRAM Reserved: {vram_reserved:.2f} GB")
        
        if vram_used > 5.5:
            print("\n⚠ Warning: Using more than 5.5GB VRAM")
            print("  This might cause issues on a 6GB GPU")
        else:
            print("\n✓ VRAM usage is within safe limits for RTX 4050")
        
        return model, tokenizer
    
    except Exception as e:
        print(f"\n❌ Error loading model: {e}")
        return None, None


def test_inference(model, tokenizer):
    """Test basic inference"""
    print("\n" + "="*60)
    print("Testing Inference")
    print("="*60)
    
    if model is None or tokenizer is None:
        print("❌ Cannot test inference - model not loaded")
        return False
    
    # Test prompt
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Hello! Can you help me create a short summary of a doctor's appointment?"}
    ]
    
    print("\nGenerating response...")
    
    try:
        # Prepare input
        inputs = tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True
        ).to(model.device)
        
        # Generate
        import time
        start_time = time.time()
        
        outputs = model.generate(
            inputs,
            max_new_tokens=150,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        end_time = time.time()
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print("\n" + "-"*60)
        print("Model Response:")
        print("-"*60)
        print(response)
        print("-"*60)
        
        print(f"\n✓ Generation time: {end_time - start_time:.2f} seconds")
        print(f"✓ Tokens generated: {len(outputs[0]) - len(inputs[0])}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Error during inference: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Llama 3.2 3B Setup Test for RTX 4050")
    print("="*60)
    
    # Test 1: GPU
    if not test_gpu():
        print("\n❌ GPU test failed!")
        sys.exit(1)
    
    # Test 2: Model loading
    model, tokenizer = test_model_loading()
    
    if model is None:
        print("\n❌ Model loading failed!")
        print("\nTroubleshooting:")
        print("1. Make sure you have internet connection (first download)")
        print("2. Check you have enough disk space (model is ~6GB)")
        print("3. Verify CUDA is properly installed")
        print("4. Try: pip install --upgrade transformers bitsandbytes")
        sys.exit(1)
    
    # Test 3: Inference
    if not test_inference(model, tokenizer):
        print("\n❌ Inference test failed!")
        sys.exit(1)
    
    # Success!
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour RTX 4050 is ready for Llama 3.2 3B!")
    print("\nNext steps:")
    print("1. Generate training data: python generate_training_data.py")
    print("2. Fine-tune the model: python finetune_llama.py")
    print("3. Use in Memora pipeline: python memora_with_llama.py")
    print("")


if __name__ == "__main__":
    main()
