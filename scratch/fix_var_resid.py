import json

with open('notebooks/02b_analisis_completo.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

modified = False
for c in nb['cells']:
    if c['cell_type'] == 'code':
        src = ''.join(c.get('source', []))
        if '_fit.resid[:,' in src:
            new_src = src.replace("_fit.resid[:, _y_idx]", "_fit.resid.values[:, _y_idx]")
            # Also fix the debug statement I added earlier to remove it
            new_src = new_src.replace(
                "        if _T < 30:\n            _n_fail += 1\n            if _n_fail == 1: print(f'  Saltando modelo {COL_LABEL.get(_all_v[1], _all_v[1])[:10]}... por falta de datos (T={_T})')\n            continue",
                "        if _T < 30:\n            continue"
            )
            c['source'] = [line + '\n' for line in new_src.split('\n')][:-1]
            modified = True
            break

if modified:
    with open('notebooks/02b_analisis_completo.ipynb', 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print("Fix applied.")
else:
    print("Could not find the resid slicing code.")
