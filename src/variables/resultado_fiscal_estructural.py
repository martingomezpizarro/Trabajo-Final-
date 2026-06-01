"""
Resultado Fiscal Estructural (SE) – Argentina 2006Q1-2025Q4
============================================================

Replica metodología de Gay & Escudero (2010) "El resultado fiscal estructural
en la Argentina: 1983-2010" con tres adaptaciones:

  (1) PIB potencial Y* via función Cobb-Douglas Y = K^0.6 · (LQ)^0.4 · PTF,
      con K vía inventario perpetuo desde FBKF, L = Pob_activa proxy
      (WB pop × (1-desempleo)), NAIRU via filtro HP sobre desempleo,
      PTF residual suavizada con HP (λ=1600 trimestral).

  (2) Ajuste de commodities sobre TI general (no precios de soja).
      Razón: TI captura el efecto agregado de precios de exportación,
      y el dato de precio de soja específico no está aislado en la base.
      Ratio: TI*/TI, con TI* = MA centrado 10 años sobre ti_base100.

  (3) Inicio en 2006Q1 (post-consolidación retenciones, evita inestabilidad
      metodológica 1993-2005).

Ecuaciones (G&E 2010, ecs. 2, 3, 5, 6, 7):

    T_CA  = T  · (Y*/Y)^ε_T              # ingresos cíclicamente ajustados
    G_CA  = G  · (Y*/Y)^ε_G              # gastos cíclicamente ajustados
    SCA   = T_CA - G_CA                  # superávit cíclicamente ajustado
    T^S   = T_CA · (TI*/TI)^γ            # ingresos estructurales (commodity)
    SE    = T^S - G_CA                   # superávit ESTRUCTURAL

Elasticidades (G&E 2010, Tabla 1):
    ε_T = 1.14   (recaudación / PIB)
    ε_G = 0.43   (gasto / PIB)
    γ   = 1.00   (ajuste commodity proporcional)

Output:
    data/Variables Finales/resultado_fiscal_estructural.csv

Autor: Martín Gómez Pizarro – Trabajo Final Lic. Economía UNC
Fecha: 2026-05-30
"""
from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.filters.hp_filter import hpfilter

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
DATA_VF = ROOT / "data" / "Variables Finales"
DATA_RAW = ROOT / "data" / "raw"
OUT_PATH = DATA_VF / "resultado_fiscal_estructural.csv"

START = "2006-01-01"
END = "2025-12-31"

# Elasticidades Gay & Escudero (2010)
EPS_T = 1.14
EPS_G = 0.43
GAMMA = 1.00

# Cobb-Douglas
ALPHA_K = 0.60
ALPHA_L = 0.40

# Inventario perpetuo
DELTA_ANNUAL = 0.05  # depreciación anual estándar Argentina (Coremberg)
DELTA_Q = 1 - (1 - DELTA_ANNUAL) ** (1 / 4)  # trimestral equivalente
K0_RATIO = 2.5  # K₀/Y₀ ≈ 2.5 (estimación PWT para Argentina ~2004)

# HP filter
LAMBDA_Q = 1600  # estándar para datos trimestrales


# ---------------------------------------------------------------------------
# 1. CARGA DE DATOS
# ---------------------------------------------------------------------------

