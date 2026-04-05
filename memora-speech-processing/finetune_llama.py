"""
Fine-tune Llama 3.2 3B for Memora Memory Generation
Optimized for RTX 4050 (6GB VRAM)
"""

import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import os
import json


class LlamaFineTuner:
    """Fine-tune Llama 3.2 3B for memory generation"""
    
    def __init__(self, model_name="unsloth/Llama-3.2-3B-Instruct"):
        self.model_name = model_name
        self.max_seq_length = 2048  # Reduced for 6GB VRAM
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """Load model with 4-bit quantization"""
        print("\n" + "="*60)
        print("Loading Llama 3.2 3B Model")
        print("="*60)
        
        print(f"\nModel: {self.model_name}")
        print(f"Max sequence length: {self.max_seq_length}")
        print(f"Using 4-bit quantization for 6GB VRAM")
        
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_name,
            max_seq_length=self.max_seq_length,
            dtype=torch.float16,
            load_in_4bit=True,
        )
        
        print("\n✓ Model loaded successfully!")
        
        # Check VRAM
        vram_used = torch.cuda.memory_allocated(0) / 1024**3
        print(f"✓ VRAM used: {vram_used:.2f} GB")
    
    def prepare_model_for_training(self):
        """Add LoRA adapters for efficient fine-tuning"""
        print("\n" + "="*60)
        print("Preparing Model for Training (LoRA)")
        print("="*60)
        
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r=16,  # LoRA rank
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ],
            lora_alpha=16,
            lora_dropout=0,
            bias="none",
            use_gradient_checkpointing=True,
            random_state=42,
        )
        
        print("\n✓ LoRA adapters added")
        print("✓ Model ready for training")
    
    def load_training_data(self, data_file="training_data.jsonl"):
        """Load and prepare training data"""
        print("\n" + "="*60)
        print("Loading Training Data")
        print("="*60)
        
        if not os.path.exists(data_file):
            raise FileNotFoundError(
                f"Training data not found: {data_file}\n"
                "Please run: python generate_training_data.py"
            )
        
        # Load dataset
        dataset = load_dataset('json', data_files=data_file, split='train')
        
        print(f"\n✓ Loaded {len(dataset)} training examples")
        
        # Format dataset for training
        def format_prompts(examples):
            texts = []
            for messages in examples["messages"]:
                # Use Llama chat template
                text = self.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=False
                )
                texts.append(text)
            return {"text": texts}
        
        dataset = dataset.map(
            format_prompts,
            batched=True,
        )
        
        print("✓ Dataset formatted for training")
        
        return dataset
    
    def train(
        self,
        dataset,
        output_dir="memora-llama-3.2-3b-finetuned",
        num_epochs=3,
        batch_size=2,
        learning_rate=2e-4
    ):
        """Train the model"""
        print("\n" + "="*60)
        print("Starting Training")
        print("="*60)
        
        print(f"\nTraining configuration:")
        print(f"  Output directory: {output_dir}")
        print(f"  Epochs: {num_epochs}")
        print(f"  Batch size: {batch_size}")
        print(f"  Learning rate: {learning_rate}")
        print(f"  Training examples: {len(dataset)}")
        
        # Calculate steps
        gradient_accumulation_steps = 4
        total_steps = (len(dataset) * num_epochs) // (batch_size * gradient_accumulation_steps)
        
        print(f"  Total training steps: {total_steps}")
        print(f"\nEstimated time: {total_steps * 2 / 60:.1f} minutes")
        
        # Training arguments optimized for RTX 4050
        training_args = TrainingArguments(
            output_dir=output_dir,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            warmup_steps=10,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            fp16=True,
            logging_steps=10,
            save_steps=50,
            save_total_limit=2,
            optim="adamw_8bit",  # Memory-efficient optimizer
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
        )
        
        # Create trainer
        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=dataset,
            dataset_text_field="text",
            max_seq_length=self.max_seq_length,
            args=training_args,
        )
        
        # Start training
        print("\n" + "-"*60)
        print("Training started...")
        print("-"*60 + "\n")
        
        trainer.train()
        
        print("\n" + "-"*60)
        print("Training complete!")
        print("-"*60)
    
    def save_model(self, output_dir="memora-llama-3.2-3b-finetuned"):
        """Save the fine-tuned model"""
        print("\n" + "="*60)
        print("Saving Model")
        print("="*60)
        
        # Save LoRA adapters
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        print(f"\n✓ Model saved to: {output_dir}")
        
        # Also save merged model (optional, but recommended)
        print("\nSaving merged model (combines base + LoRA)...")
        merged_output = f"{output_dir}_merged"
        
        self.model.save_pretrained_merged(
            merged_output,
            self.tokenizer,
            save_method="merged_16bit",
        )
        
        print(f"✓ Merged model saved to: {merged_output}")
        
        # Save training info
        info = {
            "base_model": self.model_name,
            "max_seq_length": self.max_seq_length,
            "model_type": "llama-3.2-3b",
            "task": "memory_generation",
            "project": "memora"
        }
        
        with open(f"{output_dir}/training_info.json", 'w') as f:
            json.dump(info, f, indent=2)
        
        print(f"✓ Training info saved")


def main():
    """Main training function"""
    print("="*60)
    print("Llama 3.2 3B Fine-tuning for Memora")
    print("Optimized for RTX 4050 (6GB VRAM)")
    print("="*60)
    
    # Check CUDA
    if not torch.cuda.is_available():
        print("\n❌ Error: CUDA not available!")
        print("This script requires a CUDA-capable GPU.")
        return
    
    print(f"\n✓ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✓ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    # Check for training data
    if not os.path.exists("training_data.jsonl"):
        print("\n❌ Error: training_data.jsonl not found")
        print("\nPlease generate training data first:")
        print("  python generate_training_data.py")
        return
    
    # Get training parameters
    print("\n" + "-"*60)
    print("Training Configuration")
    print("-"*60)
    
    try:
        num_epochs = int(input("\nNumber of epochs (default 3): ") or "3")
        batch_size = int(input("Batch size (default 2, max 2 for 6GB VRAM): ") or "2")
        
        if batch_size > 2:
            print("\n⚠ Warning: Batch size > 2 may cause OOM on 6GB VRAM")
            confirm = input("Continue? (y/n): ")
            if confirm.lower() != 'y':
                batch_size = 2
    except ValueError:
        num_epochs = 3
        batch_size = 2
    
    print(f"\nFinal configuration:")
    print(f"  Epochs: {num_epochs}")
    print(f"  Batch size: {batch_size}")
    
    # Initialize fine-tuner
    finetuner = LlamaFineTuner()
    
    # Load model
    finetuner.load_model()
    
    # Prepare for training
    finetuner.prepare_model_for_training()
    
    # Load training data
    dataset = finetuner.load_training_data("training_data.jsonl")
    
    # Train
    finetuner.train(
        dataset,
        output_dir="memora-llama-3.2-3b-finetuned",
        num_epochs=num_epochs,
        batch_size=batch_size
    )
    
    # Save model
    finetuner.save_model("memora-llama-3.2-3b-finetuned")
    
    print("\n" + "="*60)
    print("✅ Fine-tuning Complete!")
    print("="*60)
    print("\nYour fine-tuned model is ready to use!")
    print("\nNext steps:")
    print("1. Test the model: python test_finetuned_model.py")
    print("2. Compare with Claude: python compare_models.py")
    print("3. Use in Memora: python memora_with_llama.py")
    print("")


if __name__ == "__main__":
    main()
