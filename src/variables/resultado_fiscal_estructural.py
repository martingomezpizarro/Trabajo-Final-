"""
Resultado Fiscal Estructural (SE) – Argentina 2006Q1-2025Q4
============================================================

Replica metodología de Gay & Escudero (2010) "El resultado fiscal estructural
en la Argentina: 1983-2010" con las siguientes características:

  (1) PIB potencial Y* via función Cobb-Douglas Y = K^0.6 · L^0.4 · PTF,
      con:
        - K vía inventario perpetuo desde FBKF (K₀ steady-state mejorado)
        - L derivado de tasa de empleo y actividad EPH-INDEC trimestral
        - NAIRU = HP filter (λ=1600) sobre desempleo EPH trimestral
        - PTF residual suavizada con HP

  (2) Ajuste de commodities sobre derechos de exportación AISLADOS
      (fórmula original G&E ec. 7), no sobre toda la T como en versión previa.
      P*/P aproximado por TI*/TI (Términos de Intercambio).

  (3) Inicio en 2006Q1 (post-consolidación retenciones).

Ecuaciones (G&E 2010, ecs. 2, 3, 5, 6, 7):

    T_CA = T · (Y*/Y)^ε_T              # ingresos cíclicamente ajustados
    G_CA = G · (Y*/Y)^ε_G              # gastos cíclicamente ajustados
    SCA  = T_CA - G_CA                 # superávit cíclicamente ajustado
    Tx^S = Tx · (TI*/TI)^γ             # derechos exportación estructurales
    SE   = SCA - (Tx - Tx^S)           # superávit ESTRUCTURAL

Elasticidades (G&E 2010, Tabla 1):
    ε_T = 1.14   (recaudación / PIB)
    ε_G = 0.43   (gasto / PIB)
    γ   = 1.00   (ajuste commodity proporcional)

Output:
    data/Variables Finales/resultado_fiscal_estructural.csv

Autor: Martín Gómez Pizarro – Trabajo Final Lic. Economía UNC
Fecha: 2026-06-03 (v2 con datos EPH y Tx aislado)
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
COBB_DIR = DATA_RAW / "cobb_douglas"
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

# Inventario perpetuo con K₀ INDEC real 2003 (precios constantes 2004)
DELTA_ANNUAL = 0.05
DELTA_Q = 1 - (1 - DELTA_ANNUAL) ** (1 / 4)
# K_INDEC fin-2003 derivado de stock-constantes-1993.xls × factor P_2004/P_1993 = 1.8731
# Stock Agregado base 1993 fin-2003 = 666,660 mio pesos 1993
# → 666,660 × 1.8731 = 1,248,688 mio pesos base 2004
K0_INDEC_2003 = 1_248_688  # millones de pesos constantes base 2004

# Serie completa K INDEC base 2004 (mio pesos) — derivada de stock-constantes 1993
K_INDEC_BASE2004 = {
    1990: 958_591, 1991: 967_203, 1992: 983_495, 1993: 1_017_374,
    1994: 1_057_147, 1995: 1_086_371, 1996: 1_112_381, 1997: 1_152_573,
    1998: 1_192_369, 1999: 1_222_983, 2000: 1_242_045, 2001: 1_252_773,
    2002: 1_239_717, 2003: 1_248_688, 2004: 1_269_895, 2005: 1_308_598,
    2006: 1_362_188,
}

LAMBDA_Q = 1600


# ---------------------------------------------------------------------------
# 1. CARGA DE DATOS
# ---------------------------------------------------------------------------

def load_quarterly_data() -> pd.DataFrame:
    """Carga y alinea todas las series a frecuencia trimestral (inicio Q = 03-01, 06-01, 09-01, 12-01)."""

    # --- PBI real y nominal ---
    pbi_real = pd.read_csv(DATA_VF / "pbi_constante_2004.csv", parse_dates=["fecha"])
    pbi_real = pbi_real.rename(columns={"pbi": "Y_real"}).set_index("fecha")

    pbi_nom = pd.read_csv(DATA_VF / "pbi_corriente.csv", parse_dates=["fecha"])
    pbi_nom = pbi_nom.rename(columns={"pbi": "Y_nom"}).set_index("fecha")

    # --- FBKF real ---
    fbkf = pd.read_csv(DATA_VF / "fbkf_constante.csv", parse_dates=["fecha"])
    fbkf = fbkf.rename(columns={"fbkf_total": "I_real"}).set_index("fecha")[["I_real"]]

    # --- TI mensual → trimestral ---
    ti = pd.read_csv(DATA_VF / "ti_mensual.csv", parse_dates=["fecha"])
    ti = ti.set_index("fecha")[["ti_base100"]]
    ti_q = ti.resample("QS").mean()
    ti_q.index = ti_q.index + pd.offsets.MonthBegin(2)
    ti_q = ti_q.rename(columns={"ti_base100": "TI"})

    # --- Fiscal mensual → trimestral (suma) ---
    fis = pd.read_excel(
        DATA_VF / "Resultado fiscal-unificado.xlsx",
        sheet_name="Unificado",
        parse_dates=["indice_tiempo"],
    )
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

    # --- Derechos de exportación mensual → trimestral (suma) ---
    rt = pd.read_csv(COBB_DIR / "recursos_tributarios.csv", parse_dates=["indice_tiempo"])
    tx = rt.set_index("indice_tiempo")[["derechos_exportacion"]].rename(
        columns={"derechos_exportacion": "Tx_nom"}
    )
    tx_q = tx.resample("QS").sum()
    tx_q.index = tx_q.index + pd.offsets.MonthBegin(2)

    # --- EPH trimestral: desempleo y empleo total ---
    ud = pd.read_csv(COBB_DIR / "desempleo_eph.csv", parse_dates=["indice_tiempo"])
    ud = ud[["indice_tiempo", "eph_continua_tasa_desempleo_total"]].rename(
        columns={"indice_tiempo": "fecha", "eph_continua_tasa_desempleo_total": "u_rate"}
    ).set_index("fecha")

    ue = pd.read_csv(COBB_DIR / "empleo_eph.csv", parse_dates=["indice_tiempo"])
    ue = ue[["indice_tiempo", "eph_continua_tasa_empleo_total"]].rename(
        columns={"indice_tiempo": "fecha", "eph_continua_tasa_empleo_total": "e_rate"}
    ).set_index("fecha")

    # EPH llega en 01-01, 04-01, 07-01, 10-01 → realinear a inicio Q estándar
    eph = ud.join(ue)
    eph.index = eph.index + pd.offsets.MonthBegin(2)  # 01→03, 04→06, etc.

    # --- Población WB (anual → trimestral interpolado) ---
    pop = pd.read_csv(DATA_RAW / "worldbank" / "population.csv")
    pop = pop[pop["economy"] == "ARG"].copy()
    pop["fecha"] = pd.to_datetime(pop["year"].astype(str) + "-07-01")
    pop = pop.set_index("fecha")[["value"]].rename(columns={"value": "POP"})
    q_index = pd.date_range("2004-03-01", "2025-12-01", freq="QS-MAR")
    pop_q = pop.reindex(pop.index.union(q_index)).interpolate(method="time").reindex(q_index).ffill()

    # --- MERGE ---
    df = pbi_real.join(pbi_nom).join(fbkf).join(ti_q).join(fis_q).join(tx_q)
    df = df.join(eph, how="left").join(pop_q, how="left")
    df.index.name = "fecha"
    return df


# ---------------------------------------------------------------------------
# 2. CAPITAL STOCK (Inventario Perpetuo)
# ---------------------------------------------------------------------------

def build_capital_stock(df: pd.DataFrame) -> pd.Series:
    """
    K_t = (1-δ_q)·K_{t-1} + I_t / 4

    K₀ = K_INDEC fin-2003 (precios constantes base 2004) = 1,119,822 millones.
    FBKF está anualizada a frecuencia Q (cada Q muestra tasa anual), por lo
    que la inversión REAL del trimestre es I_t/4.
    """
    I = df["I_real"].copy()
    K = pd.Series(index=df.index, dtype=float, name="K")
    # K stock al inicio de 2004Q1 = K_INDEC fin-2003
    K.iloc[0] = K0_INDEC_2003
    for t in range(1, len(K)):
        # I anualizado → flujo trimestral = I/4
        K.iloc[t] = (1 - DELTA_Q) * K.iloc[t - 1] + I.iloc[t] / 4
    return K


# ---------------------------------------------------------------------------
# 3. EMPLEO (L) y NAIRU desde EPH
# ---------------------------------------------------------------------------

def build_labor(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye L y NAIRU desde EPH trimestral.

    Definiciones EPH (tasas sobre POBLACIÓN TOTAL):
      - tasa_empleo (e):     ocupados / pob_total
      - tasa_desempleo (u):  desocupados / pob_activa
      - tasa_actividad (TA): pob_activa / pob_total = e / (1-u)

    Empleo:
      L_observado = POP × tasa_empleo (ya es directo)
      L_pleno     = POP × TA × (1 - NAIRU)

    NAIRU = HP filter (λ=1600) sobre tasa de desempleo trimestral.
    """
    # Tasa de actividad derivada
    TA = df["e_rate"] / (1 - df["u_rate"])

    # L observado (en personas)
    L = df["POP"] * df["e_rate"]

    # NAIRU via HP sobre desempleo trimestral (manejando NaN)
    u_clean = df["u_rate"].dropna()
    if len(u_clean) > 4:
        _, u_trend = hpfilter(u_clean, lamb=LAMBDA_Q)
        NAIRU = pd.Series(u_trend, index=u_clean.index, name="NAIRU").reindex(df.index).ffill().bfill()
    else:
        NAIRU = pd.Series(u_clean.mean(), index=df.index, name="NAIRU")

    # L pleno empleo (con NAIRU, manteniendo TA observada)
    L_pleno = df["POP"] * TA * (1 - NAIRU)

    return pd.DataFrame(
        {"TA": TA, "L": L, "NAIRU": NAIRU, "L_pleno": L_pleno},
        index=df.index,
    )


