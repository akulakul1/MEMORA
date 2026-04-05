"""
Memora LLM Processor - Llama 3.2 3B Version
Inference wrapper for fine-tuned model
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import json
import re
from typing import Dict, Optional
from datetime import datetime


class MemoraLlamaLLM:
    """
    LLM processor using fine-tuned Llama 3.2 3B
    Drop-in replacement for llm_processor.py
    """
    
    def __init__(
        self,
        model_path="unsloth/Llama-3.2-3B-Instruct",  # Use Unsloth base model (or fine-tuned path later)
        device="auto",
        use_4bit=True
    ):
        """
        Initialize Llama model
        
        Args:
            model_path: Path to fine-tuned model
            device: Device to use (auto/cuda/cpu)
            use_4bit: Use 4-bit quantization (recommended for 6GB VRAM)
        """
        self.model_path = model_path
        self.device = device
        self.use_4bit = use_4bit
        
        print(f"Loading Memora Llama model from: {model_path}")
        
        self._load_model()
    
    def _load_model(self):
        """Load model and tokenizer"""
        
        if self.use_4bit:
            # 4-bit quantization config for 6GB VRAM
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                quantization_config=bnb_config,
                device_map=self.device,
                torch_dtype=torch.float16,
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map=self.device,
                torch_dtype=torch.float16,
            )
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        
        vram_used = torch.cuda.memory_allocated(0) / 1024**3 if torch.cuda.is_available() else 0
        print(f"✓ Model loaded (VRAM: {vram_used:.2f} GB)")
    
    def _format_conversation_prompt(
        self,
        transcription: Dict,
        keywords: Dict,
        summary: Dict
    ) -> str:
        """
        Format data into a prompt (same as llm_processor.py)
        """
        prompt = f"""Transcription: "{transcription.get('full_text', '')}"

Keywords: {', '.join(keywords.get('combined_keywords', [])[:10])}"""
        
        # Add entities
        if keywords.get('entities'):
            entities = keywords['entities']
            entity_parts = []
            
            if entities.get('persons'):
                entity_parts.append(f"People: {', '.join(entities['persons'])}")
            if entities.get('locations'):
                entity_parts.append(f"Places: {', '.join(entities['locations'])}")
            if entities.get('dates'):
                entity_parts.append(f"Dates: {', '.join(entities['dates'])}")
            if entities.get('times'):
                entity_parts.append(f"Times: {', '.join(entities['times'])}")
            
            if entity_parts:
                prompt += "\n" + "\n".join(entity_parts)
        
        prompt += "\n\nCreate a memory summary with title, quick_summary, key_points, action_items, people, and tags."
        
        return prompt
    
    def generate_memory_summary(
        self,
        transcription: Dict,
        keywords: Dict,
        summary: Dict,
        max_new_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict:
        """
        Generate user-friendly memory summary using fine-tuned Llama
        
        Args:
            transcription: Speech processing results
            keywords: Keyword extraction results
            summary: Summarization results
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Structured memory summary
        """
        
        # Create prompt
        user_prompt = self._format_conversation_prompt(transcription, keywords, summary)
        
        system_prompt = "You are Memora, an AI assistant that helps people with memory challenges. Convert conversation transcripts into clear, helpful memory summaries in JSON format."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Prepare input
            inputs = self.tokenizer.apply_chat_template(
                messages,
                return_tensors="pt",
                add_generation_prompt=True
            ).to(self.model.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            response = self.tokenizer.decode(
                outputs[0][len(inputs[0]):],  # Only decode generated tokens
                skip_special_tokens=True
            )
            
            # Parse JSON from response
            memory_summary = self._parse_json_response(response)
            
            # Add metadata
            memory_summary["generated_at"] = datetime.now().isoformat()
            memory_summary["model_used"] = "llama-3.2-3b-finetuned"
            memory_summary["original_timestamp"] = transcription.get('timestamp')
            
            return memory_summary
        
        except Exception as e:
            print(f"Error generating memory summary: {e}")
            
            # Return fallback structure
            return {
                "title": "Conversation Memory",
                "quick_summary": transcription.get('full_text', '')[:200] + "...",
                "key_points": [],
                "people": [],
                "action_items": [],
                "tags": ["conversation"],
                "error": str(e),
                "generated_at": datetime.now().isoformat(),
                "model_used": "llama-3.2-3b-finetuned"
            }
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from model response"""
        
        # Try to find JSON in response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse JSON: {e}")
                print(f"Response: {response[:200]}...")
        
        # Fallback: return basic structure
        return {
            "title": "Conversation Memory",
            "quick_summary": response[:200],
            "key_points": [],
            "people": [],
            "action_items": [],
            "tags": []
        }
    
    def create_reminder_text(
        self,
        memory_summary: Dict,
        reminder_type: str = "daily"
    ) -> str:
        """
        Create reminder text from memory summary
        (Same as llm_processor.py for compatibility)
        """
        reminder = f"📝 Memora Reminder - {memory_summary.get('title', 'Memory')}\n\n"
        
        if memory_summary.get('quick_summary'):
            reminder += f"{memory_summary['quick_summary']}\n\n"
        
        if memory_summary.get('action_items'):
            reminder += "Things to remember:\n"
            for item in memory_summary['action_items']:
                reminder += f"• {item}\n"
        
        if memory_summary.get('people'):
            reminder += "\nPeople involved:\n"
            for person in memory_summary['people']:
                reminder += f"• {person.get('name', 'Unknown')}"
                if person.get('context'):
                    reminder += f" - {person['context']}"
                reminder += "\n"
        
        return reminder


# For backwards compatibility with existing code
LLMProcessor = MemoraLlamaLLM


if __name__ == "__main__":
    # Test the model
    print("Testing Memora Llama LLM...")
    
    # Initialize
    llm = MemoraLlamaLLM()
    
    # Test data
    test_transcription = {
        "timestamp": datetime.now().isoformat(),
        "language": "en",
        "full_text": "I met with Dr. Johnson at Memorial Hospital today. We discussed increasing my ADHD medication from 10mg to 15mg because the current dose isn't working well enough. I need to take it in the morning now instead of the afternoon. My next appointment is Tuesday at 2 PM in two weeks."
    }
    
    test_keywords = {
        "entities": {
            "persons": ["Dr. Johnson"],
            "locations": ["Memorial Hospital"],
            "dates": ["Tuesday", "two weeks"],
            "times": ["2 PM"]
        },
        "combined_keywords": ["medication", "ADHD", "appointment", "dosage"]
    }
    
    test_summary = {
        "overall_summary": "Medical appointment to discuss ADHD medication adjustment."
    }
    
    # Generate
    print("\nGenerating memory summary...")
    result = llm.generate_memory_summary(
        test_transcription,
        test_keywords,
        test_summary
    )
    
    print("\n" + "="*60)
    print("Memory Summary:")
    print("="*60)
    print(json.dumps(result, indent=2))
    
    # Test reminder
    print("\n" + "="*60)
    print("Reminder Text:")
    print("="*60)
    reminder = llm.create_reminder_text(result)
    print(reminder)
