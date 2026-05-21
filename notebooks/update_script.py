# -*- coding: utf-8 -*-
import json

with open('02a_analisis_basico.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

found = False
for cell in nb.get('cells', []):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if '# ── 11.2 Mejor modelo global' in source:
            new_source = source.replace(
                '''    # ── 11.2 Mejor modelo global (menor AIC) ─────────────────────────────────\n    print(f'\\n{"="*70}')\n    print('MEJOR MODELO GLOBAL (menor AIC)')\n    print('='*70)\n    _best_g  = df_res.loc[df_res['aic'].idxmin()]\n    _xv_g    = [v for v in _best_g['vars_safe'].split('|') if v]\n    _xl_g    = [COL_LABEL.get(v, v) for v in _xv_g]\n    print(f'\\n  Modelo : {_best_g["modelo"]}')\n    print(f'  AIC={_best_g["aic"]:.4f}  BIC={_best_g["bic"]:.4f}  '\n          f'HQ={_best_g["hq"]:.4f}  R2={_best_g.get("r2", float("nan")):.4f}')\n    print(f'  Obs={int(_best_g["nobs"])}  N_vars={int(_best_g["n_vars"])}')\n    print(f'  Variables: {", ".join(_xl_g)}')\n    print('\\n  Coeficientes:')\n    for _x, _xl in zip(_xv_g, _xl_g):\n        _c = _best_g.get(f'coef_{_x}', float('nan'))\n        _p = _best_g.get(f'pval_{_x}', float('nan'))\n        import math\n        if math.isnan(_c):\n            continue\n        _s = '***' if _p < 0.01 else '**' if _p < 0.05 else '*' if _p < 0.10 else ''\n        print(f'    {_xl[:50]:<50}  coef={_c:+.4f}  p={_p:.4f} {_s}')\n    print('\\n  * p<10%  ** p<5%  *** p<1%')''',
                '''    # ── 11.2 Mejores modelos globales (por cada criterio) ─────────────────────\n    print(f'\\n{"="*70}')\n    print('MEJORES MODELOS GLOBALES (por cada criterio)')\n    print('='*70)\n    \n    _best_g = df_res.loc[df_res['aic'].idxmin()]\n    _xv_g   = [v for v in _best_g['vars_safe'].split('|') if v]\n    _best_models_printed = set()\n    \n    for _crit_name, (_col, _asc) in _criterios_rank.items():\n        if _col not in df_res.columns or df_res[_col].isna().all():\n            continue\n            \n        _best_idx = df_res[_col].idxmin() if _asc else df_res[_col].idxmax()\n        _best_m = df_res.loc[_best_idx]\n        _mod_sig = (_best_m['modelo'], _best_m['vars_safe'])\n        \n        print(f'\\n▶ MEJOR MODELO SEGÚN {_crit_name} ◀')\n        if _mod_sig in _best_models_printed:\n            print(f'  (Mismo modelo que el anterior: {_best_m["modelo"]} con las mismas variables)')\n            continue\n            \n        _best_models_printed.add(_mod_sig)\n        \n        _xv_m = [v for v in _best_m['vars_safe'].split('|') if v]\n        _xl_m = [COL_LABEL.get(v, v) for v in _xv_m]\n        print(f'\\n  Modelo : {_best_m["modelo"]}')\n        print(f'  AIC={_best_m["aic"]:.4f}  BIC={_best_m["bic"]:.4f}  '\n              f'HQ={_best_m["hq"]:.4f}  R2={_best_m.get("r2", float("nan")):.4f}')\n        print(f'  Obs={int(_best_m["nobs"])}  N_vars={int(_best_m["n_vars"])}')\n        print(f'  Variables: {", ".join(_xl_m)}')\n        print('\\n  Coeficientes:')\n        for _x, _xl in zip(_xv_m, _xl_m):\n            _c = _best_m.get(f'coef_{_x}', float('nan'))\n            _p = _best_m.get(f'pval_{_x}', float('nan'))\n            import math\n            if math.isnan(_c):\n                continue\n            _s = '***' if _p < 0.01 else '**' if _p < 0.05 else '*' if _p < 0.10 else ''\n            print(f'    {_xl[:50]:<50}  coef={_c:+.4f}  p={_p:.4f} {_s}')\n        print('\\n  * p<10%  ** p<5%  *** p<1%')'''
            )
            if source != new_source:
                # Convert back to list of strings with newlines
                import re
                lines = [line + '\n' for line in new_source.split('\n')]
                # remove trailing newline from last element if it didn't have one originally
                if not source.endswith('\n'):
                    lines[-1] = lines[-1].rstrip('\n')
                cell['source'] = lines
                found = True
                print("Replacement made successfully.")

if found:
    with open('02a_analisis_basico.ipynb', 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
else:
    print("Target string not found in 02a_analisis_basico.ipynb.")