# ---------------------------------------------------------------------------
# 4. PIB POTENCIAL (Cobb-Douglas)
# ---------------------------------------------------------------------------

def compute_potential_output(df: pd.DataFrame) -> pd.DataFrame:
    """Y* = K^α · L_pleno^(1-α) · PTF_suavizada. Maneja NaN en L (EPH faltante)."""
    K = df["K"]
    L = df["L"].interpolate(method="time").ffill().bfill()
    L_pleno = df["L_pleno"].interpolate(method="time").ffill().bfill()
    Y = df["Y_real"]

    PTF = Y / (K ** ALPHA_K * L ** ALPHA_L)
    # HP filter requiere serie sin NaN
    PTF_clean = PTF.dropna()
    _, PTF_trend = hpfilter(np.log(PTF_clean), lamb=LAMBDA_Q)
    PTF_smooth = pd.Series(np.exp(PTF_trend), index=PTF_clean.index).reindex(df.index).ffill().bfill()

    Y_pot = K ** ALPHA_K * L_pleno ** ALPHA_L * PTF_smooth
    GAP = (Y - Y_pot) / Y_pot

    return pd.DataFrame(
        {"PTF": PTF, "PTF_smooth": PTF_smooth, "Y_pot": Y_pot, "GAP": GAP},
        index=df.index,
    )


