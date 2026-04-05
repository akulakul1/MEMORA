import sys
import os
import json
import asyncio

print("=== Testing Diarization -> LLMProcessor flow ===")
try:
    # 1. Load SpeechProcessor
    print("Loading SpeechProcessor...")
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    from speech_processor import SpeechProcessor
    sp = SpeechProcessor(whisper_model_size="tiny", hf_token=hf_token) # use tiny for faster test
    
    # 2. Get a test audio file
    # Ensure there's a test file we can use
    audio_path = r"data\users\unknown_f23b3b9d\audio\20260312_185622.m4a"
    if not os.path.exists(audio_path):
        print(f"Test audio {audio_path} not found.")

    print(f"Processing audio: {audio_path}")
    results = sp.process_audio(audio_path=audio_path, language="en")
    full_text = results.get("full_text", "")
    print(f"Transcription text length: {len(full_text)}")
    print(f"Full text preview: {full_text[:100]}...")

    # 3. Keyword Extraction
    print("Extracting keywords...")
    from keyword_extractor import KeywordExtractor
    extractor = KeywordExtractor()
    kw_data = extractor.extract_all(full_text, top_n=10)
    results["keywords"] = kw_data
    
    # 4. LLM Processor
    print("Running LLM Processor...")
    from llm_processor_finetuned import LLMProcessor
    llm = LLMProcessor()
    
    ai_sum = llm.generate_memory_summary(
        transcription=results,
        keywords=results.get("keywords", {}),
        summary={}
    )
    results["ai_summary"] = ai_sum
    
    print("=== AI Summary Result ===")
    out_file = "test_summary_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(ai_sum, f, indent=2)
    print(f"Saved AI Summary to {out_file}")
    
    if ai_sum is None:
        print("ERROR: ai_sum is NONE!")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error occurred: {e}")
