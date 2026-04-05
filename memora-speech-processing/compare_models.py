"""
Compare Llama 3.2 3B vs Claude API
Evaluates quality, speed, and cost differences
"""

import json
import time
from anthropic import Anthropic
from memora_llama_processor import MemoraLlamaLLM
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class ModelComparison:
    """Compare fine-tuned Llama vs Claude"""
    
    def __init__(self):
        # Initialize models
        print("Loading models...")
        
        # Llama
        print("\n1. Loading Llama 3.2 3B...")
        self.llama = MemoraLlamaLLM()
        
        # Claude
        print("\n2. Initializing Claude API...")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in .env")
        self.claude_client = Anthropic(api_key=api_key)
        
        print("\n✓ Both models ready!")
    
    def create_test_cases(self):
        """Create test cases for comparison"""
        return [
            {
                "name": "Doctor's Appointment",
                "transcription": {
                    "full_text": "I met with Dr. Sarah Johnson at Memorial Hospital today at 2 PM. We discussed my ADHD medication. The 10mg dose wasn't working well, so she increased it to 15mg. I should take it in the morning now instead of the afternoon. She wants to see me again in two weeks on Tuesday at the same time to check how it's working. I need to bring my blood test results to that appointment.",
                    "language": "en",
                    "timestamp": datetime.now().isoformat()
                },
                "keywords": {
                    "entities": {
                        "persons": ["Dr. Sarah Johnson"],
                        "locations": ["Memorial Hospital"],
                        "dates": ["today", "Tuesday", "two weeks"],
                        "times": ["2 PM"]
                    },
                    "combined_keywords": ["medication", "ADHD", "dosage", "appointment", "blood test"]
                },
                "summary": {
                    "overall_summary": "Medical appointment for ADHD medication adjustment with follow-up scheduled."
                }
            },
            {
                "name": "Work Meeting",
                "transcription": {
                    "full_text": "Had a team meeting about the Johnson project. The deadline moved to March 15th. I'm responsible for the frontend design, Mike is handling the backend, and Sarah is doing QA testing. We need to have a working prototype by next Friday. Next team meeting is scheduled for Monday at 10 AM in conference room B.",
                    "language": "en",
                    "timestamp": datetime.now().isoformat()
                },
                "keywords": {
                    "entities": {
                        "persons": ["Mike", "Sarah"],
                        "dates": ["March 15th", "Friday", "Monday"],
                        "times": ["10 AM"]
                    },
                    "combined_keywords": ["project", "deadline", "frontend", "backend", "testing", "meeting"]
                },
                "summary": {
                    "overall_summary": "Project meeting with task assignments and deadline discussion."
                }
            },
            {
                "name": "Family Call",
                "transcription": {
                    "full_text": "Mom called about Sarah's birthday party next Saturday at 3 PM. It's at the community center on Maple Street. She asked if I can bring the cake and decorations. I said yes. She's handling food and games. We need to arrive by 2:30 to set everything up before guests arrive at 3.",
                    "language": "en",
                    "timestamp": datetime.now().isoformat()
                },
                "keywords": {
                    "entities": {
                        "persons": ["Mom", "Sarah"],
                        "locations": ["community center", "Maple Street"],
                        "dates": ["Saturday"],
                        "times": ["3 PM", "2:30"]
                    },
                    "combined_keywords": ["birthday", "party", "cake", "decorations", "setup"]
                },
                "summary": {
                    "overall_summary": "Planning for upcoming birthday party with task assignments."
                }
            }
        ]
    
    def test_llama(self, test_case):
        """Test Llama model"""
        start_time = time.time()
        
        result = self.llama.generate_memory_summary(
            test_case["transcription"],
            test_case["keywords"],
            test_case["summary"]
        )
        
        end_time = time.time()
        
        return {
            "result": result,
            "time": end_time - start_time,
            "model": "Llama 3.2 3B (Fine-tuned)"
        }
    
    def test_claude(self, test_case):
        """Test Claude API"""
        
        # Format prompt (similar to llm_processor.py)
        prompt = f"""Transcription: "{test_case['transcription']['full_text']}"

Keywords: {', '.join(test_case['keywords']['combined_keywords'])}

People: {', '.join(test_case['keywords']['entities']['persons'])}
Dates: {', '.join(test_case['keywords']['entities']['dates'])}
Times: {', '.join(test_case['keywords']['entities']['times'])}

Create a memory summary with title, quick_summary, key_points, action_items, people, and tags. Respond in JSON format."""
        
        start_time = time.time()
        
        response = self.claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        end_time = time.time()
        
        # Parse JSON
        import re
        content = response.content[0].text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"error": "Could not parse JSON"}
        
        return {
            "result": result,
            "time": end_time - start_time,
            "model": "Claude Sonnet 4"
        }
    
    def evaluate_quality(self, result, test_case_name):
        """Evaluate quality of result"""
        
        # Check completeness
        required_fields = ['title', 'quick_summary', 'key_points', 'action_items', 'people', 'tags']
        
        completeness = sum(1 for field in required_fields if field in result and result[field]) / len(required_fields)
        
        # Count details
        key_points_count = len(result.get('key_points', []))
        action_items_count = len(result.get('action_items', []))
        people_count = len(result.get('people', []))
        tags_count = len(result.get('tags', []))
        
        return {
            "completeness": completeness * 100,
            "key_points": key_points_count,
            "action_items": action_items_count,
            "people": people_count,
            "tags": tags_count
        }
    
    def run_comparison(self):
        """Run complete comparison"""
        print("\n" + "="*60)
        print("Model Comparison: Llama 3.2 3B vs Claude Sonnet 4")
        print("="*60)
        
        test_cases = self.create_test_cases()
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"Test Case {i}: {test_case['name']}")
            print(f"{'='*60}")
            
            # Test Llama
            print("\n1. Testing Llama 3.2 3B...")
            llama_response = self.test_llama(test_case)
            llama_quality = self.evaluate_quality(llama_response['result'], test_case['name'])
            
            print(f"   ✓ Time: {llama_response['time']:.2f}s")
            print(f"   ✓ Completeness: {llama_quality['completeness']:.0f}%")
            
            # Test Claude
            print("\n2. Testing Claude Sonnet 4...")
            claude_response = self.test_claude(test_case)
            claude_quality = self.evaluate_quality(claude_response['result'], test_case['name'])
            
            print(f"   ✓ Time: {claude_response['time']:.2f}s")
            print(f"   ✓ Completeness: {claude_quality['completeness']:.0f}%")
            
            # Store results
            results.append({
                "test_case": test_case['name'],
                "llama": {
                    "response": llama_response,
                    "quality": llama_quality
                },
                "claude": {
                    "response": claude_response,
                    "quality": claude_quality
                }
            })
            
            # Print side-by-side
            print(f"\n{'─'*60}")
            print("Comparison:")
            print(f"{'─'*60}")
            print(f"{'Metric':<25} {'Llama 3.2':<15} {'Claude':<15}")
            print(f"{'─'*60}")
            print(f"{'Time (seconds)':<25} {llama_response['time']:<15.2f} {claude_response['time']:<15.2f}")
            print(f"{'Completeness (%)':<25} {llama_quality['completeness']:<15.0f} {claude_quality['completeness']:<15.0f}")
            print(f"{'Key Points':<25} {llama_quality['key_points']:<15} {claude_quality['key_points']:<15}")
            print(f"{'Action Items':<25} {llama_quality['action_items']:<15} {claude_quality['action_items']:<15}")
            print(f"{'People Mentioned':<25} {llama_quality['people']:<15} {claude_quality['people']:<15}")
            print(f"{'Tags':<25} {llama_quality['tags']:<15} {claude_quality['tags']:<15}")
        
        # Overall summary
        self.print_summary(results)
        
        # Save detailed results
        with open('comparison_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n✓ Detailed results saved to: comparison_results.json")
        
        return results
    
    def print_summary(self, results):
        """Print overall comparison summary"""
        print("\n" + "="*60)
        print("OVERALL COMPARISON SUMMARY")
        print("="*60)
        
        # Calculate averages
        llama_avg_time = sum(r['llama']['response']['time'] for r in results) / len(results)
        claude_avg_time = sum(r['claude']['response']['time'] for r in results) / len(results)
        
        llama_avg_completeness = sum(r['llama']['quality']['completeness'] for r in results) / len(results)
        claude_avg_completeness = sum(r['claude']['quality']['completeness'] for r in results) / len(results)
        
        print(f"\nAverage Speed:")
        print(f"  Llama 3.2 3B:    {llama_avg_time:.2f}s")
        print(f"  Claude Sonnet 4: {claude_avg_time:.2f}s")
        print(f"  Speed difference: {((claude_avg_time - llama_avg_time) / claude_avg_time * 100):.0f}% faster" if llama_avg_time < claude_avg_time else f"  Speed difference: {((llama_avg_time - claude_avg_time) / llama_avg_time * 100):.0f}% slower")
        
        print(f"\nAverage Quality (Completeness):")
        print(f"  Llama 3.2 3B:    {llama_avg_completeness:.0f}%")
        print(f"  Claude Sonnet 4: {claude_avg_completeness:.0f}%")
        print(f"  Quality gap:     {(claude_avg_completeness - llama_avg_completeness):.0f}%")
        
        print(f"\nCost Comparison (per 1000 memories):")
        print(f"  Llama 3.2 3B:    $0.00 (after training)")
        print(f"  Claude Sonnet 4: ~$3-15")
        print(f"  Savings:         100%")
        
        print(f"\nVRAM Usage:")
        if torch.cuda.is_available():
            vram = torch.cuda.memory_allocated(0) / 1024**3
            print(f"  Llama 3.2 3B:    ~{vram:.1f}GB (fits RTX 4050)")
        print(f"  Claude Sonnet 4: 0GB (API)")
        
        print(f"\n{'='*60}")


def main():
    """Main function"""
    print("="*60)
    print("Memora Model Comparison Tool")
    print("="*60)
    
    # Check requirements
    if not os.path.exists("memora-llama-3.2-3b-finetuned_merged"):
        print("\n❌ Error: Fine-tuned model not found")
        print("\nPlease complete these steps first:")
        print("1. python generate_training_data.py")
        print("2. python finetune_llama.py")
        return
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ Error: ANTHROPIC_API_KEY not found in .env")
        print("\nPlease add your API key to .env file")
        return
    
    # Run comparison
    comparison = ModelComparison()
    results = comparison.run_comparison()
    
    print("\n" + "="*60)
    print("✅ Comparison Complete!")
    print("="*60)
    print("\nResults saved to: comparison_results.json")
    print("\nYou can now:")
    print("1. Review detailed results in comparison_results.json")
    print("2. Use Llama in Memora: python memora_with_llama.py")
    print("3. Continue using Claude API for production")
    print("")


if __name__ == "__main__":
    import torch
    main()