# ---------------------------------------------------------------------------
# 5. TI* (largo plazo - MA centrado 10 años)
# ---------------------------------------------------------------------------

def compute_ti_long_run(df: pd.DataFrame) -> pd.Series:
    """TI* = MA centrado 40Q. Bordes: promedio muestral."""
    TI = df["TI"].copy()
    window = 40
    sample_mean = TI.mean()
    TI_star = TI.rolling(window=window, center=True, min_periods=1).mean()
    half = window // 2
    if len(TI) > window:
        TI_star.iloc[:half] = sample_mean
        TI_star.iloc[-half:] = sample_mean
    return TI_star.rename("TI_star")


# ---------------------------------------------------------------------------
# 6. RESULTADO FISCAL ESTRUCTURAL (G&E ec. 7)
# ---------------------------------------------------------------------------

def compute_structural_balance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ecuaciones G&E (2, 3, 5, 6, 7):
      T_CA = T · (Y*/Y)^ε_T
      G_CA = G · (Y*/Y)^ε_G
      SCA  = T_CA - G_CA
      Tx^S = Tx · (TI*/TI)^γ          ← solo sobre derechos exportación
      SE   = SCA - (Tx - Tx^S)        ← resta el componente cíclico commodity

    Y_nom es PBI anualizado (cada Q muestra tasa anual). T, G, Tx son flujos
    trimestrales. % PBI: ratio = T*4/Y_nom = T/(Y_nom/4).
    """
    Y = df["Y_real"]
    Y_pot = df["Y_pot"]
    T = df["T_nom"]
    G = df["G_nom"]
    Tx = df["Tx_nom"]
    TI = df["TI"]
    TI_star = df["TI_star"]
    Y_nom = df["Y_nom"]

    ratio_Y = Y_pot / Y
    ratio_TI = TI_star / TI

    T_CA = T * ratio_Y ** EPS_T
    G_CA = G * ratio_Y ** EPS_G
    SCA = T_CA - G_CA

    Tx_S = Tx * ratio_TI ** GAMMA
    componente_ciclico_commodity = Tx - Tx_S
    SE = SCA - componente_ciclico_commodity

    SP = T - G
    Y_nom_q = Y_nom / 4

    return pd.DataFrame(
        {
            "T_CA": T_CA,
            "G_CA": G_CA,
            "SCA": SCA,
            "Tx_estruct": Tx_S,
            "componente_ciclico_commodity": componente_ciclico_commodity,
            "SE": SE,
            "SP_observado": SP,
            "SP_pctPIB": SP / Y_nom_q * 100,
            "SCA_pctPIB": SCA / Y_nom_q * 100,
            "SE_pctPIB": SE / Y_nom_q * 100,
            "Tx_pctPIB": Tx / Y_nom_q * 100,
        },
        index=df.index,
    )


# ---------------------------------------------------------------------------
# PIPELINE PRINCIPAL
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("RESULTADO FISCAL ESTRUCTURAL v2 – G&E 2010 con datos EPH + Tx aislado")
    print("=" * 70)

    print("\n[1/6] Cargando datos...")
    df = load_quarterly_data()
    print(f"      Observaciones: {len(df)} ({df.index.min().date()} a {df.index.max().date()})")
    print(f"      EPH desempleo cobertura: {df['u_rate'].notna().sum()} Q")

    print(f"\n[2/6] Construyendo capital stock K (K0_INDEC_2003={K0_INDEC_2003:,} mio)...")
    df["K"] = build_capital_stock(df)
    print(f"      K(2004Q1)={df['K'].iloc[0]:,.0f}   K(2025Q4)={df['K'].iloc[-1]:,.0f}")
    print(f"      Ratio K/Y final: {df['K'].iloc[-1] / df['Y_real'].iloc[-1]:.2f}")

    print("\n[3/6] L y NAIRU desde EPH trimestral...")
    labor = build_labor(df)
    df = df.join(labor)
    sub = df.loc["2006":"2025"]
    print(f"      Tasa actividad promedio: {sub['TA'].mean():.3f} (vs proxy anterior 0.460)")
    print(f"      Desempleo EPH promedio:  {sub['u_rate'].mean()*100:.2f}%")
    print(f"      NAIRU promedio:          {sub['NAIRU'].mean()*100:.2f}%")
    print(f"      L promedio: {sub['L'].mean()/1e6:.2f}M ocupados")

    print("\n[4/6] PBI potencial Y* (Cobb-Douglas)...")
    pot = compute_potential_output(df)
    df = df.join(pot)
    gap_06_25 = df.loc["2006":"2025", "GAP"]
    print(f"      Brecha 2006-2025: mean={gap_06_25.mean()*100:+.2f}%  max={gap_06_25.max()*100:+.2f}%  min={gap_06_25.min()*100:+.2f}%")

    print("\n[5/6] TI* (MA centrado 10 años)...")
    df["TI_star"] = compute_ti_long_run(df)

    print("\n[6/6] Resultado Fiscal Estructural (G&E ec. 7)...")
    out = compute_structural_balance(df)
    df = df.join(out)

    df_final = df.loc[START:END].copy()
    df_final["SP_oficial_pctPIB"] = df_final["SP_oficial"] / (df_final["Y_nom"] / 4) * 100

    print(f"\n      Tx promedio (% PBI):  {df_final['Tx_pctPIB'].mean():+.2f}%")
    print(f"      SP oficial promedio:  {df_final['SP_oficial_pctPIB'].mean():+.2f}% PBI")
    print(f"      SCA promedio:         {df_final['SCA_pctPIB'].mean():+.2f}% PBI")
    print(f"      SE promedio:          {df_final['SE_pctPIB'].mean():+.2f}% PBI")

    cols_export = [
        "Y_real", "Y_nom", "Y_pot", "GAP",
        "K", "L", "L_pleno", "TA", "u_rate", "e_rate", "NAIRU", "PTF_smooth",
        "TI", "TI_star",
        "T_nom", "G_nom", "Tx_nom",
        "T_CA", "G_CA", "Tx_estruct", "componente_ciclico_commodity",
        "SP_observado", "SP_oficial", "SP_oficial_neto", "SCA", "SE",
        "SP_pctPIB", "SP_oficial_pctPIB", "SCA_pctPIB", "SE_pctPIB", "Tx_pctPIB",
    ]
    df_final[cols_export].to_csv(OUT_PATH, index_label="fecha", float_format="%.4f")
    print(f"\n[OK] Guardado en: {OUT_PATH.relative_to(ROOT)}")
    print(f"     Filas: {len(df_final)}   Columnas: {len(cols_export)}")

    print("\n" + "=" * 70)
    print("Validacion vs G&E (2006-2010):")
    print("=" * 70)
    vals_06_10 = df_final.loc["2006":"2010", ["SP_oficial_pctPIB", "SCA_pctPIB", "SE_pctPIB", "GAP", "Tx_pctPIB"]].resample("YE").mean()
    vals_06_10["GAP_pct"] = vals_06_10["GAP"] * 100
    print(vals_06_10[["SP_oficial_pctPIB", "SCA_pctPIB", "SE_pctPIB", "GAP_pct", "Tx_pctPIB"]].round(2))
    print("\nReferencia G&E Fig 5: 2006 SP~4%/SE~3.5%, 2007 SP~2.5%/SE~2%, 2008 SP~3%/SE~1%")

    print("\n" + "=" * 70)
    print("Resultado completo 2006-2025 (anual):")
    print("=" * 70)
    full = df_final[["SP_oficial_pctPIB", "SCA_pctPIB", "SE_pctPIB", "GAP", "Tx_pctPIB"]].resample("YE").mean()
    full["GAP_pct"] = full["GAP"] * 100
    print(full[["SP_oficial_pctPIB", "SCA_pctPIB", "SE_pctPIB", "GAP_pct", "Tx_pctPIB"]].round(2))

    # Validacion K perpetuo vs INDEC base 2004
    print("\n" + "=" * 70)
    print("Validacion K perpetuo vs INDEC (base 2004):")
    print("=" * 70)
    print(f"{'Year':<6}{'K perpetuo (mio)':>20}{'K INDEC (mio)':>20}{'Diff %':>10}")
    K_q = df.loc["2004":"2006", "K"].resample("YE").last()
    for y in [2004, 2005, 2006]:
        K_indec = K_INDEC_BASE2004[y]
        K_perp = K_q.loc[f"{y}-12-31"]
        diff = (K_perp - K_indec) / K_indec * 100
        print(f"{y:<6}{K_perp:>20,.0f}{K_indec:>20,.0f}{diff:>9.2f}%")


if __name__ == "__main__":
    main()
