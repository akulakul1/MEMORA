import sys
import os

print("=== Testing LLMProcessor Initialisation ===")
try:
    from llm_processor_finetuned import LLMProcessor
    print("Successfully imported LLMProcessor.")
    
    print("Instantiating LLMProcessor...")
    llm = LLMProcessor()
    print("Successfully instantiated LLMProcessor.")
    
    print("Testing generate_memory_summary...")
    transcription = {"full_text": "Hi Bob, remember we have a meeting at 3 PM tomorrow.", "timestamp": "2026-03-12T15:00:00Z"}
    keywords = {"combined_keywords": ["meeting", "tomorrow"], "entities": {"persons": ["Bob"], "times": ["3 PM"]}}
    summary = {}
    
    ai_sum = llm.generate_memory_summary(transcription=transcription, keywords=keywords, summary=summary)
    print("generate_memory_summary completed.")
    print("Result:", ai_sum)
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print("Error occurred:", e)
