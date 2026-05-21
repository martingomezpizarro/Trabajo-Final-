import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import subprocess, sys, os, re

def _install(pkg):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '-q'])

for _pkg in ['statsmodels', 'scipy', 'scikit-learn', 'openpyxl', 'matplotlib', 'numpy', 'pandas', 'ipywidgets']:
    try:
        __import__(_pkg.replace('-', '_'))
    except ImportError:
        print(f'Instalando {_pkg}...')
        _install(_pkg)



import warnings
import glob
import random
from itertools import combinations
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display

warnings.filterwarnings('ignore')

sys.path.insert(0, '.')
from src.utils import test_estacionariedad, test_causalidad_granger, resumen_estadistico

print('Módulos cargados.')

# ── Directorios base (igual que generar_visualizador.py) ─────────────────────
VARS_DIR = (Path('..') / 'data' / 'Variables Finales').resolve()
RAW_DIR  = (Path('..') / 'data' / 'raw').resolve()

# ── 1. Parsear CATALOG desde visualizador_template.html ──────────────────────
def _parse_catalog():
    for _cand in [Path('visualizador_template.html'),
                  Path('notebooks') / 'visualizador_template.html']:
        if _cand.exists():
            html_path = _cand
            break
    else:
        raise FileNotFoundError('No se encontró visualizador_template.html')

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Acotar búsqueda solo a la sección CATALOG (evita falsos matches en JS posterior)
    _start = content.find('const CATALOG = [')
    _end   = content.find('\n];', _start)
    catalog_txt = content[_start:_end + 3] if _start >= 0 and _end >= 0 else content

    cat = {}
    _PREF    = {'D': 0, 'W': 1, 'M': 2, 'Q': 3, 'A': 4}
    _FREQ_RE = re.compile(r"freq\s*:\s*'([^']+)'")

    # ── Paso 1: ítems de fuente única (todos los campos en una sola línea) ────
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

    # ── Paso 2: ítems multi-fuente (sources:[...] en varias líneas) ───────────
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
            'id'     : cid,
            'file'   : best['file'],
            'dateCol': best['dateCol'],
            'valCol' : best['valCol'],
            'freq'   : best['freq'],
            'sources': srcs,
        }

    return cat


CATALOG_VIZ = _parse_catalog()
print(f'✅ CATALOG parseado: {len(CATALOG_VIZ)} series')


# ── 2. Detección automática de frecuencia ─────────────────────────────────────
def detectar_frecuencia(df_csv):
    _ORD = {'D': 0, 'W': 1, 'M': 2, 'Q': 3, 'A': 4}
    finest = []
    for _, row in df_csv.iterrows():
        for col in ['Serie A', 'Serie B']:
            nombre = str(row.get(col, '') or '').strip()
            if not nombre or nombre in ('', '—', '-', 'nan'):
                continue
            if nombre not in CATALOG_VIZ:
                continue
            meta = CATALOG_VIZ[nombre]
            if 'sources' in meta:
                src_freqs = [s['freq'] for s in meta['sources']]
                finest.append(min(src_freqs, key=lambda f: _ORD.get(f, 99)))
            else:
                finest.append(meta.get('freq', 'D'))
    if not finest:
        return 'M'
    return max(finest, key=lambda f: _ORD.get(f, -1))


# ── 3. Resampling (media por período, igual que el visualizador JS) ───────────
def _resample_mean(serie: pd.Series, to_freq: str) -> pd.Series:
    _MAP = {'D': 'D', 'W': 'W', 'M': 'ME', 'Q': 'QE', 'A': 'YE'}
    pf = _MAP.get(to_freq, to_freq)
    try:
        return serie.resample(pf).mean()
    except ValueError:
        _MAP_OLD = {'D': 'D', 'W': 'W', 'M': 'M', 'Q': 'Q', 'A': 'A'}
        return serie.resample(_MAP_OLD.get(to_freq, to_freq)).mean()


# ── 4. Carga genérica ─────────────────────────────────────────────────────────
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
        raise KeyError(f'col_fecha "{col_fecha}" no encontrada en {path.name}. '
                       f'Cols: {list(df.columns[:8])}')
    if vc is None:
        raise KeyError(f'col_valor "{col_valor}" no encontrada en {path.name}. '
                       f'Cols: {list(df.columns[:8])}')
    df['_f'] = pd.to_datetime(df[dc], errors='coerce')
    df = df.dropna(subset=['_f']).set_index('_f').sort_index()
    return pd.to_numeric(df[vc], errors='coerce').dropna()


# ── 5. Deflactores ────────────────────────────────────────────────────────────
_cache_pbi = _cache_cer = _cache_tip = _cache_mep = None

def _get_pbi():
    global _cache_pbi
    if _cache_pbi is not None: return _cache_pbi
    p = _buscar_archivo('pbi_constante_2004.csv')
    if p is None: print('  ⚠️  pbi_constante_2004.csv no encontrado'); return None
    _cache_pbi = _leer_serie_csv(p, 'fecha', 'pbi'); return _cache_pbi

def _get_cer():
    global _cache_cer
    if _cache_cer is not None: return _cache_cer
    p = _buscar_archivo('cer.csv', 'bcra/cer.csv')
    if p is None: print('  ⚠️  cer.csv no encontrado'); return None
    _cache_cer = _leer_serie_csv(p, 'fecha', 'cer'); return _cache_cer

