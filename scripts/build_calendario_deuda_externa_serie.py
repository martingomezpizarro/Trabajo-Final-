# -*- coding: utf-8 -*-
"""
Serie del CALENDARIO DE PAGO del servicio de la deuda externa bruta (INDEC, CIN).

Cada boletin trimestral de INDEC (cin_{I,II,III,IV}_{anio}.xls) trae un cuadro
"Calendario de pago del servicio de la deuda" que es una FOTO FORWARD al cierre
de ese trimestre: los pagos pendientes clasificados por tramo de plazo restante.
Juntando todos los boletines se arma una serie de "vencimientos proximos" en cada
fecha de referencia.

COBERTURA: la metodologia BPM6 con este cuadro recien existe desde 2017T3. Antes
de eso INDEC no publica este calendario (si el stock, retropolado a 2006, que se
captura en build_deuda_externa_indec.py). => serie 2017T3 .. ultimo disponible.

Descarga: https://www.indec.gob.ar/ftp/cuadros/economia/cin_{ROMANO}_{ANIO}.xls
Salidas (millones de USD):
  - deuda_externa_calendario_serie.csv : 1 fila por fecha de referencia, tramos
    totales + vencimientos proximos 1 y 2 anios (total y gobierno general).
  - deuda_externa_calendario_panel.csv : panel largo fecha x sector x tramo.
"""
import os
import urllib.request

import pandas as pd

BASE = "https://www.indec.gob.ar/ftp/cuadros/economia/cin_{r}_{y}.xls"
RAWDIR = "raw/indec_cin"
OUT = "data/Variables Finales"
ROMAN = {"I": "03", "II": "06", "III": "09", "IV": "12"}  # T -> mes fin trimestre

# orden fijo de tramos; el ultimo ('sin_fecha') puede no existir en anios viejos
BUCKETS = ["pago_inmediato", "m0a3", "m3a6", "m6a9", "m9a12",
           "m12a18", "m18a24", "mas_2y", "sin_fecha"]
# tramos que cuentan como vencimiento "proximo"
PROX_1Y = ["pago_inmediato", "m0a3", "m3a6", "m6a9", "m9a12"]
PROX_2Y = PROX_1Y + ["m12a18", "m18a24"]

# (clave de salida, substrings para reconocer la fila-encabezado del sector)
SECTORES = [
    ("total", ["saldo bruto de la deuda externa", "saldo de la deuda externa"]),
    ("gobierno", ["gobierno general"]),
    ("bcra", ["banco central"]),
    ("bancos", ["captadoras"]),
    ("otros_sectores", ["otros sectores"]),
    ("otras_financieras", ["otras sociedades financieras"]),
    ("no_financieras", ["no financieras"]),
    ("inversion_directa", ["inversi"]),
]


def descargar(r, y, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 100_000:
        return True
    url = BASE.format(r=r, y=y)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=90).read()
    except Exception as e:
        print(f"  [{r}_{y}] error descarga: {e}")
        return False
    if data[:15].lstrip().lower().startswith((b"<!doctype", b"<html")):
        return False  # stub HTML => boletin inexistente
    with open(dest, "wb") as fh:
        fh.write(data)
    return True


def hoja_calendario(xls):
    for sh in xls.sheet_names:
        if not sh.lower().startswith("cuadro"):
            continue
        t = str(pd.read_excel(xls, sheet_name=sh, header=None, nrows=1).iloc[0, 0]).lower()
        if "calendario de pago del servicio de la deuda" in t:
            return sh
    return None


def num(v):
    if isinstance(v, (int, float)) and not pd.isna(v):
        return float(v)
    return None  # '-', '...', '/', texto, vacio -> sin dato


