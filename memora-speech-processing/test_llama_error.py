import json
import traceback
from memora_llama_processor import MemoraLlamaLLM

path = r'C:\Users\VIJAY\OneDrive\Desktop\MemIot\memora-speech-processing\data\users\6b55eb4f-82f6-462b-9939-879f3a2a988e\audio\20260312_053200_transcription.json'
with open(path, 'r', encoding='utf-8') as f:
    results = json.load(f)

print('Initializing Llama...')
try:
    llm = MemoraLlamaLLM()
    print('Generating summary...')
    ai_sum = llm.generate_memory_summary(
        transcription=results,
        keywords=results.get('keywords', {}),
        summary={}
    )
    print('SUCCESS')
except Exception as e:
    with open('exception_trace.txt', 'w') as f:
        traceback.print_exc(file=f)
    print('ERROR: Details written to exception_trace.txt')
