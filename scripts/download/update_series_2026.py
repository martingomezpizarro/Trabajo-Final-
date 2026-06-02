"""
Actualiza al dia mas reciente las series de mercado (yfinance) y FRED.
- yfinance -> data/Variables Finales/{vix,dxy,ust2y,ust5y,ust10y,ust30y}.csv
  Formato: fecha,Adj Close,Close,High,Low,Open,Volume
- FRED     -> raw/global/fred_*.csv  (fecha,<col_valor>)
Reescribe historia completa desde 2000-01-01 para mantener consistencia de formato.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[2]
VF = ROOT / "data" / "Variables Finales"
RAWG = ROOT / "raw" / "global"

START = "2000-01-01"
END = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)  # inclusivo hasta hoy
FRED_KEY = "45b7109fba6ea6b87a614fa9ff67997c"

YF_TICKERS = {
    "vix":    "^VIX",
    "dxy":    "DX-Y.NYB",
    "ust2y":  "^IRX",
    "ust5y":  "^FVX",
    "ust10y": "^TNX",
    "ust30y": "^TYX",
}
YF_COLS = ["Adj Close", "Close", "High", "Low", "Open", "Volume"]

FRED_SERIES = {
    "fred_fedfunds":     ("DFF",            "fed_funds_rate"),
    "fred_embi_global":  ("BAMLEMCBPIOAS",  "embi_global_oas"),
    "fred_us_hy_oas":    ("BAMLHE00EHYIEY",  "us_hy_oas"),
    "fred_tw_usd":       ("DTWEXBGS",       "trade_weighted_usd"),
    "fred_t10y2y":       ("T10Y2Y",         "ust_spread_10y2y"),
    "fred_vix":          ("VIXCLS",         "vix_fred"),
}


def update_yf() -> None:
    print("=== yfinance -> data/Variables Finales/ ===")
    for slug, tkr in YF_TICKERS.items():
        try:
            df = yf.download(tkr, start=START, end=END.strftime("%Y-%m-%d"),
                             progress=False, auto_adjust=False, threads=False)
            if df is None or df.empty:
                print(f"  [{slug}] {tkr}: VACIO"); continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
            df = df.reset_index().rename(columns={"Date": "fecha"})
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime("%Y-%m-%d")
            for c in YF_COLS:
                if c not in df.columns:
                    df[c] = 0
            df = df[["fecha"] + YF_COLS]
            out = VF / f"{slug}.csv"
            df.to_csv(out, index=False)
            print(f"  [{slug}] {tkr}: {len(df)} obs -> {df['fecha'].iloc[-1]}")
        except Exception as e:
            print(f"  [{slug}] {tkr}: ERROR {e}")
        time.sleep(0.3)


def update_fred() -> None:
    print("=== FRED -> raw/global/ ===")
    url = "https://api.stlouisfed.org/fred/series/observations"
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    for slug, (sid, col) in FRED_SERIES.items():
        try:
            params = {
                "series_id": sid, "api_key": FRED_KEY, "file_type": "json",
                "observation_start": START, "observation_end": today,
            }
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            obs = r.json().get("observations", [])
            df = pd.DataFrame(obs)
            df["date"] = pd.to_datetime(df["date"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna(subset=["value"])
            df = df[["date", "value"]].rename(columns={"date": "fecha", "value": col})
            df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d")
            out = RAWG / f"{slug}.csv"
            df.to_csv(out, index=False)
            print(f"  [{slug}] {sid}: {len(df)} obs -> {df['fecha'].iloc[-1]}")
            time.sleep(0.4)
        except Exception as e:
            print(f"  [{slug}] {sid}: ERROR {e}")


if __name__ == "__main__":
    update_yf()
    update_fred()
    print("DONE")
