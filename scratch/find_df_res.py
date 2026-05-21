import json

path = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\02a_analisis_basico.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    source = ''.join(cell['source'])
    if 'df_res' in source:
        print(f"Cell {i} has df_res.")
        if cell['cell_type'] == 'markdown':
            print("Markdown cell!")
