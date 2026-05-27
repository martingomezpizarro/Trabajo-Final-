#!/usr/bin/env python3
"""
02a_analisis_basico.py — Análisis Básico Aislado de Modelos de Series de Tiempo
Riesgo País Argentino: Análisis Econométrico

Trabajo Final de Grado — Lic. en Economía, UNC
Autor: Martín Gómez Pizarro

Convierte el notebook 02a_analisis_basico.ipynb a Python puro con prints por sección.
Uso:
    python 02a_analisis_basico.py                    # Ejecutar todo
    python 02a_analisis_basico.py --seccion 7        # Solo sección 7 (ARDL)
    python 02a_analisis_basico.py --secciones 7,8    # Secciones 7 y 8
    python 02a_analisis_basico.py --hasta 6          # Hasta sección 6 inclusive
"""

import subprocess
import sys
import os
import re
import warnings
import glob
import random
import math
import argparse
import traceback
from itertools import combinations, permutations
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo; cambiar a 'TkAgg' si se quiere ver en pantalla
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# Forzar UTF-8 en stdout/stderr (Windows console cp1252)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ══════════════════════════════════════════════════════════════════════════════
# Resolución de rutas — funciona desde cualquier directorio
# ══════════════════════════════════════════════════════════════════════════════
_SCRIPT_DIR = Path(__file__).resolve().parent
# El script vive en notebooks/; la raíz es su padre
_PROJECT_ROOT = _SCRIPT_DIR.parent if (_SCRIPT_DIR / '..' / 'src').resolve().exists() else _SCRIPT_DIR
sys.path.insert(0, str(_PROJECT_ROOT))

from src.utils import test_estacionariedad, test_causalidad_granger, resumen_estadistico

# Directorios de datos
VARS_DIR = (_PROJECT_ROOT / 'data' / 'Variables Finales').resolve()
RAW_DIR  = (_PROJECT_ROOT / 'data' / 'raw').resolve()
NOTEBOOKS_DIR = (_PROJECT_ROOT / 'notebooks').resolve()
OUTPUT_DIR = _PROJECT_ROOT / 'outputs' / 'analisis_basico'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = OUTPUT_DIR / 'cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ── Caché en disco por sección ────────────────────────────────────────────────
def _cache_path(name: str) -> Path:
    return CACHE_DIR / f'{name}.pkl'


def _cache_load(name: str):
    import pickle
    p = _cache_path(name)
    if not p.exists():
        return None
    try:
        with open(p, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f'  ⚠️ Cache "{name}" corrupto, ignorado: {e}')
        return None


def _cache_save(name: str, obj) -> None:
    import pickle
    try:
        with open(_cache_path(name), 'wb') as f:
            pickle.dump(obj, f)
        print(f'  💾 Cache guardado: {name}.pkl')
    except Exception as e:
        print(f'  ⚠️ No se pudo cachear "{name}": {e}')


def _cache_invalidate(names) -> None:
    for n in names:
        p = _cache_path(n)
        if p.exists():
            p.unlink()
            print(f'  🗑️  Cache invalidado: {n}.pkl')


def _print_header(seccion: str, titulo: str):
    """Imprime un encabezado de sección visual."""
    print(f'\n{"="*70}')
    print(f'  SECCIÓN {seccion}: {titulo}')
    print(f'{"="*70}\n')


def _save_fig(fig, nombre: str):
    """Guarda figura en OUTPUT_DIR y cierra."""
    path = OUTPUT_DIR / f'{nombre}.png'
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  📊 Gráfico guardado: {path.name}')


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2: FUNCIONES AUXILIARES
# ══════════════════════════════════════════════════════════════════════════════

def _parse_catalog():
    """Parsea CATALOG desde visualizador_template.html."""
    for _cand in [_PROJECT_ROOT / 'visualizador_template.html',
                  NOTEBOOKS_DIR / 'visualizador_template.html']:
        if _cand.exists():
            html_path = _cand
            break
    else:
        raise FileNotFoundError('No se encontró visualizador_template.html')

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    _start = content.find('const CATALOG = [')
    _end   = content.find('\n];', _start)
    catalog_txt = content[_start:_end + 3] if _start >= 0 and _end >= 0 else content

    cat = {}
    _PREF    = {'D': 0, 'W': 1, 'M': 2, 'Q': 3, 'A': 4}
    _FREQ_RE = re.compile(r"freq\s*:\s*'([^']+)'")

    _SINGLE = re.compile(
        r"id\s*:\s*'([^']+)'.*?label\s*:\s*'([^']+)'.*?"
        r"file\s*:\s*'([^']+)'.*?dateCol\s*:\s*'([^']+)'.*?valCol\s*:\s*'([^']+)'"
    )
    for line in catalog_txt.splitlines():
        m = _SINGLE.search(line)
        if not m:
            continue
        cid, label, file_, dc, vc = m.groups()
        if label in cat:
            continue
        fm = _FREQ_RE.search(line)
        freq = fm.group(1) if fm else 'D'
        cat[label] = {'id': cid, 'file': file_, 'dateCol': dc, 'valCol': vc, 'freq': freq}

    _MULTI = re.compile(
        r"\{\s*id\s*:\s*'([^']+)'\s*,\s*label\s*:\s*'([^']+)'[^[]*?"
        r"sources\s*:\s*\[(.*?)\]",
        re.DOTALL
    )
    _SRC = re.compile(
        r"\{\s*freq\s*:\s*'([^']+)'[^}]*?"
        r"file\s*:\s*'([^']+)'[^}]*?"
        r"dateCol\s*:\s*'([^']+)'[^}]*?"
        r"valCol\s*:\s*'([^']+)'"
    )
    for m in _MULTI.finditer(catalog_txt):
        cid, label, srcs_txt = m.groups()
        if label in cat:
            continue
        srcs = [{'freq': sm.group(1), 'file': sm.group(2),
                 'dateCol': sm.group(3), 'valCol': sm.group(4)}
                for sm in _SRC.finditer(srcs_txt)]
        if not srcs:
            continue
        best = sorted(srcs, key=lambda s: _PREF.get(s['freq'], 99))[0]
        cat[label] = {
            'id': cid, 'file': best['file'], 'dateCol': best['dateCol'],
            'valCol': best['valCol'], 'freq': best['freq'], 'sources': srcs,
        }

    return cat


def detectar_frecuencia(df_csv, catalog):
    """Detecta la frecuencia más gruesa entre todas las series del CSV."""
    _ORD = {'D': 0, 'W': 1, 'M': 2, 'Q': 3, 'A': 4}
    finest = []
    for _, row in df_csv.iterrows():
        for col in ['Serie A', 'Serie B']:
            nombre = str(row.get(col, '') or '').strip()
            if not nombre or nombre in ('', '—', '-', 'nan'):
                continue
            if nombre not in catalog:
                continue
            meta = catalog[nombre]
            if 'sources' in meta:
                src_freqs = [s['freq'] for s in meta['sources']]
                finest.append(min(src_freqs, key=lambda f: _ORD.get(f, 99)))
            else:
                finest.append(meta.get('freq', 'D'))
    if not finest:
        return 'M'
    return max(finest, key=lambda f: _ORD.get(f, -1))


def _resample_mean(serie: pd.Series, to_freq: str) -> pd.Series:
    _MAP = {'D': 'D', 'W': 'W', 'M': 'ME', 'Q': 'QE', 'A': 'YE'}
    pf = _MAP.get(to_freq, to_freq)
    try:
        return serie.resample(pf).mean()
    except ValueError:
        _MAP_OLD = {'D': 'D', 'W': 'W', 'M': 'M', 'Q': 'Q', 'A': 'A'}
        return serie.resample(_MAP_OLD.get(to_freq, to_freq)).mean()


def _buscar_archivo(*rutas_relativas):
    for ruta in rutas_relativas:
        for base in [VARS_DIR, RAW_DIR]:
            p = base / ruta
            if p.exists():
                return p
    return None


def _match_col(wanted: str, available_cols) -> str | None:
    ws = wanted.strip()
    if ws in available_cols:
        return ws
    if wanted in available_cols:
        return wanted
    return None