def _get_tip():
    global _cache_tip
    if _cache_tip is not None: return _cache_tip
    p = _buscar_archivo('tip_etf.csv', 'global/tip_etf.csv')
    if p is None: print('  ⚠️  tip_etf.csv no encontrado'); return None
    _cache_tip = _leer_serie_csv(p, 'fecha', 'tip_close'); return _cache_tip

def _get_mep():
    global _cache_mep
    if _cache_mep is not None: return _cache_mep
    p = _buscar_archivo('brecha_cambiaria.csv')
    if p is None: print('  ⚠️  brecha_cambiaria.csv no encontrado'); return None
    _cache_mep = _leer_serie_csv(p, 'fecha', 'mep'); return _cache_mep


def _alinear_deflactor(raw: pd.Series, frecuencia: str,
                        target_index: pd.DatetimeIndex) -> pd.Series | None:
    """
    Resamplea `raw` a `frecuencia`, luego alinea con `target_index`.
    Maneja datos de baja frecuencia (ej. PBI trimestral) rellenando con ffill+bfill
    para que no queden NaN en el rango de análisis.
    """
    al = _resample_mean(raw, frecuencia)
    # Para frecuencias más bajas que la de la serie (ej. PBI trim → mensual),
    # solo quedan datos en los períodos exactos del deflactor.
    # reindex+ffill propaga cada valor hasta el siguiente período.
    al = al.reindex(target_index, method='ffill').ffill().bfill()
    if al.isna().all():
        return None
    return al


def _aplicar_deflactor(serie: pd.Series, deflactor_name: str,
                        frecuencia: str) -> pd.Series:
    if not deflactor_name or str(deflactor_name).strip() in ('', '—', '-', 'nan'):
        return serie
    for d in str(deflactor_name).split(','):
        d = d.strip().upper()
        if not d or d in ('—', '-'): continue

        if d == 'PBI':
            raw = _get_pbi()
            if raw is None: continue
            al = _alinear_deflactor(raw, frecuencia, serie.index)
            if al is None:
                print('  ⚠️  PBI: sin superposición de fechas con la serie'); continue
            fp = al.iloc[0]
            serie = serie * fp / al

        elif d == 'CER':
            raw = _get_cer()
            if raw is None: continue
            al = _alinear_deflactor(raw, frecuencia, serie.index)
            if al is None:
                print('  ⚠️  CER: sin superposición de fechas con la serie'); continue
            lc = al.iloc[-1]
            serie = serie / al * lc

        elif d in ('TIP', 'IPC'):
            raw = _get_tip()
            if raw is None: continue
            al = _alinear_deflactor(raw, frecuencia, serie.index)
            if al is None:
                print(f'  ⚠️  {d}: sin superposición de fechas con la serie'); continue
            lt = al.iloc[-1]
            serie = serie / al * lt

        elif d == 'MEP':
            raw = _get_mep()
            if raw is None: continue
            al = _alinear_deflactor(raw, frecuencia, serie.index)
            if al is None:
                print('  ⚠️  MEP: sin superposición de fechas con la serie'); continue
            serie = serie / al

        else:
            print(f'    ⚠️  Deflactor no reconocido: "{d}"')
    return serie


# ── 6. Carga de serie desde CATALOG ──────────────────────────────────────────
def _cargar_serie_catalog(label: str, frecuencia: str,
                           fecha_inicio: str = None, fecha_fin: str = None):
    """
    Carga la serie `label` (nombre exacto del CATALOG) en la frecuencia indicada.
    Devuelve pd.Series o None si no se encuentra / hay error.
    """
    if label not in CATALOG_VIZ:
        print(f'  ⚠️  "{label}" no encontrado en CATALOG ({len(CATALOG_VIZ)} series).')
        return None

    meta  = CATALOG_VIZ[label]
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

    if fecha_inicio: serie = serie[serie.index >= pd.Timestamp(fecha_inicio)]
    if fecha_fin:    serie = serie[serie.index <= pd.Timestamp(fecha_fin)]

    return _resample_mean(serie, frecuencia).dropna()


