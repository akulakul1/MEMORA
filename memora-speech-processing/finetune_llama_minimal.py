"""
Fine-tune Llama 3.2 3B - Ultra Low Memory Version
Optimized for 6GB VRAM (RTX 4050)
"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model
from datasets import load_dataset
import os


def main():
    print("="*70)
    print("🦙 Llama 3.2 3B Fine-Tuning - Ultra Memory Efficient")
    print("="*70)
    
    if not torch.cuda.is_available():
        print("\n❌ CUDA not available!")
        return
    
    print(f"\n✅ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    # Load model with aggressive memory settings
    print("\n🔧 Loading model...")
    model = AutoModelForCausalLM.from_pretrained(
        "unsloth/Llama-3.2-3B-Instruct",
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    
    tokenizer = AutoTokenizer.from_pretrained("unsloth/Llama-3.2-3B-Instruct")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print("✅ Model loaded")
    print(f"VRAM used: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
    
    # Ultra-aggressive LoRA
    print("\n🔧 Adding LoRA adapters...")
    lora_config = LoraConfig(
        r=4,  # Very low rank
        lora_alpha=8,
        target_modules=["q_proj"],  # Only one module!
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    model.enable_input_require_grads()
    
    # Load data
    print("\n📂 Loading training data...")
    dataset = load_dataset('json', data_files="training_data.jsonl", split='train')
    
    def format_example(example):
        messages = example['messages']
        text = tokenizer.apply_chat_template(messages, tokenize=False)
        return {"text": text}
    
    dataset = dataset.map(format_example, remove_columns=dataset.column_names)
    
    # Tokenize with very short sequences
    def tokenize(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=256,  # Very short!
            padding="max_length"
        )
    
    print("📝 Tokenizing...")
    dataset = dataset.map(tokenize, remove_columns=dataset.column_names, batched=True)
    dataset = dataset.map(lambda x: {"labels": x["input_ids"].copy()})
    
    # Ultra memory-efficient training args
    training_args = TrainingArguments(
        output_dir="memora-llama-finetuned",
        num_train_epochs=1,  # Just 1 epoch
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,  # Very large
        learning_rate=3e-4,
        fp16=True,
        logging_steps=2,
        save_strategy="epoch",
        optim="adamw_torch_fused",  # Fast optimizer
        warmup_steps=5,
        lr_scheduler_type="constant",
        gradient_checkpointing=True,
        max_grad_norm=0.3,
        dataloader_num_workers=0,  # No multiprocessing
    )
    
    print("\n⏳ Starting training...")
    print(f"Total steps: {len(dataset) // training_args.gradient_accumulation_steps}")
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
    )
    
    try:
        trainer.train()
        print("\n✅ Training complete!")
        
        model.save_pretrained("memora-llama-finetuned")
        tokenizer.save_pretrained("memora-llama-finetuned")
        print(f"✅ Model saved!")
        
    except RuntimeError as e:
        if "out of memory" in str(e):
            print("\n❌ OUT OF MEMORY!")
            print("\nYour RTX 4050 (6GB) is too small for fine-tuning Llama 3.2 3B.")
            print("\nOptions:")
            print("1. Use Gemini API (FREE, 88-92% quality, already working)")
            print("2. Use base Llama without fine-tuning (75-80% quality)")
            print("3. Use cloud GPU (Google Colab, etc.)")
        raise


if __name__ == "__main__":
    main()