def _leer_serie_csv(path: Path, col_fecha: str, col_valor: str) -> pd.Series:
    df = pd.read_csv(path, low_memory=False, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    dc = _match_col(col_fecha, df.columns)
    vc = _match_col(col_valor, df.columns)
    if dc is None:
        raise KeyError(f'col_fecha "{col_fecha}" no encontrada en {path.name}. Cols: {list(df.columns[:8])}')
    if vc is None:
        raise KeyError(f'col_valor "{col_valor}" no encontrada en {path.name}. Cols: {list(df.columns[:8])}')
    df['_f'] = pd.to_datetime(df[dc], errors='coerce')
    df = df.dropna(subset=['_f']).set_index('_f').sort_index()
    return pd.to_numeric(df[vc], errors='coerce').dropna()


# ── Deflactores ──────────────────────────────────────────────────────────────
_cache_deflactores = {}

def _get_deflactor(nombre: str):
    """Carga y cachea deflactores (PBI, CER, TIP, MEP)."""
    if nombre in _cache_deflactores:
        return _cache_deflactores[nombre]

    _config = {
        'PBI': ('pbi_constante_2004.csv', 'fecha', 'pbi'),
        'CER': ('cer.csv', 'fecha', 'cer'),
        'TIP': ('tip_etf.csv', 'fecha', 'tip_close'),
        'MEP': ('brecha_cambiaria.csv', 'fecha', 'mep'),
    }
    alt_files = {
        'CER': ('bcra/cer.csv',),
        'TIP': ('global/tip_etf.csv',),
    }

    if nombre not in _config:
        print(f'    ⚠️  Deflactor no reconocido: "{nombre}"')
        return None

    main_file, date_col, val_col = _config[nombre]
    alts = alt_files.get(nombre, ())
    p = _buscar_archivo(main_file, *alts)
    if p is None:
        print(f'  ⚠️  {main_file} no encontrado')
        return None

    serie = _leer_serie_csv(p, date_col, val_col)
    _cache_deflactores[nombre] = serie
    return serie


def _alinear_deflactor(raw: pd.Series, frecuencia: str,
                       target_index: pd.DatetimeIndex) -> pd.Series | None:
    al = _resample_mean(raw, frecuencia)
    al = al.reindex(target_index, method='ffill').ffill().bfill()
    if al.isna().all():
        return None
    return al


def _aplicar_deflactor(serie: pd.Series, deflactor_name: str, frecuencia: str) -> pd.Series:
    if not deflactor_name or str(deflactor_name).strip() in ('', '—', '-', 'nan'):
        return serie
    for d in str(deflactor_name).split(','):
        d = d.strip().upper()
        if not d or d in ('—', '-'):
            continue

        raw = _get_deflactor(d if d != 'IPC' else 'TIP')
        if raw is None:
            continue
        al = _alinear_deflactor(raw, frecuencia, serie.index)
        if al is None:
            print(f'  ⚠️  {d}: sin superposición de fechas con la serie')
            continue

        if d == 'PBI':
            fp = al.iloc[0]
            serie = serie * fp / al
        elif d == 'CER':
            lc = al.iloc[-1]
            serie = serie / al * lc
        elif d in ('TIP', 'IPC'):
            lt = al.iloc[-1]
            serie = serie / al * lt
        elif d == 'MEP':
            serie = serie / al
    return serie


def _cargar_serie_catalog(label: str, frecuencia: str, catalog: dict,
                          fecha_inicio: str = None, fecha_fin: str = None):
    """Carga la serie `label` desde CATALOG en la frecuencia indicada."""
    if label not in catalog:
        print(f'  ⚠️  "{label}" no encontrado en CATALOG ({len(catalog)} series).')
        return None

    meta  = catalog[label]
    _PREF = {'D': 0, 'W': 1, 'M': 2, 'Q': 3, 'A': 4}

    if 'sources' in meta:
        srcs  = meta['sources']
        exact = [s for s in srcs if s['freq'] == frecuencia]
        src   = exact[0] if exact else sorted(srcs, key=lambda s: _PREF.get(s['freq'], 99))[0]
        file_, dc, vc = src['file'], src['dateCol'], src['valCol']
    else:
        file_, dc, vc = meta['file'], meta['dateCol'], meta['valCol']

    file_path = VARS_DIR / file_
    if not file_path.exists():
        file_path_raw = RAW_DIR / file_
        if file_path_raw.exists():
            file_path = file_path_raw
        else:
            print(f'  ⚠️  Archivo no encontrado: {VARS_DIR / file_}')
            return None

    try:
        if str(file_).endswith(('.xlsx', '.xls')):
            sheet = 'Unificado' if 'fiscal' in str(file_).lower() else 0
            df = pd.read_excel(file_path, sheet_name=sheet)
        else:
            df = pd.read_csv(file_path, low_memory=False, encoding='utf-8-sig')
    except Exception as e:
        print(f'  ⚠️  Error leyendo {file_}: {e}')
        return None

    df.columns = df.columns.str.strip()
    dc_match = _match_col(dc, df.columns)
    vc_match = _match_col(vc, df.columns)
    if dc_match is None:
        print(f'  ⚠️  dateCol "{dc}" no hallada en {file_}. Cols: {list(df.columns[:8])}')
        return None
    if vc_match is None:
        print(f'  ⚠️  valCol "{vc}" no hallada en {file_}. Cols: {list(df.columns[:8])}')
        return None

    df['_f'] = pd.to_datetime(df[dc_match], errors='coerce')
    df = df.dropna(subset=['_f']).set_index('_f').sort_index()
    serie = pd.to_numeric(df[vc_match], errors='coerce').dropna()
    serie.name = label

    if fecha_inicio:
        serie = serie[serie.index >= pd.Timestamp(fecha_inicio)]
    if fecha_fin:
        serie = serie[serie.index <= pd.Timestamp(fecha_fin)]

    return _resample_mean(serie, frecuencia).dropna()


def construir_variable(row: pd.Series, frecuencia: str,
                       fecha_inicio: str, fecha_fin: str, catalog: dict):
    """Interpreta una fila del CSV de análisis y devuelve (serie, etiqueta)."""
    nombre_a  = str(row.get('Serie A',   '') or '').strip()
    defl_a    = str(row.get('Deflactor A','') or '').strip()
    nombre_b  = str(row.get('Serie B',   '') or '').strip()
    defl_b    = str(row.get('Deflactor B','') or '').strip()
    operacion = str(row.get('Operación', 'Solo A') or 'Solo A').strip()
    log_flag  = str(row.get('Log', 'No') or 'No').strip().lower() not in ('no', '0', 'false', '')
    n_diff    = int(float(str(row.get('Dif.', 0) or 0) or 0))

    _b_activo  = operacion != 'Solo A' and nombre_b not in ('', '—', '-', 'nan')
    _da_activo = defl_a not in ('', '—', '-', 'nan')
    _db_activo = _b_activo and defl_b not in ('', '—', '-', 'nan')

    etiqueta = nombre_a
    if _da_activo:    etiqueta += f'/{defl_a}'
    if _b_activo:     etiqueta += f' {operacion} {nombre_b}'
    if _db_activo:    etiqueta += f'/{defl_b}'
    if log_flag:      etiqueta  = f'log({etiqueta})'
    if n_diff > 0:    etiqueta  = ('Δ' * n_diff) + etiqueta

    sa = _cargar_serie_catalog(nombre_a, frecuencia, catalog, fecha_inicio, fecha_fin)
    if sa is None:
        return None, etiqueta

    sa = _aplicar_deflactor(sa, defl_a, frecuencia)
    resultado = sa.copy()

    if _b_activo:
        sb = _cargar_serie_catalog(nombre_b, frecuencia, catalog, fecha_inicio, fecha_fin)
        if sb is not None:
            sb    = _aplicar_deflactor(sb, defl_b, frecuencia)
            sb_al = sb.reindex(sa.index, method='ffill')
            op = operacion.replace(' ', '').replace('−', '-')
            if op == 'A-B':                      resultado = sa - sb_al
            elif op in ('A/B', 'A÷B'):            resultado = sa / sb_al
            elif op in ('(A-B)/B',):              resultado = (sa - sb_al) / sb_al
            elif op == 'A+B':                     resultado = sa + sb_al
            elif op in ('A*B', 'A×B'):             resultado = sa * sb_al
            elif op in ('SoloB', 'B'):             resultado = sb_al.copy()

    if log_flag:
        resultado = np.log(resultado.replace(0, np.nan))
    for _ in range(n_diff):
        resultado = resultado.diff()

    resultado = resultado.dropna()
    resultado.name = etiqueta
    return resultado, etiqueta


def _validar_catalog_vs_csv(df_csv, catalog):
    print('\n── Validación CATALOG vs CSV ────────────────────────────────────────')
    seen = set()
    for _, row in df_csv.iterrows():
        for col in ['Serie A', 'Serie B']:
            nombre = str(row.get(col, '') or '').strip()
            if not nombre or nombre in ('', '—', '-', 'nan') or nombre in seen:
                continue
            seen.add(nombre)
            if nombre not in catalog:
                print(f'  ❌ NO en CATALOG: "{nombre}"')
                continue
            meta      = catalog[nombre]
            file_name = meta.get('file', '?')
            existe    = (VARS_DIR / file_name).exists() or (RAW_DIR / file_name).exists()
            print(f'  {"✅" if existe else "⚠️ "} {nombre[:55]:<55} → {file_name}'
                  f'{"" if existe else "  (¡FALTA ARCHIVO!)"}')
    print('────────────────────────────────────────────────────────────────────\n')



# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE ESTIMACIÓN (Sección 7.1.1)
# ══════════════════════════════════════════════════════════════════════════════

def _hqic(llf, k, n):
    return -2 * llf + 2 * k * np.log(np.log(max(n, 3)))


def extraer_ardl(df_m, y_var, x_vars, max_lags_dep, max_lags_ind, criterio,
                 df_dummy=None, bj_proposed_lags=None, bj_ar_y=1):
    """Estima un modelo ARDL y extrae coeficientes de corto y largo plazo."""
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

    # ── Coeficientes de dummies (exógenas) ───────────────────────────────────
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


def extraer_var(df_m, y_var, x_vars, todas_vars, max_lags, criterio):
    """Estima un modelo VAR y extrae coeficientes para la ecuación Y."""
    from statsmodels.tsa.api import VAR

    data    = df_m[todas_vars].dropna()
    model   = VAR(data)
    lag_sel = model.select_order(maxlags=max_lags)
    k_ar    = max(1, lag_sel.selected_orders.get(criterio, 1))
    res     = model.fit(k_ar)

    aic = float(res.aic)
    bic = float(res.bic)
    hq  = float(res.hqic)

    _y_pos   = list(todas_vars).index(y_var)
    _y_resid = res.resid[:, _y_pos]
    _y_act   = data[y_var].values[-len(_y_resid):]
    _ss_res  = float(np.sum(_y_resid ** 2))
    _ss_tot  = float(np.sum((_y_act - _y_act.mean()) ** 2))
    r2 = float(1 - _ss_res / _ss_tot) if _ss_tot > 0 else np.nan

    params_df = res.params
    pvals_df  = res.pvalues
    k_endog   = len(todas_vars)
    var_pos   = {v: i for i, v in enumerate(todas_vars)}

    coefs = {}
    if y_var in params_df.columns:
        yp = params_df[y_var]
        yv = pvals_df[y_var]
        for x in x_vars:
            xpos = var_pos.get(x)
            if xpos is None:
                coefs[x] = {'coef': np.nan, 'pval': np.nan}
                continue
            idx = [lag * k_endog + xpos for lag in range(k_ar)
                   if lag * k_endog + xpos < len(yp)]
            coefs[x] = ({'coef': float(yp.iloc[idx].sum()),
                         'pval': float(yv.iloc[idx].min())}
                        if idx else {'coef': np.nan, 'pval': np.nan})
    else:
        for x in x_vars:
            coefs[x] = {'coef': np.nan, 'pval': np.nan}

    return {'aic': aic, 'bic': bic, 'hq': hq, 'r2': r2,
            'coefs': coefs, 'k_ar': k_ar, 'nobs': int(res.nobs)}


def extraer_vecm(df_m, y_var, x_vars, todas_vars, k_ar_diff, det_order,
                 df_dummy=None, dummy_names=None):
    """Estima un modelo VECM con test de Johansen y extrae alpha/gamma/beta."""
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
    # En statsmodels el atributo es `stderr_gamma` (no `gamma_se`)
    gamma_se = getattr(res, 'stderr_gamma', None)
    # En statsmodels VECM, gamma tiene shape (neqs, neqs * k_ar_diff).
    # Cada bloque de columnas corresponde a un lag de las diferencias.
    n_short  = k_ar_diff

    # Alpha
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

    # Gamma
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

    # ── BETA: relación de cointegración (largo plazo) ────────────────────────
    beta_coefs = {x: {'coef': float('nan'), 'pval': float('nan')} for x in x_vars}
    try:
        beta_mat = np.asarray(res.beta)  # (k + det_terms, n_ci)
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
                    # Delta-method: Var(theta) = (1/y_b)^2 * Var(b_x) + (b_x/y_b^2)^2 * Var(b_y)
                    var_t = (_se_raw_x / abs(y_b))**2 + (theta * _se_raw_y / abs(y_b))**2
                    se_t  = float(np.sqrt(max(var_t, 0.0)))
                    if se_t > 0:
                        z = theta / se_t
                        pv = float(t_dist.sf(abs(z), df=max(1, res.nobs - k_vars)) * 2)
                except Exception:
                    pass
            beta_coefs[x] = {'coef': theta, 'pval': pv}

    # ── Coeficientes de variables EXÓGENAS (dummies) ─────────────────────────
    # En statsmodels VECM las exógenas pasadas por `exog=` quedan en `det_coef`
    # con shape (k_endog, n_exog). El p-val ya viene en `pvalues_det_coef`.
    dummy_coefs = {}
    if dummy_names and _exog_cols:
        try:
            det_mat = np.asarray(getattr(res, 'det_coef', np.array([])))
            det_pv  = np.asarray(getattr(res, 'pvalues_det_coef', np.array([])))
            if det_mat.size and det_mat.shape == (k_vars, len(_exog_cols)):
                for _d in dummy_names:
                    if _d in _exog_cols:
                        _di = _exog_cols.index(_d)
                        _c  = float(det_mat[y_idx, _di])
                        _p  = (float(det_pv[y_idx, _di])
                               if det_pv.size and det_pv.shape == det_mat.shape
                               else float('nan'))
                        dummy_coefs[_d] = {'coef': _c, 'pval': _p}
        except Exception:
            pass
        for _d in dummy_names:
            dummy_coefs.setdefault(_d, {'coef': float('nan'), 'pval': float('nan')})

    return {'aic': aic, 'bic': bic, 'hq': hq, 'r2': r2,
            'coefs': coefs,
            'alpha_coef': alpha_coef, 'alpha_pval': alpha_pval,
            'gamma_coefs': gamma_coefs,
            'beta_coefs': beta_coefs,
            'dummy_coefs': dummy_coefs,
            'n_coint': n_ci, 'nobs': int(res.nobs),
            'resid_y': _y_resid_v}



# ══════════════════════════════════════════════════════════════════════════════
# SECCIONES EJECUTABLES
# ══════════════════════════════════════════════════════════════════════════════

def seccion_3_configuracion():
    """Sección 3: Configuración del análisis."""
    _print_header('3', 'CONFIGURACIÓN')

    config = {
        'CSV_ANALISIS': None,
        'FRECUENCIA': 'auto',
        'FECHA_INICIO': '2007-01-01',
        'FECHA_FIN': '2026-03-31',
        'MAX_LAGS_DEP': 4,
        'MAX_LAGS_IND': 4,
        'MAX_LAGS_VAR': 12,
        'MAX_VARS_POR_MODELO': None,
        'MAX_COMBINACIONES': None,
        'SEMILLA': 42,
        'CRITERIOS_SEL': ['aic', 'bic', 'hqic'],
        'NIVEL_SIG': 0.05,
    }

    for k, v in config.items():
        print(f'  {k:<25} = {v}')

    print('\n✅ Configuración cargada.')
    return config


def seccion_4_carga_panel(config, catalog):
    """Sección 4: Carga y construcción del panel de datos."""
    _print_header('4', 'CARGA Y CONSTRUCCIÓN DEL PANEL')

    random.seed(config['SEMILLA'])
    np.random.seed(config['SEMILLA'])

    # 1. Encontrar CSV
    _csv_dir = NOTEBOOKS_DIR / 'Variables Regresivas'
    if config['CSV_ANALISIS']:
        _csv_path = _csv_dir / config['CSV_ANALISIS']
    else:
        _candidates = sorted(glob.glob(str(_csv_dir / 'analisis_series_*.csv')))
        if not _candidates:
            raise FileNotFoundError(f'No encontré analisis_series_*.csv en {_csv_dir}')
        _csv_path = Path(_candidates[-1])

    print(f'📁 CSV: {_csv_path.name}')

    # 2. Leer CSV
    df_csv = pd.read_csv(_csv_path)
    df_csv.columns = df_csv.columns.str.strip()
    for _c in ['Deflactor A', 'Deflactor B', 'Serie B', 'Operación', 'Log', 'Dependiente']:
        if _c in df_csv.columns:
            df_csv[_c] = df_csv[_c].fillna('—').astype(str).str.strip()
    if 'Dif.' in df_csv.columns:
        df_csv['Dif.'] = (pd.to_numeric(
            df_csv['Dif.'].astype(str).str.extract(r'(\d+)')[0], errors='coerce'
        ).fillna(0).astype(int))

    print(f'   {len(df_csv)} variables en el CSV')
    print(df_csv[['#','Serie A','Deflactor A','Serie B','Operación','Log','Dif.']].to_string())

    # 3. Validar
    _validar_catalog_vs_csv(df_csv, catalog)

    # 4. Detectar frecuencia
    FRECUENCIA = config['FRECUENCIA']
    if FRECUENCIA == 'auto':
        FRECUENCIA_USADA = detectar_frecuencia(df_csv, catalog)
        print(f'🔍 Frecuencia auto-detectada: {FRECUENCIA_USADA}')
    else:
        FRECUENCIA_USADA = FRECUENCIA
        print(f'📅 Frecuencia configurada: {FRECUENCIA_USADA}')

    # 5. Construir series
    FECHA_INICIO = config['FECHA_INICIO']
    FECHA_FIN = config['FECHA_FIN']
    print(f'\n⏳ Cargando series ({FECHA_INICIO} → {FECHA_FIN})...')

    _series  = {}
    _eti_map = {}
    _FREQ_ORD = {'D': 0, 'W': 1, 'M': 2, 'Q': 3, 'A': 4}
    _MAX_FREQ = 2  # M = máxima frecuencia aceptada

    for _i, _row in df_csv.iterrows():
        try:
            _desde = str(_row.get('Desde', '') or '').strip()
            _hasta = str(_row.get('Hasta', '') or '').strip()
            _fi = _desde if _desde and _desde not in ('—', '-', 'nan') else FECHA_INICIO
            _ff = _hasta if _hasta and _hasta not in ('—', '-', 'nan') else FECHA_FIN

            _nombre_a = str(_row.get('Serie A', '') or '').strip()
            _nombre_b = str(_row.get('Serie B', '') or '').strip()
            _skip_freq = False
            for _sname in [_nombre_a, _nombre_b]:
                if not _sname or _sname in ('', '—', '-', 'nan'):
                    continue
                if _sname in catalog:
                    _meta_f = catalog[_sname]
                    _freq_native = _meta_f.get('freq', 'D')
                    if 'sources' in _meta_f:
                        _freq_native = min(
                            [s['freq'] for s in _meta_f['sources']],
                            key=lambda f: _FREQ_ORD.get(f, 99)
                        )
                    if _FREQ_ORD.get(_freq_native, 0) > _MAX_FREQ:
                        print(f'  ⏭️ [{_i+1}] {_sname}: freq={_freq_native} > mensual → descartada')
                        _skip_freq = True
                        break
            if _skip_freq:
                continue

            _s, _eti = construir_variable(_row, FRECUENCIA_USADA, _fi, _ff, catalog)
            if _s is not None and len(_s) >= 20:
                _series[_eti] = _s
                _eti_map[_i]  = _eti
                print(f'  ✅ [{_i+1}] {_eti[:75]}  →  {len(_s)} obs')
            else:
                print(f'  ❌ [{_i+1}] {_row["Serie A"]}: no cargó o < 20 obs')
        except Exception as _e:
            print(f'  ❌ [{_i+1}] {_row["Serie A"]}: {_e}')

    if not _series:
        raise RuntimeError('No se cargó ninguna serie.')

    # 6. Panel unificado
    df_panel = pd.concat(list(_series.values()), axis=1).dropna()
    print(f'\n✅ Panel: {df_panel.shape[0]} obs × {df_panel.shape[1]} vars')
    print(f'   Período: {df_panel.index.min().date()} → {df_panel.index.max().date()}')

    _LISTA_SERIES = list(df_panel.columns)
    print(f'\n{"═"*70}')
    print('  Series disponibles:')
    print('═'*70)
    for _n, _col in enumerate(_LISTA_SERIES, 1):
        print(f'  [{_n}]  {_col}')
    print('═'*70)

    # Etiquetas marcadas como dependiente (columna `Dependiente` del CSV)
    _DEP_LABELS = set()
    if 'Dependiente' in df_csv.columns:
        for _i, _row in df_csv.iterrows():
            _flag = str(_row.get('Dependiente', '') or '').strip().lower()
            if _flag in ('sí', 'si', 'yes', 'true', '1', 'x', 's'):
                _eti = _eti_map.get(_i)
                if _eti:
                    _DEP_LABELS.add(_eti)
        if _DEP_LABELS:
            print(f'🎯 Variable(s) marcadas como Dependiente en CSV: {sorted(_DEP_LABELS)}')

    return df_panel, df_csv, _LISTA_SERIES, FRECUENCIA_USADA, _DEP_LABELS


def seccion_45_seleccion_dependiente(df_panel, _LISTA_SERIES, FRECUENCIA_USADA, config, dep_labels=None):
    """Sección 4.5: Seleccionar variable dependiente.

    Prioridad: (1) etiquetas marcadas como `Dependiente=Sí` en el CSV;
              (2) keywords (embi, riesgo, spread, cds, country risk);
              (3) primera serie del panel.
    """
    _print_header('4.5', 'SELECCIÓN DE VARIABLE DEPENDIENTE')

    VARIABLE_DEPENDIENTE = None
    if dep_labels:
        for _i, _c in enumerate(_LISTA_SERIES, 1):
            if _c in dep_labels:
                VARIABLE_DEPENDIENTE = _i
                print(f'  ✅ Dependiente desde CSV (columna `Dependiente`): {_c}')
                break

    if VARIABLE_DEPENDIENTE is None:
        _KEYWORDS_DEP = ['embi', 'riesgo', 'spread', 'cds', 'country risk']
        VARIABLE_DEPENDIENTE = next(
            (i + 1 for i, c in enumerate(_LISTA_SERIES)
             if any(kw in c.lower() for kw in _KEYWORDS_DEP)),
            1
        )

    print('═' * 65)
    for _i, _c in enumerate(_LISTA_SERIES, 1):
        marca = '  ◄ seleccionada' if _i == VARIABLE_DEPENDIENTE else ''
        print(f'  [{_i:>2}]  {_c}{marca}')
    print('═' * 65)

    ETI_DEP  = _LISTA_SERIES[VARIABLE_DEPENDIENTE - 1]
    ETI_EXPL = [c for c in _LISTA_SERIES if c != ETI_DEP]

    _all_cols = [ETI_DEP] + ETI_EXPL
    COL_SAFE  = {c: f'v{i:02d}' for i, c in enumerate(_all_cols)}
    COL_LABEL = {v: k for k, v in COL_SAFE.items()}
    df_safe   = df_panel[_all_cols].rename(columns=COL_SAFE)
    Y_SAFE    = COL_SAFE[ETI_DEP]
    X_SAFE    = [COL_SAFE[e] for e in ETI_EXPL]

    print(f'\n✅ Y = {ETI_DEP}')
    print(f'   {len(ETI_EXPL)} variables explicativas')

    # Dummies
    _DUMMY_LABEL_PREFIX = 'Dummy_'
    _dummy_etis = [e for e in ETI_EXPL if e.startswith(_DUMMY_LABEL_PREFIX)]
    DUMMY_SAFE  = [COL_SAFE[e] for e in _dummy_etis]

    if DUMMY_SAFE:
        df_exog_dummy = df_safe[DUMMY_SAFE].fillna(0).astype(float)
        print(f'\n🔒 {len(DUMMY_SAFE)} variable(s) dummy aisladas como exógenas estrictas:')
        for _e in _dummy_etis:
            print(f'   {_e}  →  {COL_SAFE[_e]}')
    else:
        df_exog_dummy = pd.DataFrame(index=df_safe.index)
        print('ℹ️  Sin variables Dummy_ en el CSV → df_exog_dummy vacío.')

    # MAX_LAGS dinámico — cap metodológico: 3 lags si mensual, 2 si trimestral
    _T_obs  = df_safe.shape[0]
    _K_vars = len(X_SAFE) + 1
    _K_x    = len(X_SAFE)
    _FREQ_LAG_CAP = {'D': 182, 'W': 25, 'M': 6, 'Q': 2, 'A': 1}
    _freq_cap = _FREQ_LAG_CAP.get(FRECUENCIA_USADA, 3)
    _dof_var = int((_T_obs - 1) / (_K_vars + 1))
    _dof_ard = int((_T_obs - 1) / (_K_x + 2))

    MAX_LAGS_VAR = max(1, min(_freq_cap, _dof_var))
    MAX_LAGS_DEP = max(1, min(_freq_cap, _dof_ard))
    MAX_LAGS_IND = max(1, min(_freq_cap, _dof_ard))
    LAG_CAP_FREQ = _freq_cap  # tope metodológico para iteración explícita

    print(f'\n📐 MAX_LAGS (T={_T_obs}, K={_K_vars}, freq={FRECUENCIA_USADA}):')
    print(f'   freq_cap={_freq_cap}  |  dof_var={_dof_var}  dof_ardl={_dof_ard}')
    print(f'   MAX_LAGS_VAR = {MAX_LAGS_VAR}')
    print(f'   MAX_LAGS_DEP = {MAX_LAGS_DEP}')
    print(f'   MAX_LAGS_IND = {MAX_LAGS_IND}')

    return {
        'df_safe': df_safe, 'Y_SAFE': Y_SAFE, 'X_SAFE': X_SAFE,
        'COL_SAFE': COL_SAFE, 'COL_LABEL': COL_LABEL,
        'ETI_DEP': ETI_DEP, 'ETI_EXPL': ETI_EXPL,
        'DUMMY_SAFE': DUMMY_SAFE, 'df_exog_dummy': df_exog_dummy,
        'MAX_LAGS_VAR': MAX_LAGS_VAR, 'MAX_LAGS_DEP': MAX_LAGS_DEP,
        'MAX_LAGS_IND': MAX_LAGS_IND, 'LAG_CAP_FREQ': LAG_CAP_FREQ,
        'FRECUENCIA_USADA': FRECUENCIA_USADA,
    }


def seccion_5_descriptivos(df_panel, ETI_DEP):
    """Sección 5: Estadísticos descriptivos."""
    _print_header('5', 'ESTADÍSTICOS DESCRIPTIVOS')

    print(resumen_estadistico(df_panel).round(4).to_string())

    n_series = len(df_panel.columns)
    fig, axes = plt.subplots(n_series, 1, figsize=(12, 3 * n_series), sharex=True, squeeze=False)
    for i, col in enumerate(df_panel.columns):
        color = '#d62728' if col == ETI_DEP else '#1f77b4'
        axes[i][0].plot(df_panel.index, df_panel[col], color=color, linewidth=1.2)
        axes[i][0].set_title(col, fontsize=9)
    fig.suptitle('Series del panel  (rojo = variable dependiente)', fontsize=11)
    plt.tight_layout()
    _save_fig(fig, 'sec05_series_panel')


def seccion_6_estacionariedad(df_panel, ctx):
    """Sección 6: Tests de estacionariedad (ADF + KPSS)."""
    _print_header('6', 'TESTS DE ESTACIONARIEDAD (ADF + KPSS)')

    df_safe = ctx['df_safe']
    COL_SAFE = ctx['COL_SAFE']
    COL_LABEL = ctx['COL_LABEL']
    Y_SAFE = ctx['Y_SAFE']
    X_SAFE = ctx['X_SAFE']
    DUMMY_SAFE = ctx['DUMMY_SAFE']
    ETI_DEP = ctx['ETI_DEP']

    # Tests en niveles
    print('-- Tests en NIVELES --')
    _est_rows_niv = []
    for _col in df_panel.columns:
        _r = test_estacionariedad(df_panel[_col], _col)
        _est_rows_niv.append(_r)
    df_est_niv = pd.DataFrame(_est_rows_niv).set_index('Variable')
    print(df_est_niv[['ADF_stat','ADF_pvalue','ADF_estacionaria',
                      'KPSS_stat','KPSS_pvalue','KPSS_estacionaria']].to_string())

    def _es_estacionaria(row):
        adf_ok  = bool(row.get('ADF_estacionaria', False))
        kpss_ok = row.get('KPSS_estacionaria', None)
        if kpss_ok is None:
            return adf_ok
        return adf_ok and bool(kpss_ok)

    _niv_stat = {r['Variable']: _es_estacionaria(r) for r in _est_rows_niv}

    # Tests en primera diferencia
    print('\n-- Tests en PRIMERA DIFERENCIA --')
    df_panel_diff = df_panel.diff().dropna()
    _est_rows_dif = {}
    for _col in df_panel.columns:
        _r = test_estacionariedad(df_panel_diff[_col], _col)
        _est_rows_dif[_col] = _r
    df_est_dif = pd.DataFrame([_est_rows_dif[c] for c in df_panel.columns]).set_index('Variable')
    print(df_est_dif[['ADF_stat','ADF_pvalue','ADF_estacionaria',
                      'KPSS_stat','KPSS_pvalue','KPSS_estacionaria']].to_string())

    _dif_stat = {_col: _es_estacionaria(_est_rows_dif[_col]) for _col in df_panel.columns}

    # Resumen integrado
    print('\n-- Resumen integrado (nivel y diferencia) --')
    _resumen_rows = []
    for _label in df_panel.columns:
        _safe   = COL_SAFE.get(_label, _label)
        _niv_ok = _niv_stat.get(_label, False)
        _dif_ok = _dif_stat.get(_label, False)
        _orden  = 0 if _niv_ok else (1 if _dif_ok else 2)
        _resumen_rows.append({
            'Variable': _label, 'Safe': _safe,
            'Nivel OK': 'SI' if _niv_ok else 'NO',
            'Diff OK': 'SI' if _dif_ok else 'NO',
            'Orden': f'I({_orden})',
            'ARDL/VAR': 'nivel' if _niv_ok else ('diff' if _dif_ok else 'descartar'),
            'VECM': 'niveles' if _orden == 1 else ('I(0)-solo ARDL/VAR' if _orden == 0 else 'I(2)+-no aplica'),
        })
    df_resumen_est = pd.DataFrame(_resumen_rows)
    print(df_resumen_est.set_index('Variable').to_string())

    # INFO_ESTACIONARIEDAD
    INFO_ESTACIONARIEDAD = {}
    for _row in _resumen_rows:
        _s = _row['Safe']
        _orden = int(_row['Orden'][2])
        INFO_ESTACIONARIEDAD[_s] = {
            'label': _row['Variable'],
            'nivel_estacionaria': _row['Nivel OK'] == 'SI',
            'diff_estacionaria': _row['Diff OK'] == 'SI',
            'orden': _orden,
        }

    # df_safe_est
    df_safe_est = df_safe.copy()
    for _s, _info in INFO_ESTACIONARIEDAD.items():
        if _s in df_safe_est.columns and _info['orden'] >= 1:
            df_safe_est[_s] = df_safe[_s].diff()

    # Conjuntos de variables
    X_SAFE_EST = [v for v in X_SAFE
                  if INFO_ESTACIONARIEDAD.get(v, {}).get('orden', 2) <= 1
                  and v not in DUMMY_SAFE]
    X_SAFE_I1  = [v for v in X_SAFE
                  if INFO_ESTACIONARIEDAD.get(v, {}).get('orden', 2) == 1
                  and v not in DUMMY_SAFE]
    X_SAFE_I0  = [v for v in X_SAFE
                  if INFO_ESTACIONARIEDAD.get(v, {}).get('orden', 2) == 0
                  and v not in DUMMY_SAFE]
    Y_ORDEN = INFO_ESTACIONARIEDAD.get(Y_SAFE, {}).get('orden', 0)

    print(f'\n{"="*70}')
    print('  RESUMEN DE VARIABLES PARA ESTIMACIÓN')
    print('='*70)
    print(f'Y = {ETI_DEP}  I({Y_ORDEN})  -> ARDL/VAR usa: {"niveles" if Y_ORDEN == 0 else "diff"}')
    print(f'X para ARDL/VAR ({len(X_SAFE_EST)}):')
    for _v in X_SAFE_EST:
        _inf = INFO_ESTACIONARIEDAD[_v]
        print(f'    {COL_LABEL.get(_v, _v)[:55]:<55}  I({_inf["orden"]})')
    print(f'X para VECM en niveles ({len(X_SAFE_I1)}) [solo I(1)]:')
    for _v in X_SAFE_I1:
        print(f'    {COL_LABEL.get(_v, _v)[:55]}')
    if not X_SAFE_I1 or Y_ORDEN != 1:
        print('  Nota: VECM requiere Y I(1) y al menos una X I(1).')
    print('='*70)

    return {
        'df_safe_est': df_safe_est,
        'INFO_ESTACIONARIEDAD': INFO_ESTACIONARIEDAD,
        'X_SAFE_EST': X_SAFE_EST,
        'X_SAFE_I1': X_SAFE_I1,
        'X_SAFE_I0': X_SAFE_I0,
        'Y_ORDEN': Y_ORDEN,
    }



def seccion_7_ardl(ctx, est_ctx, config):
    """Sección 7: Modelos ARDL completos (BJ + estimación + control + diagnóstico)."""
    _print_header('7', 'MODELOS ARDL')

    df_safe = ctx['df_safe']
    df_safe_est = est_ctx['df_safe_est']
    Y_SAFE = ctx['Y_SAFE']
    X_SAFE_EST = est_ctx['X_SAFE_EST']
    COL_LABEL = ctx['COL_LABEL']
    df_exog_dummy = ctx['df_exog_dummy']
    MAX_LAGS_DEP = ctx['MAX_LAGS_DEP']
    MAX_LAGS_IND = ctx['MAX_LAGS_IND']
    NIVEL_SIG = config['NIVEL_SIG']
    SEMILLA = config['SEMILLA']
    CRITERIOS_SEL = config['CRITERIOS_SEL']

    # ── 7.1 Box-Jenkins Prewhitening — DESACTIVADO ───────────────────────────
    # Bloque comentado: no se usa BJ. extraer_ardl cae al fallback con
    # ardl_select_order (selección de lags por criterio de información).
    print('── 7.1 Prewhitening Box-Jenkins: DESACTIVADO (fallback ardl_select_order) ──')
    _BJ_PROPOSED_LAGS = {}   # vacío → _bj_ok = False en extraer_ardl
    _BJ_AR_Y = 1             # valor por defecto (no se usa con BJ desactivado)
    _bj_ccf_store = {}       # vacío → no se genera gráfico CCF

    # --- Código original comentado (Box-Jenkins prewhitening) ----------------
    """
    try:
        from pmdarima import auto_arima as _auto_arima_bj
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pmdarima', '-q'])
        from pmdarima import auto_arima as _auto_arima_bj

    from statsmodels.tsa.stattools import ccf as _ccf_fn_bj
    import statsmodels.api as _sm_bj

    BJ_MAX_LAGS_CCF = 12
    BJ_MAX_AR       = 4
    BJ_Z_CI         = 1.96

    _y_bj = df_safe[Y_SAFE].dropna()
    _bj_ar_y_estimates = []

    for _xvar_bj in X_SAFE_EST:
        _xlabel_bj = COL_LABEL[_xvar_bj]
        _xs        = df_safe[_xvar_bj].dropna()
        _df_xy_bj  = pd.concat([_y_bj.rename('y'), _xs.rename('x')], axis=1).dropna()
        if len(_df_xy_bj) < 30:
            _BJ_PROPOSED_LAGS[_xvar_bj] = [0, 1]
            continue

        try:
            _fit_x_bj = _auto_arima_bj(
                _df_xy_bj['x'].values, information_criterion='aic',
                stepwise=True, seasonal=False, d=0,
                max_p=BJ_MAX_AR, max_q=BJ_MAX_AR,
                suppress_warnings=True, error_action='ignore',
            )
            _p_x_bj, _, _q_x_bj = _fit_x_bj.order
            _x_resid = _fit_x_bj.resid()

            _ar_x = _fit_x_bj.arparams()
            _y_arr = _df_xy_bj['y'].values
            _p_ar  = len(_ar_x)
            if _p_ar > 0:
                _y_filt = np.array([
                    _y_arr[t] - np.dot(_ar_x, _y_arr[t - _p_ar:t][::-1])
                    for t in range(_p_ar, len(_y_arr))
                ])
            else:
                _y_filt = _y_arr.copy()

            _n_min    = min(len(_x_resid), len(_y_filt))
            _xw       = _x_resid[-_n_min:]
            _yw       = _y_filt[-_n_min:]
            _ci_bj    = BJ_Z_CI / np.sqrt(_n_min)
            _ccf_v_bj = _ccf_fn_bj(_xw, _yw, nlags=BJ_MAX_LAGS_CCF, alpha=None)

            _sig_bj  = [int(l) for l in range(len(_ccf_v_bj)) if abs(_ccf_v_bj[l]) > _ci_bj]
            _prop_bj = sorted({l for l in _sig_bj if 0 <= l <= MAX_LAGS_IND})
            if not _prop_bj:
                _prop_bj = [0, 1]

            _df_ols_bj = _df_xy_bj.copy()
            for _lag_bj in _prop_bj:
                _df_ols_bj[f'xL{_lag_bj}'] = _df_ols_bj['x'].shift(_lag_bj)
            _df_ols_bj = _df_ols_bj.dropna()
            _Xm_bj = _sm_bj.add_constant(_df_ols_bj[[f'xL{l}' for l in _prop_bj]])
            _resid_ols_bj = _sm_bj.OLS(_df_ols_bj['y'], _Xm_bj).fit().resid
            _fit_r_bj = _auto_arima_bj(
                _resid_ols_bj.values, information_criterion='aic',
                stepwise=True, seasonal=False, d=0,
                max_p=BJ_MAX_AR, max_q=BJ_MAX_AR,
                suppress_warnings=True, error_action='ignore',
            )
            _p_r_bj, _, _ = _fit_r_bj.order
            _bj_ar_y_estimates.append(max(_p_r_bj, 1))

            _BJ_PROPOSED_LAGS[_xvar_bj] = _prop_bj
            _bj_ccf_store[_xvar_bj] = {
                'label': _xlabel_bj, 'arma_x': (_p_x_bj, _q_x_bj),
                'ccf': _ccf_v_bj, 'ci': _ci_bj, 'prop': _prop_bj, 'raw': False,
            }
            print(f'  {_xlabel_bj[:55]:<55}  ARMA_X=({_p_x_bj},{_q_x_bj})  lags={_prop_bj}')
        except Exception as _e_bj:
            _BJ_PROPOSED_LAGS[_xvar_bj] = [0, 1]
            print(f'  WARN {COL_LABEL[_xvar_bj][:40]}: {_e_bj}')

    _BJ_AR_Y = int(round(np.median(_bj_ar_y_estimates))) if _bj_ar_y_estimates else 1
    print(f'\n  AR(Y) global propuesto: {_BJ_AR_Y}')

    # CCF bruta para variables sin prewhitening
    for _xvar_bj in X_SAFE_EST:
        if _xvar_bj in _bj_ccf_store:
            continue
        _xlabel_bj = COL_LABEL[_xvar_bj]
        _xs        = df_safe[_xvar_bj].dropna()
        _df_xy_bj  = pd.concat([_y_bj.rename('y'), _xs.rename('x')], axis=1).dropna()
        _n_raw     = len(_df_xy_bj)
        if _n_raw < 5:
            continue
        try:
            _nlags_raw = min(BJ_MAX_LAGS_CCF, _n_raw // 3)
            _ci_raw    = BJ_Z_CI / np.sqrt(_n_raw)
            _ccf_raw   = _ccf_fn_bj(
                _df_xy_bj['x'].values, _df_xy_bj['y'].values,
                nlags=_nlags_raw, alpha=None,
            )
            _sig_raw  = [int(l) for l in range(len(_ccf_raw)) if abs(_ccf_raw[l]) > _ci_raw]
            _prop_raw = sorted({l for l in _sig_raw if 0 <= l <= MAX_LAGS_IND}) or [0, 1]
            _bj_ccf_store[_xvar_bj] = {
                'label': _xlabel_bj, 'arma_x': (None, None),
                'ccf': _ccf_raw, 'ci': _ci_raw, 'prop': _prop_raw, 'raw': True,
            }
            print(f'  CCF bruta {_xlabel_bj[:45]:<45}  n={_n_raw}  lags={_prop_raw}')
        except Exception:
            pass

    # Gráfico CCF
    if _bj_ccf_store:
        _nv = len(_bj_ccf_store)
        _nc = 2
        _nr = (_nv + _nc - 1) // _nc
        fig, axes = plt.subplots(_nr, _nc, figsize=(10 * _nc, 4 * _nr), squeeze=False)
        for _idx, (_xvar, _res) in enumerate(_bj_ccf_store.items()):
            ax      = axes[_idx // _nc][_idx % _nc]
            _cv     = _res['ccf']
            _ci_v   = _res['ci']
            _prop_v = set(_res['prop'])
            _is_raw = _res.get('raw', False)
            _lgs    = list(range(len(_cv)))
            _clrs   = ['#d62728' if l in _prop_v
                       else '#1565C0' if abs(_cv[l]) > _ci_v
                       else '#BDBDBD' for l in _lgs]
            ax.bar(_lgs, _cv, color=_clrs,
                   alpha=0.6 if _is_raw else 1.0,
                   edgecolor='#888' if _is_raw else 'none', linewidth=0.5)
            ax.axhline( _ci_v, color='red', linestyle='--', linewidth=1)
            ax.axhline(-_ci_v, color='red', linestyle='--', linewidth=1)
            ax.axhline(0, color='black', linewidth=0.5)
            _arma_str = 'sin prewhitening' if _is_raw else f"ARMA_X=({_res['arma_x'][0]},{_res['arma_x'][1]})"
            ax.set_title(f"{_res['label'][:40]}  {_arma_str}", fontsize=8)
            ax.set_xlabel(f"Lag  |  propuestos={sorted(_prop_v)}")
        for _idx in range(_nv, _nr * _nc):
            axes[_idx // _nc][_idx % _nc].set_visible(False)
        fig.suptitle('CCF: X blanqueada vs Y filtrada por AR(X)', fontsize=10)
        plt.tight_layout()
        _save_fig(fig, 'sec07_ccf_bj')

    print('OK  _BJ_PROPOSED_LAGS y _BJ_AR_Y listos.\n')
    """
    # --- Fin código comentado ------------------------------------------------

    # ── 7.2 Estimaciones ARDL ────────────────────────────────────────────────
    print('── 7.2 Estimaciones ARDL ──')
    MAX_VARS_POR_MODELO = config['MAX_VARS_POR_MODELO']
    MAX_COMBINACIONES = config['MAX_COMBINACIONES']

    _n_max_ardl  = len(X_SAFE_EST) if MAX_VARS_POR_MODELO is None else MAX_VARS_POR_MODELO
    _combos_ardl = []
    for _r in range(1, _n_max_ardl + 1):
        _combos_ardl.extend(list(combinations(X_SAFE_EST, _r)))

    if MAX_COMBINACIONES is not None and len(_combos_ardl) > MAX_COMBINACIONES:
        random.seed(SEMILLA)
        _combos_ardl = random.sample(_combos_ardl, MAX_COMBINACIONES)

    print(f'Combinaciones ARDL : {len(_combos_ardl)}')
    print(f'Criterios          : {CRITERIOS_SEL}')
    print(f'Estimaciones esp.  : {len(_combos_ardl) * len(CRITERIOS_SEL)}')

    _RESULTADOS_ARDL = []
    _ARDL_RESIDUALS  = {}
    _t0_ardl = pd.Timestamp.now()
    _err_ardl = 0
    _ok_ardl  = 0
    _PRINT_INT_ARDL = max(1, len(_combos_ardl) // 5)

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
                for _d, _dc in _r.get('dummy_coefs', {}).items():
                    _row[f'dum_coef_{_d}'] = _dc['coef']
                    _row[f'dum_pval_{_d}'] = _dc['pval']
                _RESULTADOS_ARDL.append(_row)
                _ARDL_RESIDUALS[_row['combo_id']] = _r['resid']
                _ok_ardl += 1
            except Exception:
                _err_ardl += 1

            if (_ci + 1) % _PRINT_INT_ARDL == 0 or _ci == len(_combos_ardl) - 1:
                _el = int((pd.Timestamp.now() - _t0_ardl).total_seconds())
                print(f'  [{_criterio.upper()}] combo {_ci+1:>3}/{len(_combos_ardl)} | ok={_ok_ardl} err={_err_ardl} | {_el}s')

    df_res_ardl = pd.DataFrame(_RESULTADOS_ARDL)
    _tasa_a = f'{_ok_ardl/(_ok_ardl+_err_ardl)*100:.1f}%' if (_ok_ardl+_err_ardl) > 0 else 'n/a'
    print(f'\n{"="*60}')
    print(f'ARDL completado: {_ok_ardl} modelos | {_err_ardl} errores | tasa={_tasa_a}')
    print(f'{"="*60}')

    # ── 7.3 Control de calidad ARDL ──────────────────────────────────────────
    print('\n── 7.3 Control de calidad ARDL ──')
    if df_res_ardl.empty:
        print('Sin resultados ARDL para controlar.')
        df_res_ardl_ok = pd.DataFrame()
    else:
        CTRL_ARDL_MIN_R2   = 0.0
        CTRL_ARDL_MAX_PVAL = 1.0
        _ardl_flags = {row['combo_id']: [] for _, row in df_res_ardl.iterrows()}

        _n_flagged = sum(1 for v in _ardl_flags.values() if v)
        df_res_ardl['ctrl_flags'] = df_res_ardl['combo_id'].map(
            lambda cid: '|'.join(_ardl_flags.get(cid, [])) or 'OK')
        df_res_ardl['ctrl_ok'] = df_res_ardl['ctrl_flags'] == 'OK'
        df_res_ardl_ok = df_res_ardl[df_res_ardl['ctrl_ok']].copy()
        print(f'  Total: {len(df_res_ardl)} | Con flags: {_n_flagged} | OK: {len(df_res_ardl_ok)}')

    # ── 7.4 Diagnóstico de residuos ARDL ─────────────────────────────────────
    print('\n── 7.4 Diagnóstico de residuos ARDL (Ljung-Box) ──')
    from statsmodels.stats.diagnostic import acorr_ljungbox

    DIAG_LAGS_LB = 8
    DIAG_ALPHA   = 0.05

    if df_res_ardl_ok.empty:
        print('Sin modelos ARDL para diagnosticar.')
        df_ardl_ruido_blanco = pd.DataFrame()
    else:
        _passed_ids = []
        _failed_ids = []
        _err_ids    = []
        for _, _mrow in df_res_ardl_ok.iterrows():
            _cid   = _mrow['combo_id']
            _resid = _ARDL_RESIDUALS.get(_cid)
            if _resid is None or len(_resid) < DIAG_LAGS_LB + 2:
                _err_ids.append(_cid)
                continue
            try:
                _lb   = acorr_ljungbox(_resid, lags=[DIAG_LAGS_LB], return_df=True)
                _lb_p = float(_lb['lb_pvalue'].iloc[-1])
                if _lb_p > DIAG_ALPHA:
                    _passed_ids.append(_cid)
                else:
                    _failed_ids.append(_cid)
            except Exception:
                _err_ids.append(_cid)

        df_ardl_ruido_blanco = df_res_ardl_ok[
            df_res_ardl_ok['combo_id'].isin(_passed_ids)].copy()

        _n_total = len(df_res_ardl_ok)
        _n_pass  = len(_passed_ids)
        _n_fail  = len(_failed_ids)
        print(f'  Diagnosticados: {_n_total} | Ruido blanco: {_n_pass} ({_n_pass/_n_total*100:.0f}%) | Con estructura: {_n_fail}')

    return {
        'df_res_ardl': df_res_ardl,
        'df_res_ardl_ok': df_res_ardl_ok,
        'df_ardl_ruido_blanco': df_ardl_ruido_blanco,
        '_ARDL_RESIDUALS': _ARDL_RESIDUALS,
        '_BJ_PROPOSED_LAGS': _BJ_PROPOSED_LAGS,
        '_BJ_AR_Y': _BJ_AR_Y,
    }



def seccion_8_var(ctx, est_ctx, config):
    """Sección 8: Modelos VAR (IRF estructural Cholesky + control)."""
    _print_header('8', 'MODELOS VAR')

    df_safe = ctx['df_safe']
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
    CRITERIOS_SEL = config['CRITERIOS_SEL']

    from statsmodels.tsa.api import VAR as _VAR_est
    from statsmodels.stats.diagnostic import acorr_ljungbox as _lb_var
    from scipy.stats import norm

    # ── 8.1 Selección del orden VAR ──────────────────────────────────────────
    print('── 8.1 Selección del orden VAR ──')
    _var_order_rows = []
    _sample_size = min(10, len(list(combinations(X_SAFE_EST, min(3, len(X_SAFE_EST))))))
    for _ci, _xv_s in enumerate(combinations(X_SAFE_EST, min(3, len(X_SAFE_EST)))):
        if _ci >= _sample_size:
            break
        _tv_s = list(_xv_s) + [Y_SAFE]
        _df_s = df_safe_est[_tv_s].dropna()
        if len(_df_s) < 30:
            continue
        try:
            _sel = _VAR_est(_df_s).select_order(maxlags=MAX_LAGS_VAR)
            _var_order_rows.append({
                'vars': ' | '.join([COL_LABEL.get(v, v)[:25] for v in _xv_s]),
                'AIC': _sel.selected_orders.get('aic', None),
                'BIC': _sel.selected_orders.get('bic', None),
                'HQIC': _sel.selected_orders.get('hqic', None),
                'n_obs': len(_df_s),
            })
        except Exception:
            pass
    if _var_order_rows:
        _df_var_ord = pd.DataFrame(_var_order_rows)
        print(f'  Orden VAR sugerido (muestra de {len(_var_order_rows)} combinaciones):')
        print(_df_var_ord.to_string())

    # ── 8.2 Estimaciones VAR ─────────────────────────────────────────────────
    print('\n── 8.2 Estimaciones VAR (IRF Cholesky) ──')
    MAX_VARS_POR_MODELO = config['MAX_VARS_POR_MODELO']
    MAX_COMBINACIONES = config['MAX_COMBINACIONES']

    _n_max_var = len(X_SAFE_EST) if MAX_VARS_POR_MODELO is None else MAX_VARS_POR_MODELO
    _subsets_var = []
    for _r in range(1, _n_max_var + 1):
        _subsets_var.extend(list(combinations(X_SAFE_EST, _r)))

    if MAX_COMBINACIONES is not None and len(_subsets_var) > MAX_COMBINACIONES:
        random.seed(SEMILLA)
        _subsets_var = random.sample(_subsets_var, MAX_COMBINACIONES)

    _perms_var = []
    for _subset in _subsets_var:
        for _perm in permutations(_subset):
            _perms_var.append(list(_perm))

    MAX_PERMUTACIONES = 1500
    if len(_perms_var) > MAX_PERMUTACIONES:
        random.seed(SEMILLA)
        _perms_var = random.sample(_perms_var, MAX_PERMUTACIONES)

    # Iterar lags 1..LAG_CAP_FREQ en lugar de seleccionar por IC
    _LAGS_VAR = list(range(1, max(1, LAG_CAP_FREQ) + 1))
    print(f'Permutaciones SVAR a estimar: {len(_perms_var)} x {len(_LAGS_VAR)} lags')
    HORIZONTE_IRF = 12
    DIAG_LAGS_LB = 8

    _RESULTADOS_VAR = []
    _t0_var  = pd.Timestamp.now()
    _err_var = 0
    _ok_var  = 0
    _PRINT_INT_VAR = max(1, len(_perms_var) // 5)

    for _k_ar in _LAGS_VAR:
        for _ci, _xv_perm in enumerate(_perms_var):
            _tv_perm = list(_xv_perm) + [Y_SAFE]
            _df = df_safe_est[_tv_perm].dropna()
            _nobs = len(_df)
            _exog_d = (df_exog_dummy.reindex(_df.index).fillna(0)
                       if not df_exog_dummy.empty else None)
            _k_vars = len(_tv_perm)
            _max_p_dinamico = max(1, (_nobs - 10) // _k_vars)

            if _nobs < 30 or _k_ar > _max_p_dinamico:
                continue

            _criterio = f'lag{_k_ar}'

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
                        _se      = float(_orth_stderr[_h, _y_idx, _x_idx])
                        _pval = 2 * (1 - norm.cdf(abs(_impacto / _se))) if _se > 0 else 1.0
                        _row[f'irf_{_x}_h{_h}'] = _impacto
                        _row[f'irfpval_{_x}_h{_h}'] = _pval
                    _row[f'coef_{_x}'] = _row[f'irf_{_x}_h0']
                    _row[f'pval_{_x}'] = _row[f'irfpval_{_x}_h0']

                # Coeficientes reducidos + Wald F-test
                try:
                    _params_df = _res.params
                    _pvals_df  = _res.pvalues
                    _var_pos   = {v: i for i, v in enumerate(_tv_perm)}
                    _y_col     = Y_SAFE if Y_SAFE in _params_df.columns else _params_df.columns[_y_idx]
                    _y_coefs   = _params_df[_y_col]
                    _y_pvals   = _pvals_df[_y_col]
                    _K_endo    = len(_tv_perm)
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

                # Coeficientes de dummies (exógenas) en ecuación de Y
                try:
                    if DUMMY_SAFE and _exog_d is not None:
                        _params_y = _res.params[_y_col] if _y_col in _res.params.columns else None
                        _pvals_y  = _res.pvalues[_y_col] if _y_col in _res.pvalues.columns else None
                        if _params_y is not None:
                            for _d in DUMMY_SAFE:
                                _matches = [_n for _n in _params_y.index
                                            if _n == _d or _n.endswith(f'.{_d}') or _n == f'exog.{_d}']
                                if _matches:
                                    _idx_d = list(_params_y.index).index(_matches[0])
                                    _row[f'dum_coef_{_d}'] = float(_params_y.iloc[_idx_d])
                                    _row[f'dum_pval_{_d}'] = float(_pvals_y.iloc[_idx_d])
                                else:
                                    _row[f'dum_coef_{_d}'] = float('nan')
                                    _row[f'dum_pval_{_d}'] = float('nan')
                except Exception:
                    for _d in DUMMY_SAFE:
                        _row.setdefault(f'dum_coef_{_d}', float('nan'))
                        _row.setdefault(f'dum_pval_{_d}', float('nan'))

                # R2
                _y_resid = _res.resid.iloc[:, _y_idx]
                _y_act   = _df[Y_SAFE].values[-len(_y_resid):]
                _ss_res  = float(np.sum(_y_resid ** 2))
                _ss_tot  = float(np.sum((_y_act - _y_act.mean()) ** 2))
                _row['r2'] = float(1 - _ss_res / _ss_tot) if _ss_tot > 0 else np.nan

                # Ljung-Box sobre residuos de la ecuación Y (ruido blanco)
                try:
                    _lb = _lb_var(_y_resid, lags=[DIAG_LAGS_LB], return_df=True)
                    _lb_p = float(_lb['lb_pvalue'].iloc[-1])
                    _row['lb_pval'] = _lb_p
                    _row['ruido_blanco'] = _lb_p > NIVEL_SIG
                except Exception:
                    _row['lb_pval'] = float('nan')
                    _row['ruido_blanco'] = False

                _RESULTADOS_VAR.append(_row)
                _ok_var += 1
            except Exception:
                _err_var += 1

            if (_ci + 1) % _PRINT_INT_VAR == 0 or _ci == len(_perms_var) - 1:
                _el = int((pd.Timestamp.now() - _t0_var).total_seconds())
                print(f'  [{_criterio.upper()}] perm {_ci+1:>4}/{len(_perms_var)} | ok={_ok_var} err={_err_var} | {_el}s')

    df_res_var = pd.DataFrame(_RESULTADOS_VAR)
    print(f'\n{"="*60}')
    print(f'SVAR (IRF) completado: {_ok_var} modelos | {_err_var} errores')
    print(f'{"="*60}')

    # VAR_BEST_LAGS — usar lag con menor AIC por combo
    _var_lags_por_combo = defaultdict(list)
    for _rv in _RESULTADOS_VAR:
        _k = frozenset(v for v in _rv.get('vars_safe', '').split('|') if v)
        _var_lags_por_combo[_k].append((_rv.get('aic', float('inf')), _rv.get('k_ar', 2)))
    VAR_BEST_LAGS = {
        k: max(1, min(lags, key=lambda t: t[0])[1])
        for k, lags in _var_lags_por_combo.items() if lags
    }

    # ── 8.3 Control de calidad VAR (filtro ruido blanco) ─────────────────────
    print('\n── 8.3 Control de calidad VAR (Ljung-Box) ──')
    if df_res_var.empty:
        df_res_var_ok = pd.DataFrame()
        print('Sin resultados VAR.')
    else:
        if 'ruido_blanco' in df_res_var.columns:
            df_res_var_ok = df_res_var[df_res_var['ruido_blanco'] == True].copy()
            _n_rb = int(df_res_var['ruido_blanco'].sum())
            print(f'  Total VAR: {len(df_res_var)} | Ruido blanco (LB>α): {_n_rb} | '
                  f'Con autocorr: {len(df_res_var)-_n_rb}')
        else:
            df_res_var_ok = df_res_var.copy()
            print(f'  Total: {len(df_res_var)} | OK: {len(df_res_var_ok)}')
        df_res_var['ctrl_ok'] = df_res_var['combo_id'].isin(df_res_var_ok['combo_id'])

    return {
        'df_res_var': df_res_var,
        'df_res_var_ok': df_res_var_ok,
        'VAR_BEST_LAGS': VAR_BEST_LAGS,
        '_RESULTADOS_VAR': _RESULTADOS_VAR,
        'HORIZONTE_IRF': HORIZONTE_IRF,
    }


def seccion_9_vecm(ctx, est_ctx, config, var_res=None):
    """Sección 9: Modelos VECM (combos desde VAR + Johansen + estimación + LB + alpha)."""
    _print_header('9', 'MODELOS VECM')

    df_safe = ctx['df_safe']
    Y_SAFE = ctx['Y_SAFE']
    COL_LABEL = ctx['COL_LABEL']
    df_exog_dummy = ctx['df_exog_dummy']
    DUMMY_SAFE = ctx.get('DUMMY_SAFE', [])
    MAX_LAGS_VAR = ctx['MAX_LAGS_VAR']
    LAG_CAP_FREQ = ctx.get('LAG_CAP_FREQ', MAX_LAGS_VAR)
    X_SAFE_I1 = est_ctx['X_SAFE_I1']
    X_SAFE_EST = est_ctx['X_SAFE_EST']
    Y_ORDEN = est_ctx['Y_ORDEN']
    NIVEL_SIG = config['NIVEL_SIG']
    SEMILLA = config['SEMILLA']

    from statsmodels.tsa.vector_ar.vecm import coint_johansen as _joh_s9
    from statsmodels.stats.diagnostic import acorr_ljungbox as _lb_vecm

    # ── 9.1 Cointegración de Johansen ────────────────────────────────────────
    print('── 9.1 Cointegración de Johansen (global) ──')
    _N_COINT_GLOBAL = 0
    try:
        _X_COINT = X_SAFE_I1 if X_SAFE_I1 else X_SAFE_EST
        _data_j9 = df_safe[[Y_SAFE] + _X_COINT].dropna()
        _joh9    = _joh_s9(_data_j9, det_order=0, k_ar_diff=2)
        print(f'  Obs: {len(_data_j9)} | Variables: {len(_data_j9.columns)}')
        print(f'\n  {"r":>4} | {"Trace":>10} {"CV5%":>10} {"Sig":>5} | '
              f'{"MaxEig":>10} {"CV5%":>10} {"Sig":>5}')
        print(f'  {"-"*62}')
        for _ri in range(len(_joh9.lr1)):
            _st = 'OK' if _joh9.lr1[_ri] > _joh9.cvt[_ri, 1] else '  '
            _sm = 'OK' if _joh9.lr2[_ri] > _joh9.cvm[_ri, 1] else '  '
            print(f'  {_ri:>4} | {_joh9.lr1[_ri]:>10.3f} {_joh9.cvt[_ri,1]:>10.3f} {_st:>5} | '
                  f'{_joh9.lr2[_ri]:>10.3f} {_joh9.cvm[_ri,1]:>10.3f} {_sm:>5}')
        _k_vars_j9 = _data_j9.shape[1]
        _N_COINT_GLOBAL = min(_k_vars_j9 - 1, int(sum(_joh9.lr1 > _joh9.cvt[:, 1])))
        print(f'\n  Relaciones de cointegración globales (Trace, 5%): {_N_COINT_GLOBAL}')
    except Exception as _e9:
        print(f'  Error en Johansen global: {_e9}')

    # ── 9.2 Estimaciones VECM ────────────────────────────────────────────────
    print('\n── 9.2 Estimaciones VECM ──')
    _X_VECM = X_SAFE_I1

    if Y_ORDEN != 1:
        print('Y no es I(1) -> VECM no aplica.')
        return {'df_res_vecm': pd.DataFrame(), 'df_res_vecm_ok': pd.DataFrame(), '_RESULTADOS_VECM': []}
    if not _X_VECM:
        print('Sin variables I(1) -> VECM no aplica.')
        return {'df_res_vecm': pd.DataFrame(), 'df_res_vecm_ok': pd.DataFrame(), '_RESULTADOS_VECM': []}

    # ── Combos desde los VAR estructurales OK (filtrados a vars I(1)) ───────
    _combos_vecm = []
    _x_vecm_set = set(_X_VECM)
    if var_res is not None:
        _df_var_ok = var_res.get('df_res_var_ok', pd.DataFrame())
        _seen_combo = set()
        for _, _rv in _df_var_ok.iterrows():
            _xv = tuple(sorted(v for v in str(_rv.get('vars_safe', '')).split('|')
                               if v and v in _x_vecm_set))
            if _xv and _xv not in _seen_combo:
                _seen_combo.add(_xv)
                _combos_vecm.append(_xv)
        print(f'  Combos VECM derivados de VAR OK: {len(_combos_vecm)}')

    # Fallback: si no hay info de VAR, generar combinaciones desde X_SAFE_I1
    if not _combos_vecm:
        MAX_VARS_POR_MODELO = config['MAX_VARS_POR_MODELO']
        _n_max_vecm = len(_X_VECM) if MAX_VARS_POR_MODELO is None else MAX_VARS_POR_MODELO
        for _r in range(1, _n_max_vecm + 1):
            _combos_vecm.extend(list(combinations(_X_VECM, _r)))
        print(f'  Sin VAR OK previo: usando combinaciones completas ({len(_combos_vecm)})')

    MAX_COMBINACIONES = config['MAX_COMBINACIONES']
    if MAX_COMBINACIONES is not None and len(_combos_vecm) > MAX_COMBINACIONES:
        random.seed(SEMILLA)
        _combos_vecm = random.sample(_combos_vecm, MAX_COMBINACIONES)

    # Cap de lags: 3 si M, 2 si Q (LAG_CAP_FREQ). VECM exige k_ar_diff >= 1.
    _kdiff_range = list(range(1, max(1, LAG_CAP_FREQ) + 1))
    print(f'Combinaciones: {len(_combos_vecm)} subsets x {len(_kdiff_range)} lags (cap={LAG_CAP_FREQ})')

    _RESULTADOS_VECM = []
    _t0_vecm = pd.Timestamp.now()
    _err_vecm = 0
    _ok_vecm  = 0
    _skip_vecm = 0
    _PRINT_INT_VECM = max(1, len(_combos_vecm) // 5)

    for _ci, _combo in enumerate(_combos_vecm):
        _xv = list(_combo)
        _tv = list(_xv) + [Y_SAFE]
        _df = df_safe[_tv].dropna()
        if len(_df) < 30:
            _skip_vecm += len(_kdiff_range)
            continue

        for _k_ar_diff in _kdiff_range:
            try:
                _r = extraer_vecm(_df, Y_SAFE, _xv, _tv,
                                  k_ar_diff=_k_ar_diff, det_order=0,
                                  df_dummy=df_exog_dummy if not df_exog_dummy.empty else None,
                                  dummy_names=DUMMY_SAFE if DUMMY_SAFE else None)
                if _r is not None:
                    _row = {
                        'combo_id': f'{_ci}_k{_k_ar_diff}_vecm',
                        'criterio': 'johansen', 'modelo': 'VECM',
                        'n_vars': len(_xv),
                        'vars_safe': '|'.join(_xv),
                        'vars_label': '|'.join([COL_LABEL[v] for v in _xv]),
                        'aic': _r['aic'], 'bic': _r['bic'], 'hq': _r['hq'],
                        'r2': _r['r2'], 'nobs': _r['nobs'],
                        'n_coint': _r['n_coint'], 'k_ar_diff': _k_ar_diff,
                        'alpha_coef': _r.get('alpha_coef', float('nan')),
                        'alpha_pval': _r.get('alpha_pval', float('nan')),
                        'alpha_sig': (abs(_r.get('alpha_pval', 1)) < NIVEL_SIG
                                      if not pd.isna(_r.get('alpha_pval', float('nan'))) else False),
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
                    for _d, _dc in _r.get('dummy_coefs', {}).items():
                        _row[f'dum_coef_{_d}'] = _dc.get('coef', float('nan'))
                        _row[f'dum_pval_{_d}'] = _dc.get('pval', float('nan'))
                    # Ljung-Box sobre residuos de la ecuación Y
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
                    _ok_vecm += 1
                else:
                    _skip_vecm += 1
            except Exception:
                _err_vecm += 1

        if (_ci + 1) % _PRINT_INT_VECM == 0 or _ci == len(_combos_vecm) - 1:
            _el = int((pd.Timestamp.now() - _t0_vecm).total_seconds())
            print(f'  [VECM] combo {_ci+1:>3}/{len(_combos_vecm)} | ok={_ok_vecm} skip={_skip_vecm} err={_err_vecm} | {_el}s')

    df_res_vecm = pd.DataFrame(_RESULTADOS_VECM)
    print(f'\n{"="*60}')
    print(f'VECM completado: {_ok_vecm} modelos | {_skip_vecm} sin coint. | {_err_vecm} errores')
    print(f'{"="*60}')

    # ── 9.3 Control de calidad VECM (Ljung-Box) ──────────────────────────────
    print('\n── 9.3 Control de calidad VECM (Ljung-Box) ──')
    if df_res_vecm.empty:
        df_res_vecm_ok = pd.DataFrame()
        print('Sin resultados VECM.')
    else:
        if 'ruido_blanco' in df_res_vecm.columns:
            df_res_vecm_ok = df_res_vecm[df_res_vecm['ruido_blanco'] == True].copy()
            _n_rb = int(df_res_vecm['ruido_blanco'].sum())
            print(f'  Total VECM: {len(df_res_vecm)} | Ruido blanco (LB>α): {_n_rb} | '
                  f'Con autocorr: {len(df_res_vecm)-_n_rb}')
        else:
            df_res_vecm_ok = df_res_vecm.copy()
            print(f'  Total: {len(df_res_vecm)} | OK: {len(df_res_vecm_ok)}')
        df_res_vecm['ctrl_ok'] = df_res_vecm['combo_id'].isin(df_res_vecm_ok['combo_id'])

    # ── 9.4 Análisis Alpha ───────────────────────────────────────────────────
    print('\n── 9.4 Análisis de Alpha (velocidad de ajuste) ──')
    if not df_res_vecm.empty and 'alpha_coef' in df_res_vecm.columns:
        _df_alpha = df_res_vecm.dropna(subset=['alpha_coef', 'alpha_pval']).copy()
        _df_alpha['alpha_sig'] = _df_alpha['alpha_pval'] < NIVEL_SIG
        _n_sig = _df_alpha['alpha_sig'].sum()
        _n_tot = len(_df_alpha)
        print(f'  Alpha significativo: {_n_sig}/{_n_tot} ({_n_sig/_n_tot*100:.1f}%)')

        # Árbol de decisión
        try:
            from sklearn.tree import DecisionTreeClassifier, export_text
            _all_v = sorted(set(
                v for row in _df_alpha['vars_safe'].str.split('|') for v in row if v))
            for _v in _all_v:
                _df_alpha['feat_' + _v] = (
                    _df_alpha['vars_safe'].str.contains(_v, regex=False).astype(int))
            _feat_cols = ['feat_' + v for v in _all_v]
            _feat_labels = [COL_LABEL.get(v, v)[:25] for v in _all_v]
            X_tree = _df_alpha[_feat_cols].values
            y_tree = _df_alpha['alpha_sig'].astype(int).values
            if len(np.unique(y_tree)) >= 2 and len(X_tree) >= 5:
                _clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=2, random_state=42)
                _clf.fit(X_tree, y_tree)
                _imp = _clf.feature_importances_
                _order = np.argsort(-_imp)
                print('\n  Variables ordenadas por exogeneidad:')
                for _rk, _idx in enumerate(_order, 1):
                    if _imp[_idx] > 0:
                        print(f'    {_rk}. {_feat_labels[_idx]:<50} {_imp[_idx]:.4f}')
                print(f'\n  Reglas:\n{export_text(_clf, feature_names=_feat_labels)}')
        except Exception as e:
            print(f'  Árbol de decisión no disponible: {e}')

    return {
        'df_res_vecm': df_res_vecm,
        'df_res_vecm_ok': df_res_vecm_ok,
        '_RESULTADOS_VECM': _RESULTADOS_VECM,
    }



def seccion_10_consolidacion(ctx, ardl_res, var_res, vecm_res, config):
    """Sección 10: Consolidación de resultados + gráficos de significancia."""
    _print_header('10', 'RESULTADOS CONSOLIDADOS')

    COL_LABEL = ctx['COL_LABEL']
    ETI_DEP = ctx['ETI_DEP']
    NIVEL_SIG = config['NIVEL_SIG']

    _frames_ok = []
    _ardl_diag = ardl_res.get('df_ardl_ruido_blanco', pd.DataFrame())
    _ardl_src  = _ardl_diag if not _ardl_diag.empty else ardl_res.get('df_res_ardl_ok', pd.DataFrame())
    for _df_ok, _nombre in [
        (_ardl_src, 'ARDL'),
        (var_res.get('df_res_var_ok', pd.DataFrame()), 'VAR'),
        (vecm_res.get('df_res_vecm_ok', pd.DataFrame()), 'VECM'),
    ]:
        if not _df_ok.empty:
            _frames_ok.append(_df_ok)
            print(f'  {_nombre}: {len(_df_ok)} modelos OK')
        else:
            print(f'  {_nombre}: sin modelos')

    if not _frames_ok:
        print('\nNo hay modelos consolidados.')
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_res = pd.concat(_frames_ok, ignore_index=True)

    # Coeficiente de LARGO PLAZO por modelo
    def _coef_pval_lr(_fila, _x):
        _mod = _fila['modelo']
        if _mod == 'ARDL':
            _c = _fila.get(f'lr_coef_{_x}', float('nan'))
            _p = _fila.get(f'lr_pval_{_x}', float('nan'))
        elif _mod == 'VAR':
            _c = _fila.get(f'sum_coef_{_x}', float('nan'))
            _p = _fila.get(f'wald_pval_{_x}', float('nan'))
        elif _mod == 'VECM':
            # LP en VECM = relación de cointegración β normalizada
            _c = _fila.get(f'beta_coef_{_x}', float('nan'))
            _p = _fila.get(f'beta_pval_{_x}', float('nan'))
        else:
            _c = _fila.get(f'coef_{_x}', float('nan'))
            _p = _fila.get(f'pval_{_x}', float('nan'))
        if isinstance(_c, float) and math.isnan(_c):
            _c = _fila.get(f'coef_{_x}', float('nan'))
            _p = _fila.get(f'pval_{_x}', float('nan'))
        return _c, _p

    # Coeficiente de CORTO PLAZO por modelo
    def _coef_pval_sr(_fila, _x):
        _mod = _fila['modelo']
        if _mod == 'ARDL':
            _c = _fila.get(f'coef_{_x}', float('nan'))
            _p = _fila.get(f'pval_{_x}', float('nan'))
        elif _mod == 'VAR':
            # impacto en h=0 (IRF Cholesky)
            _c = _fila.get(f'irf_{_x}_h0', _fila.get(f'coef_{_x}', float('nan')))
            _p = _fila.get(f'irfpval_{_x}_h0', _fila.get(f'pval_{_x}', float('nan')))
        elif _mod == 'VECM':
            _c = _fila.get(f'gamma_coef_{_x}', float('nan'))
            _p = _fila.get(f'gamma_pval_{_x}', float('nan'))
        else:
            _c = _fila.get(f'coef_{_x}', float('nan'))
            _p = _fila.get(f'pval_{_x}', float('nan'))
        return _c, _p

    _coef_pval = _coef_pval_lr

    _filas = []
    for _, _fila in df_res.iterrows():
        _xv = [v for v in _fila['vars_safe'].split('|') if v]
        for _x in _xv:
            _coef_lr, _pval_lr = _coef_pval_lr(_fila, _x)
            _coef_sr, _pval_sr = _coef_pval_sr(_fila, _x)
            if (isinstance(_coef_lr, float) and math.isnan(_coef_lr)) and \
               (isinstance(_coef_sr, float) and math.isnan(_coef_sr)):
                continue
            _filas.append({
                'combo_id': _fila['combo_id'], 'modelo': _fila['modelo'],
                'criterio': _fila['criterio'], 'var_safe': _x,
                'variable': COL_LABEL.get(_x, _x),
                'coef': _coef_lr, 'pval': _pval_lr,
                'sig': (_pval_lr < NIVEL_SIG) if not (isinstance(_pval_lr, float) and math.isnan(_pval_lr)) else False,
                'coef_sr': _coef_sr, 'pval_sr': _pval_sr,
                'sig_sr': (_pval_sr < NIVEL_SIG) if not (isinstance(_pval_sr, float) and math.isnan(_pval_sr)) else False,
                'r2': _fila.get('r2', float('nan')),
                'aic': _fila.get('aic', float('nan')),
                'bic': _fila.get('bic', float('nan')),
                'hq': _fila.get('hq', float('nan')),
                'nobs': _fila.get('nobs', float('nan')),
                'n_vars': _fila['n_vars'],
                'vars_label': _fila['vars_label'],
                'alpha_coef': _fila.get('alpha_coef', float('nan')),
                'alpha_pval': _fila.get('alpha_pval', float('nan')),
            })

    df_largo = pd.DataFrame(_filas)

    # ── Consolidación de coeficientes de DUMMIES (exógenas) ──────────────────
    DUMMY_SAFE = ctx.get('DUMMY_SAFE', [])
    _filas_dum = []
    for _, _fila in df_res.iterrows():
        for _d in DUMMY_SAFE:
            _cd = _fila.get(f'dum_coef_{_d}', float('nan'))
            _pd = _fila.get(f'dum_pval_{_d}', float('nan'))
            if isinstance(_cd, float) and math.isnan(_cd):
                continue
            _filas_dum.append({
                'combo_id': _fila['combo_id'], 'modelo': _fila['modelo'],
                'criterio': _fila['criterio'], 'dummy_safe': _d,
                'dummy': COL_LABEL.get(_d, _d),
                'coef': _cd, 'pval': _pd,
                'sig': (_pd < NIVEL_SIG) if not (isinstance(_pd, float) and math.isnan(_pd)) else False,
                'aic': _fila.get('aic', float('nan')),
                'vars_label': _fila['vars_label'],
            })
    df_dum = pd.DataFrame(_filas_dum)

    print(f'\n{"="*60}')
    print(f'  df_res   : {len(df_res)} modelos')
    for _m in sorted(df_res['modelo'].unique()):
        print(f'    {_m:<8}: {len(df_res[df_res["modelo"]==_m])}')
    print(f'  df_largo : {len(df_largo)} filas')
    print(f'  Variables: {df_largo["variable"].nunique()}')

    # Exportar
    _out_path = NOTEBOOKS_DIR / 'Variables Regresivas' / 'resultados_iterativos.csv'
    try:
        df_largo.to_csv(_out_path, index=False)
        print(f'\n  Exportado a: {_out_path.name}')
    except Exception as _e:
        print(f'  No se pudo exportar: {_e}')

    # ── Gráficos de significancia ────────────────────────────────────────────
    _COLORS = {'ARDL': '#2196F3', 'VAR': '#FF9800', 'VECM': '#4CAF50'}

    if not df_largo.empty:
        _vars_plot = sorted(df_largo['variable'].unique())

        # Scatter coef vs p-valor
        _nc = min(2, len(_vars_plot))
        _nr = (len(_vars_plot) + _nc - 1) // _nc
        fig, axes = plt.subplots(_nr, _nc, figsize=(8 * _nc, 5 * _nr), squeeze=False)
        for _idx, _var in enumerate(_vars_plot):
            ax  = axes[_idx // _nc][_idx % _nc]
            _dv = df_largo[df_largo['variable'] == _var].dropna(subset=['coef', 'pval'])
            for _mod, _color in _COLORS.items():
                _dm = _dv[_dv['modelo'] == _mod]
                if _dm.empty:
                    continue
                _sig = _dm['sig'].astype(bool)
                ax.scatter(_dm.loc[_sig, 'coef'], _dm.loc[_sig, 'pval'],
                           color=_color, marker='o', label=_mod, alpha=0.7, s=40)
                ax.scatter(_dm.loc[~_sig, 'coef'], _dm.loc[~_sig, 'pval'],
                           color=_color, marker='x', alpha=0.5, s=40)
            ax.axhline(NIVEL_SIG, color='red', linestyle='--', linewidth=1)
            ax.axvline(0, color='gray', linestyle='--', linewidth=1)
            ax.set_title(_var[:50], fontsize=9)
            ax.set_xlabel('Coeficiente')
            ax.set_ylabel('P-valor')
            ax.legend(fontsize=8)
        for _idx in range(len(_vars_plot), _nr * _nc):
            axes[_idx // _nc][_idx % _nc].set_visible(False)
        fig.suptitle('Coef LARGO PLAZO vs P-valor por modelo y variable', fontsize=11)
        plt.tight_layout()
        _save_fig(fig, 'sec10_coef_vs_pval_largo_plazo')

        # ── Scatter CORTO PLAZO (ARDL coef impacto / VAR IRF h=0 / VECM γ) ──
        fig, axes = plt.subplots(_nr, _nc, figsize=(8 * _nc, 5 * _nr), squeeze=False)
        for _idx, _var in enumerate(_vars_plot):
            ax  = axes[_idx // _nc][_idx % _nc]
            _dv = df_largo[df_largo['variable'] == _var].dropna(subset=['coef_sr', 'pval_sr'])
            for _mod, _color in _COLORS.items():
                _dm = _dv[_dv['modelo'] == _mod]
                if _dm.empty:
                    continue
                _sig = _dm['sig_sr'].astype(bool)
                ax.scatter(_dm.loc[_sig, 'coef_sr'], _dm.loc[_sig, 'pval_sr'],
                           color=_color, marker='o', label=_mod, alpha=0.7, s=40)
                ax.scatter(_dm.loc[~_sig, 'coef_sr'], _dm.loc[~_sig, 'pval_sr'],
                           color=_color, marker='x', alpha=0.5, s=40)
            ax.axhline(NIVEL_SIG, color='red', linestyle='--', linewidth=1)
            ax.axvline(0, color='gray', linestyle='--', linewidth=1)
            ax.set_title(_var[:50], fontsize=9)
            ax.set_xlabel('Coeficiente CORTO PLAZO')
            ax.set_ylabel('P-valor')
            ax.legend(fontsize=8)
        for _idx in range(len(_vars_plot), _nr * _nc):
            axes[_idx // _nc][_idx % _nc].set_visible(False)
        fig.suptitle('Coef CORTO PLAZO vs P-valor por modelo y variable', fontsize=11)
        plt.tight_layout()
        _save_fig(fig, 'sec10_coef_vs_pval_corto_plazo')

        # ── Análisis ALPHA (VECM) ────────────────────────────────────────────
        _df_vecm = df_largo[df_largo['modelo'] == 'VECM'].dropna(
            subset=['alpha_coef', 'alpha_pval'])
        if not _df_vecm.empty:
            # 1) scatter alpha vs p-val por combo (unique combo_id)
            _df_alpha_uniq = _df_vecm.drop_duplicates(subset=['combo_id'])
            fig, ax = plt.subplots(figsize=(8, 5))
            _sig_a = _df_alpha_uniq['alpha_pval'] < NIVEL_SIG
            ax.scatter(_df_alpha_uniq.loc[_sig_a, 'alpha_coef'],
                       _df_alpha_uniq.loc[_sig_a, 'alpha_pval'],
                       color=_COLORS['VECM'], marker='o', alpha=0.7, s=40,
                       label='α significativo')
            ax.scatter(_df_alpha_uniq.loc[~_sig_a, 'alpha_coef'],
                       _df_alpha_uniq.loc[~_sig_a, 'alpha_pval'],
                       color=_COLORS['VECM'], marker='x', alpha=0.5, s=40,
                       label='α no significativo')
            ax.axhline(NIVEL_SIG, color='red', linestyle='--', linewidth=1)
            ax.axvline(0, color='gray', linestyle='--', linewidth=1)
            ax.set_xlabel('Coeficiente de ajuste α (variable dependiente)')
            ax.set_ylabel('P-valor')
            ax.set_title('VECM — α (velocidad de ajuste) vs P-valor')
            ax.legend()
            plt.tight_layout()
            _save_fig(fig, 'sec10_vecm_alpha_dep')

            # 2) % γ_x significativo cuando α_dep NO sig vs SI sig
            _df_vecm['gamma_x_sig'] = _df_vecm['sig_sr'].astype(bool)
            _df_vecm['alpha_dep_sig'] = (_df_vecm['alpha_pval'] < NIVEL_SIG).astype(bool)
            _grp = (_df_vecm.groupby(['variable', 'alpha_dep_sig'])['gamma_x_sig']
                    .agg(N='count', N_sig='sum').reset_index())
            _grp['Pct'] = _grp['N_sig'] / _grp['N'] * 100

            _g_no = _grp[~_grp['alpha_dep_sig']].set_index('variable')['Pct']
            _g_si = _grp[_grp['alpha_dep_sig']].set_index('variable')['Pct']
            _idx_v = sorted(set(_g_no.index) | set(_g_si.index))
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))
            _v_no = [_g_no.get(v, 0) for v in _idx_v]
            _v_si = [_g_si.get(v, 0) for v in _idx_v]
            ax1.barh([v[:35] for v in _idx_v], _v_no, color='#4CAF50', alpha=0.8)
            ax1.set_title('% γ_x significativo  |  α_dep NO sig.')
            ax1.set_xlabel('% modelos con γ_x significativo')
            ax2.barh([v[:35] for v in _idx_v], _v_si, color='#2E7D32', alpha=0.8)
            ax2.set_title('% γ_x significativo  |  α_dep SI sig.')
            ax2.set_xlabel('% modelos con γ_x significativo')
            fig.suptitle('VECM — Significancia de γ de variables independientes según α_dep', fontsize=11)
            plt.tight_layout()
            _save_fig(fig, 'sec10_vecm_gamma_pct_segun_alpha')

        # ── Scatter coef vs p-val de DUMMIES (exógenas) ─────────────────────
        if not df_dum.empty:
            _dums_plot = sorted(df_dum['dummy'].unique())
            _ncd = min(2, len(_dums_plot))
            _nrd = (len(_dums_plot) + _ncd - 1) // _ncd
            fig, axes = plt.subplots(_nrd, _ncd, figsize=(8 * _ncd, 5 * _nrd), squeeze=False)
            for _idx, _dn in enumerate(_dums_plot):
                ax  = axes[_idx // _ncd][_idx % _ncd]
                _dv = df_dum[df_dum['dummy'] == _dn].dropna(subset=['coef', 'pval'])
                for _mod, _color in _COLORS.items():
                    _dm = _dv[_dv['modelo'] == _mod]
                    if _dm.empty:
                        continue
                    _sig = _dm['sig'].astype(bool)
                    ax.scatter(_dm.loc[_sig, 'coef'], _dm.loc[_sig, 'pval'],
                               color=_color, marker='o', label=_mod, alpha=0.7, s=40)
                    ax.scatter(_dm.loc[~_sig, 'coef'], _dm.loc[~_sig, 'pval'],
                               color=_color, marker='x', alpha=0.5, s=40)
                ax.axhline(NIVEL_SIG, color='red', linestyle='--', linewidth=1)
                ax.axvline(0, color='gray', linestyle='--', linewidth=1)
                ax.set_title(f'Dummy: {_dn[:40]}', fontsize=9)
                ax.set_xlabel('Coeficiente')
                ax.set_ylabel('P-valor')
                ax.legend(fontsize=8)
            for _idx in range(len(_dums_plot), _nrd * _ncd):
                axes[_idx // _ncd][_idx % _ncd].set_visible(False)
            fig.suptitle('Variables DUMMY exógenas: coef vs p-valor por modelo', fontsize=11)
            plt.tight_layout()
            _save_fig(fig, 'sec10_dummies_coef_vs_pval')

            # % significancia por dummy
            _dsg = (df_dum.groupby(['dummy', 'modelo'])['sig']
                    .agg(N='count', N_sig='sum').reset_index())
            _dsg['Pct_Sig'] = (_dsg['N_sig'] / _dsg['N'] * 100).round(1)
            print('\n  % Significancia de DUMMIES (por modelo):')
            print(_dsg.to_string(index=False))

        # % Significancia por variable
        _sig_grp = (df_largo.groupby(['variable', 'modelo'])['sig']
                    .agg(N='count', N_sig='sum').reset_index())
        _sig_grp['Pct_Sig'] = (_sig_grp['N_sig'] / _sig_grp['N'] * 100).round(1)
        _sig_glob = (df_largo.groupby('variable')['sig']
                     .agg(N='count', N_sig='sum').reset_index())
        _sig_glob['Pct_Sig'] = (_sig_glob['N_sig'] / _sig_glob['N'] * 100).round(1)
        _order = _sig_glob.sort_values('Pct_Sig', ascending=False)['variable'].tolist()

        print('\n  % Significancia por variable (TOTAL):')
        for _, r in _sig_glob.sort_values('Pct_Sig', ascending=False).iterrows():
            print(f'    {r["variable"][:50]:<50} {r["Pct_Sig"]:>6.1f}% ({int(r["N_sig"])}/{int(r["N"])})')

    return df_res, df_largo, df_dum


def seccion_11_ranking(df_res, df_largo, ctx, est_ctx, config, ardl_res):
    """Sección 11: Ranking y comparación de modelos."""
    _print_header('11', 'RANKING Y COMPARACIÓN DE MODELOS')

    if df_res.empty:
        print('Sin resultados.')
        return

    COL_LABEL = ctx['COL_LABEL']
    ETI_DEP = ctx['ETI_DEP']
    Y_SAFE = ctx['Y_SAFE']
    df_safe = ctx['df_safe']
    df_safe_est = est_ctx['df_safe_est']
    MAX_LAGS_VAR = ctx['MAX_LAGS_VAR']

    _COLORS = {'ARDL': '#2196F3', 'VAR': '#FF9800', 'VECM': '#4CAF50'}

    _criterios_rank = {
        'R2': ('r2', False), 'AIC': ('aic', True),
        'BIC': ('bic', True), 'HQ': ('hq', True),
    }
    for _crit_name, (_col, _asc) in _criterios_rank.items():
        if _col not in df_res.columns or df_res[_col].isna().all():
            continue
        print(f'\n{"="*70}')
        print(f'TOP 10 por {_crit_name}  ({"menor" if _asc else "mayor"} = mejor)')
        print('='*70)
        _top = (
            df_res.dropna(subset=[_col])
            .sort_values(_col, ascending=_asc)
            .drop_duplicates(subset=['vars_safe', 'modelo'])
            .head(10)
            [['modelo', 'vars_label', _col, 'aic', 'bic', 'hq', 'r2', 'nobs']]
            .reset_index(drop=True)
        )
        _top.index = range(1, len(_top) + 1)
        print(_top.rename(columns={'vars_label': 'Variables', 'modelo': 'Modelo'}).to_string())

    def _fit_y_ajuste(fila):
        """Devuelve (actual_serie, fitted_serie, label) para una fila del df_res."""
        _xv = [v for v in str(fila['vars_safe']).split('|') if v]
        _mod = fila['modelo']
        _tv  = [Y_SAFE] + _xv
        _df  = df_safe[_tv].dropna()
        if _mod == 'ARDL':
            from statsmodels.tsa.ardl import ardl_select_order as _aso, ARDL as _ARDL_plt
            _df_est = est_ctx['df_safe_est'][_tv].dropna()
            _sel = _aso(_df_est[Y_SAFE], ctx['MAX_LAGS_DEP'],
                        _df_est[_xv], ctx['MAX_LAGS_IND'], ic='aic', trend='c')
            _fit = _sel.model.fit()
            return _df_est[Y_SAFE], _fit.fittedvalues, 'ARDL ajustado'
        if _mod == 'VAR':
            from statsmodels.tsa.api import VAR as _VAR_plt2
            _df_est = est_ctx['df_safe_est'][_tv].dropna()
            _kb = int(fila.get('k_ar', 1)) if 'k_ar' in fila.index else 1
            _kb = max(1, _kb)
            _fit = _VAR_plt2(_df_est).fit(_kb)
            _yi = list(_tv).index(Y_SAFE)
            return _df_est[Y_SAFE].iloc[_kb:], _fit.fittedvalues.iloc[:, _yi], f'VAR({_kb}) ajustado'
        if _mod == 'VECM':
            from statsmodels.tsa.vector_ar.vecm import (VECM as _VECM_plt2,
                                                         coint_johansen as _joh_plt2)
            _k_ar_b = int(fila.get('k_ar_diff', 2)) if 'k_ar_diff' in fila.index else 2
            _joh_b  = _joh_plt2(_df, det_order=0, k_ar_diff=_k_ar_b)
            _nci_b  = min(_df.shape[1] - 1, int(sum(_joh_b.lr1 > _joh_b.cvt[:, 1])))
            if _nci_b == 0:
                raise ValueError('Sin cointegración')
            _fit = _VECM_plt2(_df, k_ar_diff=_k_ar_b, coint_rank=_nci_b,
                              deterministic='ci').fit()
            _yi      = list(_tv).index(Y_SAFE)
            _y_lvl   = _df[Y_SAFE]
            _resid   = _fit.resid[:, _yi]
            _act_d   = _y_lvl.diff().dropna()
            _fit_idx = _act_d.index[-len(_resid):]
            _dY_hat  = _act_d.loc[_fit_idx].values - _resid
            _y_lag1  = _y_lvl.shift(1).reindex(_fit_idx).values
            return (_y_lvl.reindex(_fit_idx),
                    pd.Series(_y_lag1 + _dY_hat, index=_fit_idx),
                    f'VECM ajustado (niveles, k_ar_diff={_k_ar_b})')
        raise ValueError(f'Modelo no soportado: {_mod}')

    # Mejor modelo global
    _best_g = df_res.loc[df_res['aic'].idxmin()]
    _xv_g   = [v for v in _best_g['vars_safe'].split('|') if v]
    _best_mod = _best_g['modelo']

    print(f'\n{"="*70}')
    print(f'MEJOR MODELO GLOBAL (AIC): {_best_mod}')
    print('='*70)
    _xl_m = [COL_LABEL.get(v, v) for v in _xv_g]
    print(f'  AIC={_best_g["aic"]:.4f}  BIC={_best_g["bic"]:.4f}  R2={_best_g.get("r2", float("nan")):.4f}')
    print(f'  Variables: {", ".join(_xl_m)}')

    # ── Real vs Ajustado: global + por tipo (ARDL/VAR/VECM) ──────────────────
    _ajuste_specs = [('global', _best_g, 'sec11_real_vs_ajustado',
                      f'Mejor GLOBAL ({_best_mod})')]
    for _m in ['ARDL', 'VAR', 'VECM']:
        _df_m = df_res[df_res['modelo'] == _m].dropna(subset=['aic'])
        if _df_m.empty:
            continue
        _best_m_row = _df_m.loc[_df_m['aic'].idxmin()]
        _ajuste_specs.append(
            (_m, _best_m_row, f'sec11_real_vs_ajustado_{_m.lower()}',
             f'Mejor {_m}'))

    for _tag, _fila, _png_name, _suffix in _ajuste_specs:
        try:
            _actual_b, _fitted_b, _label_b = _fit_y_ajuste(_fila)
            _vars_lbl = _fila.get('vars_label', '')[:80]
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(_actual_b.index, _actual_b.values, color='#1f77b4', linewidth=1.5, label='Real')
            ax.plot(_fitted_b.index, _fitted_b.values,
                    color='#FF9800', linewidth=1.5, linestyle='--', label=_label_b)
            ax.set_title(f'{_suffix} — Real vs Ajustado | Y = {ETI_DEP[:40]}\n'
                         f'Vars: {_vars_lbl}  |  AIC={_fila.get("aic", float("nan")):.3f}  '
                         f'R²={_fila.get("r2", float("nan")):.4f}',
                         fontsize=10)
            ax.legend()
            plt.tight_layout()
            _save_fig(fig, _png_name)
        except Exception as _e:
            print(f'  No se pudo graficar ajuste ({_tag}): {_e}')

    # ── Boxplot de criterios de información y R² por modelo ──────────────────
    _COLORS_BOX = {'ARDL': '#2196F3', 'VAR': '#FF9800', 'VECM': '#4CAF50'}
    _mets = [('aic', 'AIC'), ('bic', 'BIC'), ('hq', 'HQIC'), ('r2', 'R² ajustado')]
    _mods_order = [m for m in ['ARDL', 'VAR', 'VECM'] if m in df_res['modelo'].unique()]
    if _mods_order:
        fig, axes = plt.subplots(1, 4, figsize=(20, 5))
        for _i, (_col, _lbl) in enumerate(_mets):
            ax = axes[_i]
            _data = [df_res[df_res['modelo'] == _m][_col].dropna().values for _m in _mods_order]
            _bp = ax.boxplot(_data, labels=_mods_order, patch_artist=True, showmeans=True)
            for _patch, _m in zip(_bp['boxes'], _mods_order):
                _patch.set_facecolor(_COLORS_BOX.get(_m, '#888'))
                _patch.set_alpha(0.6)
            ax.set_title(_lbl)
            ax.grid(True, axis='y', linestyle=':', alpha=0.4)
        fig.suptitle('Distribución de criterios de información y R² por tipo de modelo', fontsize=12)
        plt.tight_layout()
        _save_fig(fig, 'sec11_boxplot_criterios')


def seccion_B_diagnostico_residuos(df_res, ctx, est_ctx, config, ardl_res):
    """Apéndice B: Diagnóstico completo de residuos (Ljung-Box)."""
    _print_header('B', 'DIAGNÓSTICO DE RESIDUOS (Ljung-Box)')

    if df_res.empty:
        print('Sin resultados.')
        return

    from statsmodels.stats.diagnostic import acorr_ljungbox as _lb_test

    Y_SAFE = ctx['Y_SAFE']
    df_safe = ctx['df_safe']
    COL_LABEL = ctx['COL_LABEL']
    MAX_LAGS_DEP = ctx['MAX_LAGS_DEP']
    MAX_LAGS_IND = ctx['MAX_LAGS_IND']
    MAX_LAGS_VAR = ctx['MAX_LAGS_VAR']
    NIVEL_SIG = config['NIVEL_SIG']
    _LB_LAGS = 12

    def _resid_para_modelo(row):
        modelo = row['modelo']
        xv = [v for v in str(row['vars_safe']).split('|') if v]
        tv = [Y_SAFE] + xv
        df_m = df_safe[tv].dropna()
        if len(df_m) < 30:
            return None
        try:
            if modelo == 'ARDL':
                from statsmodels.tsa.ardl import ARDL as _ARDL_r
                _bj_lp = ardl_res.get('_BJ_PROPOSED_LAGS', {})
                _bj_ary = ardl_res.get('_BJ_AR_Y', 1)
                try:
                    _od = {x: max(_bj_lp.get(x, [0, 1])) for x in xv}
                    _fit = _ARDL_r(df_m[Y_SAFE], lags=_bj_ary, exog=df_m[xv],
                                    order=_od, trend='c').fit()
                except Exception:
                    from statsmodels.tsa.ardl import ardl_select_order as _aso
                    _sel = _aso(df_m[Y_SAFE], MAX_LAGS_DEP, df_m[xv],
                                MAX_LAGS_IND, ic='aic', trend='c')
                    _fit = _sel.model.fit()
                return _fit.resid.dropna().values
            elif modelo == 'VAR':
                from statsmodels.tsa.api import VAR as _VAR_r
                df_m_est = est_ctx['df_safe_est'][tv].dropna()
                _ls = _VAR_r(df_m_est).select_order(maxlags=MAX_LAGS_VAR)
                _kar = max(1, _ls.selected_orders.get('aic', 1))
                _fit = _VAR_r(df_m_est).fit(_kar)
                return _fit.resid[:, list(tv).index(Y_SAFE)]
            elif modelo == 'VECM':
                from statsmodels.tsa.vector_ar.vecm import VECM as _VECM_r, coint_johansen as _joh_r
                _joh = _joh_r(df_m, det_order=0, k_ar_diff=2)
                _nci = int(sum(_joh.lr1 > _joh.cvt[:, 1]))
                if _nci == 0:
                    return None
                _fit = _VECM_r(df_m, k_ar_diff=2, coint_rank=_nci,
                               deterministic='ci').fit()
                return _fit.resid[:, list(tv).index(Y_SAFE)]
        except Exception:
            return None

    _df_uniq = (
        df_res.sort_values('aic')
        .groupby(['vars_safe', 'modelo'], sort=False).first().reset_index()
    )
    print(f'Testeando {len(_df_uniq)} especificaciones (Ljung-Box, {_LB_LAGS} lags)...\n')

    _wb_rows = []
    for _i, _row in _df_uniq.iterrows():
        _resid = _resid_para_modelo(_row)
        if _resid is None or len(_resid) < 15:
            continue
        try:
            _lb = _lb_test(_resid, lags=[_LB_LAGS], return_df=True)
            _lbpv = float(_lb['lb_pvalue'].iloc[0])
            _es_rb = _lbpv >= NIVEL_SIG
            _xv = [v for v in str(_row['vars_safe']).split('|') if v]
            _wb_rows.append({
                'Modelo': _row['modelo'],
                'Variables': ' | '.join([COL_LABEL.get(v, v)[:22] for v in _xv]),
                'LB_pval': round(_lbpv, 4),
                'Ruido_Blanco': 'SI' if _es_rb else 'NO',
                '_pass': _es_rb,
            })
        except Exception:
            pass

    df_rb = pd.DataFrame(_wb_rows)
    if not df_rb.empty:
        print('\n  RESUMEN POR MODELO:')
        _rb_res = df_rb.groupby('Modelo').agg(
            Total=('_pass', 'count'), RB_ok=('_pass', 'sum')).reset_index()
        _rb_res['%OK'] = (_rb_res['RB_ok'] / _rb_res['Total'] * 100).round(1)
        print(_rb_res.to_string(index=False))
        _no_rb = df_rb[~df_rb['_pass']]
        print(f'\n  Modelos sin ruido blanco: {len(_no_rb)} / {len(df_rb)}')


# ══════════════════════════════════════════════════════════════════════════════
# REPORTE HTML
# ══════════════════════════════════════════════════════════════════════════════

def generar_reporte_html(ctx, est_ctx, ardl_res, var_res, vecm_res,
                          df_res, df_largo, df_dum, config):
    """Genera un reporte HTML autocontenido con todos los resultados clave."""
    _print_header('HTML', 'GENERACIÓN DE REPORTE')

    NIVEL_SIG = config['NIVEL_SIG']
    ETI_DEP = ctx.get('ETI_DEP', '')
    FREQ = ctx.get('FRECUENCIA_USADA', '?')
    LAG_CAP = ctx.get('LAG_CAP_FREQ', '?')
    df_safe = ctx.get('df_safe')

    def _img(name, title=''):
        p = OUTPUT_DIR / f'{name}.png'
        if not p.exists():
            return f'<p class="warn">⚠ Falta gráfico: {name}.png</p>'
        return (f'<figure><img src="{name}.png" alt="{name}">'
                f'<figcaption>{title}</figcaption></figure>')

    def _tabla(df, max_rows=20, cols=None, titulo=''):
        if df is None or df.empty:
            return f'<p class="muted">Sin datos: {titulo}</p>'
        d = df.copy()
        if cols:
            cols = [c for c in cols if c in d.columns]
            d = d[cols]
        d = d.head(max_rows)
        for c in d.select_dtypes(include=[float, np.float64]).columns:
            d[c] = d[c].round(4)
        html = d.to_html(index=False, classes='tbl', border=0, justify='left')
        return f'<h4>{titulo}</h4>{html}' if titulo else html

    secciones = []

    # ── Sec 3-4: Configuración ────────────────────────────────────────────────
    n_obs = len(df_safe) if df_safe is not None else 0
    n_vars = len(ctx.get('X_SAFE', []))
    secciones.append(f'''
    <section id="sec3">
      <h2>3-4. Configuración y panel</h2>
      <ul>
        <li>Variable dependiente: <b>{ETI_DEP}</b></li>
        <li>Frecuencia detectada: <b>{FREQ}</b> (cap de lags = {LAG_CAP})</li>
        <li>Observaciones: <b>{n_obs}</b></li>
        <li>Variables explicativas: <b>{n_vars}</b></li>
        <li>Período: {df_safe.index.min().date() if n_obs else '—'} → {df_safe.index.max().date() if n_obs else '—'}</li>
        <li>Nivel de significancia: α = {NIVEL_SIG}</li>
      </ul>
    </section>''')

    # ── Sec 5: Descriptivos ───────────────────────────────────────────────────
    secciones.append(f'''
    <section id="sec5">
      <h2>5. Series del panel</h2>
      {_img('sec05_series_panel', 'Series del panel (rojo = dependiente)')}
    </section>''')

    # ── Sec 6: Estacionariedad ────────────────────────────────────────────────
    info_est = est_ctx.get('INFO_ESTACIONARIEDAD', {})
    if info_est:
        rows = []
        for s, info in info_est.items():
            rows.append({
                'Variable': info['label'],
                'Nivel OK': 'SI' if info['nivel_estacionaria'] else 'NO',
                'Diff OK': 'SI' if info['diff_estacionaria'] else 'NO',
                'Orden': f"I({info['orden']})",
            })
        df_est = pd.DataFrame(rows)
        secciones.append(f'''
        <section id="sec6">
          <h2>6. Estacionariedad (ADF + KPSS)</h2>
          {_tabla(df_est, max_rows=50)}
        </section>''')

    # ── Sec 7: ARDL ───────────────────────────────────────────────────────────
    df_a = ardl_res.get('df_res_ardl', pd.DataFrame())
    df_a_rb = ardl_res.get('df_ardl_ruido_blanco', pd.DataFrame())
    secciones.append(f'''
    <section id="sec7">
      <h2>7. Modelos ARDL</h2>
      <p>Total estimados: <b>{len(df_a)}</b> | Con ruido blanco (LB): <b>{len(df_a_rb)}</b></p>
      {_img('sec07_ccf_bj', 'CCF Box-Jenkins (X blanqueada vs Y filtrada)')}
      {_tabla(df_a.sort_values('aic').head(10) if not df_a.empty else df_a,
              cols=['modelo','vars_label','aic','bic','hq','r2','nobs'],
              titulo='Top 10 ARDL por AIC')}
    </section>''')

    # ── Sec 8: VAR ────────────────────────────────────────────────────────────
    df_v = var_res.get('df_res_var', pd.DataFrame())
    df_v_ok = var_res.get('df_res_var_ok', pd.DataFrame())
    secciones.append(f'''
    <section id="sec8">
      <h2>8. Modelos VAR (Cholesky)</h2>
      <p>Total estimados: <b>{len(df_v)}</b> | Con ruido blanco (LB en Y): <b>{len(df_v_ok)}</b></p>
      {_tabla(df_v.sort_values('aic').head(10) if not df_v.empty else df_v,
              cols=['modelo','vars_label','k_ar','aic','bic','hq','r2','lb_pval','ruido_blanco','nobs'],
              titulo='Top 10 VAR por AIC')}
    </section>''')

    # ── Sec 9: VECM ───────────────────────────────────────────────────────────
    df_c = vecm_res.get('df_res_vecm', pd.DataFrame())
    df_c_ok = vecm_res.get('df_res_vecm_ok', pd.DataFrame())
    n_alpha_sig = 0
    if not df_c.empty and 'alpha_pval' in df_c.columns:
        n_alpha_sig = int((df_c['alpha_pval'] < NIVEL_SIG).sum())
    secciones.append(f'''
    <section id="sec9">
      <h2>9. Modelos VECM</h2>
      <p>Total estimados: <b>{len(df_c)}</b> | Con ruido blanco (LB en Y): <b>{len(df_c_ok)}</b> |
         α significativo: <b>{n_alpha_sig}/{len(df_c)}</b></p>
      {_tabla(df_c.sort_values('aic').head(10) if not df_c.empty else df_c,
              cols=['modelo','vars_label','k_ar_diff','n_coint','aic','bic','hq','r2',
                    'alpha_coef','alpha_pval','lb_pval','ruido_blanco','nobs'],
              titulo='Top 10 VECM por AIC')}
    </section>''')

    # ── Sec 10: Consolidación ─────────────────────────────────────────────────
    sig_html = ''
    if not df_largo.empty:
        sig_glob = (df_largo.groupby('variable')['sig']
                    .agg(N='count', N_sig='sum').reset_index())
        sig_glob['Pct_Sig'] = (sig_glob['N_sig'] / sig_glob['N'] * 100).round(1)
        sig_glob = sig_glob.sort_values('Pct_Sig', ascending=False)
        sig_html = _tabla(sig_glob, max_rows=30, titulo='% Significancia por variable (largo plazo, todos los modelos)')

    # Tabla agregada de dummies
    dum_html = ''
    if df_dum is not None and not df_dum.empty:
        _dsg = (df_dum.groupby(['dummy', 'modelo'])['sig']
                .agg(N='count', N_sig='sum').reset_index())
        _dsg['Pct_Sig'] = (_dsg['N_sig'] / _dsg['N'] * 100).round(1)
        _dmean = (df_dum.groupby(['dummy', 'modelo'])['coef']
                  .agg(['mean', 'median']).round(4).reset_index())
        _dum_summary = _dsg.merge(_dmean, on=['dummy', 'modelo'])
        dum_html = (_tabla(_dum_summary, max_rows=50,
                           titulo='Dummies: %sig + coef medio/mediana por modelo')
                    + _img('sec10_dummies_coef_vs_pval',
                           'Dummies exógenas: coef vs p-valor'))
    else:
        dum_html = '<p class="muted">Sin coeficientes de dummies extraídos.</p>'

    secciones.append(f'''
    <section id="sec10">
      <h2>10. Consolidación y gráficos comparativos</h2>
      {sig_html}
      <h3>Largo plazo</h3>
      {_img('sec10_coef_vs_pval_largo_plazo', 'Coef LARGO PLAZO vs P-valor (β en VECM)')}
      <h3>Corto plazo</h3>
      {_img('sec10_coef_vs_pval_corto_plazo', 'Coef CORTO PLAZO vs P-valor (γ en VECM)')}
      <h3>Variables DUMMY exógenas</h3>
      {dum_html}
      <h3>VECM — Velocidad de ajuste (α)</h3>
      {_img('sec10_vecm_alpha_dep', 'α vs p-valor (dependiente)')}
      {_img('sec10_vecm_gamma_pct_segun_alpha', '% γ_x significativo según α_dep')}
    </section>''')

    # ── Sec 11: Ranking ───────────────────────────────────────────────────────
    COL_LABEL = ctx.get('COL_LABEL', {})
    DUMMY_SAFE = ctx.get('DUMMY_SAFE', [])

    def _detalle_coefs(fila):
        """Tabla HTML con variables, coef LP, p-val LP, coef CP, p-val CP y dummies."""
        xv = [v for v in str(fila.get('vars_safe', '')).split('|') if v]
        modelo = fila.get('modelo', '')
        rows = []
        for x in xv:
            label = COL_LABEL.get(x, x)
            # LP
            if modelo == 'ARDL':
                lp_c, lp_p = fila.get(f'lr_coef_{x}'), fila.get(f'lr_pval_{x}')
            elif modelo == 'VAR':
                lp_c, lp_p = fila.get(f'sum_coef_{x}'), fila.get(f'wald_pval_{x}')
            elif modelo == 'VECM':
                lp_c, lp_p = fila.get(f'beta_coef_{x}'), fila.get(f'beta_pval_{x}')
            else:
                lp_c = lp_p = float('nan')
            # CP
            if modelo == 'ARDL':
                cp_c, cp_p = fila.get(f'coef_{x}'), fila.get(f'pval_{x}')
            elif modelo == 'VAR':
                cp_c, cp_p = fila.get(f'irf_{x}_h0', fila.get(f'coef_{x}')), \
                             fila.get(f'irfpval_{x}_h0', fila.get(f'pval_{x}'))
            elif modelo == 'VECM':
                cp_c, cp_p = fila.get(f'gamma_coef_{x}'), fila.get(f'gamma_pval_{x}')
            else:
                cp_c = cp_p = float('nan')
            rows.append({
                'Variable': label, 'Coef LP': lp_c, 'p-val LP': lp_p,
                'Coef CP': cp_c, 'p-val CP': cp_p,
            })
        for d in DUMMY_SAFE:
            dc, dp = fila.get(f'dum_coef_{d}'), fila.get(f'dum_pval_{d}')
            if dc is None or (isinstance(dc, float) and math.isnan(dc)):
                continue
            rows.append({
                'Variable': f'[D] {COL_LABEL.get(d, d)}',
                'Coef LP': float('nan'), 'p-val LP': float('nan'),
                'Coef CP': dc, 'p-val CP': dp,
            })
        if not rows:
            return '<p class="muted">Sin coeficientes para mostrar.</p>'
        return _tabla(pd.DataFrame(rows), max_rows=50)

    def _top_block(df_src, criterio, asc, titulo, ncoef=5):
        if df_src.empty or criterio not in df_src.columns:
            return ''
        top = (df_src.dropna(subset=[criterio])
                     .sort_values(criterio, ascending=asc)
                     .drop_duplicates(subset=['vars_safe', 'modelo'])
                     .head(10).reset_index(drop=True))
        top_tbl = _tabla(top, max_rows=10,
                         cols=['modelo', 'vars_label', 'aic', 'bic', 'hq', 'r2', 'nobs'],
                         titulo=titulo)
        # Detalle de coefs del Top-N (ncoef primeros)
        det = '<div style="margin-left:12px">'
        for i, (_, fila) in enumerate(top.head(ncoef).iterrows(), 1):
            det += (f'<h4>#{i} — {fila["modelo"]} | {fila.get("vars_label", "")[:120]} '
                    f'| AIC={fila.get("aic", float("nan")):.3f} '
                    f'BIC={fila.get("bic", float("nan")):.3f} '
                    f'HQ={fila.get("hq", float("nan")):.3f} '
                    f'R²={fila.get("r2", float("nan")):.4f}</h4>')
            det += _detalle_coefs(fila)
        det += '</div>'
        return top_tbl + det

    rankings_html = ''
    if not df_res.empty:
        # Global por AIC/BIC/HQ
        rankings_html += '<h3>Ranking GLOBAL</h3>'
        rankings_html += _top_block(df_res, 'aic', True,  'Top 10 GLOBAL por AIC', ncoef=3)
        rankings_html += _top_block(df_res, 'bic', True,  'Top 10 GLOBAL por BIC', ncoef=3)
        rankings_html += _top_block(df_res, 'hq',  True,  'Top 10 GLOBAL por HQ',  ncoef=3)
        # Por tipo de modelo
        for _m in ['ARDL', 'VAR', 'VECM']:
            _df_m = df_res[df_res['modelo'] == _m]
            if _df_m.empty:
                continue
            rankings_html += f'<h3>Ranking — {_m}</h3>'
            rankings_html += _top_block(_df_m, 'aic', True, f'Top 10 {_m} por AIC', ncoef=2)
            rankings_html += _top_block(_df_m, 'bic', True, f'Top 10 {_m} por BIC', ncoef=2)
            rankings_html += _top_block(_df_m, 'hq',  True, f'Top 10 {_m} por HQ',  ncoef=2)

    secciones.append(f'''
    <section id="sec11">
      <h2>11. Ranking y mejor modelo</h2>
      {rankings_html}
      {_img('sec11_boxplot_criterios', 'Distribución de IC/R² por tipo de modelo')}
      <h3>Real vs Ajustado — Mejor modelo GLOBAL</h3>
      {_img('sec11_real_vs_ajustado', 'Mejor modelo global — Real vs Ajustado')}
      <h3>Real vs Ajustado — Mejor por tipo de modelo</h3>
      {_img('sec11_real_vs_ajustado_ardl', 'Mejor ARDL — Real vs Ajustado')}
      {_img('sec11_real_vs_ajustado_var',  'Mejor VAR — Real vs Ajustado')}
      {_img('sec11_real_vs_ajustado_vecm', 'Mejor VECM — Real vs Ajustado')}
      <p class="muted" style="margin-top:14px;font-size:12px">
        <b>Nota sobre dummies:</b> al ser variables exógenas binarias (0/1), las dummies
        actúan como shocks de impacto y no entran en la relación de cointegración (β)
        ni en la suma de coeficientes de largo plazo. Por eso <i>Coef LP</i> y
        <i>p-val LP</i> aparecen como NaN — solo tienen interpretación de corto plazo.
      </p>
    </section>''')

    # ── HTML armado ───────────────────────────────────────────────────────────
    nav_links = ''.join(
        f'<a href="#sec{s}">§ {s}</a>' for s in ['3','5','6','7','8','9','10','11'])

    # Mapa sección → nombre de caché que invalidar al re-ejecutar
    _CACHE_MAP = {
        '5': '', '6': 'est', '7': 'ardl', '8': 'var', '9': 'vecm',
        '10': 'consolidado', '11': '',
    }
    _btn_js = '''
<script>
const SEC_CACHE = ''' + str(_CACHE_MAP).replace("'", '"') + ''';
function runSection(sec) {
  const cache = SEC_CACHE[sec] || '';
  const invalidate = cache ? ('&invalidate=' + cache) : '';
  const btn = document.getElementById('btn-sec' + sec);
  btn.disabled = true; btn.textContent = '⏳ ejecutando...';
  fetch('/api/run?secciones=' + sec + '&reuse=1' + invalidate)
    .then(r => r.json())
    .then(d => {
      btn.textContent = d.ok ? '✅ listo (recargando)' : '❌ error';
      if (d.ok) setTimeout(() => location.reload(), 800);
      else { console.error(d); alert('Error: ' + (d.error || 'ver consola')); btn.disabled = false; btn.textContent = '🔁 Re-ejecutar'; }
    })
    .catch(e => { alert('Sin servidor (corré server.py). ' + e); btn.disabled = false; btn.textContent = '🔁 Re-ejecutar'; });
}
function runAll() {
  if (!confirm('Re-correr TODAS las secciones (puede tardar)?')) return;
  fetch('/api/run?secciones=' + Object.keys(SEC_CACHE).join(',') + '&invalidate=panel,ctx,est,ardl,var,vecm,consolidado')
    .then(r => r.json()).then(d => { if (d.ok) location.reload(); else alert('Error'); });
}
</script>'''

    html = f'''<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8">
<title>Análisis Básico — Riesgo País ARG | {ETI_DEP}</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#222;background:#fafafa}}
 header{{background:#1f2937;color:#fff;padding:20px 32px;position:sticky;top:0;z-index:10}}
 header h1{{margin:0 0 6px;font-size:20px}}
 nav{{margin-top:8px}}
 nav a{{color:#9ec5fe;margin-right:14px;text-decoration:none;font-size:13px}}
 nav a:hover{{text-decoration:underline}}
 main{{max-width:1200px;margin:0 auto;padding:24px 32px 80px}}
 section{{background:#fff;padding:20px 24px;margin:18px 0;border-radius:8px;
         box-shadow:0 1px 3px rgba(0,0,0,.06)}}
 section h2{{margin-top:0;border-bottom:2px solid #1f2937;padding-bottom:6px;font-size:18px}}
 section h3{{margin-top:24px;color:#374151;font-size:15px}}
 section h4{{margin:14px 0 6px;color:#4b5563;font-size:13px;text-transform:uppercase;letter-spacing:.4px}}
 figure{{margin:14px 0;text-align:center}}
 figure img{{max-width:100%;height:auto;border:1px solid #e5e7eb;border-radius:4px}}
 figcaption{{font-size:12px;color:#6b7280;margin-top:6px;font-style:italic}}
 table.tbl{{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0 16px}}
 table.tbl th, table.tbl td{{padding:6px 10px;border-bottom:1px solid #e5e7eb;text-align:left}}
 table.tbl thead{{background:#f3f4f6}}
 table.tbl tbody tr:hover{{background:#fafbff}}
 ul{{line-height:1.6}}
 .muted{{color:#9ca3af;font-style:italic}}
 .warn{{color:#b91c1c}}
 footer{{text-align:center;color:#6b7280;font-size:12px;padding:24px}}
</style></head>
<body>
<header>
  <h1>Análisis Básico — Riesgo País Argentino
    <button onclick="runAll()" style="float:right;padding:6px 12px;background:#dc2626;color:#fff;border:0;border-radius:4px;cursor:pointer;font-size:12px">🔄 Re-correr TODO</button>
  </h1>
  <div style="font-size:13px;opacity:.85">
    Y = <b>{ETI_DEP}</b> · Frecuencia: {FREQ} (cap {LAG_CAP} lags) · Generado: {datetime.now():%Y-%m-%d %H:%M}
  </div>
  <nav>{nav_links}</nav>
</header>
<main>
  {''.join(secciones)}
</main>
<footer>Trabajo Final — Lic. en Economía, UNC · Martín Gómez Pizarro · <span class="muted">Botones requieren server.py corriendo</span></footer>
{_btn_js}
</body></html>'''

    # Inyectar botón en cada h2 de sección (sec3, sec6, sec7, sec8, sec9, sec10, sec11)
    import re as _re_btn
    def _inject_btn(match):
        secid = match.group(1)  # ej "sec7"
        snum = secid.replace('sec', '')
        btn = (f'<button id="btn-{secid}" onclick="runSection(\'{snum}\')" '
               f'style="float:right;padding:4px 10px;background:#1f2937;color:#fff;'
               f'border:0;border-radius:4px;cursor:pointer;font-size:11px">🔁 Re-ejecutar</button>')
        return match.group(0) + btn
    html = _re_btn.sub(r'<h2>(?=[^<]*(?:Modelos|Estacionariedad|Consolidaci|Ranking|Configuraci))',
                       lambda m: m.group(0), html)  # placeholder; do below
    # Mejor: insertar botón justo después de <h2> dentro de cada section
    html = _re_btn.sub(
        r'(<section id="(sec\d+(?:\.\d+)?)">\s*<h2>)([^<]+)(</h2>)',
        lambda m: (f'{m.group(1)}{m.group(3)} '
                   f'<button id="btn-{m.group(2)}" onclick="runSection(\'{m.group(2).replace("sec","")}\')" '
                   f'style="float:right;padding:4px 10px;background:#1f2937;color:#fff;'
                   f'border:0;border-radius:4px;cursor:pointer;font-size:11px">🔁 Re-ejecutar</button>'
                   f'{m.group(4)}'),
        html)

    out = OUTPUT_DIR / 'reporte.html'
    out.write_text(html, encoding='utf-8')
    print(f'  📄 Reporte HTML guardado: {out}')
    return out


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Análisis Básico - Riesgo País ARG')
    parser.add_argument('--seccion', type=str, help='Ejecutar solo una sección (ej: 7)')
    parser.add_argument('--secciones', type=str, help='Ejecutar varias secciones (ej: 7,8)')
    parser.add_argument('--hasta', type=str, help='Ejecutar hasta sección N inclusive')
    parser.add_argument('--backend', type=str, default='Agg',
                        help='Matplotlib backend (Agg, TkAgg, etc.)')
    parser.add_argument('--reuse-cache', action='store_true',
                        help='Cargar resultados previos desde outputs/.../cache/ si existen')
    parser.add_argument('--invalidate', type=str, default='',
                        help='Coma-lista de nombres de caché a borrar antes de correr '
                             '(panel,ctx,est,ardl,var,vecm,consolidado)')
    parser.add_argument('--csv', type=str, default=None,
                        help='Nombre del CSV en notebooks/Variables Regresivas/ '
                             '(default: el último analisis_series_*.csv)')
    args = parser.parse_args()

    REUSE = args.reuse_cache
    if args.invalidate:
        _cache_invalidate([n.strip() for n in args.invalidate.split(',') if n.strip()])

    matplotlib.use(args.backend)

    # Determinar qué secciones ejecutar
    ALL_SECTIONS = ['3', '4', '4.5', '5', '6', '7', '8', '9', '10', '11', 'B']
    if args.seccion:
        run_sections = {args.seccion}
    elif args.secciones:
        run_sections = set(args.secciones.split(','))
    elif args.hasta:
        idx = ALL_SECTIONS.index(args.hasta) if args.hasta in ALL_SECTIONS else len(ALL_SECTIONS) - 1
        run_sections = set(ALL_SECTIONS[:idx + 1])
    else:
        run_sections = set(ALL_SECTIONS)

    def should_run(sec):
        return sec in run_sections

    print('╔══════════════════════════════════════════════════════════════════╗')
    print('║  ANÁLISIS BÁSICO — Riesgo País Argentino                       ║')
    print('║  Trabajo Final de Grado — Lic. en Economía, UNC                ║')
    print(f'║  {datetime.now().strftime("%Y-%m-%d %H:%M:%S"):>62} ║')
    print('╚══════════════════════════════════════════════════════════════════╝')
    print(f'\nSecciones a ejecutar: {sorted(run_sections)}')
    print(f'Output: {OUTPUT_DIR}\n')

    # Siempre necesitamos el CATALOG
    CATALOG_VIZ = _parse_catalog()
    print(f'✅ CATALOG parseado: {len(CATALOG_VIZ)} series')

    # Sección 3: Config
    config = seccion_3_configuracion()
    if args.csv:
        config['CSV_ANALISIS'] = args.csv
        print(f'  📌 CSV forzado por CLI: {args.csv}')

    def _need(sec, *deps):
        """Sección a correr (la pidió el usuario o la pide una dependencia)."""
        return should_run(sec) or any(d for d in deps)

    # ── Panel (sec 4) ────────────────────────────────────────────────────────
    panel_cache = _cache_load('panel') if REUSE else None
    if panel_cache is None:
        df_panel, df_csv, _LISTA_SERIES, FRECUENCIA_USADA, _DEP_LABELS = seccion_4_carga_panel(config, CATALOG_VIZ)
        _cache_save('panel', {'df_panel': df_panel, 'df_csv': df_csv,
                              '_LISTA_SERIES': _LISTA_SERIES,
                              'FRECUENCIA_USADA': FRECUENCIA_USADA,
                              '_DEP_LABELS': _DEP_LABELS})
    else:
        print('♻️  Panel cargado desde caché')
        df_panel = panel_cache['df_panel']; df_csv = panel_cache['df_csv']
        _LISTA_SERIES = panel_cache['_LISTA_SERIES']; FRECUENCIA_USADA = panel_cache['FRECUENCIA_USADA']
        _DEP_LABELS = panel_cache.get('_DEP_LABELS', set())

    # ── Ctx (sec 4.5) ────────────────────────────────────────────────────────
    ctx_cache = _cache_load('ctx') if REUSE else None
    if ctx_cache is None:
        ctx = seccion_45_seleccion_dependiente(df_panel, _LISTA_SERIES, FRECUENCIA_USADA, config, dep_labels=_DEP_LABELS)
        _cache_save('ctx', ctx)
    else:
        print('♻️  Ctx cargado desde caché')
        ctx = ctx_cache

    # Sec 5
    if should_run('5'):
        seccion_5_descriptivos(df_panel, ctx['ETI_DEP'])

    # ── Estacionariedad (sec 6) ──────────────────────────────────────────────
    est_cache = _cache_load('est') if REUSE else None
    if est_cache is None:
        est_ctx = seccion_6_estacionariedad(df_panel, ctx)
        _cache_save('est', est_ctx)
    else:
        print('♻️  Estacionariedad cargada desde caché')
        est_ctx = est_cache

    # ── ARDL (sec 7) ─────────────────────────────────────────────────────────
    ardl_res = {}
    ardl_cache = _cache_load('ardl') if REUSE else None
    if should_run('7') and ardl_cache is None:
        ardl_res = seccion_7_ardl(ctx, est_ctx, config)
        _cache_save('ardl', ardl_res)
    elif ardl_cache is not None:
        print('♻️  ARDL cargado desde caché')
        ardl_res = ardl_cache

    # ── VAR (sec 8) ──────────────────────────────────────────────────────────
    var_res = {}
    var_cache = _cache_load('var') if REUSE else None
    if should_run('8') and var_cache is None:
        var_res = seccion_8_var(ctx, est_ctx, config)
        _cache_save('var', var_res)
    elif var_cache is not None:
        print('♻️  VAR cargado desde caché')
        var_res = var_cache

    # ── VECM (sec 9) ─────────────────────────────────────────────────────────
    vecm_res = {}
    vecm_cache = _cache_load('vecm') if REUSE else None
    if should_run('9') and vecm_cache is None:
        vecm_res = seccion_9_vecm(ctx, est_ctx, config, var_res=var_res if var_res else None)
        _cache_save('vecm', vecm_res)
    elif vecm_cache is not None:
        print('♻️  VECM cargado desde caché')
        vecm_res = vecm_cache

    # ── Consolidación (sec 10) ───────────────────────────────────────────────
    df_res = pd.DataFrame(); df_largo = pd.DataFrame(); df_dum = pd.DataFrame()
    cons_cache = _cache_load('consolidado') if REUSE else None
    if should_run('10') and cons_cache is None:
        df_res, df_largo, df_dum = seccion_10_consolidacion(ctx, ardl_res, var_res, vecm_res, config)
        _cache_save('consolidado', {'df_res': df_res, 'df_largo': df_largo, 'df_dum': df_dum})
    elif cons_cache is not None:
        print('♻️  Consolidación cargada desde caché')
        df_res = cons_cache['df_res']; df_largo = cons_cache['df_largo']; df_dum = cons_cache['df_dum']

    # Sección 11: Ranking
    if should_run('11') and not df_res.empty:
        seccion_11_ranking(df_res, df_largo, ctx, est_ctx, config, ardl_res)

    # Apéndice B: Diagnóstico residuos
    if should_run('B') and not df_res.empty:
        seccion_B_diagnostico_residuos(df_res, ctx, est_ctx, config, ardl_res)

    # Reporte HTML (siempre que haya consolidación)
    if should_run('10'):
        try:
            generar_reporte_html(ctx, est_ctx, ardl_res, var_res, vecm_res,
                                  df_res, df_largo, df_dum, config)
        except Exception as _e:
            print(f'  ⚠️ No se pudo generar reporte HTML: {_e}')

    print(f'\n{"="*70}')
    print(f'  EJECUCIÓN COMPLETADA — {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'  Gráficos guardados en: {OUTPUT_DIR}')
    print(f'{"="*70}')


if __name__ == '__main__':
    main()
