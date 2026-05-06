import json
import os
import sys

print("Current working directory:", os.getcwd())
notebook_path = os.path.abspath('notebooks/01_base_de_datos.ipynb')
print("Notebook path:", notebook_path)

if not os.path.exists(notebook_path):
    print("Notebook no encontrado")
    sys.exit(1)

with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = json.load(f)

modificado = False

for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        for i, line in enumerate(source):
            if "descargar_ambito," in line:
                if "descargar_argentinadatos" not in "".join(source):
                    source.insert(i+1, "    descargar_argentinadatos,\n")
                    print("Import modificado")
                    modificado = True
                    break

for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        for i, line in enumerate(source):
            if "'nombre': 'EMBI+ Argentina'," in line:
                if "'fuente': 'argentinadatos'," not in source[i+1]:
                    source[i+1] = "        'fuente': 'argentinadatos',\n"
                    source[i+2] = "        'ticker': 'riesgo_pais',\n"
                    print("Variables modificadas")
                    modificado = True
                    break

for cell in notebook['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        for i, line in enumerate(source):
            if "df = descargar_ambito(var['ticker'], FECHA_INICIO, FECHA_FIN)" in line:
                if "argentinadatos" not in "".join(source):
                    source.insert(i+1, "        elif var['fuente'] == 'argentinadatos':\n")
                    source.insert(i+2, "            df = descargar_argentinadatos(var['ticker'], FECHA_INICIO, FECHA_FIN)\n")
                    print("Loop descargador modificado")
                    modificado = True
                    break

if modificado:
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1)
    print("Notebook actualizado y guardado.")
else:
    print("No se encontraron lineas para modificar, o ya estaban modificadas.")
