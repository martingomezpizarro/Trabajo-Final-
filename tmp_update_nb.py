import json
import os

notebook_path = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\01_base_de_datos.ipynb'

with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        # Replace 1: Import
        source = cell['source']
        for i, line in enumerate(source):
            if "descargar_ambito," in line:
                if "descargar_argentinadatos" not in "".join(source):
                    source.insert(i+1, "    descargar_argentinadatos,\n")
                    break

for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        # Replace 2: Variables
        source = cell['source']
        for i, line in enumerate(source):
            if "'nombre': 'EMBI+ Argentina'," in line:
                source[i+1] = "        'fuente': 'argentinadatos',\n"
                source[i+2] = "        'ticker': 'riesgo_pais',\n"
                break

for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        # Replace 3: Download loop
        source = cell['source']
        for i, line in enumerate(source):
            if "df = descargar_ambito(var['ticker'], FECHA_INICIO, FECHA_FIN)" in line:
                if "argentinadatos" not in "".join(source):
                    source.insert(i+1, "        elif var['fuente'] == 'argentinadatos':\n")
                    source.insert(i+2, "            df = descargar_argentinadatos(var['ticker'], FECHA_INICIO, FECHA_FIN)\n")
                    break

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, indent=1)
    
print("Notebook actualizado.")
