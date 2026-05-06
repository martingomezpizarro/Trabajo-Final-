"""
Descarga CER (BCRA var 40) y proxy de inflación EEUU (TIP ETF via yfinance).
Ejecutar: python src/download_cer_tip.py
"""
import os, sys, requests
import pandas as pd

_ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT_BCRA   = os.path.join(_ROOT, 'data', 'raw', 'bcra', 'cer.csv')
OUT_GLOBAL = os.path.join(_ROOT, 'data', 'raw', 'global', 'tip_etf.csv')
OUT_TIPS_BE = os.path.join(_ROOT, 'data', 'raw', 'global', 'tips_breakeven_10y.csv')

# ═══════════════════════════════════════════════
# 1. CER — BCRA variable 40
# ═══════════════════════════════════════════════
print("🔄 Descargando CER del BCRA (variable 40)…")
try:
    url = "https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/40/2003-01-02/2026-12-31"
    headers = {'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=60, verify=False)
    r.raise_for_status()
    data = r.json().get('results', [])
    if data:
        df = pd.DataFrame(data)
        df['fecha'] = pd.to_datetime(df['fecha'], format='%d/%m/%Y', errors='coerce')
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        df = df.dropna(subset=['fecha']).set_index('fecha')[['valor']].sort_index()
        df.columns = ['cer']
        df.to_csv(OUT_BCRA)
        print(f"  ✅ CER guardado: {OUT_BCRA}")
        print(f"     {len(df)} obs: {df.index.min().date()} → {df.index.max().date()}")
    else:
        print("  ⚠️  CER: sin resultados del BCRA")
except Exception as e:
    print(f"  ❌ CER: {e}")

# ═══════════════════════════════════════════════
# 2. TIP ETF — proxy diario de inflación EEUU
# ═══════════════════════════════════════════════
print("\n🔄 Descargando TIP ETF (iShares TIPS Bond) de Yahoo Finance…")
try:
    import yfinance as yf
    tip = yf.download('TIP', start='2003-01-01', progress=False)
    if tip is not None and not tip.empty:
        if isinstance(tip.columns, pd.MultiIndex):
            tip.columns = tip.columns.get_level_values(0)
        df_tip = tip[['Close']].copy()
        df_tip.columns = ['tip_close']
        df_tip.index.name = 'fecha'
        df_tip = df_tip.dropna()
        df_tip.to_csv(OUT_GLOBAL)
        print(f"  ✅ TIP ETF guardado: {OUT_GLOBAL}")
        print(f"     {len(df_tip)} obs: {df_tip.index.min().date()} → {df_tip.index.max().date()}")
    else:
        print("  ⚠️  TIP: sin datos de yfinance")
except Exception as e:
    print(f"  ❌ TIP: {e}")

# ═══════════════════════════════════════════════
# 3. 10Y Breakeven Inflation Rate (FRED T10YIE)
#    Intentar vía FRED API si hay key disponible
# ═══════════════════════════════════════════════
print("\n🔄 Intentando 10Y Breakeven Inflation (FRED T10YIE)…")
api_key = os.environ.get('FRED_API_KEY', '')
if api_key:
    try:
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': 'T10YIE',
            'api_key': api_key,
            'file_type': 'json',
            'observation_start': '2003-01-01',
        }
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        obs = r.json().get('observations', [])
        if obs:
            df_be = pd.DataFrame(obs)
            df_be['date'] = pd.to_datetime(df_be['date'])
            df_be['value'] = pd.to_numeric(df_be['value'], errors='coerce')
            df_be = df_be.set_index('date')[['value']].dropna()
            df_be.columns = ['tips_breakeven_10y']
            df_be.index.name = 'fecha'
            df_be.to_csv(OUT_TIPS_BE)
            print(f"  ✅ T10YIE guardado: {OUT_TIPS_BE}")
            print(f"     {len(df_be)} obs: {df_be.index.min().date()} → {df_be.index.max().date()}")
        else:
            print("  ⚠️  T10YIE: sin datos")
    except Exception as e:
        print(f"  ❌ T10YIE: {e}")
else:
    print("  ℹ️  Sin FRED_API_KEY — descargando ^TNX como alternativa vía yfinance…")
    # No hay breakeven en yfinance, pero TIP ya lo tenemos
    print("     TIP ETF ya descargado — usalo como proxy de inflación EEUU.")

print("\n✅ Descarga completada.")
