import json
import os

nb_path = "notebooks/01_base_de_datos.ipynb"

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Buscar la primera celda de código
found = False
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = cell["source"]
        # Buscar posición para insertar
        for i, line in enumerate(source):
            if "import plotly.graph_objects as go" in line:
                # Verificar si ya existe para no duplicar
                if any("import plotly.io as pio" in l for l in source):
                    found = True
                    break
                source.insert(i + 1, "import plotly.io as pio\n")
                source.insert(i + 2, "pio.renderers.default = 'notebook_connected'\n")
                found = True
                break
    if found: break

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1)

if found:
    print("Configuración de Plotly aplicada.")
else:
    print("No se encontró la línea de import de Plotly para parchear.")
