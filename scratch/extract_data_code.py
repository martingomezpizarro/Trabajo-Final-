import json

nb_path = 'notebooks/02b_analisis_completo.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

code = []
for c in nb['cells']:
    if c['cell_type'] == 'code':
        src = ''.join(c.get('source', []))
        if '%matplotlib inline' in src:
            src = src.replace('%matplotlib inline', '')
        if 'plt.show()' in src:
            src = src.replace('plt.show()', '')
        if 'display(' in src:
            continue # skip display
        code.append(src)
        if 'df_safe = ' in src or 'X_SAFE_EST =' in src:
            pass # we need to execute up to cell 22 where ranking_exogeneidad is defined

# We'll just run up to ranking_exogeneidad
final_code = ""
for c in code:
    final_code += c + '\n'
    if 'ranking_exogeneidad =' in c or 'ranking_exogeneidad.sort_values' in c:
        break

final_code += """
print("df_safe shape:", df_safe.shape)
for col in df_safe.columns:
    print(col, "nulls:", df_safe[col].isna().sum())

# Simulate cell 8.1 dropna
_vars_est = [v for v in ranking_exogeneidad.index if v in X_SAFE_EST or v == Y_SAFE]
_others = [v for v in _vars_est if v != Y_SAFE]
from itertools import combinations
for _k in range(1, len(_others)+1):
    for _c in combinations(_others, _k):
        _all_v = [Y_SAFE] + list(_c)
        _df_var = df_safe[_all_v].dropna()
        if len(_df_var) > 0:
            print("Found valid combination:", _all_v, "length:", len(_df_var))
            break
"""

with open('scratch/run_data.py', 'w', encoding='utf-8') as f:
    f.write(final_code)
