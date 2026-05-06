"""
PBI Trimestral en USD (usando TC MEP promedio trimestral)
=========================================================
Fuentes:
  - PBI a precios corrientes (millones de pesos): INDEC, sh_oferta_demanda_03_26.xls, cuadro 8, fila 7
  - Tipo de cambio MEP diario: tc_mep_2026-04-28.xlsx

Metodología:
  1. Se extrae la serie trimestral de PBI nominal en millones de pesos
  2. Se calcula el promedio trimestral del TC MEP
  3. Se divide PBI_pesos / TC_MEP_promedio = PBI en millones de USD
  
Nota: El TC MEP tiene datos desde 2010-Q1. Los trimestres sin datos de MEP quedan sin calcular.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
RAW_DIR = Path(r"C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec")
OUTPUT_DIR = Path(r"C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PBI_FILE = RAW_DIR / "sh_oferta_demanda_03_26.xls"
MEP_FILE = RAW_DIR / "tc_mep_2026-04-28.xlsx"

# ── 1. Leer PBI a precios corrientes y constantes ──────────────────────────────
df_pbi_nom_raw = pd.read_excel(PBI_FILE, sheet_name="cuadro 8", header=None)
df_pbi_real_raw = pd.read_excel(PBI_FILE, sheet_name="cuadro 1", header=None)

# Extraer años (fila 3) y trimestres (fila 4)
row_years = df_pbi_nom_raw.iloc[3]
row_quarters = df_pbi_nom_raw.iloc[4]
row_pbi_nom = df_pbi_nom_raw.iloc[6]  # "Producto Interno Bruto"
row_pbi_real = df_pbi_real_raw.iloc[6]

# Reconstruir la serie trimestral
records = []
current_year = None

for col_idx in range(1, len(row_years)):
    # Actualizar año si hay uno nuevo
    if pd.notna(row_years[col_idx]):
        year_str = str(row_years[col_idx]).strip()
        year_clean = ''.join([c for c in year_str if c.isdigit()])[:4]
        if year_clean:
            current_year = int(year_clean)
    
    if current_year is None:
        continue
    
    # Determinar el trimestre
    quarter_label = str(row_quarters[col_idx]) if pd.notna(row_quarters[col_idx]) else ""
    
    quarter_map = {
        "1": 1, "2": 2, "3": 3, "4": 4
    }
    
    quarter = None
    for key, q in quarter_map.items():
        if f"{key}" in quarter_label and "trimestre" in quarter_label:
            quarter = q
            break
    
    if quarter is None:
        continue  # Saltar "Total" y columnas vacías
    
    pbi_nom_val = row_pbi_nom[col_idx]
    pbi_real_val = row_pbi_real[col_idx]
    if pd.notna(pbi_nom_val) and pd.notna(pbi_real_val):
        records.append({
            "year": current_year,
            "quarter": quarter,
            "pbi_pesos_mm": pbi_nom_val,  # millones de pesos corrientes
            "pbi_constante_2004_mm": pbi_real_val # millones de pesos de 2004
        })

df_pbi = pd.DataFrame(records)
# Crear fecha como fin de trimestre
df_pbi["fecha"] = pd.PeriodIndex(
    year=df_pbi["year"], quarter=df_pbi["quarter"], freq="Q"
)
df_pbi = df_pbi.sort_values("fecha").reset_index(drop=True)

print(f"[OK] PBI cargado: {len(df_pbi)} trimestres ({df_pbi['fecha'].iloc[0]} a {df_pbi['fecha'].iloc[-1]})")

# ── 2. Leer TC MEP diario y calcular promedio trimestral ──────────────────────
df_mep = pd.read_excel(MEP_FILE)
df_mep.columns = ["fecha", "valor"]
df_mep["fecha"] = pd.to_datetime(df_mep["fecha"])
df_mep["valor"] = pd.to_numeric(df_mep["valor"], errors="coerce")
df_mep = df_mep.dropna(subset=["valor"])

# Calcular promedio trimestral
df_mep["periodo"] = df_mep["fecha"].dt.to_period("Q")
tc_mep_trimestral = df_mep.groupby("periodo")["valor"].agg(["mean", "count"]).reset_index()
tc_mep_trimestral.columns = ["fecha", "tc_mep_promedio", "obs_mep"]

print(f"[OK] TC MEP cargado: {len(tc_mep_trimestral)} trimestres ({tc_mep_trimestral['fecha'].iloc[0]} a {tc_mep_trimestral['fecha'].iloc[-1]})")

# ── 3. Merge y calcular PBI en USD ───────────────────────────────────────────
df_merged = pd.merge(df_pbi, tc_mep_trimestral, on="fecha", how="inner")
df_merged["pbi_usd_mm"] = df_merged["pbi_pesos_mm"] / df_merged["tc_mep_promedio"]

# Seleccionar y formatear columnas finales
df_result = df_merged[["fecha", "year", "quarter", "pbi_pesos_mm", "pbi_constante_2004_mm", "tc_mep_promedio", "obs_mep", "pbi_usd_mm"]].copy()
df_result.columns = ["periodo", "anio", "trimestre", "pbi_pesos_mm", "pbi_constante_2004_mm", "tc_mep_promedio", "obs_mep_en_trim", "pbi_usd_mm"]

# ── 4. Guardar ────────────────────────────────────────────────────────────────
output_file = OUTPUT_DIR / "pbi_trimestral_usd_mep.csv"
df_result.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"\n[OK] Resultado guardado en: {output_file}")
print(f"  Cobertura: {df_result['periodo'].iloc[0]} a {df_result['periodo'].iloc[-1]}")
print(f"  Total trimestres: {len(df_result)}")
print()

# ── 5. Mostrar tabla ─────────────────────────────────────────────────────────
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
pd.set_option("display.max_rows", 100)
pd.set_option("display.width", 140)
print(df_result.to_string(index=False))
