"""
Fine-tune Llama 3.2 3B for Memora Memory Generation
Float16 version (no 4-bit quantization) - works on Windows!
Compatible with RTX 4050 (6GB VRAM) using LoRA
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


class LlamaFineTuner:
    """Fine-tune Llama 3.2 3B using PEFT/LoRA with float16"""
    
    def __init__(self, model_name="unsloth/Llama-3.2-3B-Instruct"):
        self.model_name = model_name
        self.max_seq_length = 512  # Reduced for memory
        
    def load_model(self):
        """Load model with float16 (no quantization)"""
        print("\n🔧 Loading model with float16...")
        
        # Load model in float16
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        print("✅ Model loaded successfully")
        
        # Check VRAM
        if torch.cuda.is_available():
            vram_used = torch.cuda.memory_allocated(0) / 1024**3
            vram_reserved = torch.cuda.memory_reserved(0) / 1024**3
            print(f"✅ VRAM allocated: {vram_used:.2f} GB")
            print(f"✅ VRAM reserved: {vram_reserved:.2f} GB")
        
    def prepare_model_for_training(self):
        """Add LoRA adapters for memory-efficient training"""
        print("\n🔧 Preparing model for training with LoRA...")
        
        # LoRA config - very aggressive to fit in 6GB
        lora_config = LoraConfig(
            r=8,  # Lower rank for less memory
            lora_alpha=16,
            target_modules=["q_proj", "v_proj"],  # Only 2 modules to save memory
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        # Add LoRA adapters
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        
        print("✅ Model prepared for training")
    
    def load_training_data(self, data_file="training_data.jsonl"):
        """Load training data"""
        print(f"\n📂 Loading training data from {data_file}...")
        
        # Load dataset
        dataset = load_dataset('json', data_files=data_file, split='train')
        
        print(f"✅ Loaded {len(dataset)} training examples")
        
        # Format function
        def format_example(example):
            messages = example['messages']
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False
            )
            return {"text": text}
        
        # Format dataset
        dataset = dataset.map(format_example, remove_columns=dataset.column_names)
        
        return dataset
    
    def train(self, dataset, output_dir="memora-llama-finetuned", num_epochs=2):
        """Train the model"""
        print(f"\n🏋️ Starting training for {num_epochs} epochs...")
        print(f"Output directory: {output_dir}")
        
        # Training arguments - optimized for 6GB VRAM
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=1,  # Minimal batch size
            gradient_accumulation_steps=8,  # Larger for effective batch size
            learning_rate=2e-4,
            fp16=True,  # Use float16 training
            logging_steps=5,
            save_strategy="epoch",
            optim="adamw_torch",  # Standard optimizer
            warmup_ratio=0.1,
            lr_scheduler_type="cosine",
            report_to="none",
            gradient_checkpointing=True,  # Save memory
            max_grad_norm=0.3,
        )
        
        # Tokenize function
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=self.max_seq_length,
                padding="max_length"
            )
        
        # Tokenize dataset
        print("\n📝 Tokenizing dataset...")
        tokenized_dataset = dataset.map(
            tokenize_function,
            remove_columns=dataset.column_names,
            batched=True
        )
        
        # Add labels
        tokenized_dataset = tokenized_dataset.map(
            lambda x: {"labels": x["input_ids"].copy()}
        )
        
        # Enable gradient checkpointing
        self.model.enable_input_require_grads()
        
        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
        )
        
        # Train
        print("\n⏳ Training started...")
        print("This will take 1-2 hours on RTX 4050")
        print("Watch VRAM usage to ensure it stays under 6GB\n")
        
        trainer.train()
        
        print("\n✅ Training complete!")
        
    def save_model(self, output_dir="memora-llama-finetuned"):
        """Save the fine-tuned model"""
        print(f"\n💾 Saving model to {output_dir}...")
        
        # Save LoRA adapters
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        print(f"✅ Model saved to {output_dir}")
        print(f"\n📝 To use this model:")
        print(f"   from peft import PeftModel")
        print(f"   from transformers import AutoModelForCausalLM")
        print(f"   base_model = AutoModelForCausalLM.from_pretrained('unsloth/Llama-3.2-3B-Instruct')")
        print(f"   model = PeftModel.from_pretrained(base_model, '{output_dir}')")


def main():
    """Main training function"""
    print("="*70)
    print("🦙 Llama 3.2 3B Fine-Tuning for Memora (Float16)")
    print("="*70)
    
    # Check training data exists
    if not os.path.exists("training_data.jsonl"):
        print("\n❌ Error: training_data.jsonl not found!")
        print("Please run: python generate_training_data_synthetic.py")
        return
    
    # Check CUDA
    if not torch.cuda.is_available():
        print("\n❌ Error: CUDA not available!")
        print("This script requires a CUDA-capable GPU")
        return
    
    print(f"\n✅ Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"✅ Available VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    # Initialize
    finetuner = LlamaFineTuner()
    
    # Load model
    finetuner.load_model()
    
    # Prepare for training
    finetuner.prepare_model_for_training()
    
    # Load data
    dataset = finetuner.load_training_data()
    
    # Train
    finetuner.train(dataset, num_epochs=2)
    
    # Save
    finetuner.save_model()
    
    print("\n" + "="*70)
    print("✅ Fine-tuning complete!")
    print("="*70)
    print("\n🎯 Your model is ready to use!")
    print("")


if __name__ == "__main__":
    main()
