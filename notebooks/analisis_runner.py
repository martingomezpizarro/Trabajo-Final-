#!/usr/bin/env python3
"""
analisis_runner.py — Runner para el visualizador.

Recibe un JSON con las series (datos + estacionariedad + dependiente) ya
seleccionadas en visualizador.html y la config (frecuencia, modelos, lags,
secciones a correr), y ejecuta una réplica de las secciones 7-11+B de
02a_analisis_basico.py (sin importar ni tocar ese archivo).

Uso:
    python analisis_runner.py --input-json in.json --out-json out.json
    python analisis_runner.py --input-json in.json --preview-only --out-json out.json

Salida (out-json): estructura con resultados de cada sección + paths a PNGs
generados en outputs/analisis_basico_runner/<run_id>/.
"""
import argparse
import json
import math
import random
import sys
import traceback
import warnings
from collections import defaultdict
from datetime import datetime
from itertools import combinations, permutations
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hqic(llf, k, n):
    return -2 * llf + 2 * k * np.log(np.log(max(n, 3)))


def _print_header(seccion: str, titulo: str):
    print(f'\n{"=" * 70}')
    print(f'  SECCIÓN {seccion}: {titulo}')
    print(f'{"=" * 70}\n')


def _save_fig(fig, output_dir: Path, nombre: str, pngs: list):
    path = output_dir / f'{nombre}.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    pngs.append(path.name)
    print(f'  📊 Gráfico guardado: {path.name}')


def _to_records(df: pd.DataFrame, max_rows=None):
    """Convierte DataFrame a list-of-dicts JSON-friendly (NaN → None)."""
    if df is None or df.empty:
        return []
    d = df.head(max_rows) if max_rows else df
    return json.loads(d.to_json(orient='records', date_format='iso'))


# ── Construcción de ctx / est_ctx desde JSON ──────────────────────────────────
def build_contexts(input_data: dict):
    """
    Construye df_safe (panel alineado a fechas comunes), ctx y est_ctx
    a partir del JSON del visualizador.

    Reglas de estacionariedad (campo `estacionariedad` por serie):
      - "niveles": orden=0  → ARDL/VAR usan niveles
      - "diff":    orden=1  → ARDL/VAR usan Δserie ; VECM elegible
      - "no":      orden=2  → se descarta de ARDL/VAR/VECM
    """
    config = input_data['config']
    series = input_data['series']
    if not series:
        raise RuntimeError('series[] vacío en input.')

    # Construir panel
    panels = {}
    for s in series:
        idx = pd.to_datetime(s['dates'])
        vals = pd.to_numeric(pd.Series(s['values']), errors='coerce').values
        panels[s['safe']] = pd.Series(vals, index=idx, name=s['safe'])

    df_safe = pd.concat(panels.values(), axis=1).dropna()
    if df_safe.shape[0] < 30:
        raise RuntimeError(f'Panel con menos de 30 obs ({df_safe.shape[0]}) tras alinear fechas.')

    # Identificación dependiente
    dep = next((s for s in series if s.get('es_dependiente')), None)
    if dep is None:
        raise RuntimeError('Ninguna serie marcada como `es_dependiente: true`.')
    Y_SAFE = dep['safe']
    ETI_DEP = dep['label']
    X_SAFE = [s['safe'] for s in series if not s.get('es_dependiente')]
    ETI_EXPL = [s['label'] for s in series if not s.get('es_dependiente')]

    COL_SAFE = {s['label']: s['safe'] for s in series}
    COL_LABEL = {s['safe']: s['label'] for s in series}

    # Estacionariedad por serie → INFO_ESTACIONARIEDAD + df_safe_est
    estac_map = {'niveles': 0, 'diff': 1, 'no': 2}
    INFO_ESTACIONARIEDAD = {}
    for s in series:
        orden = estac_map.get(s.get('estacionariedad', 'no'), 2)
        INFO_ESTACIONARIEDAD[s['safe']] = {
            'label': s['label'],
            'nivel_estacionaria': orden == 0,
            'diff_estacionaria': orden == 1,
            'orden': orden,
        }

    df_safe_est = df_safe.copy()
    for safe_id, info in INFO_ESTACIONARIEDAD.items():
        if safe_id in df_safe_est.columns and info['orden'] >= 1:
            df_safe_est[safe_id] = df_safe[safe_id].diff()

    X_SAFE_EST = [v for v in X_SAFE if INFO_ESTACIONARIEDAD.get(v, {}).get('orden', 2) <= 1]
    X_SAFE_I1  = [v for v in X_SAFE if INFO_ESTACIONARIEDAD.get(v, {}).get('orden', 2) == 1]
    X_SAFE_I0  = [v for v in X_SAFE if INFO_ESTACIONARIEDAD.get(v, {}).get('orden', 2) == 0]
    Y_ORDEN = INFO_ESTACIONARIEDAD.get(Y_SAFE, {}).get('orden', 0)

    # Lags
    ml = config.get('max_lags', {}) or {}
    MAX_LAGS_DEP = int(ml.get('ardl_dep', 3))
    MAX_LAGS_IND = int(ml.get('ardl_ind', 3))
    MAX_LAGS_VAR = int(ml.get('var', 3))
    LAG_CAP_FREQ_VAR = MAX_LAGS_VAR
    LAG_CAP_FREQ_VECM = int(ml.get('vecm', 3))

    ctx = {
        'df_safe': df_safe,
        'Y_SAFE': Y_SAFE,
        'X_SAFE': X_SAFE,
        'COL_SAFE': COL_SAFE,
        'COL_LABEL': COL_LABEL,
        'ETI_DEP': ETI_DEP,
        'ETI_EXPL': ETI_EXPL,
        'DUMMY_SAFE': [],
        'df_exog_dummy': pd.DataFrame(index=df_safe.index),
        'MAX_LAGS_VAR': MAX_LAGS_VAR,
        'MAX_LAGS_DEP': MAX_LAGS_DEP,
        'MAX_LAGS_IND': MAX_LAGS_IND,
        'LAG_CAP_FREQ': LAG_CAP_FREQ_VAR,
        'LAG_CAP_FREQ_VECM': LAG_CAP_FREQ_VECM,
        'FRECUENCIA_USADA': config.get('frecuencia', 'M'),
    }

    est_ctx = {
        'df_safe_est': df_safe_est,
        'INFO_ESTACIONARIEDAD': INFO_ESTACIONARIEDAD,
        'X_SAFE_EST': X_SAFE_EST,
        'X_SAFE_I1': X_SAFE_I1,
        'X_SAFE_I0': X_SAFE_I0,
        'Y_ORDEN': Y_ORDEN,
    }

    cfg_norm = {
        'NIVEL_SIG':            float(config.get('nivel_sig', 0.05)),
        'SEMILLA':              int(config.get('semilla', 42)),
        'CRITERIOS_SEL':        config.get('criterios_sel', ['aic', 'bic']),
        'MAX_VARS_POR_MODELO':  config.get('max_vars_por_modelo', None),
        'MAX_COMBINACIONES':    config.get('max_combinaciones', None),
        'MAX_PERMUTACIONES_VAR': int(config.get('max_permutaciones_var', 1500)),
        'AUTO_LAGS':            bool(config.get('auto_lags', False)),
        'MODELOS':              [m.upper() for m in config.get('modelos', ['ARDL', 'VAR', 'VECM'])],
        'SECCIONES':            [str(s) for s in config.get('secciones', [7, 8, 9, 10, 11, 'B'])],
    }

    print(f'Panel: {df_safe.shape[0]} obs × {df_safe.shape[1]} vars')
    print(f'Y = {ETI_DEP}  (safe={Y_SAFE}, I({Y_ORDEN}))')
    print(f'X_SAFE_EST: {len(X_SAFE_EST)}  X_SAFE_I1: {len(X_SAFE_I1)}')
    return ctx, est_ctx, cfg_norm


