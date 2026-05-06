"""
Descarga series del BCRA (API v4.0 Estadísticas Monetarias).
Endpoint público, sin API key.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests
import urllib3

urllib3.disable_warnings()

BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias"
OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "bcra"
OUT.mkdir(parents=True, exist_ok=True)

VARIABLES = {
    1:   ("reservas_brutas",         "Reservas internacionales (mill. USD)"),
    4:   ("tc_minorista",            "Tipo de cambio minorista (promedio vendedor)"),
    5:   ("tc_mayorista_a3500",      "Tipo de cambio mayorista de referencia (A3500)"),
    7:   ("tasa_badlar_privados",    "Tasa BADLAR bancos privados"),
    8:   ("tasa_tm20_privados",      "Tasa TM20 bancos privados"),
    12:  ("tasa_dep_30d",            "Tasa depósitos 30 días"),
    15:  ("base_monetaria",          "Base monetaria"),
    19:  ("dep_cc_bcra",             "Depósitos entidades fin. en CC en BCRA"),
    21:  ("dep_total",               "Depósitos en efectivo en entidades financieras"),
    22:  ("dep_cc_privado",          "Depósitos CC sector privado"),
    23:  ("dep_cajas_ahorro",        "Depósitos cajas de ahorro"),
    24:  ("dep_plazo",               "Depósitos a plazo"),
    25:  ("m2_var_anual",            "Var. i.a. M2 privado (prom. móvil 30d)"),
    26:  ("prestamos_privado",       "Préstamos al sector privado"),
    35:  ("tasa_badlar_bp",          "BADLAR bancos privados (alt)"),
    44:  ("tasa_tamar",              "Tasa TAMAR bancos privados"),
    109: ("m2",                      "M2"),
    117: ("prest_total_privado",     "Préstamos totales al sector privado"),
    155: ("leliq_notalq",            "LELIQ y NOTALQ"),
    152: ("pases_pasivos",           "Pases pasivos BCRA"),
    154: ("pases_activos",           "Pases activos BCRA"),
}


def fetch_series(id_var: int, desde: str = "2003-01-01", hasta: str = "2026-12-31") -> pd.DataFrame:
    """Descarga una serie con paginación. BCRA v4 devuelve hasta ~3000 obs por request."""
    all_rows: list[dict] = []
    offset = 0
    limit = 3000
    while True:
        url = f"{BASE}/{id_var}"
        params = {"desde": desde, "hasta": hasta, "limit": limit, "offset": offset}
        r = requests.get(url, params=params, verify=False, timeout=60)
        if r.status_code != 200:
            print(f"  ! id={id_var} offset={offset} HTTP {r.status_code}: {r.text[:120]}")
            break
        payload = r.json()
        results = payload.get("results", [])
        if not results:
            break
        detalle = results[0].get("detalle", [])
        if not detalle:
            break
        all_rows.extend(detalle)
        if len(detalle) < limit:
            break
        offset += limit
        time.sleep(0.3)

    if not all_rows:
        return pd.DataFrame(columns=["fecha", "valor"])
    df = pd.DataFrame(all_rows)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    return df[["fecha", "valor"]]


def main() -> None:
    summary = []
    for id_var, (slug, desc) in VARIABLES.items():
        print(f"[BCRA {id_var}] {desc}")
        df = fetch_series(id_var)
        path = OUT / f"{id_var:03d}_{slug}.csv"
        df.to_csv(path, index=False)
        if len(df):
            summary.append(
                {
                    "id": id_var,
                    "slug": slug,
                    "descripcion": desc,
                    "n_obs": len(df),
                    "desde": df["fecha"].min().date().isoformat(),
                    "hasta": df["fecha"].max().date().isoformat(),
                    "path": path.name,
                }
            )
            print(f"  ok {len(df)} obs ({df['fecha'].min().date()} -> {df['fecha'].max().date()})")
        else:
            print("  vacío")

    idx = pd.DataFrame(summary)
    idx.to_csv(OUT / "_index.csv", index=False)
    print(f"\nResumen: {len(summary)} series guardadas en {OUT}")


if __name__ == "__main__":
    main()
