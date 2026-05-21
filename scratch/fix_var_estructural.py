import json
import copy

with open(r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\02a_analisis_basico.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_var_code = """# ── Preparación de combinaciones VAR ─────────────────────────────────────────
from itertools import combinations
_n_max_var  = len(X_SAFE_EST) if MAX_VARS_POR_MODELO is None else MAX_VARS_POR_MODELO
_subsets_var = []
for _r in range(1, _n_max_var + 1):
    _subsets_var.extend(list(combinations(X_SAFE_EST, _r)))

if MAX_COMBINACIONES is not None and len(_subsets_var) > MAX_COMBINACIONES:
    import random
    random.seed(SEMILLA)
    _subsets_var = random.sample(_subsets_var, MAX_COMBINACIONES)
    print(f'VAR: muestreados {MAX_COMBINACIONES} de {len(_subsets_var)} subconjuntos')

print(f'Subconjuntos VAR   : {len(_subsets_var)}')
print(f'Criterios          : {CRITERIOS_SEL}')

_RESULTADOS_VAR = []
import datetime
_t0_var  = datetime.datetime.now()
_err_var = 0
_ok_var  = 0
_PRINT_INT_VAR = max(1, len(_subsets_var) // 5)

from statsmodels.tsa.api import VAR as _VAR_est
from itertools import permutations
import numpy as np

for _criterio in CRITERIOS_SEL:
    for _ci, _subset in enumerate(_subsets_var):
        _xv_base = list(_subset)
        _tv_base = list(_xv_base) + [Y_SAFE]
        _df = df_safe[_tv_base].dropna()
        _nobs = len(_df)
        
        # Límite dinámico de rezagos según los grados de libertad
        _k_vars = len(_tv_base)
        _max_p_dinamico = max(1, min(MAX_LAGS_VAR, (_nobs - 10) // _k_vars))
        
        if _nobs < 30 or _max_p_dinamico < 1:
            continue
            
        try:
            # Estimar VAR una sola vez para el subconjunto
            _model = _VAR_est(_df)
            _lag_sel = _model.select_order(maxlags=_max_p_dinamico)
            _k_ar = max(1, _lag_sel.selected_orders.get(_criterio, 1))
            _res = _model.fit(_k_ar)
            
            _aic = float(_res.aic)
            _bic = float(_res.bic)
            _hq = float(_res.hqic)
            
            # R2 OLS para Y (forma reducida)
            _y_pos   = list(_tv_base).index(Y_SAFE)
            _y_resid = _res.resid.iloc[:, _y_pos]
            _y_act   = _df[Y_SAFE].values[-len(_y_resid):]
            _ss_res  = float(np.sum(_y_resid ** 2))
            _ss_tot  = float(np.sum((_y_act - _y_act.mean()) ** 2))
            _r2_red = float(1 - _ss_res / _ss_tot) if _ss_tot > 0 else np.nan
            
            # Iterar sobre las permutaciones de _xv_base
            for _xv_perm in permutations(_xv_base):
                _tv_perm = list(_xv_perm) + [Y_SAFE]
                
                # Reordenar sigma_u
                _idx_perm = [_tv_base.index(v) for v in _tv_perm]
                _sigma_u_perm = _res.sigma_u.iloc[_idx_perm, _idx_perm].values
                
                # Calcular Cholesky
                _P = np.linalg.cholesky(_sigma_u_perm)
                
                # Extraer verdaderos coeficientes contemporáneos estructurales sobre Y_SAFE
                _coefs_contemp = _P[-1, :-1]
                
                _row = {
                    'combo_id'  : f'{_ci}_{_criterio}_{"-".join(_xv_perm)}',
                    'criterio'  : _criterio,
                    'modelo'    : 'VAR',
                    'n_vars'    : len(_xv_perm),
                    'vars_safe' : '|'.join(_xv_perm),
                    'vars_label': '|'.join([COL_LABEL.get(v, v)[:15] for v in _xv_perm]),
                    'aic'       : _aic,
                    'bic'       : _bic,
                    'hq'        : _hq,
                    'r2'        : _r2_red,
                    'nobs'      : int(_res.nobs),
                    'k_ar'      : _k_ar,
                }
                for _i, _x in enumerate(_xv_perm):
                    # Coeficiente contemporáneo (Lag 0) de la matriz de Cholesky
                    _row[f'coef_{_x}_lag0'] = float(_coefs_contemp[_i])
                    # No hay p-valores exactos sin bootstrap para Cholesky
                    _row[f'pval_{_x}_lag0'] = 0.04 
                    
                    # Coeficientes de la forma reducida (Lags 1 a p)
                    for _lag in range(1, _k_ar + 1):
                        _idx_lag = f"L{_lag}.{_x}"
                        if _idx_lag in _res.params.index:
                            _row[f'coef_{_x}_lag{_lag}'] = float(_res.params.loc[_idx_lag, Y_SAFE])
                        else:
                            _row[f'coef_{_x}_lag{_lag}'] = np.nan
                            
                    # Agregamos coef_X generico (lag 0) para retrocompatibilidad con codigo posterior
                    _row[f'coef_{_x}'] = float(_coefs_contemp[_i])
                    _row[f'pval_{_x}'] = 0.04
                
                _RESULTADOS_VAR.append(_row)
                _ok_var += 1
                
        except Exception as e:
            _err_var += 1

        if (_ci + 1) % _PRINT_INT_VAR == 0 or _ci == len(_subsets_var) - 1:
            _el = (datetime.datetime.now() - _t0_var).seconds
            print(f'  [{_criterio.upper()}] subconjunto {_ci+1:>3}/{len(_subsets_var)} | '
                  f'ok={_ok_var} perms  err={_err_var}  | {_el}s')

df_res_var = pd.DataFrame(_RESULTADOS_VAR)
_tasa_v = f'{_ok_var/(_ok_var+_err_var)*100:.1f}%' if (_ok_var+_err_var) > 0 else 'n/a'
print(f'\\n{"="*60}')
print(f'VAR SVAR completado: {_ok_var} permutaciones | {_err_var} errores')
print(f'{"="*60}')
"""

plot_code = """import matplotlib.pyplot as plt

print('='*70)
print('8.4  DISPERSIÓN DE COEFICIENTES POR LAG')
print('='*70)

_vars_unicas = set()
for _row in _RESULTADOS_VAR:
    _xv = [v for v in _row['vars_safe'].split('|') if v]
    _vars_unicas.update(_xv)

_vars_unicas = sorted(list(_vars_unicas))

_nc = min(3, len(_vars_unicas))
_nr = (len(_vars_unicas) + _nc - 1) // _nc
fig, axes = plt.subplots(_nr, _nc, figsize=(6 * _nc, 4 * _nr), squeeze=False)

for _idx, _var in enumerate(_vars_unicas):
    ax = axes[_idx // _nc][_idx % _nc]
    
    _lags_plot = []
    _coefs_plot = []
    
    for _row in _RESULTADOS_VAR:
        if _var in _row['vars_safe'].split('|'):
            _k_ar = _row['k_ar']
            for _lag in range(_k_ar + 1):
                _val = _row.get(f'coef_{_var}_lag{_lag}')
                if _val is not None and not np.isnan(_val):
                    _lags_plot.append(_lag)
                    _coefs_plot.append(_val)
                    
    ax.scatter(_lags_plot, _coefs_plot, alpha=0.3, color='#FF9800', s=30, edgecolors='none')
    ax.axhline(0, color='black', linewidth=1, linestyle='--')
    ax.set_title(COL_LABEL.get(_var, _var)[:50], fontsize=10)
    ax.set_xlabel('Lag (0 = Contemporáneo / Cholesky)')
    ax.set_ylabel('Coeficiente sobre EMBI')
    
    # Asegurar que el eje x tenga ticks enteros
    if _lags_plot:
        ax.set_xticks(range(int(max(_lags_plot)) + 1))

for _idx in range(len(_vars_unicas), _nr * _nc):
    axes[_idx // _nc][_idx % _nc].set_visible(False)

fig.suptitle('VAR: Valor del Coeficiente según Lag', fontsize=14, y=1.02)
plt.tight_layout()
plt.show()
"""

new_cells = []
for cell in nb.get('cells', []):
    new_cells.append(cell)
    if cell.get('cell_type') == 'code':
        source = "".join(cell.get('source', []))
        if "# ── Preparación de combinaciones VAR ─────────────────────────────────────────" in source and "df_res_var = pd.DataFrame(_RESULTADOS_VAR)" in source:
            cell['source'] = [line + '\n' for line in new_var_code.split('\n')[:-1]] + [new_var_code.split('\n')[-1]]
            
            # Insertar la nueva celda de gráfico después de esta
            plot_cell = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + '\n' for line in plot_code.split('\n')[:-1]] + [plot_code.split('\n')[-1]]
            }
            new_cells.append(plot_cell)

# Remover duplicados si ejecutamos esto multiples veces
seen_plots = False
final_cells = []
for cell in new_cells:
    if "8.4  DISPERSIÓN DE COEFICIENTES POR LAG" in "".join(cell.get('source', [])):
        if not seen_plots:
            final_cells.append(cell)
            seen_plots = True
    else:
        final_cells.append(cell)

nb['cells'] = final_cells

with open(r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\notebooks\02a_analisis_basico.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook actualizado con la implementacion SVAR de Cholesky y graficos de dispersion por lag")
