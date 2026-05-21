import json
import ast
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('notebooks/02b_analisis_completo.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        # Strip out ipython magics so ast.parse doesn't choke on them
        source_clean = '\n'.join([line if not line.strip().startswith('%') else '# ' + line for line in source.split('\n')])
        try:
            ast.parse(source_clean)
        except SyntaxError as e:
            print(f"SyntaxError in cell {i}: {e}")
            snippet = source_clean[max(0, e.offset-30 if e.offset else 0):min(len(source_clean), e.offset+30 if e.offset else 0)]
            print(f"Code snippet:\n{snippet}")
            print("-" * 40)
