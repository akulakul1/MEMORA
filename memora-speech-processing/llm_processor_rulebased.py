"""
Memora Rule-Based Summary Processor
Pure Python fallback — zero ML dependencies.
Generates a structured ai_summary from transcript text + extracted keywords/entities.
"""

import re
from typing import Dict, List
from datetime import datetime


class LLMProcessor:
    """
    Rule-based summary generator.
    Drop-in replacement for llm_processor_finetuned.py and llm_processor_gemini.py.
    Uses already-extracted keywords and NLP entities to build a structured summary.
    No transformers / peft / torch / cloud API required.
    """

    def __init__(self, provider=None, api_key=None):
        print("[RuleBased] Rule-based summary processor ready (no ML needed).")

    def generate_memory_summary(
        self,
        transcription: Dict,
        keywords: Dict,
        summary: Dict,
    ) -> Dict:
        full_text: str = transcription.get("full_text", "").strip()
        entities: Dict = keywords.get("entities", {})
        combined_kw: List[str] = keywords.get("combined_keywords", [])
        keybert: List[Dict] = keywords.get("keybert_keywords", [])

        # ── Title ──────────────────────────────────────────────────────────────
        title = self._make_title(full_text, combined_kw, entities)

        # ── Quick Summary ──────────────────────────────────────────────────────
        quick_summary = self._make_quick_summary(full_text)

        # ── Key Points ────────────────────────────────────────────────────────
        key_points = self._extract_key_points(full_text, keybert)

        # ── Action Items ──────────────────────────────────────────────────────
        action_items = self._extract_action_items(full_text, entities)

        # ── People ────────────────────────────────────────────────────────────
        people = [
            {"name": p, "context": "mentioned"}
            for p in entities.get("persons", [])
            if p
        ]

        # ── Tags ──────────────────────────────────────────────────────────────
        tags = self._make_tags(entities, combined_kw)

        return {
            "title": title,
            "quick_summary": quick_summary,
            "key_points": key_points,
            "action_items": action_items,
            "people": people,
            "tags": tags,
            "generated_at": datetime.now().isoformat(),
            "model_used": "rule-based",
        }

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _make_title(self, text: str, keywords: List[str], entities: Dict) -> str:
        """Build a short title from top keywords / entities."""
        # Try top keybert phrase first (usually the most descriptive multi-word)
        for kw in keywords[:3]:
            parts = kw.title().split()
            if 2 <= len(parts) <= 5:
                return " ".join(parts)
        # Fall back to first 8 words of the transcript
        words = text.split()
        snippet = " ".join(words[:8])
        if len(words) > 8:
            snippet += "..."
        return snippet if snippet else "Conversation Memory"

    def _make_quick_summary(self, text: str) -> str:
        """Use the first 1-2 sentences as summary."""
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        summary = " ".join(sentences[:2]).strip()
        if len(summary) > 300:
            summary = summary[:297] + "..."
        return summary or text[:200]

    def _extract_key_points(self, text: str, keybert: List[Dict]) -> List[str]:
        """
        Turn each sentence into a key point, capped at 5.
        If the transcript is a single sentence, use top keybert phrases instead.
        """
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
        if len(sentences) > 1:
            return sentences[:5]

        # Single sentence — use keybert phrases
        points = [k["keyword"].capitalize() for k in keybert[:5] if k.get("keyword")]
        return points if points else [sentences[0]] if sentences else []

    def _extract_action_items(self, text: str, entities: Dict) -> List[str]:
        """
        Detect action-oriented sentences with modal/imperative verbs.
        Also generate an action item from time + event pairings.
        """
        action_verbs = r'\b(need|must|should|have to|going to|will|plan|want|meet|call|send|buy|visit|check|remind|take|bring|do|complete|finish|attend|pick up|drop off)\b'
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        items = []
        for s in sentences:
            if re.search(action_verbs, s, re.IGNORECASE):
                items.append(s.strip())

        # Add time-aware action items from entities
        times = entities.get("times", [])
        persons = entities.get("persons", [])
        locations = entities.get("locations", [])

        if times and not items:
            base = "Scheduled"
            if persons:
                base = f"Meet {persons[0]}"
            if locations:
                base += f" at {locations[0]}"
            base += f" at {times[0]}"
            items.append(base)

        return items[:5]

    def _make_tags(self, entities: Dict, combined_kw: List[str]) -> List[str]:
        """Build 3-5 tags from entity types + top single-word keywords."""
        tags = set()

        # Entity-based tags
        if entities.get("persons"):
            tags.add("people")
        if entities.get("times") or entities.get("dates"):
            tags.add("schedule")
        if entities.get("locations"):
            tags.add("location")
        if entities.get("organizations"):
            tags.add("organization")

        # Top single-word keywords as tags (lowercase, skip if too generic)
        skip = {"meet", "name", "said", "told", "like", "just", "also", "even"}
        for kw in combined_kw[:10]:
            word = kw.lower().strip()
            if len(word) > 3 and word not in skip and " " not in word:
                tags.add(word)
            if len(tags) >= 5:
                break

        return sorted(tags)[:5]

    def create_reminder_text(self, memory_summary: Dict, reminder_type: str = "daily") -> str:
        reminder = f"📝 Memora Reminder — {memory_summary.get('title', 'Memory')}\n\n"
        if memory_summary.get("quick_summary"):
            reminder += f"{memory_summary['quick_summary']}\n\n"
        if memory_summary.get("action_items"):
            reminder += "Things to remember:\n"
            for item in memory_summary["action_items"]:
                reminder += f"• {item}\n"
        if memory_summary.get("people"):
            reminder += "\nPeople involved:\n"
            for person in memory_summary["people"]:
                if isinstance(person, dict):
                    reminder += f"• {person.get('name', 'Unknown')}"
                    if person.get("context"):
                        reminder += f" — {person['context']}"
                else:
                    reminder += f"• {person}"
                reminder += "\n"
        return reminder