def parse_calendario(path):
    xls = pd.ExcelFile(path)
    sh = hoja_calendario(xls)
    if sh is None:
        return None
    df = pd.read_excel(xls, sheet_name=sh, header=None)
    # columnas de datos = las que tienen algun numero en filas de sector
    ncols = df.shape[1]
    datacols = [c for c in range(1, ncols)
                if any(num(df.iloc[i, c]) is not None for i in range(df.shape[0]))]
    nb = len(datacols)
    names = BUCKETS[:nb]  # asignacion posicional; sin_fecha solo si nb==9
    # extraer cada sector tomando la PRIMERA fila-encabezado que matchee
    out = {}
    used = set()
    for key, subs in SECTORES:
        for i in range(df.shape[0]):
            lab = str(df.iloc[i, 0]).lower()
            if i in used:
                continue
            if any(s in lab for s in subs) and "principal" not in lab and "intereses" not in lab:
                vals = {names[j]: num(df.iloc[i, datacols[j]]) for j in range(nb)}
                out[key] = vals
                used.add(i)
                break
    return nb, out


def main():
    os.makedirs(RAWDIR, exist_ok=True)
    filas_serie, filas_panel = [], []
    for y in range(2017, 2027):
        for r in ["I", "II", "III", "IV"]:
            dest = os.path.join(RAWDIR, f"cin_{r}_{y}.xls")
            if not descargar(r, y, dest):
                continue
            res = parse_calendario(dest)
            if not res:
                print(f"  [{r}_{y}] sin cuadro calendario")
                continue
            nb, sec = res
            fecha = f"{y}-{ROMAN[r]}-01"
            # El TOTAL se reconstruye sumando sectores aditivos (gobierno + bcra +
            # bancos + otros_sectores + inversion_directa), todos principal+intereses.
            # Asi la serie es consistente: la fila-total publicada por INDEC excluye
            # los intereses del Gobierno general en los boletines de 2017 (footnote).
            adi = ["gobierno", "bcra", "bancos", "otros_sectores", "inversion_directa"]
            if "otros_sectores" not in sec:  # fallback si falta el agregado
                adi = ["gobierno", "bcra", "bancos", "otras_financieras",
                       "no_financieras", "inversion_directa"]
            tot = {}
            for b in BUCKETS[:nb]:
                vs = [sec[k].get(b) for k in adi if k in sec and sec[k].get(b) is not None]
                tot[b] = round(sum(vs), 3) if vs else None
            gob = sec.get("gobierno", {})
            def suma(d, ks):
                vs = [d.get(k) for k in ks if d.get(k) is not None]
                return round(sum(vs), 3) if vs else None
            row = {"fecha": fecha}
            for b in BUCKETS:
                row["venc_" + b] = tot.get(b)
            row["venc_prox_1y"] = suma(tot, PROX_1Y)
            row["venc_prox_2y"] = suma(tot, PROX_2Y)
            row["venc_gob_prox_1y"] = suma(gob, PROX_1Y)
            row["venc_gob_prox_2y"] = suma(gob, PROX_2Y)
            filas_serie.append(row)
            # panel largo
            for key, vals in sec.items():
                for b, v in vals.items():
                    if v is not None:
                        filas_panel.append({"fecha": fecha, "sector": key,
                                            "tramo": b, "valor": round(v, 3)})
            print(f"  [{r}_{y}] OK tramos={nb} prox_2y_total={row['venc_prox_2y']}")

    serie = pd.DataFrame(filas_serie).sort_values("fecha")
    panel = pd.DataFrame(filas_panel).sort_values(["fecha", "sector", "tramo"])

    # Marca de anomalia de fuente: el boletin 2023T1 de INDEC publica un valor
    # erroneo de intereses >2 anios del Gobierno general (118.441 vs ~38 en los
    # trimestres vecinos), que infla venc_mas_2y a 267.355 (lo coherente es ~189).
    # NO afecta venc_prox_1y/2y. Se conserva el valor publicado y se marca con flag.
    serie["venc_mas_2y_anomalo"] = (serie["fecha"] == "2023-03-01").astype(int)
    serie.to_csv(f"{OUT}/deuda_externa_calendario_serie.csv", index=False, encoding="utf-8")
    panel.to_csv(f"{OUT}/deuda_externa_calendario_panel.csv", index=False, encoding="utf-8")
    print(f"\nSerie: {len(serie)} fechas {serie['fecha'].min()} .. {serie['fecha'].max()}")
    print(f"Panel: {len(panel)} filas")


if __name__ == "__main__":
    main()
