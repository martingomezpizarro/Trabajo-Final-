import json

with open('notebooks/02b_analisis_completo.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for c in nb['cells']:
    if c['cell_type'] == 'code':
        src = ''.join(c.get('source', []))
        if 'Error en VAR' in src:
            src = src.replace("        if _n_fail == 1: print(f'Error en VAR: {type(_e).__name__}: {_e}')\n", "")
            c['source'] = [line + '\n' for line in src.split('\n')][:-1]
            break

with open('notebooks/02b_analisis_completo.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