def load_quarterly_data() -> pd.DataFrame:
    """Carga y alinea todas las series a frecuencia trimestral."""

    # --- PBI real (constante 2004) ---
    pbi_real = pd.read_csv(DATA_VF / "pbi_constante_2004.csv", parse_dates=["fecha"])
    pbi_real = pbi_real.rename(columns={"pbi": "Y_real"}).set_index("fecha")

    # --- PBI nominal ---
    pbi_nom = pd.read_csv(DATA_VF / "pbi_corriente.csv", parse_dates=["fecha"])
    pbi_nom = pbi_nom.rename(columns={"pbi": "Y_nom"}).set_index("fecha")

    # --- FBKF real (para construir K) ---
    fbkf = pd.read_csv(DATA_VF / "fbkf_constante.csv", parse_dates=["fecha"])
    fbkf = fbkf.rename(columns={"fbkf_total": "I_real"}).set_index("fecha")[["I_real"]]

    # --- TI mensual → trimestral (promedio) ---
    ti = pd.read_csv(DATA_VF / "ti_mensual.csv", parse_dates=["fecha"])
    ti = ti.set_index("fecha")[["ti_base100"]]
    ti_q = ti.resample("QS").mean()
    ti_q.index = ti_q.index + pd.offsets.MonthBegin(2)  # alinear a 03-01, 06-01...
    ti_q = ti_q.rename(columns={"ti_base100": "TI"})

    # --- Fiscal mensual → trimestral (suma) ---
    fis = pd.read_excel(
        DATA_VF / "Resultado fiscal-unificado.xlsx",
        sheet_name="Unificado",
        parse_dates=["indice_tiempo"],
    )
    # Usamos ingresos y gastos PRIMARIOS antes de figurativos
    # (consistente con definición G&E: excluye intereses y transferencias intra-gobierno)
    fis = fis.set_index("indice_tiempo")[
        [
            "ing_primario_antes_figurativos",
            "gtos_primario_antes_figurativos",
            "superavit_primario",
            "superavit_primario_sin_privatizaciones",
        ]
    ].rename(
        columns={
            "ing_primario_antes_figurativos": "T_nom",
            "gtos_primario_antes_figurativos": "G_nom",
            "superavit_primario": "SP_oficial",
            "superavit_primario_sin_privatizaciones": "SP_oficial_neto",
        }
    )
    fis_q = fis.resample("QS").sum()
    fis_q.index = fis_q.index + pd.offsets.MonthBegin(2)

    # --- WB anual: desempleo + población → interpolar a trimestral ---
    unemp = pd.read_csv(DATA_RAW / "worldbank" / "unemployment.csv")
    unemp = unemp[unemp["economy"] == "ARG"].copy()
    unemp["fecha"] = pd.to_datetime(unemp["year"].astype(str) + "-07-01")  # mid-year
    unemp = unemp.set_index("fecha")[["value"]].rename(columns={"value": "u_rate"})

    pop = pd.read_csv(DATA_RAW / "worldbank" / "population.csv")
    pop = pop[pop["economy"] == "ARG"].copy()
    pop["fecha"] = pd.to_datetime(pop["year"].astype(str) + "-07-01")
    pop = pop.set_index("fecha")[["value"]].rename(columns={"value": "POP"})

    # Interpolar anual a trimestral
    q_index = pd.date_range("2004-03-01", "2025-12-01", freq="QS-MAR")
    unemp_q = unemp.reindex(unemp.index.union(q_index)).interpolate(method="time").reindex(q_index)
    pop_q = pop.reindex(pop.index.union(q_index)).interpolate(method="time").reindex(q_index)
    # Extender 2025 si falta (último valor)
    pop_q = pop_q.ffill()

    # --- MERGE ---
    df = pbi_real.join(pbi_nom).join(fbkf).join(ti_q).join(fis_q)
    df = df.join(unemp_q, how="left").join(pop_q, how="left")
    df.index.name = "fecha"
    return df


# ---------------------------------------------------------------------------
# 2. CAPITAL STOCK (Inventario Perpetuo)
# ---------------------------------------------------------------------------

def build_capital_stock(df: pd.DataFrame) -> pd.Series:
    """K_t = (1-δ)·K_{t-1} + I_t, con K₀ = K0_RATIO · Y₀."""
    I = df["I_real"].copy()
    Y0 = df["Y_real"].iloc[0]
    K0 = K0_RATIO * Y0 * 4  # K0_RATIO es ratio anual, escalo a stock total
    K = pd.Series(index=df.index, dtype=float, name="K")
    K.iloc[0] = K0
    for t in range(1, len(K)):
        K.iloc[t] = (1 - DELTA_Q) * K.iloc[t - 1] + I.iloc[t]
    return K


# ---------------------------------------------------------------------------
# 3. EMPLEO (L) y NAIRU
# ---------------------------------------------------------------------------

def build_labor(df: pd.DataFrame) -> pd.DataFrame:
    """
    L = POP × tasa_actividad × (1 - desempleo/100)
    Aproximación: tasa de actividad ARG promedio ~46% (INDEC EPH 2004-2025).
    NAIRU via HP filter sobre tasa de desempleo.
    L_pleno_empleo = POP × 0.46 × (1 - NAIRU/100)
    """
    TASA_ACT = 0.46  # tasa de actividad promedio ARG (EPH)
    L = df["POP"] * TASA_ACT * (1 - df["u_rate"] / 100)

    # NAIRU = tendencia HP del desempleo
    u_series = df["u_rate"].dropna()
    _, u_trend = hpfilter(u_series, lamb=LAMBDA_Q)
    NAIRU = pd.Series(u_trend, index=u_series.index, name="NAIRU").reindex(df.index)
    L_pleno = df["POP"] * TASA_ACT * (1 - NAIRU / 100)

    return pd.DataFrame({"L": L, "NAIRU": NAIRU, "L_pleno": L_pleno}, index=df.index)