# ── 7. Construcción de variable desde fila CSV ────────────────────────────────
def construir_variable(row: pd.Series, frecuencia: str,
                        fecha_inicio: str, fecha_fin: str):
    """
    Interpreta una fila del CSV de análisis y devuelve (serie, etiqueta).

    Flujo:
      1. Carga Serie A desde CATALOG (por su nombre original, SIN deflactor).
      2. Aplica Deflactor A si corresponde.
      3. Carga Serie B si corresponde y aplica Deflactor B.
      4. Opera A y B según "Operación".
      5. Aplica Log y/o Diferencia sobre el resultado final.
    """
    nombre_a  = str(row.get('Serie A',   '') or '').strip()
    defl_a    = str(row.get('Deflactor A','') or '').strip()
    nombre_b  = str(row.get('Serie B',   '') or '').strip()
    defl_b    = str(row.get('Deflactor B','') or '').strip()
    operacion = str(row.get('Operación', 'Solo A') or 'Solo A').strip()
    log_flag  = str(row.get('Log', 'No') or 'No').strip().lower() not in ('no', '0', 'false', '')
    n_diff    = int(float(str(row.get('Dif.', 0) or 0) or 0))

    # Etiqueta legible: solo incluye deflactor y serie B si realmente se aplican
    _b_activo  = operacion != 'Solo A' and nombre_b not in ('', '—', '-', 'nan')
    _da_activo = defl_a not in ('', '—', '-', 'nan')
    _db_activo = _b_activo and defl_b not in ('', '—', '-', 'nan')

    etiqueta = nombre_a
    if _da_activo:    etiqueta += f'/{defl_a}'
    if _b_activo:     etiqueta += f' {operacion} {nombre_b}'
    if _db_activo:    etiqueta += f'/{defl_b}'
    if log_flag:      etiqueta  = f'log({etiqueta})'
    if n_diff > 0:    etiqueta  = ('Δ' * n_diff) + etiqueta

    # 1. Cargar Serie A (siempre por nombre original, sin deflactor)
    sa = _cargar_serie_catalog(nombre_a, frecuencia, fecha_inicio, fecha_fin)
    if sa is None:
        return None, etiqueta

    # 2. Deflactar Serie A
    sa = _aplicar_deflactor(sa, defl_a, frecuencia)
    resultado = sa.copy()

    # 3. Cargar y deflactar Serie B, luego operar con A
    if _b_activo:
        sb = _cargar_serie_catalog(nombre_b, frecuencia, fecha_inicio, fecha_fin)
        if sb is not None:
            sb    = _aplicar_deflactor(sb, defl_b, frecuencia)
            sb_al = sb.reindex(sa.index, method='ffill')
            # Normalizar el símbolo menos Unicode (U+2212) → guion ASCII
            op = operacion.replace(' ', '').replace('−', '-')
            if op == 'A-B':                      resultado = sa - sb_al
            elif op in ('A/B', 'A÷B'):            resultado = sa / sb_al
            elif op in ('(A-B)/B', '(A-B)/B'):    resultado = (sa - sb_al) / sb_al
            elif op == 'A+B':                     resultado = sa + sb_al
            elif op in ('A*B', 'A×B'):             resultado = sa * sb_al
            elif op in ('SoloB', 'B'):             resultado = sb_al.copy()

    # 4. Transformaciones finales sobre el resultado de la operación
    if log_flag:
        resultado = np.log(resultado.replace(0, np.nan))
    for _ in range(n_diff):
        resultado = resultado.diff()

    resultado = resultado.dropna()
    resultado.name = etiqueta
    return resultado, etiqueta


# ── 8. Validación rápida del CATALOG vs CSV ───────────────────────────────────
def _validar_catalog_vs_csv(df_csv):
    print('\n── Validación CATALOG vs CSV ────────────────────────────────────────')
    seen = set()
    for _, row in df_csv.iterrows():
        for col in ['Serie A', 'Serie B']:
            nombre = str(row.get(col, '') or '').strip()
            if not nombre or nombre in ('', '—', '-', 'nan') or nombre in seen:
                continue
            seen.add(nombre)
            if nombre not in CATALOG_VIZ:
                print(f'  ❌ NO en CATALOG: "{nombre}"')
                continue
            meta      = CATALOG_VIZ[nombre]
            file_name = meta.get('file', '?')
            existe    = (VARS_DIR / file_name).exists() or (RAW_DIR / file_name).exists()
            print(f'  {"✅" if existe else "⚠️ "} {nombre[:55]:<55} → {file_name}'
                  f'{"" if existe else "  (¡FALTA ARCHIVO!)"}')
    print('────────────────────────────────────────────────────────────────────\n')


print('✅ Funciones auxiliares listas.')
print(f'   VARS_DIR: {VARS_DIR}')
print(f'   RAW_DIR:  {RAW_DIR}')

# ── Archivo CSV ───────────────────────────────────────────────────────────────
# El visualizador descarga el archivo a la carpeta del navegador.
# Copiarlo a: notebooks/Variables Regresivas/
# Dejar None para que tome automáticamente el más reciente.
# Para un archivo específico usar solo el nombre: 'analisis_series_2026-05-06.csv'
CSV_ANALISIS = None   # None = el más reciente en notebooks/Variables Regresivas/

# ── Variable dependiente ──────────────────────────────────────────────────────
# Se elige en la Sección 4.5, luego de cargar y mostrar todas las series.

# ── Frecuencia ────────────────────────────────────────────────────────────────
# 'auto' = detecta la frecuencia más gruesa disponible entre todas las series
# Alternativas explícitas: 'D' 'W' 'M' 'Q' 'A'
FRECUENCIA = 'auto'

# ── Fechas ────────────────────────────────────────────────────────────────────
FECHA_INICIO = '2007-01-01'
FECHA_FIN    = '2026-03-31'

# ── Lags máximos ──────────────────────────────────────────────────────────────
MAX_LAGS_DEP = 4   # rezagos Y en ARDL
MAX_LAGS_IND = 4   # rezagos X en ARDL
MAX_LAGS_VAR = 8   # selección de rezagos en VAR/VECM

# ── Combinaciones ─────────────────────────────────────────────────────────────
# None = TODAS las combinaciones posibles de TODOS los tamaños
MAX_VARS_POR_MODELO = None   # None = sin límite (todas las variables)
MAX_COMBINACIONES   = None   # None = sin límite (todas las combinaciones)
SEMILLA             = 42

# ── Criterios de información ──────────────────────────────────────────────────
CRITERIOS_SEL = ['aic', 'bic', 'hqic']

# ── Nivel de significancia ────────────────────────────────────────────────────
NIVEL_SIG = 0.05

# Modelos a correr: ejecutar independientemente secciones 7 (ARDL), 8 (VAR), 9 (VECM)

print('✅ Configuración guardada.')

# ── Análisis de Exogeneidad (exclusivo de esta notebook) ──────────────────

