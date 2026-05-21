import json

with open('notebooks/02b_analisis_completo.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for c in nb['cells']:
    if c['cell_type'] == 'code':
        src = ''.join(c.get('source', []))
        if '8.1  ESTIMACIÓN VAR — TODAS LAS COMBINACIONES' in src:
            # Reemplazar la captura silenciosa de excepciones con un print para debugear
            new_src = src.replace(
                "    except Exception as _e:\n        _n_fail += 1\n        continue",
                "    except Exception as _e:\n        _n_fail += 1\n        if _n_fail == 1: print(f'Error en VAR: {type(_e).__name__}: {_e}')\n        continue"
            )
            c['source'] = [line + '\n' for line in new_src.split('\n')][:-1]
            break

with open('notebooks/02b_analisis_completo.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Added debug print to 02b VAR cell.")
