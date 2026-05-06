"""
Descarga series de Yahoo Finance vía yfinance.
Sin API key.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yfinance as yf

OUT_GLOBAL = Path(__file__).resolve().parents[2] / "data" / "raw" / "global"
OUT_LOCAL = Path(__file__).resolve().parents[2] / "data" / "raw" / "local"
OUT_GLOBAL.mkdir(parents=True, exist_ok=True)
OUT_LOCAL.mkdir(parents=True, exist_ok=True)

START = "2000-01-01"

TICKERS = {
    # Globales
    ("global", "vix"):          ("^VIX",      "CBOE Volatility Index"),
    ("global", "move"):         ("^MOVE",     "ICE BofA MOVE Index (vol. UST)"),
    ("global", "dxy"):          ("DX-Y.NYB",  "US Dollar Index"),
    ("global", "ust2y"):        ("^IRX",      "UST 13-week (proxy corto)"),
    ("global", "ust5y"):        ("^FVX",      "UST 5Y yield"),
    ("global", "ust10y"):       ("^TNX",      "UST 10Y yield"),
    ("global", "ust30y"):       ("^TYX",      "UST 30Y yield"),
    ("global", "sp500"):        ("^GSPC",     "S&P 500"),
    ("global", "msci_em"):      ("EEM",       "iShares MSCI Emerging Markets ETF (proxy EM equity)"),
    ("global", "wti"):          ("CL=F",      "Petróleo WTI futuro"),
    ("global", "brent"):        ("BZ=F",      "Petróleo Brent futuro"),
    ("global", "soja"):         ("ZS=F",      "Soja CBOT futuro"),
    ("global", "maiz"):         ("ZC=F",      "Maíz CBOT futuro"),
    ("global", "trigo"):        ("ZW=F",      "Trigo CBOT futuro"),
    ("global", "oro"):           ("GC=F",     "Oro futuro"),
    ("global", "cobre"):        ("HG=F",      "Cobre futuro"),
    ("global", "brl"):          ("BRL=X",     "USD/BRL"),
    ("global", "clp"):          ("CLP=X",     "USD/CLP"),
    ("global", "mxn"):          ("MXN=X",     "USD/MXN"),
    # Locales
    ("local",  "merval"):       ("^MERV",     "Índice Merval"),
    ("local",  "merval_usd"):   ("ARGT",      "Global X MSCI Argentina ETF (proxy USD)"),
    ("local",  "ypf_adr"):      ("YPF",       "YPF ADR"),
    ("local",  "gga_adr"):      ("GGAL",      "Grupo Financiero Galicia ADR"),
}


def fetch(ticker: str) -> pd.DataFrame:
    df = yf.download(ticker, start=START, progress=False, auto_adjust=False, threads=False)
    if df is None or df.empty:
        return pd.DataFrame()
    # Flatten multi-index columns si existe
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.reset_index().rename(columns={"Date": "fecha"})
    return df


def main() -> None:
    summary = []
    for (bucket, slug), (tkr, desc) in TICKERS.items():
        out_dir = OUT_GLOBAL if bucket == "global" else OUT_LOCAL
        print(f"[YF {tkr}] {desc}")
        try:
            df = fetch(tkr)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        if df.empty:
            print("  vacío")
            continue
        path = out_dir / f"{slug}.csv"
        df.to_csv(path, index=False)
        summary.append(
            {
                "bucket": bucket,
                "slug": slug,
                "ticker": tkr,
                "descripcion": desc,
                "n_obs": len(df),
                "desde": df["fecha"].min().date().isoformat(),
                "hasta": df["fecha"].max().date().isoformat(),
                "path": f"{bucket}/{path.name}",
            }
        )
        print(f"  ok {len(df)} obs ({df['fecha'].min().date()} -> {df['fecha'].max().date()})")

    idx_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "_yfinance_index.csv"
    pd.DataFrame(summary).to_csv(idx_path, index=False)
    print(f"\nResumen yfinance: {len(summary)} series. Índice -> {idx_path}")


if __name__ == "__main__":
    main()
