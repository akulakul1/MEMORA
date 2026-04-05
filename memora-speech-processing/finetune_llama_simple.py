"""
Fine-tune Llama 3.2 3B for Memora Memory Generation
Simplified version using standard HuggingFace transformers + PEFT
Compatible with RTX 4050 (6GB VRAM)
"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
import os


class LlamaFineTuner:
    """Fine-tune Llama 3.2 3B using PEFT/LoRA"""
    
    def __init__(self, model_name="unsloth/Llama-3.2-3B-Instruct"):
        self.model_name = model_name
        self.max_seq_length = 2048
        
    def load_model(self):
        """Load model with 4-bit quantization"""
        print("\n🔧 Loading model with 4-bit quantization...")
        
        # 4-bit quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        print("✅ Model loaded successfully")
        
        # Check VRAM
        vram_used = torch.cuda.memory_allocated(0) / 1024**3
        print(f"✅ VRAM used: {vram_used:.2f} GB")
        
    def prepare_model_for_training(self):
        """Add LoRA adapters"""
        print("\n🔧 Preparing model for training with LoRA...")
        
        # Prepare for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # LoRA config
        lora_config = LoraConfig(
            r=16,  # Rank
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
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
    
    def train(self, dataset, output_dir="memora-llama-finetuned", num_epochs=3):
        """Train the model"""
        print(f"\n🏋️ Starting training for {num_epochs} epochs...")
        print(f"Output directory: {output_dir}")
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
           num_train_epochs=num_epochs,
            per_device_train_batch_size=1,  # Small batch for 6GB VRAM
            gradient_accumulation_steps=4,  # Effective batch size = 4
            learning_rate=2e-4,
            fp16=True,
            logging_steps=10,
            save_strategy="epoch",
            optim="paged_adamw_8bit",  # Memory efficient optimizer
            warmup_ratio=0.1,
            lr_scheduler_type="cosine",
            report_to="none",  # Disable wandb
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
        tokenized_dataset = dataset.map(
            tokenize_function,
            remove_columns=dataset.column_names,
            batched=True
        )
        
        # Add labels
        tokenized_dataset = tokenized_dataset.map(
            lambda x: {"labels": x["input_ids"].copy()}
        )
        
        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
        )
        
        # Train
        print("\n⏳ Training started (this will take 1-2 hours)...")
        trainer.train()
        
        print("\n✅ Training complete!")
        
    def save_model(self, output_dir="memora-llama-finetuned"):
        """Save the fine-tuned model"""
        print(f"\n💾 Saving model to {output_dir}...")
        
        # Save LoRA adapters
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        print(f"✅ Model saved to {output_dir}")
        print(f"\n📝 To use this model, load it with:")
        print(f"   from peft import PeftModel")
        print(f"   model = PeftModel.from_pretrained(base_model, '{output_dir}')")


def main():
    """Main training function"""
    print("="*70)
    print("🦙 Llama 3.2 3B Fine-Tuning for Memora")
    print("="*70)
    
    # Check training data exists
    if not os.path.exists("training_data.jsonl"):
        print("\n❌ Error: training_data.jsonl not found!")
        print("Please run: python generate_training_data_synthetic.py")
        return
    
    # Initialize
    finetuner = LlamaFineTuner()
    
    # Load model
    finetuner.load_model()
    
    # Prepare for training
    finetuner.prepare_model_for_training()
    
    # Load data
    dataset = finetuner.load_training_data()
    
    # Train
    finetuner.train(dataset, num_epochs=3)
    
    # Save
    finetuner.save_model()
    
    print("\n" + "="*70)
    print("✅ Fine-tuning complete!")
    print("="*70)
    print("\n🎯 Your model is ready to use!")
    print("Next: Test with python test_finetuned_model.py")
    print("")


if __name__ == "__main__":
    main()
