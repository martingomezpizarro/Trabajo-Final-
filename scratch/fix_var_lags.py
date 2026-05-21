import json

with open('notebooks/02b_analisis_completo.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for c in nb['cells']:
    if c['cell_type'] == 'code':
        src = ''.join(c.get('source', []))
        if '8.1  ESTIMACIÓN VAR — TODAS LAS COMBINACIONES' in src:
            
            # Buscamos la parte de selección de orden
            old_code = """
        # ── Selección de orden por BIC ─────────────────────────────────
        _model = _VAR_est(_df_var)
        try:
            _sel = _model.select_order(maxlags=_max_p)
            _p_bic = max(1, _sel.selected_orders.get('bic', 1))
        except Exception:
            _p_bic = 1

        # ── Estimar VAR ───────────────────────────────────────────────
        _fit = _model.fit(_p_bic)

        # ── Diagnóstico: Ljung-Box sobre residuos de la ecuación Y ───
        _y_idx = list(_ordered).index(Y_SAFE)
        _resid_y = _fit.resid.values[:, _y_idx]
        _lb_lags = min(10, len(_resid_y) // 5)
        try:
            _lb_res = _lb_var(_resid_y, lags=_lb_lags, return_df=True)
            _lb_p = float(_lb_res['lb_pvalue'].iloc[-1])
        except Exception:
            _lb_p = np.nan

        _is_white = (not np.isnan(_lb_p)) and (_lb_p >= 0.05)

        # ── Estabilidad (raíces < 1) ──────────────────────────────────
        _stable = _fit.is_stable(verbose=False)

        # ── Métricas ──────────────────────────────────────────────────
        # R² de la ecuación Y
        _ss_res = np.sum(_resid_y**2)
        _y_vals = _df_var[Y_SAFE].values[_p_bic:]
        _ss_tot = np.sum((_y_vals - np.mean(_y_vals))**2)
        _r2 = 1 - _ss_res / _ss_tot if _ss_tot > 0 else 0
        _n_params = _K * _p_bic + 1
        _r2_adj = 1 - (1 - _r2) * (len(_y_vals) - 1) / max(1, len(_y_vals) - _n_params - 1)

        var_results.append({
            'x_vars': tuple(_x_combo),
            'ordered_vars': tuple(_ordered),
            'n_vars': _K,
            'T': _T,
            'max_p_allowed': _max_p,
            'p_selected': _p_bic,
            'R2_adj': _r2_adj,
            'AIC': _fit.aic,
            'BIC': _fit.bic,
            'HQ': _fit.hqic,
            'LB_pvalue': _lb_p,
            'stable': _stable,
            'resid_ruido_blanco': _is_white,
        })
        _n_ok += 1
"""

            new_code = """
        _model = _VAR_est(_df_var)
        
        # ── Iterar sobre todos los rezagos posibles (de 1 a _max_p) ───
        for _p in range(1, _max_p + 1):
            try:
                _fit = _model.fit(_p)

                # ── Diagnóstico: Ljung-Box sobre residuos de la ecuación Y ───
                _y_idx = list(_ordered).index(Y_SAFE)
                _resid_y = _fit.resid.values[:, _y_idx]
                _lb_lags = min(10, len(_resid_y) // 5)
                try:
                    _lb_res = _lb_var(_resid_y, lags=_lb_lags, return_df=True)
                    _lb_p = float(_lb_res['lb_pvalue'].iloc[-1])
                except Exception:
                    _lb_p = np.nan

                _is_white = (not np.isnan(_lb_p)) and (_lb_p >= 0.05)

                # ── Estabilidad (raíces < 1) ──────────────────────────────────
                _stable = _fit.is_stable(verbose=False)

                # ── Métricas ──────────────────────────────────────────────────
                _ss_res = np.sum(_resid_y**2)
                _y_vals = _df_var[Y_SAFE].values[_p:]
                _ss_tot = np.sum((_y_vals - np.mean(_y_vals))**2)
                _r2 = 1 - _ss_res / _ss_tot if _ss_tot > 0 else 0
                _n_params = _K * _p + 1
                _r2_adj = 1 - (1 - _r2) * (len(_y_vals) - 1) / max(1, len(_y_vals) - _n_params - 1)

                var_results.append({
                    'x_vars': tuple(_x_combo),
                    'ordered_vars': tuple(_ordered),
                    'n_vars': _K,
                    'T': _T,
                    'max_p_allowed': _max_p,
                    'p_selected': _p,
                    'R2_adj': _r2_adj,
                    'AIC': _fit.aic,
                    'BIC': _fit.bic,
                    'HQ': _fit.hqic,
                    'LB_pvalue': _lb_p,
                    'stable': _stable,
                    'resid_ruido_blanco': _is_white,
                })
                _n_ok += 1
            except Exception as _inner_e:
                _n_fail += 1
                continue
"""
            # First, check if old_code exists exactly. If not, we might have slightly different indentation or strings.
            # Let's do it line by line or using a regex.
            if "        # ── Selección de orden por BIC ─────────────────────────────────" in src:
                # We will slice out the inner part.
                start = src.find("        # ── Selección de orden por BIC ─────────────────────────────────")
                end = src.find("    except Exception as _e:")
                
                if start != -1 and end != -1:
                    src = src[:start] + new_code + src[end:]
                    c['source'] = [line + '\n' for line in src.split('\n')][:-1]
                    break

with open('notebooks/02b_analisis_completo.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Updated VAR estimation loop to iterate over all lags.")
