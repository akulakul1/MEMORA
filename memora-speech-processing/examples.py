"""
Simple Example: Using the Memora Pipeline

This script demonstrates basic usage of the Memora speech processing pipeline.
"""

import os
from pathlib import Path


def example_1_basic_usage():
    """
    Example 1: Basic transcription without diarization
    """
    print("\n" + "="*60)
    print("Example 1: Basic Transcription")
    print("="*60)
    
    from speech_processor import SpeechProcessor
    
    # Initialize processor
    processor = SpeechProcessor(
        whisper_model_size="tiny",  # Use tiny for quick testing
        hf_token=None  # No diarization
    )
    
    # Transcribe audio
    audio_file = "your_audio.mp3"  # Replace with your file
    if not os.path.exists(audio_file):
        print(f"⚠ Audio file not found: {audio_file}")
        print("Please replace 'your_audio.mp3' with an actual audio file")
        return
    
    result = processor.transcribe_audio(audio_file)
    
    print(f"\nLanguage detected: {result['language']}")
    print(f"\nTranscription:\n{result['text']}")


def example_2_with_diarization():
    """
    Example 2: Transcription with speaker diarization
    """
    print("\n" + "="*60)
    print("Example 2: Transcription with Speaker Diarization")
    print("="*60)
    
    from speech_processor import SpeechProcessor
    
    # Get HuggingFace token
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        print("⚠ HUGGINGFACE_TOKEN not found in environment")
        print("Please add it to .env file for speaker diarization")
        return
    
    # Initialize with diarization
    processor = SpeechProcessor(
        whisper_model_size="base",
        hf_token=hf_token
    )
    
    # Process audio
    audio_file = "conversation.mp3"  # Replace with your file
    if not os.path.exists(audio_file):
        print(f"⚠ Audio file not found: {audio_file}")
        return
    
    result = processor.process_audio(
        audio_file,
        num_speakers=2  # Expected number of speakers
    )
    
    print(f"\nLanguage: {result['language']}")
    print(f"Has diarization: {result['has_diarization']}")
    
    if result['has_diarization']:
        print("\nConversation segments:")
        for i, segment in enumerate(result['segments'][:5]):  # First 5 segments
            print(f"\n[{segment['speaker']}] ({segment['start']:.1f}s - {segment['end']:.1f}s)")
            print(f"  {segment['text']}")


def example_3_keyword_extraction():
    """
    Example 3: Extract keywords from text
    """
    print("\n" + "="*60)
    print("Example 3: Keyword Extraction")
    print("="*60)
    
    from keyword_extractor import KeywordExtractor
    
    sample_text = """
    Yesterday I met with Dr. Sarah Johnson at Memorial Hospital in New York.
    We discussed my treatment plan for ADHD. She recommended increasing my
    medication dosage from 10mg to 15mg. My next appointment is scheduled
    for Tuesday, March 15th at 2 PM. I need to remember to bring my test
    results and insurance card.
    """
    
    extractor = KeywordExtractor()
    results = extractor.extract_all(sample_text)
    
    print("\nNamed Entities:")
    for entity_type, entities in results['entities'].items():
        if entities:
            print(f"  {entity_type.capitalize()}: {', '.join(entities)}")
    
    print("\nTop Keywords:")
    if results['keybert_keywords']:
        for kw in results['keybert_keywords'][:5]:
            print(f"  • {kw['keyword']} (score: {kw['score']:.2f})")


def example_4_summarization():
    """
    Example 4: Generate summaries
    """
    print("\n" + "="*60)
    print("Example 4: Text Summarization")
    print("="*60)
    
    from summarizer import TextSummarizer
    
    long_text = """
    The patient arrived for their scheduled appointment at 3 PM. During the
    consultation, we reviewed their current medication regimen and discussed
    any side effects they've been experiencing. The patient reported improved
    focus and concentration since starting the new medication two weeks ago.
    However, they mentioned some difficulty falling asleep at night. After
    careful consideration, we decided to adjust the dosage timing. The patient
    will now take their medication in the morning instead of the afternoon.
    We scheduled a follow-up appointment for two weeks from today to assess
    the effectiveness of this change. The patient was advised to maintain
    a sleep journal and to contact us if any concerning symptoms develop.
    They left the office with a new prescription and clear instructions for
    the medication adjustment. The patient expressed satisfaction with the
    treatment plan and asked good questions about long-term management.
    """
    
    summarizer = TextSummarizer()
    
    # Generate different types of summaries
    summaries = summarizer.generate_all_summaries(long_text, sentences_count=2)
    
    print("\nTextRank Summary:")
    print(summaries['textrank'])
    
    print("\nLexRank Summary:")
    print(summaries['lexrank'])


