import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_lags_cells(filename):
    print(f"=== {filename} ===")
    with open(filename, 'r', encoding='utf-8') as f:
        nb = json.load(f)
    for c in nb['cells']:
        src = ''.join(c.get('source', []))
        if 'MAX_LAGS_DEP' in src:
            print(src)

get_lags_cells('notebooks/02a_analisis_basico.ipynb')
get_lags_cells('notebooks/02b_analisis_completo.ipynb')
