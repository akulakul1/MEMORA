"""
Keyword Extraction Module
Extracts important keywords and entities from transcribed text
"""

from typing import List, Dict, Set, Tuple
from collections import Counter

try:
    from keybert import KeyBERT
    _KEYBERT_AVAILABLE = True
except ImportError:
    _KEYBERT_AVAILABLE = False

try:
    import yake as _yake_mod
    _YAKE_AVAILABLE = True
except ImportError:
    _YAKE_AVAILABLE = False

try:
    import spacy as _spacy_mod
    _SPACY_AVAILABLE = True
except ImportError:
    _SPACY_AVAILABLE = False


class KeywordExtractor:
    """
    Extract keywords and entities from text using multiple methods
    """
    
    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        use_keybert: bool = True,
        use_yake: bool = True
    ):
        """
        Initialize keyword extractor
        
        Args:
            spacy_model: Spacy model name to use
            use_keybert: Whether to use KeyBERT
            use_yake: Whether to use YAKE
        """
        self.use_keybert = use_keybert and _KEYBERT_AVAILABLE
        self.use_yake = use_yake and _YAKE_AVAILABLE
        self.nlp = None
        
        # Load spaCy model for NER
        if _SPACY_AVAILABLE:
            try:
                self.nlp = _spacy_mod.load(spacy_model)
            except OSError:
                print(f"Downloading spaCy model: {spacy_model}")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", spacy_model])
                self.nlp = _spacy_mod.load(spacy_model)
        else:
            print("Warning: spacy not installed. Named entity extraction will be disabled.")
        
        # Initialize KeyBERT
        if self.use_keybert:
            try:
                self.kw_model = KeyBERT()
            except Exception as e:
                print(f"Warning: Could not initialize KeyBERT: {e}")
                self.use_keybert = False
        
        # Initialize YAKE
        if self.use_yake:
            self.yake_extractor = _yake_mod.KeywordExtractor(
                lan="en",
                n=3,  # Max n-gram size
                dedupLim=0.9,
                dedupFunc='seqm',
                windowsSize=1,
                top=20
            )

    
    def extract_named_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities using spaCy
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of entity types and their values
        """
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "times": [],
            "other": []
        }
        
        if self.nlp is None:
            return entities
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            entity_text = ent.text.strip()
            
            if ent.label_ == "PERSON":
                entities["persons"].append(entity_text)
            elif ent.label_ in ["ORG", "PRODUCT"]:
                entities["organizations"].append(entity_text)
            elif ent.label_ in ["GPE", "LOC", "FAC"]:
                entities["locations"].append(entity_text)
            elif ent.label_ == "DATE":
                entities["dates"].append(entity_text)
            elif ent.label_ == "TIME":
                entities["times"].append(entity_text)
            else:
                entities["other"].append(f"{entity_text} ({ent.label_})")
        
        # Remove duplicates while preserving order
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))
        
        return entities

    
    def extract_keywords_keybert(
        self,
        text: str,
        top_n: int = 10,
        diversity: float = 0.5
    ) -> List[Tuple[str, float]]:
        """
        Extract keywords using KeyBERT
        
        Args:
            text: Input text
            top_n: Number of keywords to extract
            diversity: Diversity factor (0-1)
            
        Returns:
            List of (keyword, score) tuples
        """
        if not self.use_keybert:
            return []
        
        try:
            keywords = self.kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 3),
                stop_words='english',
                top_n=top_n,
                diversity=diversity
            )
            return keywords
        except Exception as e:
            print(f"Warning: KeyBERT extraction failed: {e}")
            return []
    
    def extract_keywords_yake(
        self,
        text: str,
        top_n: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Extract keywords using YAKE
        
        Args:
            text: Input text
            top_n: Number of keywords to extract
            
        Returns:
            List of (keyword, score) tuples
        """
        if not self.use_yake:
            return []
        
        try:
            keywords = self.yake_extractor.extract_keywords(text)
            # YAKE returns lower scores for better keywords
            return keywords[:top_n]
        except Exception as e:
            print(f"Warning: YAKE extraction failed: {e}")
            return []
    
    def extract_all(
        self,
        text: str,
        top_n: int = 10
    ) -> Dict:
        """
        Extract keywords using all available methods
        
        Args:
            text: Input text
            top_n: Number of keywords per method
            
        Returns:
            Dictionary with all extraction results
        """
        results = {
            "entities": self.extract_named_entities(text),
            "keybert_keywords": [],
            "yake_keywords": [],
            "combined_keywords": []
        }
        
        # Extract with KeyBERT
        if self.use_keybert:
            keybert_kws = self.extract_keywords_keybert(text, top_n)
            results["keybert_keywords"] = [
                {"keyword": kw, "score": float(score)}
                for kw, score in keybert_kws
            ]
        
        # Extract with YAKE
        if self.use_yake:
            yake_kws = self.extract_keywords_yake(text, top_n)
            results["yake_keywords"] = [
                {"keyword": kw, "score": float(score)}
                for kw, score in yake_kws
            ]
        
        # Combine keywords from both methods
        all_keywords = []
        
        if results["keybert_keywords"]:
            all_keywords.extend([kw["keyword"].lower() for kw in results["keybert_keywords"]])
        if results["yake_keywords"]:
            all_keywords.extend([kw["keyword"].lower() for kw in results["yake_keywords"]])
        
        # Filter and deduplicate (remove sub-phrases)
        # e.g., if "blood pressure" and "blood pressure okay" exist, keep "blood pressure okay", 
        # or maybe the other way around. Let's keep the shorter ones if they are more distinct, 
        # but generally KeyBERT/YAKE tend to output variations. We will remove phrases that are 
        # exact substrings of other longer phrases to reduce noise, or vice versa.
        # Removing substrings:
        
        unique_kws = list(set(all_keywords))
        
        # Sort by length descending, so we see longer phrases first
        unique_kws.sort(key=len, reverse=True)
        filtered_kws = []
        
        for kw in unique_kws:
            # Skip very common conversational filler words
            if kw in [ "good", "morning", "afternoon", "hello", "yes", "no", "okay", "right"]:
                continue
                
            # Check if this kw is a substring of an already accepted *longer* kw
            # Actually, standard NLP practice is to keep the shorter, more precise keyword 
            # and drop the longer noisy one (e.g. keep "appointment" instead of "appointment thursday right")
            # Let's reverse the sort and keep shorter ones.
            pass

        # Sort by length ASCENDING (shortest first)
        unique_kws.sort(key=len)
        filtered_kws = []

        for kw in unique_kws:
            # Clean up
            kw = kw.strip(',.!? \t')
            if len(kw) < 3 or kw in ["good", "morning", "afternoon", "hello", "yes", "no", "okay", "right", "yeah", "sure"]:
                continue
            
            # If this longer phrase contains an already accepted shorter core keyword, 
            # we skip it to prevent variations (e.g. keep "blood pressure", skip "blood pressure okay")
            is_redundant = False
            for accepted in filtered_kws:
                # If the accepted keyword is a substantial part of this new keyword
                if accepted in kw and len(accepted) > 3:
                    is_redundant = True
                    break
            
            if not is_redundant:
                # capitalize first letter for presentation
                filtered_kws.append(kw.title())
                
        # Only take top 8 distinct keywords
        results["combined_keywords"] = filtered_kws[:8]
        
        return results
    
    def extract_important_phrases(
        self,
        text: str,
        min_length: int = 3
    ) -> List[str]:
        """
        Extract noun phrases from text
        
        Args:
            text: Input text
            min_length: Minimum phrase length in characters
            
        Returns:
            List of noun phrases
        """
        doc = self.nlp(text)
        
        phrases = []
        for chunk in doc.noun_chunks:
            phrase = chunk.text.strip()
            if len(phrase) >= min_length:
                phrases.append(phrase)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(phrases))


if __name__ == "__main__":
    # Example usage
    sample_text = """
    Yesterday, Dr. Sarah Johnson met with her patient John Smith at Memorial Hospital
    in New York. They discussed his treatment plan for managing ADHD symptoms.
    The doctor recommended cognitive behavioral therapy and mentioned a follow-up
    appointment scheduled for next Tuesday at 2 PM. John expressed concerns about
    his memory issues and difficulty concentrating at work.
    """
    
    extractor = KeywordExtractor()
    results = extractor.extract_all(sample_text)
    
    print("Named Entities:")
    for entity_type, entities in results["entities"].items():
        if entities:
            print(f"  {entity_type}: {', '.join(entities)}")
    
    print("\nKeyBERT Keywords:")
    for kw in results["keybert_keywords"][:5]:
        print(f"  {kw['keyword']}: {kw['score']:.3f}")
    
    print("\nYAKE Keywords:")
    for kw in results["yake_keywords"][:5]:
        print(f"  {kw['keyword']}: {kw['score']:.3f}")
    
    print("\nCombined Keywords:")
    print(f"  {', '.join(results['combined_keywords'][:10])}")