# ---------------------------------------------------------------------------
# 4. PIB POTENCIAL (Cobb-Douglas)
# ---------------------------------------------------------------------------

def compute_potential_output(df: pd.DataFrame) -> pd.DataFrame:
    """Y* = K^α · L_pleno^(1-α) · PTF_suavizada."""
    K = df["K"]
    L = df["L"]
    L_pleno = df["L_pleno"]
    Y = df["Y_real"]

    # PTF residual: Y / (K^α · L^(1-α))
    PTF = Y / (K ** ALPHA_K * L ** ALPHA_L)
    _, PTF_trend = hpfilter(np.log(PTF), lamb=LAMBDA_Q)
    PTF_smooth = np.exp(PTF_trend)

    # Y* = K^α · L_pleno^(1-α) · PTF_smooth
    Y_pot = K ** ALPHA_K * L_pleno ** ALPHA_L * PTF_smooth

    # Brecha del producto: GAP = (Y - Y*) / Y*
    GAP = (Y - Y_pot) / Y_pot

    return pd.DataFrame(
        {"PTF": PTF, "PTF_smooth": PTF_smooth, "Y_pot": Y_pot, "GAP": GAP},
        index=df.index,
    )


# ---------------------------------------------------------------------------
# 5. TI* (largo plazo - MA centrado 10 años)
# ---------------------------------------------------------------------------

def compute_ti_long_run(df: pd.DataFrame) -> pd.Series:
    """
    TI* = MA centrado de 10 años (40 trimestres).
    Para extremos (5 años hacia atrás/adelante de la muestra): promedio muestral.
    """
    TI = df["TI"].copy()
    window = 40  # 10 años trimestrales
    sample_mean = TI.mean()

    TI_star = TI.rolling(window=window, center=True, min_periods=1).mean()

    # Reemplazar bordes (primeros y últimos 20 períodos) con promedio muestral
    half = window // 2
    n = len(TI)
    if n > window:
        # Mezcla suave: bordes = promedio simple muestral
        TI_star.iloc[:half] = sample_mean
        TI_star.iloc[-half:] = sample_mean

    return TI_star.rename("TI_star")


# ---------------------------------------------------------------------------
# 6. RESULTADO FISCAL ESTRUCTURAL
# ---------------------------------------------------------------------------

