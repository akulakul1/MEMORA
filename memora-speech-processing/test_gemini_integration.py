# Quick Test Script for Gemini-Powered Memora Pipeline

"""
Quick test to verify Gemini integration works
"""

from llm_processor_gemini import LLMProcessor
from datetime import datetime
import json

print("="*70)
print("Testing Gemini LLM Integration")
print("="*70)

# Test 1: Initialize processor
print("\nTest 1: Initializing Gemini LLM...")
try:
    llm = LLMProcessor()
    print("✅ SUCCESS: Gemini LLM initialized")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit(1)

# Test 2: Generate memory summary
print("\nTest 2: Generating memory summary...")

test_transcription = {
    "timestamp": datetime.now().isoformat(),
    "language": "en",
    "full_text": "I met with Dr. Johnson today at 2 PM. We talked about my ADHD medication. The 10mg wasn't working well, so she increased it to 15mg. I need to take it in the morning now instead of afternoon. She said to come back in two weeks on Tuesday."
}

test_keywords = {
    "entities": {
        "persons": ["Dr. Johnson"],
        "locations": [],
        "dates": ["Tuesday", "two weeks"],
        "times": ["2 PM"]
    },
    "combined_keywords": ["medication", "ADHD", "appointment", "dosage"]
}

test_summary = {
    "overall_summary": "Medical appointment to discuss ADHD medication adjustment."
}

try:
    result = llm.generate_memory_summary(
        test_transcription,
        test_keywords,
        test_summary
    )
    print("✅ SUCCESS: Memory summary generated")
    print("\nGenerated Summary:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*70)
print("✅ ALL TESTS PASSED - Gemini integration is working!")
print("="*70)
print("\n📝 Next steps:")
print("  1. Run full pipeline: python run_memora.py audio/sample.wav")
print("  2. Or use memora_pipeline.py directly")
print("\n✨ Your Memora system is now using FREE Gemini API!")
