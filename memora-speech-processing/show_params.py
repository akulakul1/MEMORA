import json
import glob
import os
from pprint import pprint

files = glob.glob(r'data\users\*\audio\*_transcription.json')
if not files:
    print("No JSON files found")
else:
    files.sort(key=os.path.getmtime)
    latest = files[-1]
    print(f"Using {latest}")
    with open(latest, 'r', encoding='utf-8') as f:
        d = json.load(f)
    print("\n--- Parameters passed to generate_memory_summary ---")
    print("transcription keys:", list(d.keys()))
    print("full_text:", repr(d.get("full_text", "")[:100] + "..."))
    print("\nkeywords:")
    pprint(d.get("keywords", {}))
    print("\nsummary: {}")
