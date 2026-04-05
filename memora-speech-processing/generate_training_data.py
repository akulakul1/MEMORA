"""
Generate Training Data for Llama 3.2 3B Fine-tuning
Uses Anthropic API to create high-quality training examples
"""

import os
import json
import jsonlines
from anthropic import Anthropic
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load environment
load_dotenv()


class TrainingDataGenerator:
    """Generate training data using Claude API"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env file")
        
        self.client = Anthropic(api_key=api_key)
        self.examples = []
    
    def create_example_transcriptions(self):
        """Create example conversation transcriptions"""
        # These are example scenarios - you can add more
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
        ]
        
        return scenarios
    
    def generate_memory_summary(self, transcription, keywords):
        """Use Claude to generate a perfect memory summary"""
        
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

Focus on what someone would need to remember later. Be clear, concise, and helpful."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                print(f"Warning: Could not extract JSON from response")
                return None
        
        except Exception as e:
            print(f"Error generating summary: {e}")
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
        
        print(f"\nGenerating {num_examples} training examples...")
        print("This will use Anthropic API and may take a few minutes.\n")
        
        # Get base scenarios
        scenarios = self.create_example_transcriptions()
        
        # Generate variations and get summaries
        training_examples = []
        
        for i in tqdm(range(num_examples), desc="Generating examples"):
            # Pick a random scenario (or cycle through them)
            scenario = scenarios[i % len(scenarios)]
            
            # Generate summary using Claude
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
            
            # Rate limiting - be nice to the API
            if i % 10 == 0 and i > 0:
                time.sleep(1)
        
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
    print("Training Data Generator for Llama 3.2 3B")
    print("="*60)
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY not found in .env file")
        print("\nPlease add your Anthropic API key to .env:")
        print("ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx")
        return
    
    # Initialize generator
    generator = TrainingDataGenerator()
    
    # Get user input
    print("\nHow many training examples do you want to generate?")
    print("Recommended: 100-200 for good fine-tuning results")
    print("Note: Each example costs ~$0.01 with Claude API")
    
    try:
        num_examples = int(input("\nNumber of examples (default 100): ") or "100")
    except ValueError:
        num_examples = 100
    
    estimated_cost = num_examples * 0.01
    print(f"\nEstimated API cost: ${estimated_cost:.2f}")
    
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