def example_5_full_pipeline():
    """
    Example 5: Complete pipeline with LLM
    """
    print("\n" + "="*60)
    print("Example 5: Full Pipeline with LLM")
    print("="*60)
    
    from memora_pipeline import MemoraProcessor
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ No LLM API key found")
        print("Please add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env")
        return
    
    # Initialize processor
    processor = MemoraProcessor(
        whisper_model="tiny",  # Fast for testing
        llm_provider="anthropic" if os.getenv("ANTHROPIC_API_KEY") else "openai",
        enable_diarization=False  # Disable for speed
    )
    
    # Process audio file
    audio_file = "sample.mp3"  # Replace with your file
    if not os.path.exists(audio_file):
        print(f"⚠ Audio file not found: {audio_file}")
        print("Creating a sample would require actual audio")
        return
    
    # Process
    results = processor.process_audio_file(
        audio_file,
        output_dir="./example_output"
    )
    
    print("\n✓ Processing complete!")
    print(f"Results saved to: ./example_output/")


def example_6_custom_processing():
    """
    Example 6: Custom processing pipeline
    """
    print("\n" + "="*60)
    print("Example 6: Custom Processing Pipeline")
    print("="*60)
    
    from speech_processor import SpeechProcessor
    from keyword_extractor import KeywordExtractor
    from summarizer import TextSummarizer
    
    # Step 1: Transcribe
    print("\n1. Transcribing audio...")
    processor = SpeechProcessor(whisper_model_size="tiny")
    
    # Simulate with sample text (replace with actual transcription)
    transcription = {
        "text": "Sample transcribed text about a doctor's appointment",
        "language": "en"
    }
    print(f"   Language: {transcription['language']}")
    
    # Step 2: Extract keywords
    print("\n2. Extracting keywords...")
    extractor = KeywordExtractor()
    keywords = extractor.extract_all(transcription['text'])
    print(f"   Found {len(keywords['combined_keywords'])} keywords")
    
    # Step 3: Summarize
    print("\n3. Generating summary...")
    summarizer = TextSummarizer()
    summary = summarizer.summarize_textrank(transcription['text'])
    print(f"   Summary: {summary[:100]}...")
    
    print("\n✓ Custom pipeline complete!")


def main():
    """
    Run examples
    """
    print("\n" + "="*70)
    print("MEMORA PIPELINE - USAGE EXAMPLES")
    print("="*70)
    
    print("\nAvailable examples:")
    print("1. Basic transcription")
    print("2. Transcription with speaker diarization")
    print("3. Keyword extraction")
    print("4. Text summarization")
    print("5. Full pipeline with LLM")
    print("6. Custom processing pipeline")
    
    choice = input("\nEnter example number (1-6) or 'all' to run all: ").strip()
    
    if choice == '1':
        example_1_basic_usage()
    elif choice == '2':
        example_2_with_diarization()
    elif choice == '3':
        example_3_keyword_extraction()
    elif choice == '4':
        example_4_summarization()
    elif choice == '5':
        example_5_full_pipeline()
    elif choice == '6':
        example_6_custom_processing()
    elif choice.lower() == 'all':
        example_3_keyword_extraction()  # Doesn't need audio
        example_4_summarization()  # Doesn't need audio
        example_6_custom_processing()  # Simulated
        print("\n✓ All available examples completed!")
        print("\nNote: Examples 1, 2, and 5 require actual audio files.")
    else:
        print("Invalid choice. Please run again and select 1-6 or 'all'")
    
    print("\n" + "="*70)
    print("For more information, see README.md and ARCHITECTURE.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main()
