import sys, json, re
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

filepath = 'visualizador.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract just the EMBEDDED JSON object
emb_start = content.find('const EMBEDDED=')
emb_start += len('const EMBEDDED=')
emb_end   = content.find('const CATALOG', emb_start)

emb_text = content[emb_start:emb_end].strip()
# Should end with };  — remove the trailing ;
if emb_text.endswith(';'):
    emb_text = emb_text[:-1]

print(f'EMBEDDED JSON length: {len(emb_text)}')
print(f'Starts with: {repr(emb_text[:30])}')
print(f'Ends with:   {repr(emb_text[-30:])}')

# Try to parse it
try:
    data = json.loads(emb_text)
    print(f'\n✓ JSON válido. Keys count: {len(data)}')
    keys = list(data.keys())
    print(f'Last 3 keys: {keys[-3:]}')
except json.JSONDecodeError as e:
    print(f'\n✗ JSON INVÁLIDO: {e}')
    # Show context around the error
    pos = e.pos
    print(f'At position {pos}:')
    print(repr(emb_text[max(0,pos-50):pos+50]))
