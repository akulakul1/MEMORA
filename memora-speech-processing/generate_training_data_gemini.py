"""
Generate Training Data for Llama 3.2 3B Fine-tuning
Uses Google Gemini 2.0 Flash API (FREE tier - 1,500 requests/day!)
Cost: $0 for 100 examples with free tier
"""

import os
import json
import jsonlines
from google import genai
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load environment
load_dotenv()



class TrainingDataGenerator:
    """Generate training data using Google Gemini API (FREE!)"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in .env file")
        
        self.client = genai.Client(api_key=api_key)
        self.examples = []
    
    def create_example_transcriptions(self):
        """Create example conversation transcriptions"""
        scenarios = [
            {
                "context": "doctor's appointment about ADHD medication",
                "keywords": ["medication", "dosage", "ADHD", "appointment"],
                "transcription": "I met with Dr. Johnson today at 2 PM. We talked about my ADHD medication. The 10mg wasn't working well, so she increased it to 15mg. I need to take it in the morning now instead of afternoon. She said to come back in two weeks on Tuesday to see how it's working."
            },
            {
                "context": "family conversation about birthday party",
                "keywords": ["birthday", "party", "planning", "venue"],
                "transcription": "Mom called about Sarah's birthday party. It's going to be next Saturday at 3 PM at the community center. She asked if I can bring the cake and decorations. I said yes. She'll handle the food and games. We need to arrive by 2:30 to set up."
            },
            {
                "context": "work meeting about project deadline",
                "keywords": ["project", "deadline", "meeting", "tasks"],
                "transcription": "Had a meeting with the team about the Johnson project. The deadline is moved to March 15th. I'm responsible for the frontend design. Mike will handle backend. Sarah is doing testing. We're meeting again Friday at 10 AM to check progress."
            },
            {
                "context": "therapy session about anxiety management",
                "keywords": ["therapy", "anxiety", "coping", "techniques"],
                "transcription": "Met with Dr. Roberts for therapy today. We discussed my anxiety about work. She taught me some breathing exercises to do when I feel overwhelmed. I should practice them twice a day. She recommended I try journaling before bed. Next session is in two weeks."
            },
            {
                "context": "phone call about car repair",
                "keywords": ["car", "repair", "appointment", "cost"],
                "transcription": "Called the mechanic about my car. The brake pads need replacing. It'll cost about $300. I scheduled an appointment for Thursday at 9 AM. They said it'll take about 2 hours. I need to drop the car off and they'll call when it's ready."
            },
            {
                "context": "grocery shopping reminder",
                "keywords": ["groceries", "shopping", "list", "errands"],
                "transcription": "Need to go to the grocery store this weekend. Mom said we're out of milk, eggs, bread, and coffee. I also need to pick up ingredients for dinner on Friday - chicken, rice, and vegetables. The store closes at 9 PM. I should go early to avoid crowds."
            },
            {
                "context": "exercise and fitness goal",
                "keywords": ["exercise", "gym", "fitness", "routine"],
                "transcription": "Started a new workout routine with my trainer Alex. Three days a week - Monday, Wednesday, Friday at 6 AM. Focus on cardio and strength training. She gave me a meal plan too. Need to drink more water and get 8 hours of sleep. Next weigh-in is in two weeks."
            },
            {
                "context": "study session planning",
                "keywords": ["study", "exam", "schedule", "preparation"],
                "transcription": "Talked to my study group about the biology exam. It's next Thursday at 1 PM. We're meeting Tuesday and Wednesday at the library from 3-6 PM. I need to review chapters 5-8. Emma will bring flashcards. Jason is making a study guide. We should all read chapter 7 by Tuesday."
            },
        ]
        
        return scenarios
    
    def generate_memory_summary(self, transcription, keywords):
        """Use Gemini to generate a perfect memory summary with retry logic"""
        
        prompt = f"""Given this conversation transcription, create a memory summary that would help someone with memory challenges.

Transcription: "{transcription}"

Keywords extracted: {', '.join(keywords)}

Create a JSON response with:
- title: Short descriptive title (5-7 words)
- quick_summary: 1-2 sentences capturing the essence
- key_points: Array of 3-5 most important points
- action_items: Array of specific things to do or remember
- people: Array of objects with "name" and "context" for each person mentioned
- tags: Array of 3-5 relevant categorical tags

