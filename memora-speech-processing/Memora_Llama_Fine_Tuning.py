# Fine-Tuning Llama 3.2 3B for Memora - Google Colab
# Upload this to Google Colab and run with free T4 GPU

# Cell 1: Setup
"""
## Llama 3.2 3B Fine-Tuning for Memora Memory Generation
**Author:** [Your Name]
**Project:** Memora - AI Memory Assistant for ADHD
**Date:** January 2026

This notebook fine-tunes Llama 3.2 3B on custom memory generation data.
"""

# Cell 2: Install Dependencies
!pip install -q transformers accelerate peft datasets bitsandbytes

# Cell 3: Mount Google Drive (to save/load data)
from google.colab import drive
drive.mount('/content/drive')

# Cell 4: Upload Training Data
"""
Upload your training_data.jsonl file:
1. Click the folder icon on the left
2. Upload training_data.jsonl
   OR
3. Copy from Google Drive if you uploaded it there
"""

# Uncomment if using Google Drive:
# !cp /content/drive/MyDrive/memora/training_data.jsonl /content/

# Cell 5: Verify Training Data
import json

with open('training_data.jsonl', 'r') as f:
    lines = f.readlines()
    print(f"Total training examples: {len(lines)}")
    print("\nFirst example:")
    print(json.dumps(json.loads(lines[0]), indent=2)[:500])

# Cell 6: Import Libraries
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

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

# Cell 7: Load Model with 4-bit Quantization
print("Loading Llama 3.2 3B with 4-bit quantization...")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    "unsloth/Llama-3.2-3B-Instruct",
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

tokenizer = AutoTokenizer.from_pretrained("unsloth/Llama-3.2-3B-Instruct")
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("✅ Model loaded!")
print(f"VRAM used: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")

# Cell 8: Prepare Model for Training with LoRA
print("Adding LoRA adapters...")

model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropdown=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Cell 9: Load and Prepare Training Data
print("Loading training data...")

dataset = load_dataset('json', data_files='training_data.jsonl', split='train')
print(f"✅ Loaded {len(dataset)} examples")

def format_example(example):
    messages = example['messages']
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )
    return {"text": text}

dataset = dataset.map(format_example, remove_columns=dataset.column_names)

# Cell 10: Tokenize Dataset
def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=512,
        padding="max_length"
    )

print("Tokenizing dataset...")
tokenized_dataset = dataset.map(
    tokenize_function,
    remove_columns=dataset.column_names,
    batched=True
)

tokenized_dataset = tokenized_dataset.map(
    lambda x: {"labels": x["input_ids"].copy()}
)

print(f"✅ Dataset ready: {len(tokenized_dataset)} examples")

# Cell 11: Configure Training
training_args = TrainingArguments(
    output_dir="memora-llama-finetuned",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=5,
    save_strategy="epoch",
    optim="paged_adamw_8bit",
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    report_to="none",
)

print("Training configuration:")
print(f"  Epochs: {training_args.num_train_epochs}")
print(f"  Batch size: {training_args.per_device_train_batch_size}")
print(f"  Total steps: {len(tokenized_dataset) // (training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps) * training_args.num_train_epochs}")

# Cell 12: Create Trainer and Start Fine-Tuning
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

print("\n🏋️ Starting fine-tuning...")
print("This will take approximately 30-60 minutes on T4 GPU\n")

trainer.train()

print("\n✅ Fine-tuning complete!")

# Cell 13: Save Model
print("Saving fine-tuned model...")

model.save_pretrained("memora-llama-finetuned")
tokenizer.save_pretrained("memora-llama-finetuned")

print("✅ Model saved to: memora-llama-finetuned")

# Cell 14: Test the Fine-Tuned Model
print("\n🧪 Testing fine-tuned model...\n")

test_input = """Transcription: "I have a doctor's appointment with Dr. Smith tomorrow at 2 PM at City Hospital. Need to discuss my ADHD medication dosage. Should bring my current prescription and insurance card."

Keywords: doctor, appointment, ADHD, medication

Create a memory summary with title, quick_summary, key_points, action_items, people, and tags."""

# Prepare for inference
model.eval()
inputs = tokenizer([test_input], return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        temperature=0.7,
        do_sample=True,
        top_p=0.9
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("Generated Memory Summary:")
print("="*70)
print(response)

# Cell 15: Download Fine-Tuned Model
"""
Download the fine-tuned model to use locally:

1. Zip the model folder:
"""
!zip -r memora-llama-finetuned.zip memora-llama-finetuned

"""
2. Download to your computer:
   - Click the folder icon on left
   - Right-click memora-llama-finetuned.zip
   - Click Download

OR save to Google Drive:
"""
!cp -r memora-llama-finetuned /content/drive/MyDrive/memora/

print("✅ Model ready to download!")
print("\nTo use locally:")
print("1. Download memora-llama-finetuned.zip")
print("2. Extract to your memora project folder")
print("3. Update memora_llama_processor.py to use this model")

# Cell 16: Compare with Base Model (Optional)
"""
Compare your fine-tuned model with the base model to show improvement
"""

print("\n📊 Comparing Base vs Fine-Tuned Model\n")

# Load base model for comparison
base_model = AutoModelForCausalLM.from_pretrained(
    "unsloth/Llama-3.2-3B-Instruct",
    quantization_config=bnb_config,
    device_map="auto"
)

test_cases = [
    "Medical appointment about ADHD medication adjustment",
    "Birthday party planning with family",
    "Work project deadline discussion"
]

for idx, test in enumerate(test_cases, 1):
    print(f"\nTest {idx}: {test}")
    print("-" * 70)
    
    prompt = f"Create a concise memory summary for: {test}"
    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
    
    # Base model
    with torch.no_grad():
        base_output = base_model.generate(**inputs, max_new_tokens=100)
    print(f"BASE: {tokenizer.decode(base_output[0], skip_special_tokens=True)[len(prompt):]}")
    
    # Fine-tuned model
    with torch.no_grad():
        finetuned_output = model.generate(**inputs, max_new_tokens=100)
    print(f"FINE-TUNED: {tokenizer.decode(finetuned_output[0], skip_special_tokens=True)[len(prompt):]}")

print("\n✅ Comparison complete!")