# ── extraer_ardl / extraer_vecm (copia desde 02a, sin cambios funcionales) ───
def extraer_ardl(df_m, y_var, x_vars, max_lags_dep, max_lags_ind, criterio,
                 df_dummy=None, bj_proposed_lags=None, bj_ar_y=1):
    from statsmodels.tsa.ardl import ARDL as _ARDL_direct
    from scipy.stats import norm as _norm_ardl

    data = df_m[[y_var] + x_vars].dropna()
    y    = data[y_var]
    Xd   = data[x_vars]

    _dum_cols = []
    if df_dummy is not None and not df_dummy.empty:
        _dum = df_dummy.reindex(data.index).fillna(0)
        _dum_cols = list(_dum.columns)
        Xd = pd.concat([Xd, _dum], axis=1)

    _bj_ok = bj_proposed_lags is not None and len(bj_proposed_lags) > 0
    if _bj_ok:
        try:
            _order_dict = {x: max(bj_proposed_lags.get(x, [0, 1])) for x in x_vars}
            res = _ARDL_direct(y, lags=bj_ar_y, exog=Xd,
                               order=_order_dict, trend='c').fit()
        except Exception:
            _bj_ok = False

    if not _bj_ok:
        from statsmodels.tsa.ardl import ardl_select_order
        _Xd_endo = data[x_vars]
        sel = ardl_select_order(y, max_lags_dep, _Xd_endo, max_lags_ind,
                                ic=criterio, trend='c')
        _sel_p = sel.model.ardl_order[0]
        _sel_q = {x: sel.model.ardl_order[i + 1] for i, x in enumerate(x_vars)}
        res = _ARDL_direct(y, lags=_sel_p, exog=Xd,
                           order=_sel_q, trend='c').fit()

    n   = res.nobs
    k   = len(res.params)
    aic = float(res.aic)
    bic = float(res.bic)
    hq  = float(getattr(res, 'hqic', _hqic(res.llf, k, n)))
    r2  = float(getattr(res, 'rsquared', np.nan))

    coefs = {}
    lr_coefs = {}

    _y_lag_idx = [i for i, p in enumerate(res.params.index) if p.startswith(f'{y_var}.L')]
    _sum_alpha_y = float(res.params.iloc[_y_lag_idx].sum()) if _y_lag_idx else 0.0
    _denom_lr    = 1.0 - _sum_alpha_y

    try:
        _cov_mat = res.cov_params()
        _cov_mat = _cov_mat.values if hasattr(_cov_mat, 'values') else np.asarray(_cov_mat)
    except Exception:
        _cov_mat = None

    for x in x_vars:
        px = [p for p in res.params.index if p.startswith(f'{x}.L') or p == x]
        if not px:
            px = [p for p in res.params.index
                  if p == x or (p.startswith('L') and p.split('.', 1)[-1] == x)]
        if px:
            _px_idx   = [list(res.params.index).index(p) for p in px]
            _coef_sum = float(res.params.iloc[_px_idx].sum())
            try:
                _R = np.zeros((len(_px_idx), len(res.params)))
                for _i, _j in enumerate(_px_idx):
                    _R[_i, _j] = 1.0
                _pval_f = float(res.f_test(_R).pvalue)
            except Exception:
                _pval_f = float(res.pvalues.iloc[_px_idx].min())
            coefs[x] = {'coef': _coef_sum, 'pval': _pval_f}

            if abs(_denom_lr) < 1e-9 or _cov_mat is None:
                lr_coefs[x] = {'coef': float('nan'), 'pval': float('nan')}
            else:
                _theta = _coef_sum / _denom_lr
                _grad = np.zeros(len(res.params))
                for _i in _px_idx:
                    _grad[_i] = 1.0 / _denom_lr
                for _i in _y_lag_idx:
                    _grad[_i] = _coef_sum / (_denom_lr ** 2)
                try:
                    _var_t = float(_grad @ _cov_mat @ _grad)
                    _se_t  = float(np.sqrt(max(_var_t, 0.0)))
                    if _se_t > 0:
                        _z = _theta / _se_t
                        _p_t = float(2.0 * _norm_ardl.sf(abs(_z)))
                    else:
                        _p_t = float('nan')
                except Exception:
                    _p_t = float('nan')
                lr_coefs[x] = {'coef': float(_theta), 'pval': _p_t}
        else:
            coefs[x]    = {'coef': np.nan, 'pval': np.nan}
            lr_coefs[x] = {'coef': np.nan, 'pval': np.nan}

    dummy_coefs = {}
    for _d in _dum_cols:
        if _d in res.params.index:
            _ci = list(res.params.index).index(_d)
            dummy_coefs[_d] = {
                'coef': float(res.params.iloc[_ci]),
                'pval': float(res.pvalues.iloc[_ci]),
            }
        else:
            dummy_coefs[_d] = {'coef': float('nan'), 'pval': float('nan')}

    return {'aic': aic, 'bic': bic, 'hq': hq, 'r2': r2,
            'coefs': coefs, 'lr_coefs': lr_coefs,
            'dummy_coefs': dummy_coefs,
            'nobs': int(n),
            'resid': res.resid.dropna()}


