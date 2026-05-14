import json

with open('notebooks/02a_analisis_basico.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# The user wants to copy the fixed criteria from 02b to 02a.
# 02b has:
# MAX_LAGS_DEP = 4
# MAX_LAGS_IND = 4
# MAX_LAGS_VAR = 8
# 02a currently has them set to None, and then later has a dynamic block.

for c in nb['cells']:
    if c['cell_type'] == 'code':
        source = c['source']
        if not source:
            continue
        new_source = []
        skip_dynamic = False
        for line in source:
            if 'MAX_LAGS_DEP = None' in line:
                new_source.append("MAX_LAGS_DEP = 4   # rezagos Y en ARDL\n")
            elif 'MAX_LAGS_IND = None' in line:
                new_source.append("MAX_LAGS_IND = 4   # rezagos X en ARDL\n")
            elif 'MAX_LAGS_VAR = None' in line:
                new_source.append("MAX_LAGS_VAR = 8   # selección de rezagos en VAR/VECM\n")
            elif '# Calcular MAX_LAGS según grados de libertad' in line:
                skip_dynamic = True
                new_source.append(line)
                new_source.append("    # (Se usa el criterio estático de la Sección 3 en lugar del dinámico para evitar explosión de lags)\n")
            elif skip_dynamic:
                if 'print' in line or 'MAX_LAGS_' in line:
                    new_source.append("    # " + line.lstrip())
                else:
                    new_source.append(line)
                    skip_dynamic = False
            else:
                new_source.append(line)
        c['source'] = new_source

with open('notebooks/02a_analisis_basico.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook 02a modificado con los lags fijos de 02b.")
