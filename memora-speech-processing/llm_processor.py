"""
LLM Integration Module
Processes transcription data through LLMs to generate user-friendly summaries
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
import json


class LLMProcessor:
    """
    Process memory data through LLM to generate user-friendly summaries
    """
    
    def __init__(
        self,
        provider: str = "anthropic",
        api_key: Optional[str] = None,
        model: str = None
    ):
        """
        Initialize LLM processor
        
        Args:
            provider: LLM provider (anthropic, openai)
            api_key: API key for the provider
            model: Model name to use
        """
        self.provider = provider.lower()
        self.api_key = api_key or self._get_api_key()
        
        if self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            self.model = model or "claude-sonnet-4-20250514"
        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.model = model or "gpt-4-turbo-preview"
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _get_api_key(self) -> str:
        """Get API key from environment"""
        if self.provider == "anthropic":
            key = os.getenv("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
        elif self.provider == "openai":
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY not found in environment")
        return key
    
    def _format_conversation_prompt(
        self,
        transcription: Dict,
        keywords: Dict,
        summary: Dict
    ) -> str:
        """
        Format data into a prompt for the LLM
        
        Args:
            transcription: Speech processing results
            keywords: Keyword extraction results
            summary: Summarization results
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are Memora, an AI assistant helping individuals with memory challenges. 
You've been given a conversation recording and need to create a clear, helpful memory summary.

CONVERSATION DETAILS:
Date/Time: {transcription.get('timestamp', 'Unknown')}
Language: {transcription.get('language', 'Unknown')}
Duration: Multiple segments

FULL TRANSCRIPTION:
{transcription.get('full_text', '')}

KEY INFORMATION EXTRACTED:
"""
        
        # Add entities
        if keywords.get('entities'):
            entities = keywords['entities']
            if entities.get('persons'):
                prompt += f"\nPeople mentioned: {', '.join(entities['persons'])}"
            if entities.get('locations'):
                prompt += f"\nPlaces: {', '.join(entities['locations'])}"
            if entities.get('dates'):
                prompt += f"\nDates: {', '.join(entities['dates'])}"
            if entities.get('times'):
                prompt += f"\nTimes: {', '.join(entities['times'])}"
            if entities.get('organizations'):
                prompt += f"\nOrganizations: {', '.join(entities['organizations'])}"
        
        # Add keywords
        if keywords.get('combined_keywords'):
            prompt += f"\n\nImportant topics: {', '.join(keywords['combined_keywords'][:10])}"
        
        # Add automated summary
        if summary.get('overall_summary'):
            prompt += f"\n\nAutomatic summary: {summary['overall_summary']}"
        
        prompt += """

Please create a memory summary that includes:

1. **Title**: A short, descriptive title (5-7 words)
2. **Quick Summary**: 1-2 sentences capturing the essence of the conversation
3. **Key Points**: 3-5 bullet points of the most important information
4. **People**: List anyone mentioned with their role/context
5. **Action Items**: Any tasks, appointments, or things to remember
6. **Context Tags**: 3-5 relevant tags for categorization

Format your response as JSON with these exact keys:
{
  "title": "...",
  "quick_summary": "...",
  "key_points": ["...", "...", "..."],
  "people": [{"name": "...", "context": "..."}],
  "action_items": ["...", "..."],
  "tags": ["...", "...", "..."]
}

Be clear, concise, and helpful. Focus on what someone with memory challenges would need to recall this conversation later."""
        
        return prompt
    
    def generate_memory_summary(
        self,
        transcription: Dict,
        keywords: Dict,
        summary: Dict,
        max_tokens: int = 1000
    ) -> Dict:
        """
        Generate user-friendly memory summary using LLM
        
        Args:
            transcription: Speech processing results
            keywords: Keyword extraction results
            summary: Summarization results
            max_tokens: Maximum tokens for response
            
        Returns:
            Structured memory summary
        """
        prompt = self._format_conversation_prompt(transcription, keywords, summary)
        
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.content[0].text
            
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are Memora, an AI assistant for memory support."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
            
            # Parse JSON response
            memory_summary = json.loads(content)
            
            # Add metadata
            memory_summary["generated_at"] = datetime.now().isoformat()
            memory_summary["model_used"] = self.model
            memory_summary["original_timestamp"] = transcription.get('timestamp')
            
            return memory_summary
        
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Raw response: {content}")
            
            # Return fallback structure
            return {
                "title": "Conversation Memory",
                "quick_summary": transcription.get('full_text', '')[:200] + "...",
                "key_points": [],
                "people": [],
                "action_items": [],
                "tags": ["conversation"],
                "error": "Failed to parse LLM response",
                "generated_at": datetime.now().isoformat()
            }
        
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
                "generated_at": datetime.now().isoformat()
            }
    
    def create_reminder_text(
        self,
        memory_summary: Dict,
        reminder_type: str = "daily"
    ) -> str:
        """
        Create reminder text from memory summary
        
        Args:
            memory_summary: LLM-generated memory summary
            reminder_type: Type of reminder (daily, weekly, specific)
            
        Returns:
            Formatted reminder text
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


if __name__ == "__main__":
    # Example usage
    sample_transcription = {
        "timestamp": datetime.now().isoformat(),
        "language": "en",
        "full_text": "Dr. Johnson said to take medication at 8 AM daily. Next appointment is Tuesday at 2 PM. Remember to bring test results."
    }
    
    sample_keywords = {
        "entities": {
            "persons": ["Dr. Johnson"],
            "dates": ["Tuesday"],
            "times": ["8 AM", "2 PM"]
        },
        "combined_keywords": ["medication", "appointment", "test results"]
    }
    
    sample_summary = {
        "overall_summary": "Doctor's appointment with medication instructions and follow-up scheduled."
    }
    
    # Initialize processor (requires API key in environment)
    try:
        processor = LLMProcessor(provider="anthropic")
        
        # Generate memory summary
        result = processor.generate_memory_summary(
            sample_transcription,
            sample_keywords,
            sample_summary
        )
        
        print("Memory Summary:")
        print(json.dumps(result, indent=2))
        
        # Create reminder
        reminder = processor.create_reminder_text(result)
        print("\n" + "="*50)
        print("Reminder Text:")
        print(reminder)
    
    except Exception as e:
        print(f"Error: {e}")
        print("Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in your environment")
