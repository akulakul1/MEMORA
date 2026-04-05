"""
Memora LLM Processor - Google Gemini 2.0 Flash Version (FREE!)
Drop-in replacement for llm_processor.py
Uses FREE Google Gemini API instead of paid Claude API
"""

import google.generativeai as genai
import json
import re
import os
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()


class LLMProcessor:
    """
    LLM processor using Google Gemini 2.0 Flash (FREE tier)
    Drop-in replacement for llm_processor.py
    """
    
    def __init__(self, provider=None, api_key=None):
        """Initialize Gemini model (provider/api_key args for compatibility)"""
        # Get API key from parameter or environment
        google_key = api_key if provider == "google" else os.getenv("GOOGLE_API_KEY")
        
        if not google_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        genai.configure(api_key=google_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        print("✓ Gemini 2.0 Flash LLM initialized (FREE tier)")
    
    def _format_conversation_prompt(
        self,
        transcription: Dict,
        keywords: Dict,
        summary: Dict
    ) -> str:
        """Format data into a prompt (same as original llm_processor.py)"""
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
        Generate user-friendly memory summary using Gemini (FREE!)
        
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
            # Generate response
            response = self.model.generate_content(full_prompt)
            content = response.text
            
            # Parse JSON from response
            memory_summary = self._parse_json_response(content)
            
            # Add metadata
            memory_summary["generated_at"] = datetime.now().isoformat()
            memory_summary["model_used"] = "gemini-2.0-flash-exp"
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
                "model_used": "gemini-2.0-flash-exp"
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
                if isinstance(person, dict):
                    reminder += f"• {person.get('name', 'Unknown')}"
                    if person.get('context'):
                        reminder += f" - {person['context']}"
                else:
                    reminder += f"• {person}"
                reminder += "\n"
        
        return reminder


if __name__ == "__main__":
    # Test the model
    print("Testing Gemora (Gemini) LLM...")
    
    # Initialize
    llm = LLMProcessor()
    
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
