import json
import os

def patch_02b():
    path = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\02b_analisis_completo.ipynb'
    with open(path, 'r', encoding='utf-8') as f:
        nb = json.load(f)
        
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if '7.2  ESTIMACIONES ARDL' in source and 'df_ardl_full = pd.DataFrame(results_list)' in source:
                old_code = """    for _combo in _all_combos:
        try:
            _df_reg = pd.DataFrame({'y': df_safe[_yvar]})
            
            # Rezagos de Y
            for lag in range(1, MAX_LAGS_DEP + 1):
                _df_reg[f'{_yvar}_L{lag}'] = df_safe[_yvar].shift(lag)
            
            # Rezagos de X segun CCF
            for _xvar in _combo:
                _lags = bj_lags.get((_yvar, _xvar), {}).get('lags', [0, 1])
                for lag in _lags:
                    _df_reg[f'{_xvar}_L{lag}'] = df_safe[_xvar].shift(lag)"""
                new_code = """    import itertools
    for _combo in _all_combos:
        _lag_combinations = list(itertools.product(range(1, MAX_LAGS_DEP + 1), repeat=len(_combo) + 1))
        for _lags in _lag_combinations:
            try:
                _y_lag = _lags[0]
                _x_lags = _lags[1:]
                _df_reg = pd.DataFrame({'y': df_safe[_yvar]})
                
                # Rezagos de Y
                for lag in range(1, _y_lag + 1):
                    _df_reg[f'{_yvar}_L{lag}'] = df_safe[_yvar].shift(lag)
                
                # Rezagos de X
                for _idx, _xvar in enumerate(_combo):
                    for lag in range(1, _x_lags[_idx] + 1):
                        _df_reg[f'{_xvar}_L{lag}'] = df_safe[_xvar].shift(lag)"""
                
                if old_code in source:
                    new_source = source.replace(old_code, new_code)
                    # Convert back to list of lines with newlines
                    lines = new_source.split('\n')
                    cell['source'] = [line + '\n' for line in lines[:-1]] + [lines[-1]]
                    print("Patched 02b!")
                else:
                    print("Could not find old_code in 02b cell.")
                    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

patch_02b()
