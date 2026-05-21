import json
import os
import numpy as np

path = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\02a_analisis_basico.ipynb'
with open(path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'r2  = float(getattr(res, \'rsquared\', np.nan))' in source:
            new_code = """
    r2 = getattr(res, 'rsquared', np.nan)
    if np.isnan(r2):
        try:
            r2 = 1 - (res.ssr / res.centered_tss)
        except Exception:
            r2 = np.nan
    r2 = float(r2)"""
            new_source = source.replace("    r2  = float(getattr(res, 'rsquared', np.nan))", new_code)
            
            # Convert back to list of lines
            lines = new_source.split('\n')
            cell['source'] = [line + '\n' for line in lines[:-1]] + [lines[-1]]
            print("Patched R2 calculation in 02a!")

with open(path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
