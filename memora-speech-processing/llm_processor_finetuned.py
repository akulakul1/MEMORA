"""
Memora LLM Processor - Fine-Tuned Llama Version
Uses YOUR fine-tuned Llama 3.2 3B model
"""

import json
import re
import os
from typing import Dict, Optional
from datetime import datetime

class LLMProcessor:
    """
    LLM processor using YOUR fine-tuned Llama 3.2 3B model
    Drop-in replacement for llm_processor.py and llm_processor_gemini.py
    """
    
    def __init__(self, provider=None, api_key=None):
        """Initialize fine-tuned Llama model (provider/api_key args ignored for compatibility)"""
        
        # Import heavy dependencies here so module import never fails
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel
        import torch
        self._torch = torch
        
        print("Loading YOUR fine-tuned Llama model...")
        
        # Create offload directory
        os.makedirs("offload_folder", exist_ok=True)
        
        # 4-bit quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            "unsloth/Llama-3.2-3B-Instruct",
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            offload_folder="offload_folder"
        )
        
        # Load YOUR fine-tuned LoRA weights
        self.model = PeftModel.from_pretrained(
            base_model,
            "memora-llama-finetuned",
            offload_folder="offload_folder"
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained("memora-llama-finetuned")
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model.eval()  # Set to evaluation mode
        print("[OK] YOUR fine-tuned Llama model loaded!")
    
    def _format_conversation_prompt(
        self,
        transcription: Dict,
        keywords: Dict,
        summary: Dict
    ) -> str:
        """Format data into a prompt"""
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
        summary: Dict
    ) -> Dict:
        """
        Generate memory summary using YOUR fine-tuned Llama model
        
        Args:
            transcription: Speech processing results
            keywords: Keyword extraction results
            summary: Summarization results
            
        Returns:
            Structured memory summary
        """
        
        # Create prompt
        user_prompt = self._format_conversation_prompt(transcription, keywords, summary)
        
        system_prompt = """You are Memora, an AI assistant that helps people with memory challenges. 
Convert conversation transcripts into clear, helpful memory summaries in JSON format.

Create a JSON response with:
- title: Short descriptive title (5-7 words)
- quick_summary: 1-2 sentences capturing the essence
- key_points: Array of 3-5 most important points to remember
- action_items: Array of specific things to do or remember
- people: Array of objects with "name" and "context" for each person mentioned
- tags: Array of 3-5 relevant categorical tags

Focus on what someone would need to remember later. Be clear, concise, and helpful.
Return ONLY valid JSON, no other text or markdown formatting."""

        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        try:
            torch = self._torch
            # Generate response
            inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=300,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    repetition_penalty=1.1
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (after the prompt)
            if full_prompt in response:
                generated = response.split(full_prompt)[-1].strip()
            else:
                generated = response
            
            # Parse JSON from response
            memory_summary = self._parse_json_response(generated)
            
            # Add metadata
            memory_summary["generated_at"] = datetime.now().isoformat()
            memory_summary["model_used"] = "fine-tuned-llama-3.2-3b"
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
                "model_used": "fine-tuned-llama-3.2-3b"
            }
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from model response"""
        
        # Remove markdown code blocks if present
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
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
            "quick_summary": response[:200] if response else "No summary generated",
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
        """Create reminder text from memory summary"""
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
                if isinstance(person, dict):
                    reminder += f"• {person.get('name', 'Unknown')}"
                    if person.get('context'):
                        reminder += f" - {person['context']}"
                else:
                    reminder += f"• {person}"
                reminder += "\n"
        
        return reminder
