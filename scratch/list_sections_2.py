import json

path = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\02a_analisis_basico.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source'])
        lines = [line.strip() for line in source.split('\n') if line.strip().startswith('#')]
        for line in lines:
            print(f"Cell {i}: {line}")
