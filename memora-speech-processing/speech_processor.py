"""
Memora Speech Processing Pipeline
Handles audio transcription, speaker diarization, keyword extraction, and summarization
"""

import whisper
import torch
from pyannote.audio import Pipeline
from pyannote.core import Segment
import os
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime
import numpy as np

class SpeechProcessor:
    """
    Main class for processing audio recordings into structured memory data
    """
    
    def __init__(
        self,
        whisper_model_size: str = "base",
        hf_token: Optional[str] = None,
        device: str = None
    ):
        """
        Initialize the speech processor
        
        Args:
            whisper_model_size: Size of Whisper model (tiny, base, small, medium, large)
            hf_token: HuggingFace token for pyannote.audio
            device: Device to run models on (cuda/cpu)
        """
        # Set device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"Using device: {self.device}")
        
        # Load Whisper model
        print(f"Loading Whisper {whisper_model_size} model...")
        self.whisper_model = whisper.load_model(whisper_model_size, device=self.device)
        
        # Load diarization pipeline (requires HuggingFace token)
        self.diarization_pipeline = None
        if hf_token:
            try:
                print("Loading speaker diarization pipeline...")
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token
                )
                if self.device == "cuda":
                    self.diarization_pipeline.to(torch.device("cuda"))
            except Exception as e:
                print(f"Warning: Could not load diarization pipeline: {e}")
                print("Speaker diarization will be disabled.")
        else:
            print("No HuggingFace token provided. Speaker diarization will be disabled.")
    
    def transcribe_audio(
        self,
        audio_path: str,
        language: str = None
    ) -> Dict:
        """
        Transcribe audio file using Whisper
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en'). None for auto-detect
            
        Returns:
            Dictionary with transcription results
        """
        print(f"Transcribing audio: {audio_path}")
        
        # Transcribe with Whisper
        result = self.whisper_model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            verbose=False
        )
        
        return {
            "text": result["text"],
            "segments": result["segments"],
            "language": result["language"]
        }
    
    def diarize_audio(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> Optional[List[Dict]]:
        """
        Perform speaker diarization on audio file
        
        Args:
            audio_path: Path to audio file
            num_speakers: Expected number of speakers (optional)
            
        Returns:
            List of speaker segments or None if diarization unavailable
        """
        if self.diarization_pipeline is None:
            return None
        
        print("Performing speaker diarization...")
        
        # ── Handle .m4a/.mp3 files for Pyannote ──
        # Pyannote uses soundfile which fails on .m4a, so we convert it to .wav
        import subprocess
        wav_path = audio_path
        if audio_path.lower().endswith(('.m4a', '.mp3', '.mp4')):
            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
            if not os.path.exists(wav_path):
                print(f"[diarize] Converting {os.path.basename(audio_path)} to WAV format...")
                try:
                    subprocess.run(
                        ['ffmpeg', '-i', audio_path, '-ar', '16000', '-ac', '1', '-y', wav_path],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
                    )
                except Exception as e:
                    print(f"[diarize] Failed to convert audio: {e}")
                    wav_path = audio_path # Fallback to original and pray
        
        # Run diarization
        diarization_params = {}
        if num_speakers is not None:
            diarization_params["num_speakers"] = num_speakers
        
        try:
            diarization = self.diarization_pipeline(
                wav_path,
                **diarization_params
            )
        finally:
            # Clean up the temporary wav file
            if wav_path != audio_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass
        
        # Convert to list of segments
        speaker_segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        
        return speaker_segments
    
    def align_transcription_with_speakers(
        self,
        transcription: Dict,
        speaker_segments: List[Dict]
    ) -> List[Dict]:
        """
        Align transcription segments with speaker labels
        
        Args:
            transcription: Whisper transcription result
            speaker_segments: Diarization results
            
        Returns:
            List of aligned segments with speaker labels
        """
        aligned_segments = []
        
        for segment in transcription["segments"]:
            seg_start = segment["start"]
            seg_end = segment["end"]
            seg_mid = (seg_start + seg_end) / 2
            
            # Find the speaker at the midpoint of this segment
            speaker = "Unknown"
            for spk_seg in speaker_segments:
                if spk_seg["start"] <= seg_mid <= spk_seg["end"]:
                    speaker = spk_seg["speaker"]
                    break
            
            aligned_segments.append({
                "start": seg_start,
                "end": seg_end,
                "text": segment["text"].strip(),
                "speaker": speaker
            })
        
        return aligned_segments
    
    def process_audio(
        self,
        audio_path: str,
        language: str = None,
        num_speakers: Optional[int] = None
    ) -> Dict:
        """
        Complete audio processing pipeline
        
        Args:
            audio_path: Path to audio file
            language: Language code for transcription
            num_speakers: Expected number of speakers
            
        Returns:
            Dictionary with complete processing results
        """
        # Transcribe
        transcription = self.transcribe_audio(audio_path, language)
        
        # Diarize (if available)
        speaker_segments = None
        aligned_segments = None
        
        if self.diarization_pipeline is not None:
            speaker_segments = self.diarize_audio(audio_path, num_speakers)
            if speaker_segments:
                aligned_segments = self.align_transcription_with_speakers(
                    transcription,
                    speaker_segments
                )
        
        # Prepare result
        result = {
            "timestamp": datetime.now().isoformat(),
            "audio_file": audio_path,
            "full_text": transcription["text"],
            "language": transcription["language"],
            "segments": aligned_segments if aligned_segments else transcription["segments"],
            "has_diarization": aligned_segments is not None
        }
        
        return result


def save_results(results: Dict, output_path: str):
    """
    Save processing results to JSON file
    
    Args:
        results: Processing results dictionary
        output_path: Path to save JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python speech_processor.py <audio_file> [language] [num_speakers]")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else None
    num_speakers = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    # Get HuggingFace token from environment
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    # Initialize processor
    processor = SpeechProcessor(
        whisper_model_size="base",
        hf_token=hf_token
    )
    
    # Process audio
    results = processor.process_audio(
        audio_file,
        language=language,
        num_speakers=num_speakers
    )
    
    # Save results
    output_file = audio_file.rsplit('.', 1)[0] + '_transcription.json'
    save_results(results, output_file)
    
    # Print summary
    print("\n" + "="*50)
    print("TRANSCRIPTION SUMMARY")
    print("="*50)
    print(f"Language: {results['language']}")
    print(f"Speaker diarization: {'Enabled' if results['has_diarization'] else 'Disabled'}")
    print(f"\nFull text:\n{results['full_text']}")
