"""
Descarga indicadores del World Bank vía wbgapi (sin API key).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import wbgapi as wb

OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "worldbank"
OUT.mkdir(parents=True, exist_ok=True)

COUNTRIES = ["ARG", "BRA", "CHL", "COL", "MEX", "PER", "URY"]
YEAR_RANGE = range(1990, 2026)

INDICATORS = {
    "gdp_usd":        "NY.GDP.MKTP.CD",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "gdp_growth":     "NY.GDP.MKTP.KD.ZG",
    "inflation_cpi":  "FP.CPI.TOTL.ZG",
    "gov_debt_gdp":   "GC.DOD.TOTL.GD.ZS",
    "exports_gdp":    "NE.EXP.GNFS.ZS",
    "imports_gdp":    "NE.IMP.GNFS.ZS",
    "trade_gdp":      "NE.TRD.GNFS.ZS",
    "cab_gdp":        "BN.CAB.XOKA.GD.ZS",
    "fdi_gdp":        "BX.KLT.DINV.WD.GD.ZS",
    "reserves":       "FI.RES.TOTL.CD",
    "credit_private_gdp": "FS.AST.PRVT.GD.ZS",
    "market_cap_gdp": "CM.MKT.LCAP.GD.ZS",
    "broad_money_gdp": "FM.LBL.BMNY.GD.ZS",
    "unemployment":   "SL.UEM.TOTL.ZS",
    "population":     "SP.POP.TOTL",
}

WGI_INDICATORS = {
    "wgi_polstab":             "GOV_WGI_PV.EST",
    "wgi_goveff":              "GOV_WGI_GE.EST",
    "wgi_rol":                 "GOV_WGI_RL.EST",
    "wgi_regqual":             "GOV_WGI_RQ.EST",
    "wgi_control_corruption":  "GOV_WGI_CC.EST",
    "wgi_voice_accountability": "GOV_WGI_VA.EST",
}


def fetch_wgi() -> list[dict]:
    """WGI vive en source=3 con códigos 'GOV_WGI_*'. Usamos la API REST directa."""
    import requests

    summary = []
    for slug, code in WGI_INDICATORS.items():
        print(f"[WB WGI {code}] {slug}")
        rows = []
        page = 1
        while True:
            url = (
                f"https://api.worldbank.org/v2/country/{';'.join(COUNTRIES)}"
                f"/indicator/{code}?format=json&source=3&per_page=1000"
                f"&date=1996:2024&page={page}"
            )
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list) or len(data) < 2 or data[1] is None:
                break
            for obs in data[1]:
                if obs.get("value") is None:
                    continue
                rows.append({
                    "economy": obs["countryiso3code"],
                    "year": int(obs["date"]),
                    "value": float(obs["value"]),
                })
            meta = data[0]
            if page >= int(meta.get("pages", 1)):
                break
            page += 1
        if not rows:
            print("  vacío")
            continue
        import pandas as pd
        df = pd.DataFrame(rows).sort_values(["economy", "year"])
        path = OUT / f"{slug}.csv"
        df.to_csv(path, index=False)
        summary.append({
            "slug": slug, "code": code, "n_obs": len(df),
            "countries": df["economy"].nunique(),
            "years": f"{df['year'].min()}-{df['year'].max()}",
            "path": path.name,
        })
        print(f"  ok {len(df)} obs, {df['economy'].nunique()} países")
    return summary


def main() -> None:
    summary = []
    for slug, code in INDICATORS.items():
        print(f"[WB {code}] {slug}")
        try:
            df = wb.data.DataFrame(code, COUNTRIES, time=YEAR_RANGE, labels=False, skipBlanks=False)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        if df is None or df.empty:
            print("  vacío")
            continue
        df = df.reset_index()
        # Pivot a long format
        long = df.melt(id_vars="economy", var_name="year", value_name="value")
        long["year"] = long["year"].astype(str).str.replace("YR", "").astype(int)
        long = long.dropna(subset=["value"])
        path = OUT / f"{slug}.csv"
        long.to_csv(path, index=False)
        summary.append({
            "slug": slug,
            "code": code,
            "n_obs": len(long),
            "countries": long["economy"].nunique(),
            "years": f"{long['year'].min()}-{long['year'].max()}" if len(long) else "",
            "path": path.name,
        })
        print(f"  ok {len(long)} obs, {long['economy'].nunique()} países")

    # WGI en source=3
    summary.extend(fetch_wgi())

    pd.DataFrame(summary).to_csv(OUT / "_index.csv", index=False)
    print(f"\n{len(summary)} indicadores guardados en {OUT}")


if __name__ == "__main__":
    main()