def compute_structural_balance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica las ecuaciones G&E 2010:
      T_CA = T · (Y*/Y)^ε_T
      G_CA = G · (Y*/Y)^ε_G
      SCA  = T_CA - G_CA
      T^S  = T_CA · (TI*/TI)^γ
      SE   = T^S - G_CA

    Expresado como % del PIB nominal.
    """
    Y = df["Y_real"]
    Y_pot = df["Y_pot"]
    T = df["T_nom"]
    G = df["G_nom"]
    TI = df["TI"]
    TI_star = df["TI_star"]
    Y_nom = df["Y_nom"]

    ratio_Y = Y_pot / Y
    ratio_TI = TI_star / TI

    T_CA = T * ratio_Y ** EPS_T
    G_CA = G * ratio_Y ** EPS_G
    SCA = T_CA - G_CA
    T_S = T_CA * ratio_TI ** GAMMA
    SE = T_S - G_CA

    # Superávit primario observado (sin ajuste)
    SP = T - G

    # OJO: Y_nom es PBI anualizado a frecuencia Q (cada Q muestra la tasa anual).
    # T, G son flujos trimestrales (suma de meses). Para % PBI correcto:
    # ratio = T_quarterly / Y_quarterly_flow = T / (Y_nom / 4)
    Y_nom_q = Y_nom / 4

    return pd.DataFrame(
        {
            "T_CA": T_CA,
            "G_CA": G_CA,
            "SCA": SCA,
            "T_estruct": T_S,
            "SE": SE,
            "SP_observado": SP,
            # En % del PBI nominal (corregido por escala anualizada)
            "SP_pctPIB": SP / Y_nom_q * 100,
            "SCA_pctPIB": SCA / Y_nom_q * 100,
            "SE_pctPIB": SE / Y_nom_q * 100,
        },
        index=df.index,
    )


# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("RESULTADO FISCAL ESTRUCTURAL – Gay & Escudero (2010) adaptado")
    print("=" * 70)

    print("\n[1/6] Cargando datos…")
    df = load_quarterly_data()
    print(f"      Período inicial: {df.index.min().date()} a {df.index.max().date()}")
    print(f"      Observaciones: {len(df)}")

    print("\n[2/6] Construyendo capital stock K (inventario perpetuo)…")
    df["K"] = build_capital_stock(df)
    print(f"      K(2006Q1)={df.loc['2006-03-01', 'K']:,.0f}   K(2025Q4)={df['K'].iloc[-1]:,.0f}")

    print("\n[3/6] Estimando L y NAIRU…")
    labor = build_labor(df)
    df = df.join(labor)
    print(f"      NAIRU promedio 2006-2025: {df.loc['2006':'2025', 'NAIRU'].mean():.2f}%")
    print(f"      L promedio: {df.loc['2006':'2025', 'L'].mean()/1e6:.2f}M personas")

    print("\n[4/6] Estimando PBI potencial Y* (Cobb-Douglas)…")
    pot = compute_potential_output(df)
    df = df.join(pot)
    gap_mean = df.loc["2006":"2025", "GAP"].mean() * 100
    print(f"      Brecha promedio: {gap_mean:+.2f}%")
    print(f"      GAP máx: {df['GAP'].max()*100:+.2f}%   mín: {df['GAP'].min()*100:+.2f}%")

    print("\n[5/6] Construyendo TI* (MA centrado 10 años)…")
    df["TI_star"] = compute_ti_long_run(df)
    print(f"      TI promedio 2006-2025: {df.loc['2006':'2025', 'TI'].mean():.1f}")
    print(f"      TI* promedio: {df.loc['2006':'2025', 'TI_star'].mean():.1f}")

    print("\n[6/6] Calculando Resultado Fiscal Estructural…")
    out = compute_structural_balance(df)
    df = df.join(out)

    # Filtrar a período de análisis
    df_final = df.loc[START:END].copy()
    print(f"\n      SP promedio 2006-2025: {df_final['SP_pctPIB'].mean():+.2f}% del PIB")
    print(f"      SCA promedio:         {df_final['SCA_pctPIB'].mean():+.2f}% del PIB")
    print(f"      SE promedio:          {df_final['SE_pctPIB'].mean():+.2f}% del PIB")

    # Guardar output
    # Calcular SP oficial en % PBI (Y_nom anualizado → dividir por 4 para flujo Q)
    df_final["SP_oficial_pctPIB"] = df_final["SP_oficial"] / (df_final["Y_nom"] / 4) * 100

    cols_export = [
        "Y_real", "Y_nom", "Y_pot", "GAP",
        "K", "L", "L_pleno", "NAIRU", "PTF_smooth",
        "TI", "TI_star",
        "T_nom", "G_nom",
        "T_CA", "G_CA", "T_estruct",
        "SP_observado", "SP_oficial", "SP_oficial_neto", "SCA", "SE",
        "SP_pctPIB", "SP_oficial_pctPIB", "SCA_pctPIB", "SE_pctPIB",
    ]
    df_final[cols_export].to_csv(OUT_PATH, index_label="fecha", float_format="%.4f")
    print(f"\n[OK] Guardado en: {OUT_PATH.relative_to(ROOT)}")
    print(f"     Filas: {len(df_final)}   Columnas: {len(cols_export)}")

    print("\n" + "=" * 70)
    print("Validacion vs G&E (2006-2010) - SP oficial vs SE estimado:")
    print("=" * 70)
    annual = df_final.loc["2006":"2010", ["SP_oficial_pctPIB", "SP_pctPIB", "SCA_pctPIB", "SE_pctPIB"]].resample("YE").mean()
    print(annual.round(2))
    print("\nReferencia G&E Fig 5: 2006 SP~4%/SE~3.5%, 2007 SP~2.5%/SE~2%, 2008 SP~3%/SE~1%")

    print("\n" + "=" * 70)
    print("Resultado completo 2006-2025 (anual):")
    print("=" * 70)
    annual_full = df_final[["SP_oficial_pctPIB", "SP_pctPIB", "SCA_pctPIB", "SE_pctPIB", "GAP"]].resample("YE").mean()
    annual_full["GAP_pct"] = annual_full["GAP"] * 100
    print(annual_full[["SP_oficial_pctPIB", "SP_pctPIB", "SCA_pctPIB", "SE_pctPIB", "GAP_pct"]].round(2))


if __name__ == "__main__":
    main()
