# -*- coding: utf-8 -*-
"""
Descarga las series diarias de spread EMBIG (JPMorgan, via Reuters) que publica
el Banco Central de Reserva del Peru (BCRP) en su API REST. Son spreads en
PUNTOS BASICOS, fin de dia, desde 1998. Fuente homogenea (EMBI Global) para todo
el periodo, a diferencia de empalmar EMBI+ con EMBIG.

API: https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{cod}/json/{ini}/{fin}/ing

Salidas (en data/raw/bcrp_embig/):
  - embig_<pais>.csv : fecha,embig_<pais>_pbs   (una por serie, en pbs)
  - embig_bcrp_wide.csv : panel ancho fecha x todas las series (pbs)
"""
import csv
import json
import os
import urllib.request
from datetime import datetime

OUT = "data/raw/bcrp_embig"
INI, FIN = "1998-01-01", datetime.today().strftime("%Y-%m-%d")
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{cod}/json/{ini}/{fin}/ing"

SERIES = [
    ("PD04708XD", "america_latina"),
    ("PD04709XD", "peru"),
    ("PD04710XD", "argentina"),
    ("PD04711XD", "brasil"),
    ("PD04712XD", "ecuador"),
    ("PD04713XD", "mexico"),
    ("PD04714XD", "venezuela"),
    ("PD04715XD", "colombia"),
    ("PD38581XD", "chile"),
    ("PD38580XD", "emergentes"),
    ("PD04707XD", "embig_general"),   # discontinuada
    ("PD04716XD", "peru_pdi"),        # discontinuada
    ("PD04717XD", "peru_flirb"),      # discontinuada
]


def fetch(cod):
    url = API.format(cod=cod, ini=INI, fin=FIN)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=120).read().decode("utf-8")
    return json.loads(raw)


def parse_date(name):
    # API daily format: "02.Jan.98" -> date
    return datetime.strptime(name.strip(), "%d.%b.%y").date()


def main():
    os.makedirs(OUT, exist_ok=True)
    all_data = {}  # fecha -> {clave: valor}
    keys = []
    for cod, key in SERIES:
        try:
            js = fetch(cod)
        except Exception as e:
            print(f"  [!] {cod} ({key}) error: {e}")
            continue
        rows = []
        for p in js.get("periods", []):
            v = p["values"][0]
            if v in (None, "", "n.d.", "n.d", "-"):
                continue
            try:
                dt = parse_date(p["name"])
                val = float(v)
            except Exception:
                continue
            rows.append((dt, val))
            all_data.setdefault(dt, {})[key] = val
        if not rows:
            print(f"  [!] {cod} ({key}) sin datos")
            continue
        keys.append(key)
        rows.sort()
        path = os.path.join(OUT, f"embig_{key}.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["fecha", f"embig_{key}_pbs"])
            for dt, val in rows:
                w.writerow([dt.isoformat(), f"{val:g}"])
        print(f"  [OK] embig_{key:16s} {len(rows):5d} filas  {rows[0][0]} .. {rows[-1][0]}")

    # panel ancho
    wide = os.path.join(OUT, "embig_bcrp_wide.csv")
    with open(wide, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["fecha"] + [f"embig_{k}_pbs" for k in keys])
        for dt in sorted(all_data):
            row = all_data[dt]
            w.writerow([dt.isoformat()] + [f"{row[k]:g}" if k in row else "" for k in keys])
    print(f"\n[OK] panel ancho: {wide} ({len(all_data)} fechas, {len(keys)} series)")


if __name__ == "__main__":
    main()