# Pesos para el score de exogeneidad compuesto
W_PVALUE = 0.35   # Peso del p-value promedio cuando actúa como X
W_R2INV  = 0.25   # Peso del R² invertido cuando actúa como Y
W_FREQ   = 0.25   # Peso de la frecuencia de significancia como X
W_BIC    = 0.15   # Peso de la parsimonia (BIC) de modelos donde participa

# ¿Probar TODAS las variables como dependientes? (lento pero completo)
TODAS_COMO_DEPENDIENTE = True   # True = completo, False = solo EMBI como Y

# Lags para prewhitening
MAX_AR_ORDER = 4   # Orden máximo AR
MAX_MA_ORDER = 4   # Orden máximo MA

# Top N variables para VECM (usar las mejor rankeadas)
TOP_N_VECM = 5

print('✅ Configuración extendida guardada.')

# ══════════════════════════════════════════════════════════════════════════════
#  ELEGÍ LA VARIABLE DEPENDIENTE — cambiá solo el número de abajo
#  y volvé a correr esta celda
# ══════════════════════════════════════════════════════════════════════════════

# Auto-detecta riesgo país; si no lo encuentra usa 1
_KEYWORDS_DEP = ['embi', 'riesgo', 'spread', 'cds', 'country risk']
_auto_idx = next(
    (i + 1 for i, c in enumerate(_LISTA_SERIES)
     if any(kw in c.lower() for kw in _KEYWORDS_DEP)),
    1
)

VARIABLE_DEPENDIENTE = _auto_idx   # ← CAMBIÁ ESTE NÚMERO SI QUERÉS OTRA VARIABLE

# ── Lista disponible ──────────────────────────────────────────────────────────
print('═' * 65)
for _i, _c in enumerate(_LISTA_SERIES, 1):
    marca = '  ◄ seleccionada' if _i == VARIABLE_DEPENDIENTE else ''
    print(f'  [{_i:>2}]  {_c}{marca}')
print('═' * 65)

# ── Aplicar selección ─────────────────────────────────────────────────────────
if not (1 <= VARIABLE_DEPENDIENTE <= len(_LISTA_SERIES)):
    raise ValueError(f'VARIABLE_DEPENDIENTE={VARIABLE_DEPENDIENTE} fuera de rango (1–{len(_LISTA_SERIES)})')

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

# ═══════════════════════════════════════════════════════════════════════════
# 7.1a  ESTRUCTURAS ARMA INDIVIDUALES (auto_arima)
# ═══════════════════════════════════════════════════════════════════════════

try:
    from pmdarima import auto_arima as _auto_arima_ind
except ImportError:
    import subprocess as _sp_ind, sys as _sys_ind
    _sp_ind.check_call([_sys_ind.executable, '-m', 'pip', 'install', 'pmdarima', '-q'])
    from pmdarima import auto_arima as _auto_arima_ind

print('═'*70)
print('7.1a  ESTRUCTURAS ARMA INDIVIDUALES (auto_arima)')
print('═'*70)

arma_orders = {}

for _v in df_safe.columns:
    _s = df_safe[_v].dropna()
    if len(_s) < 20:
        print(f'  ⚠️  {COL_LABEL.get(_v, _v)[:40]:<40}  n={len(_s)} insuficiente')
        arma_orders[_v] = {'order': (0, 0), 'aic': np.nan}
        continue
    try:
        _fit = _auto_arima_ind(
            _s.values, information_criterion='aic',
            stepwise=True, seasonal=False, d=0,
            max_p=MAX_AR_ORDER, max_q=MAX_MA_ORDER,
            suppress_warnings=True, error_action='ignore',
        )
        _p, _, _q = _fit.order
        _aic = _fit.aic() if hasattr(_fit, 'aic') and callable(_fit.aic) else getattr(_fit, 'aic', np.nan)
        arma_orders[_v] = {'order': (_p, _q), 'aic': _aic}
        print(f'  ✅ {COL_LABEL.get(_v, _v)[:40]:<40}  ARMA({_p},{_q})  AIC={_aic:.2f}')
    except Exception as _e:
        print(f'  ❌ {COL_LABEL.get(_v, _v)[:40]:<40}  error: {_e}')
        arma_orders[_v] = {'order': (0, 0), 'aic': np.nan}

_n_found = sum(1 for v in arma_orders if arma_orders[v]['order'] != (0, 0))
print(f'Estructuras ARMA identificadas: {_n_found} / {len(df_safe.columns)} variables')

# ═══════════════════════════════════════════════════════════════════════════
# 7.1b  PREWHITENING + CCF — TODAS LAS COMBINACIONES (Y_i, X_j)
# ═══════════════════════════════════════════════════════════════════════════
from statsmodels.tsa.arima.model import ARIMA as _ARIMA_mod
from statsmodels.tsa.stattools import ccf as _ccf_fn

print('═'*70)
print('7.1b  PREWHITENING + CCF — TODAS LAS COMBINACIONES (Y_i, X_j)')
print('═'*70)

bj_lags = {}

_ccf_nlags = MAX_LAGS_VAR
_z_ci = 1.96

ALL_VARS = [Y_SAFE] + X_SAFE_EST if not TODAS_COMO_DEPENDIENTE else list(df_safe.columns)

_n_pairs_ok = 0

