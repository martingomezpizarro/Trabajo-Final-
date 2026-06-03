# -*- coding: utf-8 -*-
"""
Genera series de DEUDA EXTERNA BRUTA (INDEC, Cuentas Internacionales) a partir
de cin_IV_2025.xls. OJO: concepto distinto a la deuda bruta MECON
(data/Variables Finales/saldo_deuda*.csv). Esto es deuda con NO RESIDENTES,
de TODOS los sectores. Se guarda en archivos NUEVOS y separados.

Salidas (millones de USD, fin de trimestre):
  - deuda_externa_sectores.csv  (Cuadro 24: total + por sector institucional)
  - deuda_externa_plazo.csv     (Cuadro 23: total + corto/largo plazo)
Fechas: T1->MM-03, T2->06, T3->09, T4->12, dia 01 (igual que saldo_deuda.csv).
"""
import pandas as pd

XLS = "cin_IV_2025.xls"
OUT = "data/Variables Finales"


def periodos(row):
    """Convierte la fila de encabezado '2006T1','2025T4*' -> '2006-03-01'."""
    fechas = []
    cols = []
    for c, v in enumerate(row.tolist()):
        s = str(v).strip().replace("*", "")
        if len(s) == 6 and s[4] == "T" and s[:4].isdigit():
            mm = {"1": "03", "2": "06", "3": "09", "4": "12"}[s[5]]
            fechas.append(f"{s[:4]}-{mm}-01")
            cols.append(c)
    return cols, fechas


def fmt(x):
    if pd.isna(x):
        return ""
    return f"{float(x):.3f}".rstrip("0").rstrip(".")


# ---------------- Cuadro 23: por sector institucional (aditivo) ----------------
# Se usa el Cuadro 23 (no el 24) porque alli los sectores son ADITIVOS al total:
# en el Cuadro 24, "Sociedades no financieras" ya incluye la inversion directa y
# la fila "Inversion directa" es solo un memo (doble conteo si se suma).
# Cuadro 23: Total = Gobierno + BCRA + Bancos + Otros sectores + Inversion directa.
c23s = pd.read_excel(XLS, sheet_name="Cuadro 23", header=None)
cols, fechas = periodos(c23s.iloc[4])

# Matching por prefijo ASCII; se toma la PRIMERA aparicion de cada encabezado.
secdefs = [
    ("dext_total", "Saldo deuda extrena bruta"),
    ("dext_gobierno", "Gobierno general"),
    ("dext_bcra", "Banco central"),
    ("dext_bancos", "Sociedades captadoras"),
    ("dext_otros_sectores", "Otros sectores"),
    ("dext_otras_financieras", "Otras sociedades financieras"),
    ("dext_no_financieras", "Sociedades no financieras"),
    ("dext_inversion_directa", "Inversi"),  # 'Inversion directa: Credito entre empresas'
]
data23 = {}
for i, row in c23s.iterrows():
    lab = str(row[0]).strip()
    for key, pref in secdefs:
        if key not in data23 and lab.startswith(pref):
            data23[key] = [row[c] for c in cols]
            break

orden = ["dext_total", "dext_gobierno", "dext_bcra", "dext_bancos",
         "dext_otros_sectores", "dext_otras_financieras", "dext_no_financieras",
         "dext_inversion_directa"]
df24 = pd.DataFrame({"fecha": fechas})
for k in orden:
    df24[k] = data23[k]

# validacion: gobierno+bcra+bancos+otros_sectores+ID == total
aditivos = ["dext_gobierno", "dext_bcra", "dext_bancos",
            "dext_otros_sectores", "dext_inversion_directa"]
suma = sum(df24[k] for k in aditivos)
maxdif = (suma - df24["dext_total"]).abs().max()
print(f"[Sectores] maxima diferencia |sum sectores - total| = {maxdif:.4f} M USD")
# validacion: otras_financieras + no_financieras == otros_sectores
maxdif2 = (df24["dext_otras_financieras"] + df24["dext_no_financieras"]
           - df24["dext_otros_sectores"]).abs().max()
print(f"[Sectores] maxima diferencia |fin+nofin - otros_sectores| = {maxdif2:.4f} M USD")

df24_out = df24.copy()
for k in orden:
    df24_out[k] = df24_out[k].map(fmt)
