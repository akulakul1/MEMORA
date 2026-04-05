"""
Summarization Module
Generates summaries of transcribed conversations
"""

from typing import List, Dict
import re

try:
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lsa import LsaSummarizer
    from sumy.summarizers.text_rank import TextRankSummarizer
    from sumy.summarizers.lex_rank import LexRankSummarizer
    _SUMY_AVAILABLE = True
except ImportError:
    _SUMY_AVAILABLE = False

try:
    import nltk
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        try:
            nltk.download('punkt_tab')
        except Exception:
            pass
except ImportError:
    pass


class TextSummarizer:
    """
    Generate summaries using multiple algorithms
    """
    
    def __init__(self, language: str = "english"):
        """
        Initialize summarizer
        
        Args:
            language: Language for tokenization
        """
        self.language = language
        if _SUMY_AVAILABLE:
            self.tokenizer = Tokenizer(language)
        else:
            self.tokenizer = None
            print("Warning: sumy not installed. Summaries will use simple sentence extraction.")
    
    def _parse_text(self, text: str):
        """Parse text for summarization"""
        if not _SUMY_AVAILABLE:
            return None
        return PlaintextParser.from_string(text, self.tokenizer)
    
    def _simple_summarize(self, text: str, sentences_count: int = 3) -> str:
        """Fallback summarizer using first N sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return ' '.join(sentences[:sentences_count])
    
    def summarize_lsa(
        self,
        text: str,
        sentences_count: int = 3
    ) -> str:
        """
        Summarize using Latent Semantic Analysis
        
        Args:
            text: Input text
            sentences_count: Number of sentences in summary
            
        Returns:
            Summary text
        """
        if not _SUMY_AVAILABLE:
            return self._simple_summarize(text, sentences_count)
        parser = self._parse_text(text)
        summarizer = LsaSummarizer()
        
        summary_sentences = summarizer(parser.document, sentences_count)
        return ' '.join(str(sentence) for sentence in summary_sentences)
    
    def summarize_textrank(
        self,
        text: str,
        sentences_count: int = 3
    ) -> str:
        """
        Summarize using TextRank algorithm
        
        Args:
            text: Input text
            sentences_count: Number of sentences in summary
            
        Returns:
            Summary text
        """
        if not _SUMY_AVAILABLE:
            return self._simple_summarize(text, sentences_count)
        parser = self._parse_text(text)
        summarizer = TextRankSummarizer()
        
        summary_sentences = summarizer(parser.document, sentences_count)
        return ' '.join(str(sentence) for sentence in summary_sentences)

    
    def summarize_lexrank(
        self,
        text: str,
        sentences_count: int = 3
    ) -> str:
        """
        Summarize using LexRank algorithm
        
        Args:
            text: Input text
            sentences_count: Number of sentences in summary
            
        Returns:
            Summary text
        """
        if not _SUMY_AVAILABLE:
            return self._simple_summarize(text, sentences_count)
        parser = self._parse_text(text)
        summarizer = LexRankSummarizer()
        
        summary_sentences = summarizer(parser.document, sentences_count)
        return ' '.join(str(sentence) for sentence in summary_sentences)
    
    def generate_all_summaries(
        self,
        text: str,
        sentences_count: int = 3
    ) -> Dict[str, str]:
        """
        Generate summaries using all available methods
        
        Args:
            text: Input text
            sentences_count: Number of sentences in summary
            
        Returns:
            Dictionary of summaries from different methods
        """
        if not text or len(text.strip()) < 50:
            return {
                "lsa": text,
                "textrank": text,
                "lexrank": text
            }
        
        try:
            summaries = {
                "lsa": self.summarize_lsa(text, sentences_count),
                "textrank": self.summarize_textrank(text, sentences_count),
                "lexrank": self.summarize_lexrank(text, sentences_count)
            }
        except Exception as e:
            print(f"Warning: Summarization failed: {e}")
            summaries = {
                "lsa": text,
                "textrank": text,
                "lexrank": text
            }
        
        return summaries
    
    def create_conversation_summary(
        self,
        segments: List[Dict],
        method: str = "textrank"
    ) -> Dict:
        """
        Create a structured summary from conversation segments
        
        Args:
            segments: List of conversation segments with speaker info
            method: Summarization method to use (lsa, textrank, lexrank)
            
        Returns:
            Dictionary with conversation summary
        """
        # Extract full text
        full_text = ' '.join(seg.get('text', '') for seg in segments)
        
        # Count speakers
        speakers = set()
        speaker_utterances = {}
        
        for seg in segments:
            speaker = seg.get('speaker', 'Unknown')
            speakers.add(speaker)
            
            if speaker not in speaker_utterances:
                speaker_utterances[speaker] = []
            speaker_utterances[speaker].append(seg.get('text', ''))
        
        # Generate summary
        if method == "lsa":
            summary = self.summarize_lsa(full_text)
        elif method == "textrank":
            summary = self.summarize_textrank(full_text)
        elif method == "lexrank":
            summary = self.summarize_lexrank(full_text)
        else:
            summary = full_text[:200] + "..."  # Fallback
        
        # Create per-speaker summaries
        speaker_summaries = {}
        for speaker, utterances in speaker_utterances.items():
            speaker_text = ' '.join(utterances)
            if len(speaker_text) > 50:
                if method == "lsa":
                    speaker_summaries[speaker] = self.summarize_lsa(speaker_text, 2)
                elif method == "textrank":
                    speaker_summaries[speaker] = self.summarize_textrank(speaker_text, 2)
                else:
                    speaker_summaries[speaker] = self.summarize_lexrank(speaker_text, 2)
            else:
                speaker_summaries[speaker] = speaker_text
        
        return {
            "overall_summary": summary,
            "num_speakers": len(speakers),
            "speakers": list(speakers),
            "speaker_summaries": speaker_summaries,
            "total_segments": len(segments),
            "method_used": method
        }


class BulletPointSummarizer:
    """
    Create bullet-point summaries from text
    """
    
    def __init__(self):
        self.summarizer = TextSummarizer()
    
    def create_bullet_points(
        self,
        text: str,
        num_points: int = 5
    ) -> List[str]:
        """
        Create bullet point summary
        
        Args:
            text: Input text
            num_points: Number of bullet points
            
        Returns:
            List of bullet point strings
        """
        # Get key sentences
        summary = self.summarizer.summarize_textrank(text, num_points)
        
        # Split into sentences
        import re
        sentences = re.split(r'[.!?]+', summary)
        
        # Clean and format
        bullet_points = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                bullet_points.append(sentence)
        
        return bullet_points[:num_points]


if __name__ == "__main__":
    # Example usage
    sample_text = """
    The patient arrived at 3 PM for their scheduled appointment. We discussed
    their progress with the new medication regimen. They reported improved focus
    but mentioned experiencing some sleep difficulties. The dosage was adjusted
    from 10mg to 15mg. A follow-up appointment was scheduled for two weeks from
    today. The patient was advised to maintain a sleep journal and continue with
    cognitive behavioral therapy sessions. They expressed satisfaction with the
    overall treatment plan and asked about dietary recommendations. We provided
    information about foods that support cognitive function.
    """
    
    summarizer = TextSummarizer()
    
    # Generate summaries
    summaries = summarizer.generate_all_summaries(sample_text, sentences_count=2)
    
    print("LSA Summary:")
    print(summaries["lsa"])
    print("\nTextRank Summary:")
    print(summaries["textrank"])
    print("\nLexRank Summary:")
    print(summaries["lexrank"])
    
    # Bullet points
    print("\n" + "="*50)
    bullet_summarizer = BulletPointSummarizer()
    bullets = bullet_summarizer.create_bullet_points(sample_text, 3)
    
    print("Bullet Point Summary:")
    for i, bullet in enumerate(bullets, 1):
        print(f"{i}. {bullet}")