def extraer_vecm(df_m, y_var, x_vars, todas_vars, k_ar_diff, det_order,
                 df_dummy=None, dummy_names=None):
    from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen
    from scipy.stats import t as t_dist

    data = df_m[todas_vars].dropna().reset_index(drop=True)
    _exog_d = None
    _exog_cols = []
    if df_dummy is not None and not df_dummy.empty:
        _df_dum = df_dummy.reindex(df_m[todas_vars].dropna().index).fillna(0)
        _exog_d = _df_dum.reset_index(drop=True).values
        _exog_cols = list(_df_dum.columns)
    joh    = coint_johansen(data, det_order=det_order, k_ar_diff=k_ar_diff)
    _k_v   = data.shape[1]
    n_ci   = min(_k_v - 1, int(sum(joh.lr1 > joh.cvt[:, 1])))
    if n_ci == 0:
        return None

    try:
        res = VECM(data, k_ar_diff=k_ar_diff, coint_rank=n_ci,
                   deterministic='ci', exog=_exog_d).fit()
    except Exception:
        res = VECM(data, k_ar_diff=k_ar_diff, coint_rank=n_ci,
                   deterministic='ci').fit()

    _n_ic  = int(res.nobs)
    _k_ic  = int(res.neqs)
    _p_ic  = int(res.k_ar)
    _ld_ic = float(np.log(np.linalg.det(res.sigma_u)))
    _nf_ic = _k_ic * _p_ic + n_ci
    aic = _ld_ic + (2.0 / _n_ic) * _nf_ic * _k_ic
    bic = _ld_ic + (np.log(_n_ic) / _n_ic) * _nf_ic * _k_ic
    hq  = _ld_ic + (2.0 * np.log(np.log(max(_n_ic, 3))) / _n_ic) * _nf_ic * _k_ic

    all_list = list(todas_vars)
    y_idx    = all_list.index(y_var)
    _y_resid_v = res.resid[:, y_idx]
    _y_act_v   = data[y_var].diff().dropna().values[-len(_y_resid_v):]
    _ss_res_v  = float(np.sum(_y_resid_v ** 2))
    _ss_tot_v  = float(np.sum((_y_act_v - _y_act_v.mean()) ** 2))
    r2 = float(1 - _ss_res_v / _ss_tot_v) if _ss_tot_v > 0 else np.nan

    k_vars   = len(all_list)
    gamma    = res.gamma
    gamma_se = getattr(res, 'stderr_gamma', None)
    n_short  = k_ar_diff

    alpha_coef = np.nan
    alpha_pval = np.nan
    try:
        alpha_coef = float(res.alpha[y_idx, 0])
        _alpha_se_mat = getattr(res, 'stderr_alpha', None)
        if _alpha_se_mat is not None and _alpha_se_mat.shape[0] > y_idx:
            _alpha_se_val = float(_alpha_se_mat[y_idx, 0])
            if _alpha_se_val > 0:
                _alpha_t = alpha_coef / _alpha_se_val
                alpha_pval = float(t_dist.sf(abs(_alpha_t), df=max(1, res.nobs - k_vars)) * 2)
    except Exception:
        pass

    gamma_coefs = {}
    for x in x_vars:
        if x not in all_list:
            gamma_coefs[x] = {'coef': np.nan, 'pval': np.nan}
            continue
        xi   = all_list.index(x)
        cols = [l * k_vars + xi for l in range(n_short) if l * k_vars + xi < gamma.shape[1]]
        if cols:
            c = float(gamma[y_idx, cols].sum())
            if gamma_se is not None:
                if n_short == 1:
                    _se = float(gamma_se[y_idx, cols[0]])
                    pv  = (float(t_dist.sf(abs(c / (_se + 1e-12)),
                                           df=max(1, res.nobs - k_vars)) * 2)
                           if _se > 0 else np.nan)
                else:
                    pv = float(min(
                        t_dist.sf(abs(float(gamma[y_idx, ci]) / (float(gamma_se[y_idx, ci]) + 1e-12)),
                                  df=max(1, res.nobs - k_vars)) * 2
                        for ci in cols if float(gamma_se[y_idx, ci]) > 0
                    )) if any(float(gamma_se[y_idx, ci]) > 0 for ci in cols) else np.nan
            else:
                pv = np.nan
            gamma_coefs[x] = {'coef': c, 'pval': pv}
        else:
            gamma_coefs[x] = {'coef': np.nan, 'pval': np.nan}

    coefs = {}
    for x in x_vars:
        if x not in all_list:
            coefs[x] = {'coef': np.nan, 'pval': np.nan}
            continue
        xi   = all_list.index(x)
        cols = [l * k_vars + xi for l in range(n_short) if l * k_vars + xi < gamma.shape[1]]
        if cols:
            c  = float(gamma[y_idx, cols].sum())
            se = (float(np.sqrt(np.sum(gamma_se[y_idx, cols] ** 2)))
                  if gamma_se is not None else None)
            pv = (float(t_dist.sf(abs(c / (se + 1e-12)),
                                  df=max(1, res.nobs - k_vars)) * 2)
                  if se is not None else np.nan)
        else:
            c = pv = np.nan
        coefs[x] = {'coef': c, 'pval': pv}

    beta_coefs = {x: {'coef': float('nan'), 'pval': float('nan')} for x in x_vars}
    try:
        beta_mat = np.asarray(res.beta)
        b0       = beta_mat[:, 0]
        y_b      = float(b0[y_idx])
    except Exception:
        beta_mat = None
        y_b = 0.0

    try:
        beta_se = np.asarray(res.stderr_beta)
    except Exception:
        beta_se = None

    if beta_mat is not None and abs(y_b) > 1e-12:
        for x in x_vars:
            if x not in all_list:
                continue
            xi    = all_list.index(x)
            try:
                theta = -float(b0[xi]) / y_b
            except Exception:
                continue
            pv = float('nan')
            if beta_se is not None and beta_se.shape[0] > xi:
                try:
                    _se_raw_x = float(beta_se[xi, 0])
                    _se_raw_y = float(beta_se[y_idx, 0]) if beta_se.shape[0] > y_idx else 0.0
                    var_t = (_se_raw_x / abs(y_b))**2 + (theta * _se_raw_y / abs(y_b))**2
                    se_t  = float(np.sqrt(max(var_t, 0.0)))
                    if se_t > 0:
                        z = theta / se_t
                        pv = float(t_dist.sf(abs(z), df=max(1, res.nobs - k_vars)) * 2)
                except Exception:
                    pass
            beta_coefs[x] = {'coef': theta, 'pval': pv}

    dummy_coefs = {}

    return {'aic': aic, 'bic': bic, 'hq': hq, 'r2': r2,
            'coefs': coefs,
            'alpha_coef': alpha_coef, 'alpha_pval': alpha_pval,
            'gamma_coefs': gamma_coefs,
            'beta_coefs': beta_coefs,
            'dummy_coefs': dummy_coefs,
            'n_coint': n_ci, 'nobs': int(res.nobs),
            'resid_y': _y_resid_v}


# ── Preview de combinatoria (cantidad de pruebas) ─────────────────────────────
def calcular_preview(ctx, est_ctx, config):
    """Estima cuántas pruebas se van a correr (sin ejecutar nada)."""
    X_SAFE_EST = est_ctx['X_SAFE_EST']
    X_SAFE_I1 = est_ctx['X_SAFE_I1']
    Y_ORDEN = est_ctx['Y_ORDEN']
    MAX_VARS = config['MAX_VARS_POR_MODELO']
    MAX_COMBOS = config['MAX_COMBINACIONES']
    MAX_PERMS = config['MAX_PERMUTACIONES_VAR']
    CRITS = config['CRITERIOS_SEL']
    MODELOS = config['MODELOS']
    AUTO = config['AUTO_LAGS']

    _n_max = len(X_SAFE_EST) if MAX_VARS is None else MAX_VARS
    combos = []
    for r in range(1, _n_max + 1):
        combos.extend(list(combinations(X_SAFE_EST, r)))
    if MAX_COMBOS is not None and len(combos) > MAX_COMBOS:
        combos = combos[:MAX_COMBOS]

    n_ardl = len(combos) * len(CRITS) if 'ARDL' in MODELOS else 0

    perms = []
    for sub in combos:
        for p in permutations(sub):
            perms.append(p)
    if len(perms) > MAX_PERMS:
        perms = perms[:MAX_PERMS]
    lags_var = [1] if AUTO else list(range(1, max(1, ctx['LAG_CAP_FREQ']) + 1))
    n_var = len(perms) * len(lags_var) if 'VAR' in MODELOS else 0

    n_vecm = 0
    if 'VECM' in MODELOS and Y_ORDEN == 1 and X_SAFE_I1:
        _n_max_v = len(X_SAFE_I1) if MAX_VARS is None else MAX_VARS
        combos_v = []
        for r in range(1, _n_max_v + 1):
            combos_v.extend(list(combinations(X_SAFE_I1, r)))
        if MAX_COMBOS is not None and len(combos_v) > MAX_COMBOS:
            combos_v = combos_v[:MAX_COMBOS]
        lags_vecm = [1] if AUTO else list(range(1, max(1, ctx.get('LAG_CAP_FREQ_VECM', ctx['LAG_CAP_FREQ'])) + 1))
        n_vecm = len(combos_v) * len(lags_vecm)

    return {
        'n_pruebas_ardl': n_ardl,
        'n_pruebas_var':  n_var,
        'n_pruebas_vecm': n_vecm,
        'n_pruebas_total': n_ardl + n_var + n_vecm,
        'n_combos': len(combos),
        'n_perms_var': len(perms),
    }


