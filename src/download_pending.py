"""
download_pending.py — Descarga todas las series pendientes (⬜) y construye ratios
Trabajo Final de Grado — Riesgo País Argentino — UNC
Ejecutar: python src/download_pending.py
"""
import pandas as pd
import numpy as np
import requests
import os
import json
import time
import warnings
warnings.filterwarnings('ignore')

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(BASE, '..')
RAW  = os.path.join(ROOT, 'data', 'raw')
PROC = os.path.join(ROOT, 'data', 'processed')
os.makedirs(PROC, exist_ok=True)

FRED_KEY = '45b7109fba6ea6b87a614fa9ff67997c'
FECHA_INICIO = '2000-01-01'
FECHA_FIN = pd.Timestamp.today().strftime('%Y-%m-%d')

log = []
def report(msg):
    print(msg)
    log.append(msg)

report("=" * 70)
report("  DESCARGA DE SERIES PENDIENTES + CONSTRUCCIÓN DE RATIOS")
report("=" * 70)

# ============================================================
# 1. FRED SERIES
# ============================================================
FRED_SERIES = {
    'DFF':            ('fed_funds_rate',       'raw/global/fred_fedfunds.csv'),
    'BAMLEMCBPIOAS':  ('embi_global_oas',      'raw/global/fred_embi_global.csv'),  # EM Corporate OAS
    'BAMLHE00EHYIEY': ('us_hy_oas',            'raw/global/fred_us_hy_oas.csv'),    # US HY OAS
    'T10Y2Y':         ('ust_spread_10y2y',     'raw/global/fred_t10y2y.csv'),       # Yield curve spread
    'DTWEXBGS':       ('trade_weighted_usd',   'raw/global/fred_tw_usd.csv'),       # Trade-weighted USD
    'VIXCLS':         ('vix_fred',             'raw/global/fred_vix.csv'),           # VIX from FRED
}

report("\n--- 1. FRED (Federal Reserve Economic Data) ---")
for serie_id, (nombre, path_rel) in FRED_SERIES.items():
    out_path = os.path.join(ROOT, path_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': serie_id,
            'api_key': FRED_KEY,
            'file_type': 'json',
            'observation_start': FECHA_INICIO,
            'observation_end': FECHA_FIN,
        }
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        obs = r.json().get('observations', [])
        df = pd.DataFrame(obs)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.dropna(subset=['value']).set_index('date')[['value']]
        df.columns = [nombre]
        df.index.name = 'fecha'
        df.to_csv(out_path)
        report(f"  ✅ {serie_id} → {path_rel} ({len(df)} obs, {df.index.min().date()} a {df.index.max().date()})")
        time.sleep(0.5)
    except Exception as e:
        report(f"  ❌ {serie_id}: {e}")

# ============================================================
# 2. TC BLUE / MEP / CCL — ArgentinaDatos API
# ============================================================
report("\n--- 2. TC Blue / MEP / CCL (ArgentinaDatos) ---")
TC_SERIES = {
    'blue':       'raw/mep/tc_blue.csv',
    'bolsa':      'raw/mep/tc_mep.csv',       # MEP = dolar bolsa
    'contadoconliqui': 'raw/mep/tc_ccl.csv',
}