df24_out.to_csv(f"{OUT}/deuda_externa_sectores.csv", index=False, encoding="utf-8")
print(f"[Sectores] {len(df24)} trimestres: {fechas[0]} .. {fechas[-1]}")

# ---------------- Cuadro 23: corto / largo plazo (total) ----------------
c23 = pd.read_excel(XLS, sheet_name="Cuadro 23", header=None)
cols2, fechas2 = periodos(c23.iloc[4])

total_row = None
corto = [0.0] * len(cols2)
largo = [0.0] * len(cols2)
for i, row in c23.iterrows():
    lab = str(row[0]).strip()
    if lab == "Saldo deuda extrena bruta":
        total_row = [row[c] for c in cols2]
    elif lab == "A corto plazo":
        for j, c in enumerate(cols2):
            corto[j] += float(row[c]) if not pd.isna(row[c]) else 0.0
    elif lab == "A largo plazo":
        for j, c in enumerate(cols2):
            largo[j] += float(row[c]) if not pd.isna(row[c]) else 0.0

df23 = pd.DataFrame({
    "fecha": fechas2,
    "dext_total": total_row,
    "dext_corto_plazo": corto,
    "dext_largo_plazo": largo,
})
# inversion directa (credito entre empresas) no tiene split de plazo:
df23["dext_inversion_directa"] = df23["dext_total"] - df23["dext_corto_plazo"] - df23["dext_largo_plazo"]
print(f"[Cuadro 23] inversion directa (residual) rango: "
      f"{df23['dext_inversion_directa'].min():.0f} .. {df23['dext_inversion_directa'].max():.0f} M USD")

df23_out = df23.copy()
for k in ["dext_total", "dext_corto_plazo", "dext_largo_plazo", "dext_inversion_directa"]:
    df23_out[k] = df23_out[k].map(fmt)
df23_out.to_csv(f"{OUT}/deuda_externa_plazo.csv", index=False, encoding="utf-8")
print(f"[Cuadro 23] {len(df23)} trimestres: {fechas2[0]} .. {fechas2[-1]}")

# ---------------- Cuadro 25: calendario de servicio (foto forward 2025T4) ----
# OJO: NO es serie temporal. Es el calendario de pagos pendientes al cierre
# 2025T4, por sector institucional y tramo de plazo restante. Snapshot.
c25 = pd.read_excel(XLS, sheet_name="Cuadro 25", header=None)
buckets = ["pago_inmediato", "m0a3", "m3a6", "m6a9", "m9a12",
           "m12a18", "m18a24", "mas_2y", "sin_fecha"]  # columnas 1..9
# (fila_indice, sector, concepto)
filas25 = [
    (9, "gobierno_general", "total"), (10, "gobierno_general", "principal"), (11, "gobierno_general", "intereses"),
    (12, "banco_central", "total"), (13, "banco_central", "principal"), (14, "banco_central", "intereses"),
    (15, "soc_captadoras", "total"), (16, "soc_captadoras", "principal"), (17, "soc_captadoras", "intereses"),
    (18, "otros_sectores", "total"),
    (19, "otras_soc_financieras", "total"), (20, "otras_soc_financieras", "principal"), (21, "otras_soc_financieras", "intereses"),
    (22, "soc_no_financieras", "total"), (23, "soc_no_financieras", "principal"), (24, "soc_no_financieras", "intereses"),
    (25, "inversion_directa", "total"), (26, "inversion_directa", "principal"), (27, "inversion_directa", "intereses"),
    (28, "total_deuda_externa", "total"), (29, "total_deuda_externa", "principal"), (30, "total_deuda_externa", "intereses"),
]
rows = []
for ri, sector, concepto in filas25:
    rec = {"sector": sector, "concepto": concepto}
    for j, b in enumerate(buckets):
        rec[b] = fmt(c25.iloc[ri, j + 1])
    rows.append(rec)
df25 = pd.DataFrame(rows, columns=["sector", "concepto"] + buckets)
df25.to_csv(f"{OUT}/deuda_externa_calendario_pagos_2025T4.csv", index=False, encoding="utf-8")
print(f"[Cuadro 25] calendario de pagos (snapshot 2025T4): {len(df25)} filas")
