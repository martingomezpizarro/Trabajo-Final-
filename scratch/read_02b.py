import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('notebooks/02b_analisis_completo.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Show full content of cells 20-26 (ARDL estimation, ranking, VAR placeholder)
for i in [10, 14, 20, 22, 25, 26]:
    if i < len(nb['cells']):
        c = nb['cells'][i]
        ct = c['cell_type']
        src = ''.join(c['source']) if isinstance(c['source'], list) else c['source']
        print(f"{'='*80}")
        print(f"CELL {i} ({ct})")
        print(f"{'='*80}")
        print(src)
        print()
