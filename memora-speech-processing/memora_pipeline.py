"""
Memora Main Pipeline
Integrates speech processing, keyword extraction, summarization, and LLM processing
"""

import sys
import os

# Ensure this file's directory is on sys.path so sibling modules resolve correctly
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from speech_processor import SpeechProcessor
from keyword_extractor import KeywordExtractor
from summarizer import TextSummarizer
from typing import Dict, Optional
import json
from datetime import datetime


class MemoraProcessor:
    """
    Complete pipeline for processing audio into memory summaries
    """
    
    def __init__(
        self,
        whisper_model: str = "base",
        hf_token: Optional[str] = None,
        llm_provider: str = "anthropic",
        llm_api_key: Optional[str] = None,
        enable_diarization: bool = True
    ):
        """
        Initialize Memora processor
        
        Args:
            whisper_model: Whisper model size
            hf_token: HuggingFace token for diarization
            llm_provider: LLM provider (anthropic/openai)
            llm_api_key: API key for LLM
            enable_diarization: Whether to enable speaker diarization
        """
        print("Initializing Memora Pipeline...")
        
        # Initialize components
        self.speech_processor = SpeechProcessor(
            whisper_model_size=whisper_model,
            hf_token=hf_token if enable_diarization else None
        )
        
        self.keyword_extractor = KeywordExtractor()
        self.summarizer = TextSummarizer()
        
        try:
            from llm_processor_finetuned import LLMProcessor
            self.llm_processor = LLMProcessor(
                provider=llm_provider,
                api_key=llm_api_key
            )
            self.llm_enabled = True
        except Exception as e:
            print(f"Warning: Fine-tuned LLM not available ({e}). Trying rule-based fallback...")
            try:
                from llm_processor_rulebased import LLMProcessor as RuleProcessor
                self.llm_processor = RuleProcessor()
                self.llm_enabled = True
            except Exception as e2:
                print(f"Warning: LLM processor not available: {e2}")
                self.llm_processor = None
                self.llm_enabled = False
        
        print("Memora Pipeline ready!")
    
    def process_audio_file(
        self,
        audio_path: str,
        language: Optional[str] = None,
        num_speakers: Optional[int] = None,
        output_dir: str = "./output"
    ) -> Dict:
        """
        Process audio file through complete pipeline
        
        Args:
            audio_path: Path to audio file
            language: Language code (None for auto-detect)
            num_speakers: Expected number of speakers
            output_dir: Directory to save outputs
            
        Returns:
            Complete processing results
        """
        print(f"\n{'='*60}")
        print(f"Processing: {audio_path}")
        print(f"{'='*60}\n")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Speech processing (transcription + diarization)
        print("Step 1: Transcribing audio...")
        transcription = self.speech_processor.process_audio(
            audio_path,
            language=language,
            num_speakers=num_speakers
        )
        print(f"✓ Transcription complete ({transcription['language']})")
        
        # 2. Keyword extraction
        print("\nStep 2: Extracting keywords and entities...")
        keywords = self.keyword_extractor.extract_all(
            transcription['full_text']
        )
        print(f"✓ Found {len(keywords['combined_keywords'])} keywords")
        print(f"✓ Found {sum(len(v) for v in keywords['entities'].values())} entities")
        
        # 3. Summarization
        print("\nStep 3: Generating summaries...")
        if transcription.get('segments'):
            summary = self.summarizer.create_conversation_summary(
                transcription['segments']
            )
        else:
            summaries = self.summarizer.generate_all_summaries(
                transcription['full_text']
            )
            summary = {
                "overall_summary": summaries['textrank'],
                "method_used": "textrank"
            }
        print("✓ Summaries generated")
        
        # 4. LLM processing
        memory_summary = None
        if self.llm_enabled:
            print("\nStep 4: Generating AI-powered memory summary...")
            try:
                memory_summary = self.llm_processor.generate_memory_summary(
                    transcription,
                    keywords,
                    summary
                )
                print("✓ Memory summary generated")
            except Exception as e:
                print(f"⚠ LLM processing failed: {e}")
        else:
            print("\nStep 4: Skipped (LLM not available)")
        
        # Compile results
        results = {
            "metadata": {
                "audio_file": audio_path,
                "processed_at": datetime.now().isoformat(),
                "language": transcription.get('language'),
                "has_diarization": transcription.get('has_diarization', False)
            },
            "transcription": transcription,
            "keywords": keywords,
            "summary": summary,
            "memory_summary": memory_summary
        }
        
        # Save results
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        # Save complete results
        results_file = os.path.join(output_dir, f"{base_name}_complete.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Complete results saved to: {results_file}")
        
        # Save memory summary separately (for app consumption)
        if memory_summary:
            memory_file = os.path.join(output_dir, f"{base_name}_memory.json")
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_summary, f, ensure_ascii=False, indent=2)
            print(f"✓ Memory summary saved to: {memory_file}")
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: Dict):
        """Print processing summary to console"""
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print(f"{'='*60}")
        
        # Transcription
        print(f"\nLanguage: {results['metadata']['language']}")
        print(f"Speaker Diarization: {'Enabled' if results['metadata']['has_diarization'] else 'Disabled'}")
        print(f"\nFull Transcription:\n{results['transcription']['full_text']}")
        
        # Entities
        print("\n" + "-"*60)
        print("KEY ENTITIES:")
        for entity_type, entities in results['keywords']['entities'].items():
            if entities:
                print(f"  {entity_type.capitalize()}: {', '.join(entities)}")
        
        # Keywords
        if results['keywords']['combined_keywords']:
            print("\nKEYWORDS:")
            print(f"  {', '.join(results['keywords']['combined_keywords'][:10])}")
        
        # Summary
        print("\n" + "-"*60)
        print("AUTOMATIC SUMMARY:")
        print(f"  {results['summary'].get('overall_summary', 'N/A')}")
        
        # Memory summary
        if results.get('memory_summary'):
            mem = results['memory_summary']
            print("\n" + "-"*60)
            print("AI-GENERATED MEMORY SUMMARY:")
            print(f"\nTitle: {mem.get('title', 'N/A')}")
            print(f"\nQuick Summary:\n  {mem.get('quick_summary', 'N/A')}")
            
            if mem.get('key_points'):
                print("\nKey Points:")
                for i, point in enumerate(mem['key_points'], 1):
                    print(f"  {i}. {point}")
            
            if mem.get('action_items'):
                print("\nAction Items:")
                for item in mem['action_items']:
                    print(f"  • {item}")
            
            if mem.get('people'):
                print("\nPeople:")
                for person in mem['people']:
                    print(f"  • {person.get('name', 'Unknown')}", end="")
                    if person.get('context'):
                        print(f" - {person['context']}", end="")
                    print()
            
            if mem.get('tags'):
                print(f"\nTags: {', '.join(mem['tags'])}")
        
        print("\n" + "="*60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memora Audio Processing Pipeline")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--language", "-l", help="Language code (e.g., 'en')")
    parser.add_argument("--speakers", "-s", type=int, help="Number of speakers")
    parser.add_argument("--output", "-o", default="./output", help="Output directory")
    parser.add_argument("--whisper-model", default="base", 
                       choices=["tiny", "base", "small", "medium", "large"],
                       help="Whisper model size")
    parser.add_argument("--llm-provider", default="anthropic",
                       choices=["anthropic", "openai"],
                       help="LLM provider")
    parser.add_argument("--no-diarization", action="store_true",
                       help="Disable speaker diarization")
    
    args = parser.parse_args()
    
    # Get tokens from environment
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    llm_key = None
    
    if args.llm_provider == "anthropic":
        llm_key = os.getenv("ANTHROPIC_API_KEY")
    elif args.llm_provider == "openai":
        llm_key = os.getenv("OPENAI_API_KEY")
    
    # Initialize processor
    processor = MemoraProcessor(
        whisper_model=args.whisper_model,
        hf_token=hf_token,
        llm_provider=args.llm_provider,
        llm_api_key=llm_key,
        enable_diarization=not args.no_diarization
    )
    
    # Process audio
    results = processor.process_audio_file(
        args.audio_file,
        language=args.language,
        num_speakers=args.speakers,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
