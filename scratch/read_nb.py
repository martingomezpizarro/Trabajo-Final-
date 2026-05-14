import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('notebooks/02_modelos_regresion.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Show full content of cells 0-14 (sections 1-6)
for i, c in enumerate(nb['cells'][:15]):
    ct = c['cell_type']
    src = ''.join(c['source']) if isinstance(c['source'], list) else c['source']
    print(f"{'='*80}")
    print(f"CELL {i} ({ct})")
    print(f"{'='*80}")
    # For code cells, show full source
    print(src)
    print()