# ── Sección 7: ARDL ───────────────────────────────────────────────────────────
def seccion_7_ardl(ctx, est_ctx, config):
    _print_header('7', 'MODELOS ARDL')

    df_safe_est = est_ctx['df_safe_est']
    Y_SAFE = ctx['Y_SAFE']
    X_SAFE_EST = est_ctx['X_SAFE_EST']
    COL_LABEL = ctx['COL_LABEL']
    df_exog_dummy = ctx['df_exog_dummy']
    MAX_LAGS_DEP = ctx['MAX_LAGS_DEP']
    MAX_LAGS_IND = ctx['MAX_LAGS_IND']
    SEMILLA = config['SEMILLA']
    CRITERIOS_SEL = config['CRITERIOS_SEL']
    MAX_VARS = config['MAX_VARS_POR_MODELO']
    MAX_COMBOS = config['MAX_COMBINACIONES']

    _BJ_PROPOSED_LAGS = {}
    _BJ_AR_Y = 1

    _n_max = len(X_SAFE_EST) if MAX_VARS is None else MAX_VARS
    _combos_ardl = []
    for _r in range(1, _n_max + 1):
        _combos_ardl.extend(list(combinations(X_SAFE_EST, _r)))
    if MAX_COMBOS is not None and len(_combos_ardl) > MAX_COMBOS:
        random.seed(SEMILLA)
        _combos_ardl = random.sample(_combos_ardl, MAX_COMBOS)

    print(f'Combinaciones ARDL : {len(_combos_ardl)}')
    print(f'Criterios          : {CRITERIOS_SEL}')
    print(f'Estimaciones esp.  : {len(_combos_ardl) * len(CRITERIOS_SEL)}')

    _RESULTADOS_ARDL = []
    _ARDL_RESIDUALS  = {}
    _t0 = pd.Timestamp.now()
    _ok = 0
    _err = 0
    _print_int = max(1, len(_combos_ardl) // 5)

    for _criterio in CRITERIOS_SEL:
        for _ci, _combo in enumerate(_combos_ardl):
            _xv = list(_combo)
            _tv = list(_xv) + [Y_SAFE]
            _df = df_safe_est[_tv].dropna()
            if len(_df) < 30:
                continue
            try:
                _r = extraer_ardl(_df, Y_SAFE, _xv, MAX_LAGS_DEP, MAX_LAGS_IND, _criterio,
                                  df_dummy=df_exog_dummy if not df_exog_dummy.empty else None,
                                  bj_proposed_lags=_BJ_PROPOSED_LAGS, bj_ar_y=_BJ_AR_Y)
                _row = {
                    'combo_id': f'{_ci}_{_criterio}', 'criterio': _criterio,
                    'modelo': 'ARDL', 'n_vars': len(_xv),
                    'vars_safe': '|'.join(_xv),
                    'vars_label': '|'.join([COL_LABEL[v] for v in _xv]),
                    'aic': _r['aic'], 'bic': _r['bic'], 'hq': _r['hq'],
                    'r2': _r['r2'], 'nobs': _r['nobs'],
                }
                for _x in _xv:
                    _row[f'coef_{_x}']    = _r['coefs'][_x]['coef']
                    _row[f'pval_{_x}']    = _r['coefs'][_x]['pval']
                    _row[f'lr_coef_{_x}'] = _r['lr_coefs'][_x]['coef']
                    _row[f'lr_pval_{_x}'] = _r['lr_coefs'][_x]['pval']
                _RESULTADOS_ARDL.append(_row)
                _ARDL_RESIDUALS[_row['combo_id']] = _r['resid']
                _ok += 1
            except Exception:
                _err += 1

            if (_ci + 1) % _print_int == 0 or _ci == len(_combos_ardl) - 1:
                _el = int((pd.Timestamp.now() - _t0).total_seconds())
                print(f'  [{_criterio.upper()}] combo {_ci+1:>3}/{len(_combos_ardl)} | ok={_ok} err={_err} | {_el}s')

    df_res_ardl = pd.DataFrame(_RESULTADOS_ARDL)
    print(f'\nARDL: {_ok} modelos OK | {_err} errores')

    # Control de calidad (sin filtros duros, replica 02a)
    if df_res_ardl.empty:
        df_res_ardl_ok = pd.DataFrame()
    else:
        df_res_ardl['ctrl_flags'] = 'OK'
        df_res_ardl['ctrl_ok'] = True
        df_res_ardl_ok = df_res_ardl.copy()

    # Diagnóstico LB
    from statsmodels.stats.diagnostic import acorr_ljungbox
    DIAG_LAGS_LB = 8
    DIAG_ALPHA = 0.05
    if df_res_ardl_ok.empty:
        df_ardl_ruido_blanco = pd.DataFrame()
    else:
        _passed_ids = []
        for _, _mrow in df_res_ardl_ok.iterrows():
            _cid = _mrow['combo_id']
            _resid = _ARDL_RESIDUALS.get(_cid)
            if _resid is None or len(_resid) < DIAG_LAGS_LB + 2:
                continue
            try:
                _lb = acorr_ljungbox(_resid, lags=[DIAG_LAGS_LB], return_df=True)
                if float(_lb['lb_pvalue'].iloc[-1]) > DIAG_ALPHA:
                    _passed_ids.append(_cid)
            except Exception:
                pass
        df_ardl_ruido_blanco = df_res_ardl_ok[df_res_ardl_ok['combo_id'].isin(_passed_ids)].copy()
        print(f'  Ruido blanco LB: {len(df_ardl_ruido_blanco)}/{len(df_res_ardl_ok)}')

    return {
        'df_res_ardl': df_res_ardl,
        'df_res_ardl_ok': df_res_ardl_ok,
        'df_ardl_ruido_blanco': df_ardl_ruido_blanco,
        '_ARDL_RESIDUALS': _ARDL_RESIDUALS,
        '_BJ_PROPOSED_LAGS': _BJ_PROPOSED_LAGS,
        '_BJ_AR_Y': _BJ_AR_Y,
        'n_ok': _ok, 'n_err': _err,
    }


# ── Sección 8: VAR ────────────────────────────────────────────────────────────
def seccion_8_var(ctx, est_ctx, config):
    _print_header('8', 'MODELOS VAR')

    df_safe_est = est_ctx['df_safe_est']
    Y_SAFE = ctx['Y_SAFE']
    X_SAFE_EST = est_ctx['X_SAFE_EST']
    COL_LABEL = ctx['COL_LABEL']
    df_exog_dummy = ctx['df_exog_dummy']
    DUMMY_SAFE = ctx.get('DUMMY_SAFE', [])
    MAX_LAGS_VAR = ctx['MAX_LAGS_VAR']
    LAG_CAP_FREQ = ctx.get('LAG_CAP_FREQ', MAX_LAGS_VAR)
    NIVEL_SIG = config['NIVEL_SIG']
    SEMILLA = config['SEMILLA']
    AUTO_LAGS = config['AUTO_LAGS']
    MAX_VARS = config['MAX_VARS_POR_MODELO']
    MAX_COMBOS = config['MAX_COMBINACIONES']
    MAX_PERMS = config['MAX_PERMUTACIONES_VAR']

    from statsmodels.tsa.api import VAR as _VAR_est
    from statsmodels.stats.diagnostic import acorr_ljungbox as _lb_var
    from scipy.stats import norm

    _n_max = len(X_SAFE_EST) if MAX_VARS is None else MAX_VARS
    _subsets = []
    for _r in range(1, _n_max + 1):
        _subsets.extend(list(combinations(X_SAFE_EST, _r)))
    if MAX_COMBOS is not None and len(_subsets) > MAX_COMBOS:
        random.seed(SEMILLA)
        _subsets = random.sample(_subsets, MAX_COMBOS)

    _perms = []
    for _subset in _subsets:
        for _perm in permutations(_subset):
            _perms.append(list(_perm))
    if len(_perms) > MAX_PERMS:
        random.seed(SEMILLA)
        _perms = random.sample(_perms, MAX_PERMS)

    HORIZONTE_IRF = 12
    DIAG_LAGS_LB = 8

    _RESULTADOS_VAR = []
    _t0 = pd.Timestamp.now()
    _ok = 0
    _err = 0
    _print_int = max(1, len(_perms) // 5)

    for _ci, _xv_perm in enumerate(_perms):
        _tv_perm = list(_xv_perm) + [Y_SAFE]
        _df = df_safe_est[_tv_perm].dropna()
        _nobs = len(_df)
        if _nobs < 30:
            continue

        # Decide lags a probar
        if AUTO_LAGS:
            try:
                _sel = _VAR_est(_df).select_order(maxlags=MAX_LAGS_VAR)
                _k_auto = max(1, _sel.selected_orders.get('aic', 1))
                _lags_iter = [_k_auto]
            except Exception:
                _lags_iter = [1]
        else:
            _lags_iter = list(range(1, max(1, LAG_CAP_FREQ) + 1))

        _exog_d = (df_exog_dummy.reindex(_df.index).fillna(0)
                   if not df_exog_dummy.empty else None)
        _k_vars = len(_tv_perm)
        _max_p_din = max(1, (_nobs - 10) // _k_vars)

        for _k_ar in _lags_iter:
            if _k_ar > _max_p_din:
                continue
            _criterio = f'lag{_k_ar}' if not AUTO_LAGS else 'auto'

            try:
                _model = _VAR_est(_df, exog=_exog_d)
                _res = _model.fit(_k_ar)

                _irf = _res.irf(periods=HORIZONTE_IRF)
                _orth_irfs = _irf.orth_irfs
                _orth_stderr = _irf.stderr(orth=True)
                _y_idx = _k_vars - 1

                _row = {
                    'combo_id': f'{_ci}_{_criterio}_{"-".join(_xv_perm)}',
                    'criterio': _criterio, 'modelo': 'VAR',
                    'n_vars': len(_xv_perm),
                    'vars_safe': '|'.join(_xv_perm),
                    'vars_label': '|'.join([COL_LABEL.get(v, v)[:15] for v in _xv_perm]),
                    'aic': float(_res.aic), 'bic': float(_res.bic),
                    'hq': float(_res.hqic), 'nobs': int(_res.nobs), 'k_ar': _k_ar,
                }

                for _x_idx, _x in enumerate(_xv_perm):
                    for _h in range(HORIZONTE_IRF + 1):
                        _impacto = float(_orth_irfs[_h, _y_idx, _x_idx])
                        _se = float(_orth_stderr[_h, _y_idx, _x_idx])
                        _pval = 2 * (1 - norm.cdf(abs(_impacto / _se))) if _se > 0 else 1.0
                        _row[f'irf_{_x}_h{_h}'] = _impacto
                        _row[f'irfpval_{_x}_h{_h}'] = _pval
                    _row[f'coef_{_x}'] = _row[f'irf_{_x}_h0']
                    _row[f'pval_{_x}'] = _row[f'irfpval_{_x}_h0']

                # sum_coef + wald (largo plazo VAR)
                try:
                    _params_df = _res.params
                    _pvals_df = _res.pvalues
                    _var_pos = {v: i for i, v in enumerate(_tv_perm)}
                    _y_col = Y_SAFE if Y_SAFE in _params_df.columns else _params_df.columns[_y_idx]
                    _y_coefs = _params_df[_y_col]
                    _y_pvals = _pvals_df[_y_col]
                    _K_endo = len(_tv_perm)
                    for _x in _xv_perm:
                        _xpos = _var_pos.get(_x)
                        if _xpos is None:
                            _row[f'sum_coef_{_x}']  = float('nan')
                            _row[f'wald_pval_{_x}'] = float('nan')
                            continue
                        _names = list(_y_coefs.index)
                        _idx_x = [_i for _i, _n in enumerate(_names)
                                  if _n.startswith('L') and _n.endswith(f'.{_x}')]
                        if not _idx_x:
                            _idx_x = [_la*_K_endo + _xpos + 1 for _la in range(_k_ar)
                                      if _la*_K_endo + _xpos + 1 < len(_names)]
                        if _idx_x:
                            _sum_c = float(_y_coefs.iloc[_idx_x].sum())
                            try:
                                _all_names = list(_res.params.stack().index)
                                _R_rows = []
                                for _ii in _idx_x:
                                    _term = _names[_ii]
                                    if (_y_col, _term) in _all_names:
                                        _full_idx = _all_names.index((_y_col, _term))
                                        _r_row = np.zeros(len(_all_names))
                                        _r_row[_full_idx] = 1.0
                                        _R_rows.append(_r_row)
                                if _R_rows:
                                    _Rm = np.vstack(_R_rows)
                                    _wald = _res.wald_test(_Rm, use_f=True, scalar=False)
                                    _pval_w = float(_wald.pvalue)
                                else:
                                    _pval_w = float(_y_pvals.iloc[_idx_x].min())
                            except Exception:
                                _pval_w = float(_y_pvals.iloc[_idx_x].min())
                        else:
                            _sum_c = float('nan')
                            _pval_w = float('nan')
                        _row[f'sum_coef_{_x}']  = _sum_c
                        _row[f'wald_pval_{_x}'] = _pval_w
                except Exception:
                    for _x in _xv_perm:
                        _row[f'sum_coef_{_x}']  = float('nan')
                        _row[f'wald_pval_{_x}'] = float('nan')

                # R²
                _y_resid = _res.resid.iloc[:, _y_idx]
                _y_act = _df[Y_SAFE].values[-len(_y_resid):]
                _ss_res = float(np.sum(_y_resid ** 2))
                _ss_tot = float(np.sum((_y_act - _y_act.mean()) ** 2))
                _row['r2'] = float(1 - _ss_res / _ss_tot) if _ss_tot > 0 else np.nan

                # Ljung-Box
                try:
                    _lb = _lb_var(_y_resid, lags=[DIAG_LAGS_LB], return_df=True)
                    _lb_p = float(_lb['lb_pvalue'].iloc[-1])
                    _row['lb_pval'] = _lb_p
                    _row['ruido_blanco'] = _lb_p > NIVEL_SIG
                except Exception:
                    _row['lb_pval'] = float('nan')
                    _row['ruido_blanco'] = False

                _RESULTADOS_VAR.append(_row)
                _ok += 1
            except Exception:
                _err += 1

        if (_ci + 1) % _print_int == 0 or _ci == len(_perms) - 1:
            _el = int((pd.Timestamp.now() - _t0).total_seconds())
            print(f'  perm {_ci+1:>4}/{len(_perms)} | ok={_ok} err={_err} | {_el}s')

    df_res_var = pd.DataFrame(_RESULTADOS_VAR)
    print(f'\nVAR: {_ok} modelos OK | {_err} errores')

    # VAR_BEST_LAGS
    _var_lags = defaultdict(list)
    for _rv in _RESULTADOS_VAR:
        _k = frozenset(v for v in _rv.get('vars_safe', '').split('|') if v)
        _var_lags[_k].append((_rv.get('aic', float('inf')), _rv.get('k_ar', 2)))
    VAR_BEST_LAGS = {k: max(1, min(lags, key=lambda t: t[0])[1])
                     for k, lags in _var_lags.items() if lags}

    if df_res_var.empty:
        df_res_var_ok = pd.DataFrame()
    else:
        if 'ruido_blanco' in df_res_var.columns:
            df_res_var_ok = df_res_var[df_res_var['ruido_blanco'] == True].copy()
        else:
            df_res_var_ok = df_res_var.copy()
        df_res_var['ctrl_ok'] = df_res_var['combo_id'].isin(df_res_var_ok['combo_id'])
        print(f'  Ruido blanco: {len(df_res_var_ok)}/{len(df_res_var)}')

    return {
        'df_res_var': df_res_var,
        'df_res_var_ok': df_res_var_ok,
        'VAR_BEST_LAGS': VAR_BEST_LAGS,
        'HORIZONTE_IRF': HORIZONTE_IRF,
        'n_ok': _ok, 'n_err': _err,
    }


# ── Sección 9: VECM ───────────────────────────────────────────────────────────
def seccion_9_vecm(ctx, est_ctx, config, var_res=None):
    _print_header('9', 'MODELOS VECM')

    df_safe = ctx['df_safe']
    Y_SAFE = ctx['Y_SAFE']
    COL_LABEL = ctx['COL_LABEL']
    df_exog_dummy = ctx['df_exog_dummy']
    DUMMY_SAFE = ctx.get('DUMMY_SAFE', [])
    LAG_CAP_FREQ_VECM = ctx.get('LAG_CAP_FREQ_VECM', ctx['LAG_CAP_FREQ'])
    X_SAFE_I1 = est_ctx['X_SAFE_I1']
    X_SAFE_EST = est_ctx['X_SAFE_EST']
    Y_ORDEN = est_ctx['Y_ORDEN']
    NIVEL_SIG = config['NIVEL_SIG']
    SEMILLA = config['SEMILLA']
    MAX_VARS = config['MAX_VARS_POR_MODELO']
    MAX_COMBOS = config['MAX_COMBINACIONES']

    from statsmodels.tsa.vector_ar.vecm import coint_johansen as _joh
    from statsmodels.stats.diagnostic import acorr_ljungbox as _lb_vecm

    _empty = {'df_res_vecm': pd.DataFrame(), 'df_res_vecm_ok': pd.DataFrame(),
              'n_ok': 0, 'n_err': 0}

    if Y_ORDEN != 1:
        print('Y no es I(1) → VECM no aplica.')
        return _empty
    if not X_SAFE_I1:
        print('Sin variables I(1) → VECM no aplica.')
        return _empty

    # Combos: desde VAR OK si hay; sino combinaciones de X_SAFE_I1
    _combos_vecm = []
    _x_set = set(X_SAFE_I1)
    if var_res is not None:
        _df_var_ok = var_res.get('df_res_var_ok', pd.DataFrame())
        _seen = set()
        for _, _rv in _df_var_ok.iterrows():
            _xv = tuple(sorted(v for v in str(_rv.get('vars_safe', '')).split('|')
                               if v and v in _x_set))
            if _xv and _xv not in _seen:
                _seen.add(_xv)
                _combos_vecm.append(_xv)

    if not _combos_vecm:
        _n_max = len(X_SAFE_I1) if MAX_VARS is None else MAX_VARS
        for _r in range(1, _n_max + 1):
            _combos_vecm.extend(list(combinations(X_SAFE_I1, _r)))

    if MAX_COMBOS is not None and len(_combos_vecm) > MAX_COMBOS:
        random.seed(SEMILLA)
        _combos_vecm = random.sample(_combos_vecm, MAX_COMBOS)

    _kdiff_range = list(range(1, max(1, LAG_CAP_FREQ_VECM) + 1))
    print(f'Combos VECM: {len(_combos_vecm)} × {len(_kdiff_range)} lags')

    _RESULTADOS_VECM = []
    _t0 = pd.Timestamp.now()
    _ok = 0
    _err = 0
    _skip = 0
    _print_int = max(1, len(_combos_vecm) // 5)

    for _ci, _combo in enumerate(_combos_vecm):
        _xv = list(_combo)
        _tv = list(_xv) + [Y_SAFE]
        _df = df_safe[_tv].dropna()
        if len(_df) < 30:
            _skip += len(_kdiff_range)
            continue

        for _k in _kdiff_range:
            try:
                _r = extraer_vecm(_df, Y_SAFE, _xv, _tv,
                                  k_ar_diff=_k, det_order=0,
                                  df_dummy=df_exog_dummy if not df_exog_dummy.empty else None,
                                  dummy_names=DUMMY_SAFE if DUMMY_SAFE else None)
                if _r is not None:
                    _row = {
                        'combo_id': f'{_ci}_k{_k}_vecm',
                        'criterio': 'johansen', 'modelo': 'VECM',
                        'n_vars': len(_xv),
                        'vars_safe': '|'.join(_xv),
                        'vars_label': '|'.join([COL_LABEL[v] for v in _xv]),
                        'aic': _r['aic'], 'bic': _r['bic'], 'hq': _r['hq'],
                        'r2': _r['r2'], 'nobs': _r['nobs'],
                        'n_coint': _r['n_coint'], 'k_ar_diff': _k,
                        'alpha_coef': _r.get('alpha_coef', float('nan')),
                        'alpha_pval': _r.get('alpha_pval', float('nan')),
                    }
                    for _x in _xv:
                        _gc = _r.get('gamma_coefs', {}).get(_x, {})
                        _row[f'gamma_coef_{_x}'] = _gc.get('coef', float('nan'))
                        _row[f'gamma_pval_{_x}'] = _gc.get('pval', float('nan'))
                        _row[f'coef_{_x}'] = _r['coefs'][_x]['coef']
                        _row[f'pval_{_x}'] = _r['coefs'][_x]['pval']
                        _bc = _r.get('beta_coefs', {}).get(_x, {})
                        _row[f'beta_coef_{_x}'] = _bc.get('coef', float('nan'))
                        _row[f'beta_pval_{_x}'] = _bc.get('pval', float('nan'))
                    # LB
                    try:
                        _ry = _r.get('resid_y')
                        if _ry is not None and len(_ry) > 10:
                            _lbv = _lb_vecm(_ry, lags=[8], return_df=True)
                            _lbp = float(_lbv['lb_pvalue'].iloc[-1])
                            _row['lb_pval'] = _lbp
                            _row['ruido_blanco'] = _lbp > NIVEL_SIG
                        else:
                            _row['lb_pval'] = float('nan')
                            _row['ruido_blanco'] = False
                    except Exception:
                        _row['lb_pval'] = float('nan')
                        _row['ruido_blanco'] = False
                    _RESULTADOS_VECM.append(_row)
                    _ok += 1
                else:
                    _skip += 1
            except Exception:
                _err += 1

        if (_ci + 1) % _print_int == 0 or _ci == len(_combos_vecm) - 1:
            _el = int((pd.Timestamp.now() - _t0).total_seconds())
            print(f'  VECM combo {_ci+1:>3}/{len(_combos_vecm)} | ok={_ok} skip={_skip} err={_err} | {_el}s')

    df_res_vecm = pd.DataFrame(_RESULTADOS_VECM)
    print(f'\nVECM: {_ok} modelos OK | {_skip} sin coint. | {_err} errores')

    if df_res_vecm.empty:
        df_res_vecm_ok = pd.DataFrame()
    else:
        if 'ruido_blanco' in df_res_vecm.columns:
            df_res_vecm_ok = df_res_vecm[df_res_vecm['ruido_blanco'] == True].copy()
        else:
            df_res_vecm_ok = df_res_vecm.copy()
        df_res_vecm['ctrl_ok'] = df_res_vecm['combo_id'].isin(df_res_vecm_ok['combo_id'])
        print(f'  Ruido blanco: {len(df_res_vecm_ok)}/{len(df_res_vecm)}')

    return {
        'df_res_vecm': df_res_vecm,
        'df_res_vecm_ok': df_res_vecm_ok,
        'n_ok': _ok, 'n_err': _err,
    }


# ── Sección 10: Consolidación ─────────────────────────────────────────────────
def seccion_10_consolidacion(ctx, ardl_res, var_res, vecm_res, config, output_dir, pngs):
    _print_header('10', 'RESULTADOS CONSOLIDADOS')

    COL_LABEL = ctx['COL_LABEL']
    NIVEL_SIG = config['NIVEL_SIG']

    _frames = []
    _ardl_diag = ardl_res.get('df_ardl_ruido_blanco', pd.DataFrame()) if ardl_res else pd.DataFrame()
    _ardl_src  = _ardl_diag if not _ardl_diag.empty else (ardl_res.get('df_res_ardl_ok', pd.DataFrame()) if ardl_res else pd.DataFrame())
    _var_ok    = var_res.get('df_res_var_ok', pd.DataFrame()) if var_res else pd.DataFrame()
    _vecm_ok   = vecm_res.get('df_res_vecm_ok', pd.DataFrame()) if vecm_res else pd.DataFrame()

    for _df_ok, _nombre in [(_ardl_src, 'ARDL'), (_var_ok, 'VAR'), (_vecm_ok, 'VECM')]:
        if not _df_ok.empty:
            _frames.append(_df_ok)
            print(f'  {_nombre}: {len(_df_ok)} modelos OK')
        else:
            print(f'  {_nombre}: sin modelos')

    if not _frames:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_res = pd.concat(_frames, ignore_index=True)

    def _coef_pval_lr(fila, x):
        mod = fila['modelo']
        if mod == 'ARDL':
            c, p = fila.get(f'lr_coef_{x}', float('nan')), fila.get(f'lr_pval_{x}', float('nan'))
        elif mod == 'VAR':
            c, p = fila.get(f'sum_coef_{x}', float('nan')), fila.get(f'wald_pval_{x}', float('nan'))
        elif mod == 'VECM':
            c, p = fila.get(f'beta_coef_{x}', float('nan')), fila.get(f'beta_pval_{x}', float('nan'))
        else:
            c, p = fila.get(f'coef_{x}', float('nan')), fila.get(f'pval_{x}', float('nan'))
        if isinstance(c, float) and math.isnan(c):
            c, p = fila.get(f'coef_{x}', float('nan')), fila.get(f'pval_{x}', float('nan'))
        return c, p

    def _coef_pval_sr(fila, x):
        mod = fila['modelo']
        if mod == 'ARDL':
            return fila.get(f'coef_{x}', float('nan')), fila.get(f'pval_{x}', float('nan'))
        if mod == 'VAR':
            return fila.get(f'irf_{x}_h0', fila.get(f'coef_{x}', float('nan'))), \
                   fila.get(f'irfpval_{x}_h0', fila.get(f'pval_{x}', float('nan')))
        if mod == 'VECM':
            return fila.get(f'gamma_coef_{x}', float('nan')), fila.get(f'gamma_pval_{x}', float('nan'))
        return fila.get(f'coef_{x}', float('nan')), fila.get(f'pval_{x}', float('nan'))

    _filas = []
    for _, fila in df_res.iterrows():
        xv = [v for v in fila['vars_safe'].split('|') if v]
        for x in xv:
            c_lr, p_lr = _coef_pval_lr(fila, x)
            c_sr, p_sr = _coef_pval_sr(fila, x)
            if (isinstance(c_lr, float) and math.isnan(c_lr)) and \
               (isinstance(c_sr, float) and math.isnan(c_sr)):
                continue
            _filas.append({
                'combo_id': fila['combo_id'], 'modelo': fila['modelo'],
                'criterio': fila['criterio'], 'var_safe': x,
                'variable': COL_LABEL.get(x, x),
                'coef': c_lr, 'pval': p_lr,
                'sig': (p_lr < NIVEL_SIG) if not (isinstance(p_lr, float) and math.isnan(p_lr)) else False,
                'coef_sr': c_sr, 'pval_sr': p_sr,
                'sig_sr': (p_sr < NIVEL_SIG) if not (isinstance(p_sr, float) and math.isnan(p_sr)) else False,
                'r2': fila.get('r2', float('nan')),
                'aic': fila.get('aic', float('nan')),
                'bic': fila.get('bic', float('nan')),
                'hq':  fila.get('hq', float('nan')),
                'nobs': fila.get('nobs', float('nan')),
                'n_vars': fila['n_vars'],
                'vars_label': fila['vars_label'],
                'alpha_coef': fila.get('alpha_coef', float('nan')),
                'alpha_pval': fila.get('alpha_pval', float('nan')),
            })
    df_largo = pd.DataFrame(_filas)
    df_dum = pd.DataFrame()  # sin dummies en runner

    print(f'\n  df_res: {len(df_res)} | df_largo: {len(df_largo)}')

    # Gráficos de significancia
    _COLORS = {'ARDL': '#2196F3', 'VAR': '#FF9800', 'VECM': '#4CAF50'}
    if not df_largo.empty:
        _vars_plot = sorted(df_largo['variable'].unique())
        _nc = min(2, len(_vars_plot))
        _nr = (len(_vars_plot) + _nc - 1) // _nc

        # Largo plazo
        fig, axes = plt.subplots(_nr, _nc, figsize=(8 * _nc, 5 * _nr), squeeze=False)
        for _idx, _var in enumerate(_vars_plot):
            ax = axes[_idx // _nc][_idx % _nc]
            _dv = df_largo[df_largo['variable'] == _var].dropna(subset=['coef', 'pval'])
            for _m, _c in _COLORS.items():
                _dm = _dv[_dv['modelo'] == _m]
                if _dm.empty: continue
                _sig = _dm['sig'].astype(bool)
                ax.scatter(_dm.loc[_sig, 'coef'], _dm.loc[_sig, 'pval'], color=_c, marker='o', label=_m, alpha=0.7, s=40)
                ax.scatter(_dm.loc[~_sig, 'coef'], _dm.loc[~_sig, 'pval'], color=_c, marker='x', alpha=0.5, s=40)
            ax.axhline(NIVEL_SIG, color='red', linestyle='--', linewidth=1)
            ax.axvline(0, color='gray', linestyle='--', linewidth=1)
            ax.set_title(_var[:50], fontsize=9)
            ax.set_xlabel('Coeficiente'); ax.set_ylabel('P-valor'); ax.legend(fontsize=8)
        for _idx in range(len(_vars_plot), _nr * _nc):
            axes[_idx // _nc][_idx % _nc].set_visible(False)
        fig.suptitle('Coef LARGO PLAZO vs P-valor', fontsize=11)
        plt.tight_layout()
        _save_fig(fig, output_dir, 'sec10_coef_vs_pval_largo_plazo', pngs)

        # Corto plazo
        fig, axes = plt.subplots(_nr, _nc, figsize=(8 * _nc, 5 * _nr), squeeze=False)
        for _idx, _var in enumerate(_vars_plot):
            ax = axes[_idx // _nc][_idx % _nc]
            _dv = df_largo[df_largo['variable'] == _var].dropna(subset=['coef_sr', 'pval_sr'])
            for _m, _c in _COLORS.items():
                _dm = _dv[_dv['modelo'] == _m]
                if _dm.empty: continue
                _sig = _dm['sig_sr'].astype(bool)
                ax.scatter(_dm.loc[_sig, 'coef_sr'], _dm.loc[_sig, 'pval_sr'], color=_c, marker='o', label=_m, alpha=0.7, s=40)
                ax.scatter(_dm.loc[~_sig, 'coef_sr'], _dm.loc[~_sig, 'pval_sr'], color=_c, marker='x', alpha=0.5, s=40)
            ax.axhline(NIVEL_SIG, color='red', linestyle='--', linewidth=1)
            ax.axvline(0, color='gray', linestyle='--', linewidth=1)
            ax.set_title(_var[:50], fontsize=9)
            ax.set_xlabel('Coeficiente CORTO PLAZO'); ax.set_ylabel('P-valor'); ax.legend(fontsize=8)
        for _idx in range(len(_vars_plot), _nr * _nc):
            axes[_idx // _nc][_idx % _nc].set_visible(False)
        fig.suptitle('Coef CORTO PLAZO vs P-valor', fontsize=11)
        plt.tight_layout()
        _save_fig(fig, output_dir, 'sec10_coef_vs_pval_corto_plazo', pngs)

    return df_res, df_largo, df_dum


# ── Sección 11: Ranking ───────────────────────────────────────────────────────
def seccion_11_ranking(df_res, df_largo, ctx, est_ctx, config, ardl_res, output_dir, pngs):
    _print_header('11', 'RANKING Y COMPARACIÓN DE MODELOS')

    if df_res.empty:
        print('Sin resultados.')
        return {}

    rankings = {}
    crits = {'r2': ('r2', False), 'aic': ('aic', True),
             'bic': ('bic', True), 'hq': ('hq', True)}
    for name, (col, asc) in crits.items():
        if col not in df_res.columns or df_res[col].isna().all():
            continue
        _cols = list(dict.fromkeys(['modelo', 'vars_label', col, 'aic', 'bic', 'hq', 'r2', 'nobs']))
        _top = (df_res.dropna(subset=[col])
                .sort_values(col, ascending=asc)
                .drop_duplicates(subset=['vars_safe', 'modelo'])
                .head(10)[_cols]
                .reset_index(drop=True))
        rankings[f'top10_{name}'] = _to_records(_top)
        print(f'\nTOP 10 por {name.upper()}:')
        print(_top.to_string())

    # Mejor global
    mejor_global = None
    try:
        _best = df_res.loc[df_res['aic'].idxmin()]
        mejor_global = {
            'modelo': _best['modelo'],
            'vars_label': _best['vars_label'],
            'aic': float(_best['aic']),
            'bic': float(_best.get('bic', float('nan'))),
            'r2': float(_best.get('r2', float('nan'))),
        }
        print(f'\nMEJOR GLOBAL (AIC): {mejor_global["modelo"]} | AIC={mejor_global["aic"]:.4f}')
    except Exception:
        pass

    # Boxplots
    _COLORS = {'ARDL': '#2196F3', 'VAR': '#FF9800', 'VECM': '#4CAF50'}
    _mets = [('aic', 'AIC'), ('bic', 'BIC'), ('hq', 'HQIC'), ('r2', 'R²')]
    _mods = [m for m in ['ARDL', 'VAR', 'VECM'] if m in df_res['modelo'].unique()]
    if _mods:
        fig, axes = plt.subplots(1, 4, figsize=(20, 5))
        for _i, (_col, _lbl) in enumerate(_mets):
            ax = axes[_i]
            _data = [df_res[df_res['modelo'] == _m][_col].dropna().values for _m in _mods]
            _bp = ax.boxplot(_data, labels=_mods, patch_artist=True, showmeans=True)
            for _p, _m in zip(_bp['boxes'], _mods):
                _p.set_facecolor(_COLORS.get(_m, '#888')); _p.set_alpha(0.6)
            ax.set_title(_lbl); ax.grid(True, axis='y', linestyle=':', alpha=0.4)
        fig.suptitle('Criterios de información y R² por tipo de modelo', fontsize=12)
        plt.tight_layout()
        _save_fig(fig, output_dir, 'sec11_boxplot_criterios', pngs)

    return {'rankings': rankings, 'mejor_global': mejor_global}


# ── Sección B: Diagnóstico de residuos ────────────────────────────────────────
def seccion_B_diagnostico(df_res, ctx, est_ctx, config, ardl_res):
    _print_header('B', 'DIAGNÓSTICO DE RESIDUOS (Ljung-Box)')

    if df_res.empty:
        return {'resumen': []}

    from statsmodels.stats.diagnostic import acorr_ljungbox as _lb_test
    Y_SAFE = ctx['Y_SAFE']
    df_safe = ctx['df_safe']
    COL_LABEL = ctx['COL_LABEL']
    MAX_LAGS_DEP = ctx['MAX_LAGS_DEP']
    MAX_LAGS_IND = ctx['MAX_LAGS_IND']
    MAX_LAGS_VAR = ctx['MAX_LAGS_VAR']
    NIVEL_SIG = config['NIVEL_SIG']
    _LB_LAGS = 12

    def _resid(row):
        mod = row['modelo']
        xv = [v for v in str(row['vars_safe']).split('|') if v]
        tv = [Y_SAFE] + xv
        df_m = df_safe[tv].dropna()
        if len(df_m) < 30:
            return None
        try:
            if mod == 'ARDL':
                from statsmodels.tsa.ardl import ardl_select_order as _aso
                sel = _aso(df_m[Y_SAFE], MAX_LAGS_DEP, df_m[xv], MAX_LAGS_IND, ic='aic', trend='c')
                return sel.model.fit().resid.dropna().values
            if mod == 'VAR':
                from statsmodels.tsa.api import VAR as _VAR_r
                df_e = est_ctx['df_safe_est'][tv].dropna()
                _ls = _VAR_r(df_e).select_order(maxlags=MAX_LAGS_VAR)
                _k = max(1, _ls.selected_orders.get('aic', 1))
                return _VAR_r(df_e).fit(_k).resid[:, list(tv).index(Y_SAFE)]
            if mod == 'VECM':
                from statsmodels.tsa.vector_ar.vecm import VECM as _V, coint_johansen as _J
                _j = _J(df_m, det_order=0, k_ar_diff=2)
                _n = int(sum(_j.lr1 > _j.cvt[:, 1]))
                if _n == 0: return None
                return _V(df_m, k_ar_diff=2, coint_rank=_n, deterministic='ci').fit().resid[:, list(tv).index(Y_SAFE)]
        except Exception:
            return None

    df_uniq = df_res.sort_values('aic').groupby(['vars_safe', 'modelo'], sort=False).first().reset_index()
    rows = []
    for _, row in df_uniq.iterrows():
        r = _resid(row)
        if r is None or len(r) < 15:
            continue
        try:
            _lb = _lb_test(r, lags=[_LB_LAGS], return_df=True)
            _p = float(_lb['lb_pvalue'].iloc[0])
            xv = [v for v in str(row['vars_safe']).split('|') if v]
            rows.append({
                'Modelo': row['modelo'],
                'Variables': ' | '.join([COL_LABEL.get(v, v)[:22] for v in xv]),
                'LB_pval': round(_p, 4),
                'Ruido_Blanco': 'SI' if _p >= NIVEL_SIG else 'NO',
            })
        except Exception:
            pass
    df_rb = pd.DataFrame(rows)
    if not df_rb.empty:
        print(df_rb.to_string(index=False))
    return {'resumen': _to_records(df_rb)}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-json', required=True, help='JSON con series + config')
    ap.add_argument('--out-json', required=True, help='JSON de salida con resultados')
    ap.add_argument('--preview-only', action='store_true',
                    help='Solo calcular cantidad de pruebas, no estimar')
    ap.add_argument('--output-dir', default=None,
                    help='Directorio para PNGs (default: outputs/analisis_basico_runner/<run_id>)')
    args = ap.parse_args()

    with open(args.input_json, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    started = datetime.now()
    run_id = started.strftime('%Y%m%d_%H%M%S')

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = _PROJECT_ROOT / 'outputs' / 'analisis_basico_runner' / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        ctx, est_ctx, config = build_contexts(input_data)
        preview = calcular_preview(ctx, est_ctx, config)
        print(f'\nPreview: {preview}')

        if args.preview_only:
            result = {
                'ok': True, 'preview_only': True,
                'started_at': started.isoformat(),
                'finished_at': datetime.now().isoformat(),
                'run_id': run_id,
                'output_dir': str(output_dir),
                'preview': preview,
            }
        else:
            pngs = []
            modelos = config['MODELOS']
            secciones = config['SECCIONES']

            ardl_res = var_res = vecm_res = None
            if 'ARDL' in modelos and '7' in secciones:
                ardl_res = seccion_7_ardl(ctx, est_ctx, config)
            if 'VAR' in modelos and '8' in secciones:
                var_res = seccion_8_var(ctx, est_ctx, config)
            if 'VECM' in modelos and '9' in secciones:
                vecm_res = seccion_9_vecm(ctx, est_ctx, config, var_res=var_res)

            df_res = df_largo = df_dum = pd.DataFrame()
            if '10' in secciones:
                df_res, df_largo, df_dum = seccion_10_consolidacion(
                    ctx, ardl_res or {}, var_res or {}, vecm_res or {},
                    config, output_dir, pngs)

            ranking = {}
            if '11' in secciones and not df_res.empty:
                ranking = seccion_11_ranking(df_res, df_largo, ctx, est_ctx, config,
                                             ardl_res or {}, output_dir, pngs)

            diagnostico = {}
            if 'B' in secciones and not df_res.empty:
                diagnostico = seccion_B_diagnostico(df_res, ctx, est_ctx, config,
                                                    ardl_res or {})

            def _pack_modelo(res, prefix):
                if not res:
                    return None
                return {
                    'n_ok': res.get('n_ok', 0),
                    'n_err': res.get('n_err', 0),
                    'df_res': _to_records(res.get(f'df_res_{prefix}', pd.DataFrame()), max_rows=200),
                    'df_ok':  _to_records(res.get(f'df_res_{prefix}_ok', pd.DataFrame()), max_rows=200),
                }

            result = {
                'ok': True,
                'started_at': started.isoformat(),
                'finished_at': datetime.now().isoformat(),
                'run_id': run_id,
                'output_dir': str(output_dir),
                'preview': preview,
                'ardl': _pack_modelo(ardl_res, 'ardl'),
                'var':  _pack_modelo(var_res, 'var'),
                'vecm': _pack_modelo(vecm_res, 'vecm'),
                'consolidacion': {
                    'df_res': _to_records(df_res, max_rows=200),
                    'df_largo': _to_records(df_largo, max_rows=500),
                    'df_dum': _to_records(df_dum, max_rows=200),
                },
                'ranking': ranking,
                'diagnostico': diagnostico,
                'pngs': pngs,
            }

        with open(args.out_json, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        print(f'\n✅ Resultados escritos en {args.out_json}')

    except Exception as e:
        traceback.print_exc()
        with open(args.out_json, 'w', encoding='utf-8') as f:
            json.dump({
                'ok': False,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'run_id': run_id,
                'output_dir': str(output_dir),
            }, f, indent=2)
        sys.exit(1)


if __name__ == '__main__':
    main()