for tipo, path_rel in TC_SERIES.items():
    out_path = os.path.join(ROOT, path_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    try:
        url = f'https://api.argentinadatos.com/v1/cotizaciones/dolares/{tipo}'
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        # Usar 'venta' como precio de referencia
        for col in ['venta', 'compra']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.set_index('fecha').sort_index()
        df.to_csv(out_path)
        report(f"  ✅ TC {tipo} → {path_rel} ({len(df)} obs, {df.index.min().date()} a {df.index.max().date()})")
    except Exception as e:
        report(f"  ❌ TC {tipo}: {e}")
    time.sleep(0.5)

# ============================================================
# 3. BCRA — ITCRM (variable 28)
# ============================================================
report("\n--- 3. BCRA — ITCRM ---")
try:
    # ITCRM es variable 28 en la API del BCRA
    url = f'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/28/{FECHA_INICIO}/{FECHA_FIN}'
    headers = {'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=30, verify=False)
    r.raise_for_status()
    data = r.json().get('results', [])
    df = pd.DataFrame(data)
    df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    df = df.dropna().set_index('fecha')[['valor']].sort_index()
    df.columns = ['itcrm']
    out_path = os.path.join(RAW, 'bcra', 'itcrm.csv')
    df.to_csv(out_path)
    report(f"  ✅ ITCRM → raw/bcra/itcrm.csv ({len(df)} obs, {df.index.min().date()} a {df.index.max().date()})")
except Exception as e:
    report(f"  ❌ ITCRM: {e}")

# ============================================================
# 4. RIESGO PAÍS — ArgentinaDatos (variable dependiente Y)
# ============================================================
report("\n--- 4. Riesgo País (EMBI+ Argentina) ---")
try:
    url = 'https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data)
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    df = df.set_index('fecha')[['valor']].sort_index()
    df.columns = ['embi_arg']
    out_path = os.path.join(RAW, 'global', 'riesgo_pais_arg.csv')
    df.to_csv(out_path)
    report(f"  ✅ EMBI+ ARG → raw/global/riesgo_pais_arg.csv ({len(df)} obs, {df.index.min().date()} a {df.index.max().date()})")
except Exception as e:
    report(f"  ❌ Riesgo País: {e}")

# ============================================================
# 5. DUMMIES (cepo, gobiernos, electoral, defaults)
# ============================================================
report("\n--- 5. Dummies y History Matters ---")
idx = pd.date_range('1999-01-01', pd.Timestamp.today(), freq='B', name='fecha')
report(f"  Índice: {len(idx)} días hábiles")

# 5a. Cepo
CEPO = [('2011-10-28','2015-12-16'), ('2019-09-01','2024-12-13')]
cepo = pd.Series(0, index=idx, name='dummy_cepo', dtype='int8')
for s, e in CEPO:
    cepo.loc[s:e] = 1
cepo.to_frame().to_csv(os.path.join(PROC, 'dummy_cepo.csv'))
report(f"  ✅ dummy_cepo.csv ({cepo.sum()} días con cepo)")

# 5b. Gobiernos
GOB = [
    ('1999-01-01','1999-12-09',1,'Menem'),('1999-12-10','2001-12-20',2,'De la Rúa'),
    ('2001-12-21','2002-01-01',3,'Transición 2001'),('2002-01-02','2003-05-24',4,'Duhalde'),
    ('2003-05-25','2007-12-09',5,'Néstor Kirchner'),('2007-12-10','2015-12-09',6,'Cristina Kirchner'),
    ('2015-12-10','2019-12-09',7,'Macri'),('2019-12-10','2023-12-09',8,'Alberto Fernández'),
    ('2023-12-10','2030-12-31',9,'Milei'),
]
gob_id = pd.Series(0, index=idx, name='gobierno_id', dtype='int8')
gob_nm = pd.Series('', index=idx, name='gobierno_nombre')
for s, e, gid, nm in GOB:
    mask = (idx >= pd.Timestamp(s)) & (idx <= pd.Timestamp(e))
    gob_id[mask] = gid; gob_nm[mask] = nm
pd.DataFrame({'gobierno_id': gob_id, 'gobierno_nombre': gob_nm}).to_csv(os.path.join(PROC, 'dummy_gob.csv'))
report(f"  ✅ dummy_gob.csv ({gob_id.nunique()} gobiernos)")

# 5c. Electoral
ELEC = [
    '1999-10-24','2001-10-14','2003-04-27','2003-05-18','2005-10-23','2007-10-28',
    '2009-06-28','2011-08-14','2011-10-23','2013-08-11','2013-10-27','2015-08-09',
    '2015-10-25','2015-11-22','2017-08-13','2017-10-22','2019-08-11','2019-10-27',
    '2021-09-12','2021-11-14','2023-08-13','2023-10-22','2023-11-19','2025-08-10','2025-10-26',
]
elec = pd.Series(0, index=idx, name='dummy_electoral', dtype='int8')
for f_str in ELEC:
    t = pd.Timestamp(f_str)
    elec.loc[t - pd.Timedelta(days=60):t + pd.Timedelta(days=60)] = 1
elec.to_frame().to_csv(os.path.join(PROC, 'dummy_elec.csv'))
report(f"  ✅ dummy_elec.csv ({len(ELEC)} elecciones, {elec.sum()} días en ventana)")

# 5d. Defaults
DEFAULTS = [pd.Timestamp('2001-12-23'), pd.Timestamp('2014-07-30'), pd.Timestamp('2020-05-22')]
dates_ts = idx.to_series()
ultimo = pd.Series(pd.Timestamp('1989-07-09'), index=idx, dtype='datetime64[ns]')
for d in sorted(DEFAULTS):
    ultimo = ultimo.where(dates_ts < d, d)
ysd = ((dates_ts - ultimo).dt.days / 365.25).rename('years_since_default')
ysd.to_frame().to_csv(os.path.join(PROC, 'years_since_default.csv'))
nd = pd.Series(0, index=idx, name='n_defaults', dtype='int8')
for d in DEFAULTS:
    nd.loc[d:] += 1
nd.to_frame().to_csv(os.path.join(PROC, 'defaults_history.csv'))
report(f"  ✅ years_since_default.csv (rango {ysd.min():.1f} a {ysd.max():.1f} años)")
report(f"  ✅ defaults_history.csv ({len(DEFAULTS)} defaults)")

# ============================================================
# 6. BRECHA CAMBIARIA
# ============================================================
report("\n--- 6. Brecha Cambiaria ---")
try:
    tc_of = pd.read_csv(os.path.join(RAW, 'bcra', '005_tc_mayorista_a3500.csv'),
                        index_col=0, parse_dates=True)
    tc_ccl = pd.read_csv(os.path.join(ROOT, 'data', 'raw', 'mep', 'tc_ccl.csv'),
                         index_col=0, parse_dates=True)
    # Usar columna 'venta' del CCL
    col_ccl = 'venta' if 'venta' in tc_ccl.columns else tc_ccl.columns[0]
    col_of = tc_of.columns[0]
    merged = pd.DataFrame({
        'tc_oficial': tc_of[col_of],
        'tc_ccl': tc_ccl[col_ccl]
    }).dropna()
    merged['brecha_pct'] = (merged['tc_ccl'] / merged['tc_oficial'] - 1) * 100
    merged[['brecha_pct']].to_csv(os.path.join(PROC, 'brecha.csv'))
    report(f"  ✅ brecha.csv ({len(merged)} obs, brecha media: {merged['brecha_pct'].mean():.1f}%)")
except Exception as e:
    report(f"  ❌ Brecha: {e}")

# ============================================================
# 7. RATIOS / VARIABLES CALCULADAS
# ============================================================
report("\n--- 7. Variables Ratio Calculadas ---")

# 7a. (X+M)/PBI — desde World Bank (anual)
try:
    # trade_gdp.csv ya tiene esto directamente del World Bank (NE.TRD.GNFS.ZS)
    trade = pd.read_csv(os.path.join(RAW, 'worldbank', 'trade_gdp.csv'), index_col=0, parse_dates=True)
    trade.columns = ['apertura_xm_pbi']
    trade.to_csv(os.path.join(PROC, 'apertura_xm.csv'))
    report(f"  ✅ apertura_xm.csv = Trade/GDP del World Bank (serie NE.TRD.GNFS.ZS) — {len(trade.dropna())} obs")
    report(f"      Detalle: (X+M)/PBI calculado por World Bank como % del PBI. Ya incluye bienes y servicios.")
except Exception as e:
    report(f"  ❌ (X+M)/PBI: {e}")

# 7b. Deuda/PBI — desde World Bank (anual)
try:
    debt = pd.read_csv(os.path.join(RAW, 'worldbank', 'gov_debt_gdp.csv'), index_col=0, parse_dates=True)
    debt.columns = ['deuda_pbi']
    debt.to_csv(os.path.join(PROC, 'deuda_pbi.csv'))
    report(f"  ✅ deuda_pbi.csv = Gov Debt/GDP del World Bank (GC.DOD.TOTL.GD.ZS) — {len(debt.dropna())} obs")
    report(f"      Detalle: Deuda bruta del gobierno central / PBI, datos del World Bank anuales.")
except Exception as e:
    report(f"  ❌ Deuda/PBI: {e}")

# 7c. Spread tasas activa-pasiva (BADLAR vs tasa préstamos)
try:
    badlar = pd.read_csv(os.path.join(RAW, 'bcra', '007_tasa_badlar_privados.csv'),
                         index_col=0, parse_dates=True)
    # Usamos tasa depósitos 30d como proxy de la tasa pasiva
    dep30 = pd.read_csv(os.path.join(RAW, 'bcra', '012_tasa_dep_30d.csv'),
                        index_col=0, parse_dates=True)
    merged_t = pd.DataFrame({
        'tasa_badlar': badlar.iloc[:, 0],
        'tasa_dep30d': dep30.iloc[:, 0]
    }).dropna()
    merged_t['spread_tasas'] = merged_t['tasa_badlar'] - merged_t['tasa_dep30d']
    merged_t[['spread_tasas']].to_csv(os.path.join(PROC, 'spread_tasas.csv'))
    report(f"  ✅ spread_tasas.csv = BADLAR - Tasa Dep 30d ({len(merged_t)} obs)")
    report(f"      Detalle: Spread = Tasa BADLAR privados (serie 7) - Tasa Depósitos 30d (serie 12).")
except Exception as e:
    report(f"  ❌ Spread tasas: {e}")

# ============================================================
# 8. AUDITORÍA DE COBERTURA TEMPORAL
# ============================================================
report("\n" + "=" * 70)
report("  AUDITORÍA DE COBERTURA TEMPORAL")
report("=" * 70)

problemas = []

def auditar_csv(path, nombre, min_year=2003, max_year=2026):
    """Audita un CSV verificando cobertura temporal."""
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True, nrows=None)
        if df.empty:
            problemas.append((nombre, 'VACÍO', '', ''))
            return
        inicio = df.index.min()
        fin = df.index.max()
        flag = ''
        if inicio.year > min_year:
            flag += f'⚠️ INICIA en {inicio.date()} (después de {min_year}). '
        if fin.year < max_year:
            flag += f'⚠️ TERMINA en {fin.date()} (antes de {max_year}). '
        if flag:
            problemas.append((nombre, flag.strip(), str(inicio.date()), str(fin.date())))
        return (nombre, len(df), inicio.date(), fin.date(), flag)
    except Exception as e:
        problemas.append((nombre, f'ERROR: {e}', '', ''))
        return None

report("\n  Auditando archivos raw/global/...")
for f in sorted(os.listdir(os.path.join(RAW, 'global'))):
    if f.endswith('.csv'):
        auditar_csv(os.path.join(RAW, 'global', f), f'global/{f}')

report("  Auditando archivos raw/bcra/...")
for f in sorted(os.listdir(os.path.join(RAW, 'bcra'))):
    if f.endswith('.csv') and not f.startswith('_'):
        auditar_csv(os.path.join(RAW, 'bcra', f), f'bcra/{f}')

report("  Auditando archivos raw/local/...")
for f in sorted(os.listdir(os.path.join(RAW, 'local'))):
    if f.endswith('.csv'):
        auditar_csv(os.path.join(RAW, 'local', f), f'local/{f}')

report("  Auditando archivos raw/worldbank/...")
for f in sorted(os.listdir(os.path.join(RAW, 'worldbank'))):
    if f.endswith('.csv') and not f.startswith('_'):
        auditar_csv(os.path.join(RAW, 'worldbank', f), f'worldbank/{f}')

report("  Auditando archivos raw/mep/...")
mep_dir = os.path.join(RAW, 'mep')
if os.path.exists(mep_dir):
    for f in sorted(os.listdir(mep_dir)):
        if f.endswith('.csv'):
            auditar_csv(os.path.join(mep_dir, f), f'mep/{f}')

report("  Auditando archivos processed/...")
for f in sorted(os.listdir(PROC)):
    if f.endswith('.csv'):
        auditar_csv(os.path.join(PROC, f), f'processed/{f}')

report("\n--- VARIABLES CON PROBLEMAS DE COBERTURA ---")
if problemas:
    report(f"{'Variable':<50} {'Problema':<60} {'Desde':<12} {'Hasta':<12}")
    report("-" * 134)
    for nombre, flag, desde, hasta in sorted(problemas):
        report(f"{nombre:<50} {flag:<60} {desde:<12} {hasta:<12}")
else:
    report("  Todas las series cumplen con cobertura 2003-2026.")

# ============================================================
# GUARDAR LOG
# ============================================================
log_path = os.path.join(PROC, '_download_log.txt')
with open(log_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(log))
report(f"\nLog guardado en: {log_path}")
report("DONE ✅")