Focus on what someone would need to remember later. Be clear, concise, and helpful.
Return ONLY valid JSON, no other text or markdown formatting."""

        # Retry logic for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt
                )
                content = response.text
                
                # Extract JSON from response
                import re
                # Remove markdown code blocks if present
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    print(f"Warning: Could not extract JSON from response (attempt {attempt+1})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return None
            
            except Exception as e:
                error_msg = str(e)
                if "rate" in error_msg.lower() or "quota" in error_msg.lower():
                    # Rate limit error - wait longer
                    wait_time = 3 * (2 ** attempt)
                    print(f"Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    if attempt < max_retries - 1:
                        continue
                else:
                    print(f"Error generating summary: {e}")
                    return None
        
        return None
    
    def create_training_example(self, transcription, keywords, summary):
        """Format as training example for Llama"""
        
        system_message = "You are Memora, an AI assistant that helps people with memory challenges. Convert conversation transcripts into clear, helpful memory summaries in JSON format."
        
        user_message = f"""Transcription: "{transcription}"

Keywords: {', '.join(keywords)}

Create a memory summary with title, quick_summary, key_points, action_items, people, and tags."""

        assistant_message = json.dumps(summary, indent=2)
        
        return {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message}
            ]
        }
    
    def generate_dataset(self, num_examples=100, output_file="training_data.jsonl"):
        """Generate complete training dataset"""
        
        print(f"\nGenerating {num_examples} training examples using Gemini 2.0 Flash (FREE!)...")
        print("This may take a few minutes.\n")
        
        # Get base scenarios
        scenarios = self.create_example_transcriptions()
        
        # Generate variations and get summaries
        training_examples = []
        
        for i in tqdm(range(num_examples), desc="Generating examples"):
            # Pick a scenario (cycle through them with variations)
            scenario = scenarios[i % len(scenarios)]
            
            # Generate summary using Gemini
            summary = self.generate_memory_summary(
                scenario["transcription"],
                scenario["keywords"]
            )
            
            if summary:
                # Create training example
                example = self.create_training_example(
                    scenario["transcription"],
                    scenario["keywords"],
                    summary
                )
                
                training_examples.append(example)
            
            # Rate limiting - wait after every 10 requests to avoid quotas
            if (i + 1) % 10 == 0:
                time.sleep(3)  # Wait 3 seconds every 10 requests
        
        # Save to file
        print(f"\nSaving {len(training_examples)} examples to {output_file}...")
        
        with jsonlines.open(output_file, mode='w') as writer:
            writer.write_all(training_examples)
        
        print(f"✓ Training data saved to {output_file}")
        print(f"✓ Total examples: {len(training_examples)}")
        
        # Save a sample for inspection
        sample_file = "training_sample.json"
        with open(sample_file, 'w') as f:
            json.dump(training_examples[:3], f, indent=2)
        
        print(f"✓ Sample saved to {sample_file} for inspection")
        
        return training_examples


def main():
    """Main function"""
    print("="*60)
    print("Training Data Generator - Gemini 2.0 Flash (FREE!)")
    print("="*60)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n❌ Error: GOOGLE_API_KEY not found in .env file")
        print("\nPlease add your Google API key to .env:")
        print("GOOGLE_API_KEY=AIzaSy...")
        print("\nGet your FREE API key from: https://aistudio.google.com/apikey")
        print("Free tier includes 1,500 requests per day!")
        return
    
    # Initialize generator
    generator = TrainingDataGenerator()
    
    # Get user input
    print("\nHow many training examples do you want to generate?")
    print("Recommended: 100-200 for good fine-tuning results")
    print("Note: Gemini 2.0 Flash is FREE (1,500 requests/day)")
    
    try:
        num_examples = int(input("\nNumber of examples (default 100): ") or "100")
    except ValueError:
        num_examples = 100
    
    print(f"\n💰 Estimated cost: $0.00 (FREE with Gemini!)")
    print(f"📊 This will use {num_examples} of your 1,500 daily free requests")
    
    confirm = input("Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    # Generate dataset
    training_examples = generator.generate_dataset(
        num_examples=num_examples,
        output_file="training_data.jsonl"
    )
    
    print("\n" + "="*60)
    print("✅ Training data generation complete!")
    print("="*60)
    print("\nNext step: Fine-tune the model")
    print("Run: python finetune_llama.py")
    print("")


if __name__ == "__main__":
    main()
