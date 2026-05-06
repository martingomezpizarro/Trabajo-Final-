import json
import os
import sys

print("Current working directory:", os.getcwd())
nb_path = "01_base_de_datos.ipynb"

try:
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
        
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            src = cell["source"]
            # Import replace
            for i, line in enumerate(src):
                if "descargar_ambito," in line and "descargar_argentinadatos" not in "".join(src):
                    src.insert(i+1, "    descargar_argentinadatos,\n")
            
            # Variables replace
            for i, line in enumerate(src):
                if "'nombre': 'EMBI+ Argentina'," in line:
                    src[i+1] = "        'fuente': 'argentinadatos',\n"
                    src[i+2] = "        'ticker': 'riesgo_pais',\n"
                    
            # Descargador replace
            for i, line in enumerate(src):
                if "df = descargar_ambito(var['ticker'], FECHA_INICIO, FECHA_FIN)" in line and "argentinadatos" not in "".join(src):
                    src.insert(i+1, "        elif var['fuente'] == 'argentinadatos':\n")
                    src.insert(i+2, "            df = descargar_argentinadatos(var['ticker'], FECHA_INICIO, FECHA_FIN)\n")
                    
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
        
    print("Modificacion terminada.")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
