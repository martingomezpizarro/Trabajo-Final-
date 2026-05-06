"""
OFR Financial Stress Index (US Treasury / Office of Financial Research).
Endpoint público CSV.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "global"
OUT.mkdir(parents=True, exist_ok=True)

URL = "https://www.financialresearch.gov/financial-stress-index/data/fsi.csv"


def main() -> None:
    print(f"[OFR] Descargando FSI de {URL}")
    headers = {"User-Agent": "Mozilla/5.0 (academic research)"}
    r = requests.get(URL, headers=headers, timeout=60)
    r.raise_for_status()
    path = OUT / "ofr_fsi.csv"
    path.write_bytes(r.content)
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
    df.to_csv(path, index=False)
    print(f"  ok {len(df)} obs -> {path.name}")
    print(df.head(3).to_string(index=False))
    print("...")
    print(df.tail(3).to_string(index=False))


if __name__ == "__main__":
    main()
