import json

with open(r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\02a_analisis_basico.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        source = cell.get('source', [])
        for i, line in enumerate(source):
            if 'from itertools import combinations as _comb_pt' in line:
                source.insert(i, 'from itertools import permutations\n')
                break

for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        source = cell.get('source', [])
        for i, line in enumerate(source):
            if '_combos_var.extend(list(combinations(X_SAFE_EST, _r)))' in line:
                source[i] = line.replace('combinations', 'permutations')
            if '_tv = [Y_SAFE] + _xv' in line:
                source[i] = line.replace('_tv = [Y_SAFE] + _xv', '_tv = list(_xv) + [Y_SAFE]')
            if '_tv_s = [Y_SAFE] + list(_xv_s)' in line:
                source[i] = line.replace('_tv_s = [Y_SAFE] + list(_xv_s)', '_tv_s = list(_xv_s) + [Y_SAFE]')
            if '_tv_vc     = [Y_SAFE] + _xv_vc' in line:
                source[i] = line.replace('_tv_vc     = [Y_SAFE] + _xv_vc', '_tv_vc     = list(_xv_vc) + [Y_SAFE]')
            if '_tv_var     = [Y_SAFE] + _xv_var' in line:
                source[i] = line.replace('_tv_var     = [Y_SAFE] + _xv_var', '_tv_var     = list(_xv_var) + [Y_SAFE]')

with open(r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\02a_analisis_basico.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook modificado con exito.")