for _yi, _yvar in enumerate(ALL_VARS):
    _y_s = df_safe[_yvar].dropna()
    for _xj, _xvar in enumerate(ALL_VARS):
        if _xvar == _yvar:
            continue
        
        _x_s = df_safe[_xvar].dropna()
        _df_xy = pd.concat([_y_s.rename('y'), _x_s.rename('x')], axis=1).dropna()
        
        if len(_df_xy) < 30:
            bj_lags[(_yvar, _xvar)] = {'lags': [0, 1], 'ccf_max': 0.0, 'arma_order': (0, 0), 'raw': True}
            continue
        
        _arma_info = arma_orders.get(_xvar, {'order': (0, 0)})
        _p_ord, _q_ord = _arma_info['order']
        _p_ord = min(_p_ord, MAX_AR_ORDER)
        _q_ord = min(_q_ord, MAX_MA_ORDER)
        
        try:
            if _p_ord == 0 and _q_ord == 0:
                _x_w = _df_xy['x'].values
                _y_w = _df_xy['y'].values
                _raw = True
            else:
                _fit_x = _ARIMA_mod(_df_xy['x'].values, order=(_p_ord, 0, _q_ord)).fit()
                _x_resid = _fit_x.resid
                _ar_coefs = _fit_x.arparams if hasattr(_fit_x, 'arparams') and len(_fit_x.arparams) > 0 else []
                
                _y_arr = _df_xy['y'].values
                if len(_ar_coefs) > 0:
                    _p_ar = len(_ar_coefs)
                    _y_filt = np.array([
                        _y_arr[t] - np.dot(_ar_coefs, _y_arr[t - _p_ar:t][::-1])
                        for t in range(_p_ar, len(_y_arr))
                    ])
                else:
                    _y_filt = _y_arr.copy()
                
                _n_min = min(len(_x_resid), len(_y_filt))
                _x_w = _x_resid[-_n_min:]
                _y_w = _y_filt[-_n_min:]
                _raw = False
            
            _nlags_actual = min(_ccf_nlags, len(_x_w) // 3)
            _ci = _z_ci / np.sqrt(len(_x_w))
            _ccf_vals = _ccf_fn(_x_w, _y_w, nlags=_nlags_actual, alpha=None)
            
            _sig_lags = [int(l) for l in range(len(_ccf_vals)) if abs(_ccf_vals[l]) > _ci]
            _prop_lags = sorted({l for l in _sig_lags if 0 <= l <= MAX_LAGS_IND})
            if not _prop_lags:
                _prop_lags = [0, 1]
            
            _ccf_max = max(abs(_ccf_vals)) if len(_ccf_vals) > 0 else 0.0
            
            bj_lags[(_yvar, _xvar)] = {
                'lags': _prop_lags,
                'ccf_max': _ccf_max,
                'arma_order': (_p_ord, _q_ord),
                'raw': _raw,
            }
            _n_pairs_ok += 1
            
        except Exception as _e:
            bj_lags[(_yvar, _xvar)] = {'lags': [0, 1], 'ccf_max': 0.0, 'arma_order': (_p_ord, _q_ord), 'raw': True}
    
    _y_label = COL_LABEL.get(_yvar, _yvar)
    print(f'  [{_yi+1:>2}/{len(ALL_VARS)}] {_y_label[:40]:<40} → {len(ALL_VARS)-1} pares')

print(f'Pares analizados exitosamente: {_n_pairs_ok} / {len(ALL_VARS) * (len(ALL_VARS) - 1)}')

# Heatmap N×N
if bj_lags:
    _n = len(ALL_VARS)
    _mat = np.zeros((_n, _n))
    for i, _yv in enumerate(ALL_VARS):
        for j, _xv in enumerate(ALL_VARS):
            if _yv == _xv:
                _mat[i, j] = 0
            else:
                _mat[i, j] = bj_lags.get((_yv, _xv), {}).get('ccf_max', 0)
    
    fig, ax = plt.subplots(figsize=(max(6, _n*1.5), max(5, _n*1.0)))
    _labels_short = [COL_LABEL.get(v, v)[:20] for v in ALL_VARS]
    _im = ax.imshow(_mat, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    ax.set_xticks(range(_n))
    ax.set_yticks(range(_n))
    ax.set_xticklabels(_labels_short, rotation=45, ha='right', fontsize=7)
    ax.set_yticklabels(_labels_short, fontsize=7)
    ax.set_title('CCF maximo (abs) por par (Y fila → X columna)')
    plt.colorbar(_im, ax=ax, label='|CCF| maximo')
    plt.tight_layout()
    

# ═══════════════════════════════════════════════════════════════════════════
# 7.2  ESTIMACIONES ARDL EXHAUSTIVAS + DIAGNOSTICOS DE RESIDUOS
# ═══════════════════════════════════════════════════════════════════════════
from itertools import combinations
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.tsa.stattools import acf

# Importar tests de autocorrelacion con fallback
try:
    from statsmodels.stats.diagnostic import acorr_ljungbox
    _has_ljungbox = True
except ImportError:
    _has_ljungbox = False
try:
    from statsmodels.stats.diagnostic import acorr_breusch_godfrey
    _has_bg = True
except ImportError:
    _has_bg = False

print('═'*70)
print('7.2  ESTIMACIONES ARDL — TODAS LAS VARIABLES COMO DEPENDIENTES')
print('═'*70)

_y_vars = ALL_VARS if TODAS_COMO_DEPENDIENTE else [Y_SAFE]
results_list = []

_total_models = 0
for _yvar in _y_vars:
    _other = [v for v in ALL_VARS if v != _yvar]
    _all_combos = []
    for k in range(1, len(_other) + 1):
        if MAX_VARS_POR_MODELO is not None and k > MAX_VARS_POR_MODELO:
            continue
        _all_combos.extend(list(combinations(_other, k)))
    
    if MAX_COMBINACIONES is not None and len(_all_combos) > MAX_COMBINACIONES:
        random.seed(SEMILLA)
        _all_combos = random.sample(_all_combos, MAX_COMBINACIONES)
    
    print(f'  {COL_LABEL.get(_yvar, _yvar)[:40]:<40} → {len(_all_combos)} combinaciones')
    
    for _combo in _all_combos:
        try:
            _df_reg = pd.DataFrame({'y': df_safe[_yvar]})
            
            # Rezagos de Y
            for lag in range(1, MAX_LAGS_DEP + 1):
                _df_reg[f'{_yvar}_L{lag}'] = df_safe[_yvar].shift(lag)
            
            # Rezagos de X segun CCF
            for _xvar in _combo:
                _lags = bj_lags.get((_yvar, _xvar), {}).get('lags', [0, 1])
                for lag in _lags:
                    _df_reg[f'{_xvar}_L{lag}'] = df_safe[_xvar].shift(lag)
            
            _df_reg = _df_reg.dropna()
            if len(_df_reg) < 20:
                continue
            
            _y_vals = _df_reg['y']
            _X_vals = _df_reg.drop(columns=['y'])
            _X_vals = sm.add_constant(_X_vals)
            
            # Evitar rank deficiency
            if np.linalg.matrix_rank(_X_vals) < _X_vals.shape[1]:
                continue
            
            _model = sm.OLS(_y_vals, _X_vals).fit()
            _resid = _model.resid
            
            # ── Diagnosticos ──
            _dw = durbin_watson(_resid)
            
            # Ljung-Box
            _lb_p = np.nan
            if _has_ljungbox:
                try:
                    _lb_lags = min(10, len(_resid) // 5)
                    _lb_res = acorr_ljungbox(_resid, lags=_lb_lags, return_df=True)
                    if hasattr(_lb_res, 'columns'):
                        if 'lb_pvalue' in _lb_res.columns:
                            _lb_p = _lb_res['lb_pvalue'].iloc[-1]
                        elif 'pvalue' in _lb_res.columns:
                            _lb_p = _lb_res['pvalue'].iloc[-1]
                    elif isinstance(_lb_res, tuple):
                        _lb_p = _lb_res[1][-1]
                except Exception:
                    _lb_p = np.nan
            
            # Breusch-Godfrey
            _bg_p = np.nan
            if _has_bg:
                try:
                    _bg_lags = min(MAX_LAGS_VAR, len(_resid) // 5)
                    _bg_res = acorr_breusch_godfrey(_model, nlags=_bg_lags)
                    _bg_p = _bg_res[1]
                except Exception:
                    _bg_p = np.nan
            
            # Jarque-Bera
            try:
                _jb_res = jarque_bera(_resid)
                _jb_p = _jb_res[1]
            except Exception:
                _jb_p = np.nan
            
            _is_white = (_lb_p >= 0.05) and (_bg_p >= 0.05)
            
            # Orden AR en residuos (si no es ruido blanco)
            _resid_ar = None
            if not _is_white:
                try:
                    _acf_resid = acf(_resid, nlags=MAX_AR_ORDER, fft=False)
                    _sig_count = sum(1 for i in range(1, len(_acf_resid)) if abs(_acf_resid[i]) > 1.96/np.sqrt(len(_resid)))
                    _resid_ar = _sig_count if _sig_count > 0 else None
                except Exception:
                    _resid_ar = None
            
            # Coeficientes y p-values (excluyendo constante)
            _coefs = {}
            _pvals = {}
            for _col in _X_vals.columns:
                if _col == 'const':
                    continue
                _coefs[_col] = _model.params[_col]
                _pvals[_col] = _model.pvalues[_col]
            
            results_list.append({
                'y_var': _yvar,
                'x_vars': _combo,
                'n_vars': len(_combo),
                'R2_adj': _model.rsquared_adj,
                'AIC': _model.aic,
                'BIC': _model.bic,
                'HQ': getattr(_model, 'hqic', np.nan),
                'coefs': _coefs,
                'pvalues': _pvals,
                'n_obs': len(_df_reg),
                'DW': _dw,
                'LB_pvalue': _lb_p,
                'BG_pvalue': _bg_p,
                'JB_pvalue': _jb_p,
                'resid_ruido_blanco': _is_white,
                'resid_AR_order': _resid_ar,
            })
            _total_models += 1
            
        except Exception:
            continue

df_ardl_full = pd.DataFrame(results_list)

print(f'\nModelos estimados: {len(df_ardl_full)}')
if not df_ardl_full.empty:
    _n_white = df_ardl_full['resid_ruido_blanco'].sum()
    print(f'Modelos con residuos de ruido blanco: {_n_white} ({_n_white/len(df_ardl_full)*100:.1f}%)')
    
    _df_white = df_ardl_full[df_ardl_full['resid_ruido_blanco'] == True]
    if not _df_white.empty:
        _r2_media = _df_white['R2_adj'].mean()
        _bic_media_white = _df_white['BIC'].mean()
        print(f'  -> R2_adj medio (ruido blanco): {_r2_media:.4f}')
        print(f'  -> BIC medio (ruido blanco):    {_bic_media_white:.2f}')
    
    print('\n' + '═'*70)
    print('  RESUMEN DE DIAGNOSTICOS POR VARIABLE DEPENDIENTE')
    print('═'*70)
    _diag_summary = df_ardl_full.groupby('y_var').agg({
        'R2_adj': 'mean',
        'BIC': 'mean',
        'resid_ruido_blanco': 'sum',
        'n_vars': 'count',
    }).rename(columns={'resid_ruido_blanco': 'n_ruido_blanco', 'n_vars': 'n_modelos'})
    _diag_summary.index = [COL_LABEL.get(v, v)[:40] for v in _diag_summary.index]
    print(_diag_summary.round(4).to_string())
    print('═'*70)
else:
    print('⚠️  No se estimo ningún modelo.')

# ═══════════════════════════════════════════════════════════════════════════
# 7.4  Validación cruzada del ranking
# ═══════════════════════════════════════════════════════════════════════════

# TODO: Implementar validación cruzada
# Ver guía: docs/guia_02b_analisis_completo.md, Sección 7.4

print('Sección 7.4 pendiente de implementación.')

# ═══════════════════════════════════════════════════════════════════════════
# 8.1  ESTIMACIÓN VAR — TODAS LAS COMBINACIONES
#      Lags máximos dinámicos por combinación + orden Cholesky por ranking
# ═══════════════════════════════════════════════════════════════════════════
from statsmodels.tsa.api import VAR as _VAR_est
from statsmodels.stats.diagnostic import acorr_ljungbox as _lb_var
from itertools import combinations as _comb_var

print('═'*70)
print('8.1  ESTIMACIÓN VAR — TODAS LAS COMBINACIONES')
print('═'*70)

# ── Orden jerárquico de Cholesky (del ranking de exogeneidad) ──────────
if ranking_exogeneidad.empty:
    raise RuntimeError('ranking_exogeneidad vacío. Ejecutar sección 7.3.')

CHOLESKY_ORDER = list(ranking_exogeneidad.index)  # más exógena primero
print(f'Orden Cholesky (exógena → endógena):')
for _i_ch, _v_ch in enumerate(CHOLESKY_ORDER, 1):
    print(f'  [{_i_ch}] {COL_LABEL.get(_v_ch, _v_ch)}')

# ── Generar combinaciones ──────────────────────────────────────────────
_vars_est = [v for v in CHOLESKY_ORDER if v in X_SAFE_EST or v == Y_SAFE]
_combos_var = []
# VAR necesita al menos 2 variables; siempre incluimos Y_SAFE
_others = [v for v in _vars_est if v != Y_SAFE]
_max_k = len(_others) if MAX_VARS_POR_MODELO is None else min(MAX_VARS_POR_MODELO, len(_others))
for _k in range(1, _max_k + 1):
    for _c in _comb_var(_others, _k):
        _combos_var.append(list(_c))

if MAX_COMBINACIONES is not None and len(_combos_var) > MAX_COMBINACIONES:
    random.seed(SEMILLA)
    _combos_var = random.sample(_combos_var, MAX_COMBINACIONES)

print(f'\nCombinaciones a estimar: {len(_combos_var)}')
print(f'Variables disponibles:  {len(_vars_est)}')

# ── Loop de estimación ─────────────────────────────────────────────────
var_results = []
_n_ok = _n_fail = 0

for _ci, _x_combo in enumerate(_combos_var):
    try:
        # Variables del modelo: Y + combo, ordenadas según Cholesky
        _all_v = [Y_SAFE] + list(_x_combo)
        _ordered = [v for v in CHOLESKY_ORDER if v in _all_v]

        _df_var = df_safe[_ordered].dropna()
        _T = len(_df_var)
        _K = len(_ordered)

        if _T < 30:
            continue

        # ── Lags máximos dinámicos: floor((T-1) / (K+1)), mínimo 1, máximo MAX_LAGS_VAR
        _max_p = min(MAX_LAGS_VAR, max(1, int((_T - 1) / (_K + 1))))

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
        _resid_y = _fit.resid[:, _y_idx]
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

    except Exception as _e:
        _n_fail += 1
        if _n_fail == 1: print(f'Error en VAR: {type(_e).__name__}: {_e}')
        continue

    if (_ci + 1) % 50 == 0:
        print(f'  {_ci+1}/{len(_combos_var)} ...  OK={_n_ok}  fail={_n_fail}')

df_var_full = pd.DataFrame(var_results)
print(f'\n✅ Modelos VAR estimados: {len(df_var_full)}')
if not df_var_full.empty:
    _n_w = df_var_full['resid_ruido_blanco'].sum()
    _n_s = df_var_full['stable'].sum()
    print(f'   Ruido blanco: {_n_w} ({_n_w/len(df_var_full)*100:.1f}%)')
    print(f'   Estables:     {_n_s} ({_n_s/len(df_var_full)*100:.1f}%)')
    print(f'   BIC medio:    {df_var_full["BIC"].mean():.2f}')
    print(f'   R² adj medio: {df_var_full["R2_adj"].mean():.4f}')

# ═══════════════════════════════════════════════════════════════════════════
# 8.2  FEVD — TOP 5 MODELOS (ruido blanco + BIC < media)
# ═══════════════════════════════════════════════════════════════════════════

print('═'*70)
print('8.2  FEVD — DESCOMPOSICIÓN DE VARIANZA DEL ERROR DE PRONÓSTICO')
print('═'*70)

if df_var_full.empty:
    print('⚠️  Sin modelos VAR. Ejecutar sección 8.1.')
else:
    # ── Filtrar: ruido blanco + estable + BIC < media ──────────────────
    _df_ok = df_var_full[
        (df_var_full['resid_ruido_blanco'] == True) &
        (df_var_full['stable'] == True)
    ].copy()

    if _df_ok.empty:
        print('⚠️  Ningún modelo pasa ruido blanco + estabilidad.')
        print('    Usando todos los modelos estables como fallback.')
        _df_ok = df_var_full[df_var_full['stable'] == True].copy()

    if not _df_ok.empty:
        _bic_mean = _df_ok['BIC'].mean()
        _df_good = _df_ok[_df_ok['BIC'] < _bic_mean].copy()
        if _df_good.empty:
            _df_good = _df_ok.copy()
        _df_good = _df_good.sort_values('BIC').head(5).reset_index(drop=True)

        print(f'Modelos con ruido blanco + estables: {len(_df_ok)}')
        print(f'BIC medio: {_bic_mean:.2f}')
        print(f'Top 5 por BIC (de {len(_df_ok)} filtrados):\n')

        # ── Horizonte FEVD ─────────────────────────────────────────────
        FEVD_HORIZONTE = 24  # períodos hacia adelante

        _COLORS_FEVD = plt.cm.tab10.colors

        for _rank, _row in _df_good.iterrows():
            _ordered = list(_row['ordered_vars'])
            _p = int(_row['p_selected'])
            _df_v = df_safe[_ordered].dropna()

            try:
                _fit = _VAR_est(_df_v).fit(_p)
                _fevd = _fit.fevd(FEVD_HORIZONTE)
            except Exception as _e:
                print(f'  Error FEVD modelo {_rank+1}: {_e}')
                continue

            # Índice de Y en el modelo
            _y_idx = _ordered.index(Y_SAFE)
            _decomp = _fevd.decomp  # shape (horizonte, K, K)
            # FEVD de Y: _decomp[:, _y_idx, :] → (horizonte, K)
            _fevd_y = _decomp[:, _y_idx, :]  # cada columna = contribución de var j a Y

            _labels_v = [COL_LABEL.get(v, v)[:25] for v in _ordered]
            _vars_str = ', '.join([COL_LABEL.get(v, v)[:20] for v in _row['x_vars']])

            print(f'\n── Modelo {_rank+1}: BIC={_row["BIC"]:.1f}  '
                  f'p={_p}  R²adj={_row["R2_adj"]:.3f}  '
                  f'LB_p={_row["LB_pvalue"]:.3f}')
            print(f'   Vars: {_vars_str}')
            print(f'   Orden: {" → ".join(_labels_v)}')

            # ── Tabla FEVD a horizontes seleccionados ──────────────────
            _horizons = [1, 3, 6, 12, min(FEVD_HORIZONTE, 24)]
            _horizons = sorted(set(h for h in _horizons if h <= FEVD_HORIZONTE))
            _fevd_table = pd.DataFrame(
                {f'h={h}': _fevd_y[h-1] for h in _horizons},
                index=_labels_v
            ).T
            print(_fevd_table.round(4).to_string())

            # ── Gráfico de barras apiladas ─────────────────────────────
            fig, ax = plt.subplots(figsize=(12, 5))
            _x_pos = np.arange(FEVD_HORIZONTE)
            _bottom = np.zeros(FEVD_HORIZONTE)

            for _j, _lbl in enumerate(_labels_v):
                _vals = _fevd_y[:, _j]
                ax.bar(_x_pos, _vals, bottom=_bottom,
                       label=_lbl, color=_COLORS_FEVD[_j % len(_COLORS_FEVD)],
                       edgecolor='white', linewidth=0.3)
                _bottom += _vals

            ax.set_xlabel('Horizonte (períodos)', fontsize=10)
            ax.set_ylabel('Proporción de varianza explicada', fontsize=10)
            ax.set_title(
                f'FEVD del {COL_LABEL.get(Y_SAFE, Y_SAFE)[:30]} — '
                f'Modelo {_rank+1} (BIC={_row["BIC"]:.0f}, p={_p})',
                fontsize=11
            )
            ax.set_xticks(_x_pos[::2])
            ax.set_xticklabels([str(h+1) for h in _x_pos[::2]])
            ax.set_ylim(0, 1.05)
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
            plt.tight_layout()
            

        # ── Resumen comparativo FEVD h=12 de los 5 modelos ────────────
        print('\n' + '═'*70)
        print('  RESUMEN FEVD h=12 — TOP 5 MODELOS')
        print('═'*70)
    else:
        print('⚠️  Ningún modelo VAR es estable.')

# ═══════════════════════════════════════════════════════════════════════════
# 9.1-9.3  VECM — Dinámica de Largo Plazo
# ═══════════════════════════════════════════════════════════════════════════
from statsmodels.tsa.vector_ar.vecm import coint_johansen, VECM as _VECM

print('═'*70)
print('9.  DINÁMICA DE LARGO PLAZO — VECM')
print('═'*70)

# TODO: Implementar secciones 9.1 a 9.3
# Ver guía: docs/guia_02b_analisis_completo.md, Secciones 9.1-9.3

print('Sección 9 pendiente de implementación.')

# ═══════════════════════════════════════════════════════════════════════════
# 10.  SÍNTESIS Y CONCLUSIONES
# ═══════════════════════════════════════════════════════════════════════════

print('═'*70)
print('10.  SÍNTESIS Y CONCLUSIONES')
print('═'*70)

# TODO: Implementar sección 10
# Ver guía: docs/guia_02b_analisis_completo.md, Sección 10

print('Sección 10 pendiente de implementación.')


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
