"""
kalman_filter.py - Filtro de Kalman para variables macroeconomicas argentinas
Trabajo Final de Grado

Estructura de cada serie (target + exogena):
1.  SE - Nivel (Mill. ARS)         | ARIMA(4,0,4) | Superavit primario (mensual)
2.  PBI nominal                     | ARIMA(4,1,4) | EMAE (mensual)
3.  Total Cuenta Corriente          | ARIMA(4,1,1) | Saldo Comercial (mensual)
4.  Total Cuenta Financiera         | ARIMA(1,1,4) | Saldo Comercial (mensual)
5.  Deuda Externa Bruta Total       | ARIMA(4,2,0) | Reservas Brutas BCRA / PBI
6.  Vencimientos USD a 1 anio       | ARIMA(0,1,4) | --
7.  Vencimientos USD a 2 anios      | ARIMA(0,1,4) | --
"""

import sys
import os
import warnings

# Fix Unicode output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# ── Rutas ────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
VARS_DIR = os.path.join(BASE, "data", "Variables Finales")
RAW_DIR = os.path.join(BASE, "data", "raw")
OUT_DIR = os.path.join(BASE, "outputs", "kalman")
os.makedirs(OUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_se() -> pd.DataFrame:
    """SE - Nivel (Mill. ARS), trimestral."""
    path = os.path.join(VARS_DIR, "resultado_fiscal_estructural.csv")
    df = pd.read_csv(path, parse_dates=["fecha"])
    df = df.set_index("fecha")[["SE"]].rename(columns={"SE": "se"})
    # frecuencia inferida automáticamente por pandas
    return df


def cargar_pbi_nominal() -> pd.DataFrame:
    """PBI nominal trimestral (Mill. ARS corrientes)."""
    path = os.path.join(VARS_DIR, "pbi_corriente.csv")
    df = pd.read_csv(path, parse_dates=["fecha"])
    df = df.set_index("fecha")[["pbi"]].rename(columns={"pbi": "pbi_nominal"})
    # frecuencia inferida automáticamente por pandas
    return df


def cargar_pbi_constante() -> pd.DataFrame:
    """PBI constante (real) trimestral, base 2004."""
    path = os.path.join(VARS_DIR, "pbi_constante_2004.csv")
    df = pd.read_csv(path, parse_dates=["fecha"])
    df = df.set_index("fecha")[["pbi"]].rename(columns={"pbi": "pbi_real"})
    # frecuencia inferida automáticamente por pandas
    return df


def cargar_balanza_pagos() -> pd.DataFrame:
    """Balance de Pagos MBP6 trimestral: Cuenta Corriente y Cuenta Financiera."""
    path = os.path.join(
        VARS_DIR,
        "balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv",
    )
    df = pd.read_csv(path, parse_dates=["indice_tiempo"])
    df = df.rename(
        columns={
            "indice_tiempo": "fecha",
            "total_cuenta_corriente": "cuenta_corriente",
            "total_cuenta_financiera": "cuenta_financiera",
        }
    )
    df = df.set_index("fecha")[["cuenta_corriente", "cuenta_financiera"]]
    # frecuencia inferida automáticamente por pandas
    return df


def cargar_deuda_externa() -> pd.DataFrame:
    """Deuda Externa Bruta Total, trimestral (Mill. USD)."""
    path = os.path.join(VARS_DIR, "deuda_externa_sectores.csv")
    df = pd.read_csv(path, parse_dates=["fecha"])
    df = df.set_index("fecha")[["dext_total"]].rename(
        columns={"dext_total": "deuda_externa"}
    )
    return df

def cargar_pbi_usd() -> pd.DataFrame:
    """PBI USD trimestral."""
    path = os.path.join(VARS_DIR, "pbi_trimestral_usd_mep.csv")
    df = pd.read_csv(path)
    # El archivo tiene periodo tipo "2004Q1". Convertir al ultimo dia del mes del trimestre.
    fechas = pd.to_datetime([f"{row.anio}-{(row.trimestre*3):02d}-01" for _, row in df.iterrows()])
    fechas = fechas + pd.offsets.MonthEnd(0)
    df["fecha"] = fechas
    df = df.set_index("fecha")[["pbi_usd_mm"]].rename(columns={"pbi_usd_mm": "pbi_usd"})
    return df


def cargar_vencimientos_2y() -> pd.DataFrame:
    """Vencimientos totales moneda extranjera a 2 años, trimestral (Mill. USD)."""
    path = os.path.join(VARS_DIR, "vencimientos_2y_nuevo.csv")
    df = pd.read_csv(path, parse_dates=["fecha"])
    df = df.set_index("fecha")[["venc_total_ext"]].rename(
        columns={"venc_total_ext": "venc_2y"}
    )
    # frecuencia inferida automáticamente por pandas
    return df


def cargar_vencimientos_1y() -> pd.DataFrame:
    """Vencimientos totales moneda extranjera a 1 año, trimestral (Mill. USD).

    El Excel tiene estructura:
    - Fila 5: fechas (cabecera de columnas) en formato 'MM/YYYY'
    - Fila 6: TOTAL (suma local + extranjera)
    - Fila 7: Moneda Local
    - Fila 8: Moneda Extranjera  <- esta es la que necesitamos
    Luego siguen los instrumentos individuales.
    """
    path = os.path.join(VARS_DIR, "vencimientos_1y_nuevo.xlsx")
    raw = pd.read_excel(path, sheet_name="Por Tipo y Moneda", header=None)

    # Fila 5: cabeceras de fecha (col 1 en adelante)
    date_strs = raw.iloc[5, 1:].tolist()
    fechas = pd.to_datetime(
        [f"01/{d}" for d in date_strs if pd.notna(d)],
        format="%d/%m/%Y",
        errors="coerce",
    )
    # Mover al fin del trimestre (las fechas son MM/YYYY, ej 06/2007 → 2007-06-30)
    fechas = fechas + pd.offsets.MonthEnd(0)

    # Fila 8: "Moneda Extranjera" del TOTAL
    valores = pd.to_numeric(raw.iloc[8, 1:].values, errors="coerce")

    n = min(len(fechas), len(valores))
    fechas = fechas[:n]
    valores = valores[:n]

    mask = pd.notna(fechas) & pd.notna(valores)
    df = pd.DataFrame(
        {"fecha": fechas[mask], "venc_1y": valores[mask]}
    ).set_index("fecha")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 1b. VARIABLES EXTERNAS (exógenas)
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_superavit_primario() -> pd.DataFrame:
    """Superavit primario mensual (Mill. ARS)."""
    path = os.path.join(VARS_DIR, "Resultado fiscal-unificado.xlsx")
    df = pd.read_excel(path, sheet_name="Unificado")
    df["fecha"] = pd.to_datetime(df["indice_tiempo"])
    df = df.set_index("fecha")[["superavit_primario"]]
    # frecuencia inferida automáticamente por pandas
    return df


def cargar_emae() -> pd.DataFrame:
    """EMAE original mensual (indice base 2004=100)."""
    import glob

    pattern = os.path.join(
        RAW_DIR, "indec", "emae_emae_ndice_base_2004_valores_men*.csv"
    )
    files = glob.glob(pattern)
    path = files[0] if files else os.path.join(RAW_DIR, "indec", "emae.csv")

    df = pd.read_csv(path, parse_dates=["indice_tiempo"])
    if "emae_original" in df.columns:
        col = "emae_original"
    elif "emae" in df.columns:
        col = "emae"
    else:
        col = df.columns[1]
    df = df.rename(columns={"indice_tiempo": "fecha", col: "emae"})
    df = df.set_index("fecha")[["emae"]]
    return df


def cargar_saldo_comercial() -> pd.DataFrame:
    """Saldo comercial mensual (Mill. USD)."""
    path = os.path.join(
        VARS_DIR,
        "ica_intercambio_comercial_argentino_valores_mensuales.csv",
    )
    df = pd.read_csv(path, parse_dates=["indice_tiempo"])
    df = df.rename(
        columns={"indice_tiempo": "fecha", "ica_saldo_comercial": "saldo_comercial"}
    )
    df = df.set_index("fecha")[["saldo_comercial"]]
    # frecuencia inferida automáticamente por pandas
    return df


def cargar_reservas_brutas() -> pd.DataFrame:
    """Reservas Brutas BCRA, diarias → mensual (último dato del mes, Mill. USD)."""
    path = os.path.join(VARS_DIR, "001_reservas_brutas.csv")
    df = pd.read_csv(path, parse_dates=["fecha"])
    df = df.set_index("fecha")[["valor"]].rename(columns={"valor": "reservas"})
    monthly = df.resample("MS").first().dropna()
    return monthly


def cargar_dummies() -> pd.DataFrame:
    """Carga las variables dummies (COVID, Cepo)."""
    # Covid (mensual)
    path_covid = os.path.join(VARS_DIR, "dummy_covid.csv")
    if os.path.exists(path_covid):
        df_covid = pd.read_csv(path_covid, parse_dates=["fecha"]).set_index("fecha")
    else:
        df_covid = pd.DataFrame(columns=["dummy_covid"])
        
    # Cepo (diario, se pasa a mensual usando max)
    path_cepo = os.path.join(VARS_DIR, "dummy_cepo.csv")
    if os.path.exists(path_cepo):
        df_cepo = pd.read_csv(path_cepo, parse_dates=["fecha"]).set_index("fecha")
        df_cepo = df_cepo.resample("MS").max()
    else:
        df_cepo = pd.DataFrame(columns=["dummy_cepo"])

    df = df_covid[["dummy_covid"]].join(df_cepo[["dummy_cepo"]], how="outer").fillna(0)
    return df


def cargar_cer_mensual() -> pd.DataFrame:
    """CER (BCRA) diario → mensual (promedio del mes). Sirve de deflactor/precio."""
    path = os.path.join(RAW_DIR, "bcra", "cer.csv")
    df = pd.read_csv(path, parse_dates=["fecha"]).set_index("fecha")
    m = df["cer"].resample("MS").mean().to_frame("cer")
    m["cer"] = m["cer"].ffill().bfill()
    return m


def cargar_mep_mensual() -> pd.DataFrame:
    """TC para pasar ARS→USD, mensual (promedio del mes desde el diario).

    Devuelve dos columnas:
      - mep    : TC MEP. Recién existe ~2010; se rellena hacia atrás sólo para no
                 romper la estimación SARIMAX (es exógena en varios modelos).
      - tc_usd : TC de conversión a USD = MEP donde existe; antes (2004-2009) el TC
                 oficial mayorista A3500 (BCRA). Permite convertir el período previo
                 al MEP sin distorsión por el flat-bfill.
    """
    path = os.path.join(VARS_DIR, "brecha_cambiaria.csv")
    df = pd.read_csv(path, parse_dates=["fecha"]).set_index("fecha")
    mep_real = df["mep"].resample("MS").mean()          # NaN antes de ~2010
    a3500 = df["bcra_a3500"].resample("MS").mean()       # TC oficial, desde 2003
    tc_usd = mep_real.where(mep_real.notna(), a3500)      # MEP si hay; si no, oficial
    m = pd.DataFrame({"mep": mep_real, "tc_usd": tc_usd})
    m["mep"] = m["mep"].ffill().bfill()
    m["tc_usd"] = m["tc_usd"].ffill().bfill()
    return m


def cargar_deuda_bruta_total_mensual() -> pd.DataFrame:
    """Deuda Bruta Total (saldo_deuda_unificado.xlsx, hoja A.1, fila 'DEUDA BRUTA TOTAL').

    Estructura: 2007-2018 = trimestral (SIGADE), 2019-2026 = mensual (Boletín MECON).
    Devuelve serie MENSUAL: los meses sin dato trimestral quedan NaN (los completa el
    filtro de Kalman); desde 2019 cada mes tiene su valor observado.
    """
    path = os.path.join(VARS_DIR, "saldo_deuda_unificado.xlsx")
    raw = pd.read_excel(path, sheet_name="A.1", header=None)
    dates = raw.iloc[8, 1:].tolist()   # fila 8 = cabeceras MM/YYYY
    vals = raw.iloc[9, 1:].tolist()    # fila 9 = DEUDA BRUTA TOTAL
    recs = {}
    for d, v in zip(dates, vals):
        if pd.isna(d) or pd.isna(v):
            continue
        mm, yy = str(d).strip().split("/")
        recs[pd.Timestamp(int(yy), int(mm), 1)] = float(v)
    s = pd.Series(recs).sort_index()
    idx = pd.date_range(s.index[0], s.index[-1], freq="MS")
    out = pd.DataFrame(index=idx, columns=["deuda_bruta_total"], dtype=float)
    out.loc[s.index, "deuda_bruta_total"] = s.values
    return out


def cargar_serie_trimestral_csv(filename: str, col: str, salida: str) -> pd.DataFrame:
    """Helper genérico: lee un CSV trimestral con columna 'fecha' y devuelve [salida]."""
    path = os.path.join(VARS_DIR, filename)
    df = pd.read_csv(path, parse_dates=["fecha"])
    df = df.set_index("fecha")[[col]].rename(columns={col: salida})
    return df


def cargar_serie_trimestral_bp(col: str, salida: str) -> pd.DataFrame:
    """Helper: columna del Balance de Pagos MBP6 trimestral."""
    path = os.path.join(
        VARS_DIR,
        "balance_pagos_estimaci_n_del_balance_de_pagos_mbp6_valores_trimestrales.csv",
    )
    df = pd.read_csv(path, parse_dates=["indice_tiempo"])
    df = df.rename(columns={"indice_tiempo": "fecha"}).set_index("fecha")
    return df[[col]].rename(columns={col: salida})


# ═══════════════════════════════════════════════════════════════════════════════
# 1c. CONFIGURACIÓN DE SERIES ADICIONALES A MENSUALIZAR (punto 4)
# ═══════════════════════════════════════════════════════════════════════════════
# Balance de Pagos (flujos USD) — exógena: saldo comercial mensual.
BP_SERIES = {
    "bp_bys":    ("cuenta_corriente_total_bienes_servicios",      "BP - Bienes y Servicios"),
    "bp_bienes": ("cuenta_corriente_bienes_servicios_total_bienes","BP - Bienes (neto)"),
    "bp_serv":   ("cuenta_corriente_bienes_servicios_total_servicios","BP - Servicios (neto)"),
    "bp_ip":     ("cuenta_corriente_total_ingresos_primarios",    "BP - Ingresos Primarios"),
    "bp_is":     ("cuenta_corriente_ingresos_secundarios",        "BP - Ingresos Secundarios"),
    "bp_cap":    ("total_cuenta_capital",                          "BP - Cuenta Capital"),
    "bp_id":     ("cuenta_financiera_total_inversion_directa",    "BP - Inversion Directa"),
    "bp_ic":     ("cuenta_financiera_total_inversion_cartera",    "BP - Inversion Cartera"),
    "bp_oi":     ("cuenta_financiera_total_otra_inversion",       "BP - Otra Inversion"),
    "bp_res":    ("activos_reserva",                              "BP - Activos de Reserva"),
    "bp_err":    ("errores_omisiones_netos",                      "BP - Errores y Omisiones"),
}
# Deuda externa por sector (stocks USD) — exógena: reservas/PBI + MEP.
DEXT_SECTORES = {
    "dext_gobierno":   ("dext_gobierno",      "Deuda Externa - Gobierno General"),
    "dext_bcra":       ("dext_bcra",          "Deuda Externa - Banco Central"),
    "dext_bancos":     ("dext_bancos",        "Deuda Externa - Bancos"),
    "dext_otros_sec":  ("dext_otros_sectores","Deuda Externa - Otros Sectores"),
}
# Deuda externa por plazo (stocks USD).
DEXT_PLAZO = {
    "dextp_corto":  ("dext_corto_plazo",       "Deuda Externa - Corto Plazo"),
    "dextp_largo":  ("dext_largo_plazo",       "Deuda Externa - Largo Plazo"),
    "dextp_invdir": ("dext_inversion_directa", "Deuda Externa - Inversion Directa"),
}
# Cuentas Nacionales reales (flujos ARS constante 2004) — exógena EMAE; se deriva
# el nominal mensual con CER (mismo proceso que el PBI). col es igual en
# oferta_demanda_constante.csv y oferta_demanda_corriente.csv.
CN_REALES = {
    "od_cpriv": ("consumo_priv", "Consumo Privado"),
    "od_cpub":  ("consumo_pub",  "Consumo Publico"),
    "od_fbkf":  ("fbkf",         "FBKF"),
    "od_expo":  ("expo",         "Exportaciones (CN)"),
    "od_impo":  ("impo",         "Importaciones (CN)"),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. MENSUALIZACIÓN DE SERIES TRIMESTRALES
# ═══════════════════════════════════════════════════════════════════════════════

def trimestral_a_mensual_con_nan(df_trimestral: pd.DataFrame, es_flujo: bool = False) -> pd.DataFrame:
    """
    Convierte una serie trimestral a mensual colocando el dato en el último mes del trimestre
    y rellenando con NaN los otros dos meses. Esto permite que el Filtro de Kalman
    de statsmodels opere de manera óptima manejando los 'missing values'.
    Para variables de flujo, se divide el valor trimestral por 3 para que represente
    el nivel mensual promedio. Para variables de stock, se mantiene el valor original.
    """
    col = df_trimestral.columns[0]
    q_dates = df_trimestral.index
    if len(q_dates) == 0:
        return df_trimestral
        
    first_date = q_dates[0]
    last_date = q_dates[-1]

    # Normalizar al inicio del trimestre
    first_month = first_date.month
    if first_month in [1, 2, 3]: q_start_month = 1
    elif first_month in [4, 5, 6]: q_start_month = 4
    elif first_month in [7, 8, 9]: q_start_month = 7
    else: q_start_month = 10

    # Normalizar al final del trimestre
    last_month = last_date.month
    if last_month in [1, 2, 3]: q_end_month = 3
    elif last_month in [4, 5, 6]: q_end_month = 6
    elif last_month in [7, 8, 9]: q_end_month = 9
    else: q_end_month = 12

    first_m_date = pd.Timestamp(year=first_date.year, month=q_start_month, day=1)
    last_m_date = pd.Timestamp(year=last_date.year, month=q_end_month, day=1)
    
    monthly_idx = pd.date_range(start=first_m_date, end=last_m_date, freq='MS')
    df_m = pd.DataFrame(index=monthly_idx, columns=[col])
    
    for q_date in q_dates:
        m = q_date.month
        y = q_date.year
        if m in [1, 2, 3]: target_month = 3
        elif m in [4, 5, 6]: target_month = 6
        elif m in [7, 8, 9]: target_month = 9
        else: target_month = 12
        
        target_date = pd.Timestamp(year=y, month=target_month, day=1)
        val = df_trimestral.loc[q_date, col]
        
        if es_flujo:
            df_m.loc[target_date, col] = val / 3.0
        else:
            df_m.loc[target_date, col] = val
            
    df_m[col] = df_m[col].astype(float)
    return df_m



# ═══════════════════════════════════════════════════════════════════════════════
# 3. PREPARAR DATASET UNIFICADO
# ═══════════════════════════════════════════════════════════════════════════════

def preparar_datos():
    """
    Carga todas las series, mensualiza las trimestrales y alinea fechas.
    Retorna (datasets, aux):
      - datasets: dict {key -> DataFrame} listo para cada modelo SARIMAX.
      - aux: dict con insumos para derivar nominal/USD (cer_m, mep_m, series Q).
    """
    print("Cargando datos...")

    # -- Target variables (trimestrales) --
    se_q = cargar_se()
    pbi_nominal_q = cargar_pbi_nominal()
    pbi_real_q = cargar_pbi_constante()
    bp = cargar_balanza_pagos()
    deuda_q = cargar_deuda_externa()
    venc_2y_q = cargar_vencimientos_2y()
    venc_1y_q = cargar_vencimientos_1y()
    deuda_bruta_m = cargar_deuda_bruta_total_mensual()  # ya viene mensual (Q hasta 2018, M desde 2019)

    # Cuentas Nacionales reales (constante 2004) y nominales (corriente)
    od_const = pd.read_csv(os.path.join(VARS_DIR, "oferta_demanda_constante.csv"), parse_dates=["fecha"]).set_index("fecha")
    od_corr = pd.read_csv(os.path.join(VARS_DIR, "oferta_demanda_corriente.csv"), parse_dates=["fecha"]).set_index("fecha")

    # -- Variables externas (mensuales) --
    sp = cargar_superavit_primario()
    emae = cargar_emae()
    sc = cargar_saldo_comercial()
    res = cargar_reservas_brutas()
    cer_m = cargar_cer_mensual()
    mep_m = cargar_mep_mensual()
    dummies = cargar_dummies()

    # -- Reservas / PBI ratio (mensual) --
    # PBI trimestral viene ANUALIZADO (cada trim = tasa anual) → es_flujo=False (nivel, sin /3).
    pbi_nominal_m_ff = trimestral_a_mensual_con_nan(pbi_nominal_q, es_flujo=False).ffill().bfill()
    common = res.index.intersection(pbi_nominal_m_ff.index)
    res_pbi = (res.loc[common].values.flatten() / pbi_nominal_m_ff.loc[common].values.flatten())
    res_pbi_df = pd.DataFrame({"res_pbi": res_pbi}, index=common)

    # -- Exógenas mensuales disponibles (cada una single-col) --
    exog_series = {
        "superavit_primario": sp,
        "emae": emae,
        "saldo_comercial": sc,
        "res_pbi": res_pbi_df,
        "mep": mep_m,
        "cer": cer_m,
    }

    print("Mensualizando series trimestrales con NaNs...")
    datasets = {}

    def build(target_m, target_col, exog_keys):
        """Arma el dataset: target mensual (con NaN) + exógenas + dummies, dropeando
        sólo las filas donde falte alguna exógena (preserva los NaN del target)."""
        idx = target_m.index
        df = pd.DataFrame(index=idx)
        df[target_col] = target_m[target_col].astype(float)
        for k in exog_keys:
            df[k] = exog_series[k].reindex(idx).iloc[:, 0]
        df["dummy_covid"] = dummies["dummy_covid"].reindex(idx).fillna(0) if not dummies.empty else 0
        df["dummy_cepo"] = dummies["dummy_cepo"].reindex(idx).fillna(0) if not dummies.empty else 0
        df = df.dropna(subset=list(exog_keys))
        return df

    # ── Series base ───────────────────────────────────────────────────────────
    datasets["se"] = build(trimestral_a_mensual_con_nan(se_q, es_flujo=True), "se", ["superavit_primario"])
    # PBI (constante) anualizado → es_flujo=False: el mensual queda al MISMO nivel anual que el
    # trimestral/anual (no se divide por 3). El nominal y USD derivados heredan este nivel.
    datasets["pbi_constante"] = build(trimestral_a_mensual_con_nan(pbi_real_q, es_flujo=False), "pbi_real", ["emae"])
    datasets["cuenta_corriente"] = build(trimestral_a_mensual_con_nan(bp[["cuenta_corriente"]], es_flujo=True), "cuenta_corriente", ["saldo_comercial"])
    datasets["cuenta_financiera"] = build(trimestral_a_mensual_con_nan(bp[["cuenta_financiera"]], es_flujo=True), "cuenta_financiera", ["saldo_comercial"])
    datasets["deuda_externa"] = build(trimestral_a_mensual_con_nan(deuda_q, es_flujo=False), "deuda_externa", ["res_pbi", "mep"])
    datasets["venc_1y"] = build(trimestral_a_mensual_con_nan(venc_1y_q, es_flujo=False), "venc_1y", [])
    datasets["venc_2y"] = build(trimestral_a_mensual_con_nan(venc_2y_q, es_flujo=False), "venc_2y", [])

    # ── Deuda Bruta Total (punto 2): exógena reservas/PBI + MEP ─────────────────
    datasets["deuda_bruta_total"] = build(deuda_bruta_m, "deuda_bruta_total", ["res_pbi", "mep"])

    # ── Balance de Pagos (flujos USD) ~ saldo comercial (punto 4) ──────────────
    for key, (col, _nombre) in BP_SERIES.items():
        tm = trimestral_a_mensual_con_nan(cargar_serie_trimestral_bp(col, key), es_flujo=True)
        datasets[key] = build(tm, key, ["saldo_comercial"])

    # ── Deuda externa por sector/plazo (stocks USD) ~ reservas/PBI + MEP ───────
    for key, (col, _nombre) in DEXT_SECTORES.items():
        tm = trimestral_a_mensual_con_nan(cargar_serie_trimestral_csv("deuda_externa_sectores.csv", col, key), es_flujo=False)
        datasets[key] = build(tm, key, ["res_pbi", "mep"])
    for key, (col, _nombre) in DEXT_PLAZO.items():
        tm = trimestral_a_mensual_con_nan(cargar_serie_trimestral_csv("deuda_externa_plazo.csv", col, key), es_flujo=False)
        datasets[key] = build(tm, key, ["res_pbi", "mep"])

    # ── Cuentas Nacionales reales (ARS const., ANUALIZADAS) ~ EMAE ─────────────
    # Igual que el PBI: es_flujo=False (nivel anual). El nominal se deriva con CER.
    for key, (col, _nombre) in CN_REALES.items():
        tm = trimestral_a_mensual_con_nan(od_const[[col]].rename(columns={col: key}), es_flujo=False)
        datasets[key] = build(tm, key, ["emae"])

    for k, v in datasets.items():
        if len(v):
            print(f"  {k}: {len(v)} obs, {v.index[0].date()} --> {v.index[-1].date()}")
        else:
            print(f"  {k}: 0 obs (revisar)")

    aux = {
        "cer_m": cer_m,
        "mep_m": mep_m,
        "pbi_nominal_q": pbi_nominal_q,
        "pbi_real_q": pbi_real_q,
        "od_const": od_const,
        "od_corr": od_corr,
    }
    return datasets, aux


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FILTRO DE KALMAN (SARIMAX con variables exógenas)
# ═══════════════════════════════════════════════════════════════════════════════

def estimar_kalman(
    df: pd.DataFrame,
    target: str,
    exog_cols: list,
    order: tuple,
    seasonal_order: tuple,
    nombre: str,
) -> dict:
    """
    Estima un modelo SARIMAX (filtro de Kalman) y extrae:
    - Estados filtrados y suavizados
    - Predicciones in-sample
    - Predicciones out-of-sample (12 periodos)
    - Diagnosticos (AIC, BIC, Ljung-Box, etc.)
    """
    y = df[target].astype(float)
    exog = df[exog_cols].astype(float) if exog_cols else None

    y_train = y
    exog_train = exog
    
    y_test = None
    exog_test = None

    modelo = SARIMAX(
        y_train,
        exog=exog_train,
        order=order,
        seasonal_order=seasonal_order,
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    )

    try:
        resultado = modelo.fit(disp=False, maxiter=500, method="powell")
        import numpy as np
        if getattr(resultado, "aic", np.nan) != getattr(resultado, "aic", np.nan) or np.isnan(float(getattr(resultado, "aic", np.nan))):
            raise ValueError("AIC is NaN")
    except:
        k = modelo.k_params
        import numpy as np
        start_params = np.zeros(k)
        start_params[-1] = 1.0 # Varianza base
        resultado = modelo.fit(start_params=start_params, disp=False, maxiter=500, method="powell")

    # Predicción in-sample (suavizada, para interpolar NaNs correctamente)
    y_pred_in = pd.Series(
        resultado.smoother_results.smoothed_forecasts[0],
        index=y_train.index
    )

    # ── Anclaje a los valores observados ──────────────────────────────────────
    # 1) La serie filtrada debe pasar EXACTO por las observaciones (anclas) y el
    #    filtro de Kalman sólo interpola los NaN intermedios. Esto garantiza que
    #    la serie mensual coincida con la trimestral/mensual original en cada dato
    #    real (y, p.ej. para Deuda Bruta Total, que use el valor mensual desde 2019).
    obs_mask = y_train.notna()
    y_pred_in[obs_mask] = y_train[obs_mask]

    # 2) NaN iniciales (antes de la 1ra observación): el backcast del modelo
    #    integrado puede irse a 0 o a valores absurdos y producir el "salto" inicial
    #    que se ve en las series de stock. Reemplazamos por la media marginal
    #    (= primer valor observado) para que la serie arranque plana sin salto.
    first_valid = y_train.first_valid_index()
    if first_valid is not None:
        lead = y_train.index < first_valid
        if lead.any():
            y_pred_in[lead] = y_train.loc[first_valid]

    # Estados suavizados
    smoothed = resultado.smoothed_state
    filtered = resultado.filtered_state

    y_pred_out = None
    ci = None

    # Métricas
    residuos = resultado.resid.dropna()
    mask = ~np.isnan(y_train.values)
    if mask.sum() > 0:
        rmse_in = np.sqrt(np.mean((y_train.values[mask] - y_pred_in.values[mask]) ** 2))
    else:
        rmse_in = np.nan

    # Ljung-Box test
    try:
        lb = sm.stats.acorr_ljungbox(residuos, lags=[min(12, len(residuos) // 5)], return_df=True)
        lb_pvalue = lb["lb_pvalue"].values[0]
    except Exception:
        lb_pvalue = np.nan

    return {
        "nombre": nombre,
        "modelo": resultado,
        "y_train": y_train,
        "y_test": y_test,
        "y_pred_in": y_pred_in,
        "y_pred_out": y_pred_out,
        "ci_out": ci,
        "smoothed_state": smoothed,
        "filtered_state": filtered,
        "aic": resultado.aic,
        "bic": resultado.bic,
        "rmse_in": rmse_in,
        "ljung_box_pval": lb_pvalue,
        "residuos": residuos,
        "params": resultado.params,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. GRÁFICOS
# ═══════════════════════════════════════════════════════════════════════════════

def graficar_resultado(resultado: dict) -> go.Figure:
    """Genera figura Plotly con: serie observada, ajuste in-sample, forecast out-of-sample."""
    r = resultado
    nombre = r["nombre"]
    y_train = r["y_train"]
    y_test = r["y_test"]
    y_pred_in = r["y_pred_in"]
    y_pred_out = r["y_pred_out"]
    ci = r["ci_out"]

    fig = go.Figure()

    # Serie observada (train)
    fig.add_trace(
        go.Scatter(
            x=y_train.index,
            y=y_train.values,
            mode="markers",
            name="Observado (train)",
            marker=dict(color="#1f77b4", size=8),
        )
    )

    # Ajuste in-sample
    fig.add_trace(
        go.Scatter(
            x=y_train.index,
            y=y_pred_in.values,
            mode="lines",
            name="Ajuste Kalman (in-sample)",
            line=dict(color="#ff7f0e", width=1.5, dash="dash"),
        )
    )

    # Observado (test) si existe
    if y_test is not None:
        fig.add_trace(
            go.Scatter(
                x=y_test.index,
                y=y_test.values,
                mode="lines+markers",
                name="Observado (test)",
                line=dict(color="#2ca02c", width=2),
                marker=dict(size=6),
            )
        )

    # Forecast out-of-sample
    if y_pred_out is not None:
        forecast_idx = y_pred_out.index
        fig.add_trace(
            go.Scatter(
                x=forecast_idx,
                y=y_pred_out.values,
                mode="lines+markers",
                name="Forecast Kalman",
                line=dict(color="#d62728", width=2),
                marker=dict(size=6),
            )
        )

    # Intervalo de confianza
    if ci is not None:
        fig.add_trace(
            go.Scatter(
                x=list(forecast_idx) + list(forecast_idx[::-1]),
                y=list(ci.iloc[:, 0]) + list(ci.iloc[:, 1][::-1]),
                fill="toself",
                fillcolor="rgba(214,39,40,0.15)",
                line=dict(color="rgba(255,255,255,0)"),
                name="IC 95%",
            )
        )

    fig.update_layout(
        title=f"Filtro de Kalman — {nombre}",
        xaxis_title="Fecha",
        yaxis_title="Valor",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def generar_reporte(resultados: dict) -> str:
    """Genera tabla de métricas en formato markdown para el reporte."""
    lineas = [
        "# Reporte de Filtros de Kalman",
        "",
        "| Variable | ARIMA | Exógena | AIC | BIC | RMSE in-sample | Ljung-Box p-val |",
        "|----------|-------|---------|-----|-----|----------------|-----------------|",
    ]

    specs = {
        "SE - Nivel (Mill. ARS)": ((4, 0, 4), "Superavit primario"),
        "PBI Nominal": ((4, 1, 4), "EMAE"),
        "PBI Constante": ((4, 1, 4), "EMAE"),
        "PBI USD": ((4, 1, 4), "EMAE"),
        "Total Cuenta Corriente": ((4, 1, 1), "Saldo Comercial"),
        "Total Cuenta Financiera": ((1, 1, 4), "Saldo Comercial"),
        "Deuda Externa Bruta Total": ((4, 2, 0), "Reservas/PBI"),
        "Vencimientos USD 1 anio": ((0, 1, 4), "--"),
        "Vencimientos USD 2 anios": ((0, 1, 4), "--"),
    }

    for nombre, (order, exog_name) in specs.items():
        if nombre not in resultados:
            continue
        r = resultados[nombre]
        lineas.append(
            f"| {nombre} | {order} | {exog_name} | "
            f"{r['aic']:.1f} | {r['bic']:.1f} | "
            f"{r['rmse_in']:.2f} | {r['ljung_box_pval']:.4f} |"
        )

    lineas.append("")
    lineas.append("---")
    lineas.append("*Estimado con `SARIMAX` de statsmodels, que utiliza el filtro de Kalman para la estimación de máxima verosimilitud.*")

    return "\n".join(lineas)


# ═══════════════════════════════════════════════════════════════════════════════
# 5b. DERIVACIÓN NOMINAL / USD (desde la serie real mensualizada)
# ═══════════════════════════════════════════════════════════════════════════════

def _qkey(ts):
    return (ts.year, (ts.month - 1) // 3 + 1)


def derivar_nominal_usd(real_m, real_q, nominal_q, cer_m, mep_m=None, usd_desde="2004-01-01"):
    """
    A partir de la serie REAL mensual (Kalman) deriva la NOMINAL mensual usando el
    deflactor trimestral implícito (nominal_q / real_q) y la forma intra-trimestral
    del CER; opcionalmente la versión en USD dividiendo por el TC MEP mensual.

    real_m   : pd.Series mensual (precios constantes).
    real_q   : serie/DataFrame trimestral a precios constantes (mismo concepto).
    nominal_q: serie/DataFrame trimestral a precios corrientes (mismo concepto).
    """
    cer = cer_m["cer"]
    rq = real_q.iloc[:, 0] if isinstance(real_q, pd.DataFrame) else real_q
    nq = nominal_q.iloc[:, 0] if isinstance(nominal_q, pd.DataFrame) else nominal_q

    rq_by_q = {_qkey(t): rq[t] for t in rq.index if pd.notna(rq[t])}
    defl = {}
    for t in nq.index:
        qk = _qkey(t)
        rv = rq_by_q.get(qk)
        if rv and rv != 0 and pd.notna(nq[t]):
            defl[qk] = nq[t] / rv

    nominal_m = pd.Series(index=real_m.index, dtype=float)
    for t in real_m.index:
        d = defl.get(_qkey(t))
        rv = real_m.get(t)
        if d is None or pd.isna(rv):
            continue
        qs = ((t.month - 1) // 3) * 3 + 1
        qmonths = [pd.Timestamp(t.year, qs + k, 1) for k in range(3)]
        cavg = cer.reindex(qmonths).mean()
        ct = cer.get(t, np.nan)
        if pd.isna(cavg) or cavg == 0 or pd.isna(ct):
            nominal_m[t] = rv * d
        else:
            nominal_m[t] = rv * d * ct / cavg

    usd_m = None
    if mep_m is not None:
        # tc_usd = MEP donde existe; TC oficial A3500 antes de ~2010 (ver cargar_mep_mensual)
        tc = mep_m["tc_usd"] if "tc_usd" in mep_m.columns else mep_m["mep"]
        cut = pd.Timestamp(usd_desde)
        usd_m = pd.Series(index=real_m.index, dtype=float)
        for t in nominal_m.index:
            if t < cut or pd.isna(nominal_m[t]):
                continue
            mv = tc.get(t, np.nan)
            if pd.notna(mv) and mv != 0:
                usd_m[t] = nominal_m[t] / mv
    return nominal_m, usd_m


def _write_kalman_csv(out_base, idx, y_obs, y_pred):
    df = pd.DataFrame({"fecha": idx, "y_obs": y_obs, "y_pred": y_pred}).set_index("fecha")
    df.to_csv(os.path.join(VARS_DIR, f"{out_base}_kalman.csv"))
    print(f"  [derivado] {out_base}_kalman.csv  ({len(df)} filas)")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EJECUCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("FILTRO DE KALMAN - Variables Macroeconomicas Argentinas")
    print("=" * 70)

    # -- Preparar datos --
    datasets, aux = preparar_datos()

    # -- Especificaciones base --
    # NB: PBI Nominal y PBI USD ya NO se estiman por SARIMAX: se DERIVAN de
    # PBI Constante (× CER → nominal, ÷ MEP → USD). Ver bloque de derivación.
    specs = {
        "SE - Nivel (Mill. ARS)": {"key": "se", "target": "se", "exog": ["superavit_primario", "dummy_covid", "dummy_cepo"], "order": (4, 0, 4), "seasonal_order": (1, 0, 1, 12)},
        "PBI Constante": {"key": "pbi_constante", "target": "pbi_real", "exog": ["emae", "dummy_covid", "dummy_cepo"], "order": (4, 1, 4), "seasonal_order": (1, 0, 1, 12)},
        "Total Cuenta Corriente": {"key": "cuenta_corriente", "target": "cuenta_corriente", "exog": ["saldo_comercial", "dummy_covid", "dummy_cepo"], "order": (4, 1, 1), "seasonal_order": (1, 0, 1, 12)},
        "Total Cuenta Financiera": {"key": "cuenta_financiera", "target": "cuenta_financiera", "exog": ["saldo_comercial", "dummy_covid", "dummy_cepo"], "order": (1, 1, 4), "seasonal_order": (1, 0, 1, 12)},
        "Deuda Externa Bruta Total": {"key": "deuda_externa", "target": "deuda_externa", "exog": ["res_pbi", "mep", "dummy_covid", "dummy_cepo"], "order": (4, 1, 0), "seasonal_order": (1, 0, 1, 12)},
        "Deuda Bruta Total": {"key": "deuda_bruta_total", "target": "deuda_bruta_total", "exog": ["res_pbi", "mep", "dummy_covid", "dummy_cepo"], "order": (4, 1, 0), "seasonal_order": (1, 0, 1, 12), "out": "deuda_bruta_total"},
        "Vencimientos USD 1 anio": {"key": "venc_1y", "target": "venc_1y", "exog": ["dummy_covid", "dummy_cepo"], "order": (0, 1, 4), "seasonal_order": (1, 0, 1, 12)},
        "Vencimientos USD 2 anios": {"key": "venc_2y", "target": "venc_2y", "exog": ["dummy_covid", "dummy_cepo"], "order": (0, 1, 4), "seasonal_order": (1, 0, 1, 12)},
    }

    # -- Agregados adicionales (punto 4) generados programáticamente --
    for key, (_col, nombre) in BP_SERIES.items():
        specs[nombre] = {"key": key, "target": key, "exog": ["saldo_comercial", "dummy_covid", "dummy_cepo"], "order": (2, 1, 2), "seasonal_order": (1, 0, 1, 12), "out": key, "graf": False}
    for key, (_col, nombre) in {**DEXT_SECTORES, **DEXT_PLAZO}.items():
        specs[nombre] = {"key": key, "target": key, "exog": ["res_pbi", "mep", "dummy_covid", "dummy_cepo"], "order": (4, 1, 0), "seasonal_order": (1, 0, 1, 12), "out": key, "graf": False}
    for key, (_col, nombre) in CN_REALES.items():
        specs[nombre] = {"key": key, "target": key, "exog": ["emae", "dummy_covid", "dummy_cepo"], "order": (2, 1, 2), "seasonal_order": (1, 0, 1, 12), "out": key, "graf": False}

    resultados = {}

    for nombre, spec in specs.items():
        df = datasets.get(spec["key"])
        if df is None or len(df) < 24:
            print(f"  [SKIP] {nombre}: dataset insuficiente ({0 if df is None else len(df)} obs)")
            continue
        print(f"\n{'-'*60}")
        print(f"Estimando: {nombre}")
        print(f"  ARIMA{spec['order']} + exogena(s): {spec['exog'] if spec['exog'] else 'ninguna'}")

        try:
            r = estimar_kalman(
                df,
                target=spec["target"],
                exog_cols=spec["exog"],
                order=spec["order"],
                seasonal_order=spec["seasonal_order"],
                nombre=nombre,
            )
        except Exception as e:
            print(f"  [ERROR] {nombre}: {e}")
            continue

        print(f"  AIC: {r['aic']:.1f}  |  BIC: {r['bic']:.1f}  |  RMSE: {r['rmse_in']:.2f}")
        print(f"  Ljung-Box p-value: {r['ljung_box_pval']:.4f}")

        safe_name = nombre.lower().replace(" ", "_").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
        out_base = spec.get("out") or safe_name

        # Guardar grafico (sólo para las series base)
        if spec.get("graf", True):
            try:
                fig = graficar_resultado(r)
                fig.write_html(os.path.join(OUT_DIR, f"{safe_name}.html"))
            except Exception as e:
                print(f"  [warn] grafico {nombre}: {e}")

        # Guardar CSV con observados y prediccion (in-sample)
        res_df = pd.DataFrame({
            "fecha": r["y_train"].index,
            "y_obs": r["y_train"].values,
            "y_pred": r["y_pred_in"].values
        }).set_index("fecha")
        res_df.to_csv(os.path.join(VARS_DIR, f"{out_base}_kalman.csv"))

        resultados[nombre] = r

    # ── DERIVACIÓN: PBI nominal y PBI USD desde PBI Constante (punto 3) ─────────
    print(f"\n{'-'*60}\nDerivando PBI nominal y PBI USD desde PBI Constante...")
    if "PBI Constante" in resultados:
        real_m = resultados["PBI Constante"]["y_pred_in"]
        nominal_m, usd_m = derivar_nominal_usd(real_m, aux["pbi_real_q"], aux["pbi_nominal_q"], aux["cer_m"], aux["mep_m"])
        obs_nom = trimestral_a_mensual_con_nan(aux["pbi_nominal_q"], es_flujo=False).reindex(real_m.index)
        _write_kalman_csv("pbi_nominal", real_m.index, obs_nom.iloc[:, 0].values, nominal_m.values)
        obs_usd = trimestral_a_mensual_con_nan(cargar_pbi_usd(), es_flujo=False).reindex(real_m.index)
        _write_kalman_csv("pbi_usd", real_m.index, obs_usd.iloc[:, 0].values, usd_m.values)

    # ── DERIVACIÓN: nominal de Cuentas Nacionales (mismo proceso que PBI) ───────
    print("Derivando nominales de Cuentas Nacionales...")
    for key, (col, nombre) in CN_REALES.items():
        if nombre not in resultados:
            continue
        real_m = resultados[nombre]["y_pred_in"]
        nominal_m, _ = derivar_nominal_usd(real_m, aux["od_const"][[col]], aux["od_corr"][[col]], aux["cer_m"])
        obs_nom = trimestral_a_mensual_con_nan(aux["od_corr"][[col]].rename(columns={col: key}), es_flujo=False).reindex(real_m.index)
        _write_kalman_csv(f"{key}_nominal", real_m.index, obs_nom.iloc[:, 0].values, nominal_m.values)

    # -- Reporte --
    reporte = generar_reporte(resultados)
    reporte_path = os.path.join(OUT_DIR, "reporte_kalman.md")
    with open(reporte_path, "w", encoding="utf-8") as f:
        f.write(reporte)
    print(f"\nReporte: {reporte_path}")

    # -- Tabla resumen de parametros --
    print(f"\n{'='*70}")
    print("RESUMEN DE PARAMETROS ESTIMADOS")
    print(f"{'='*70}")
    for nombre, r in resultados.items():
        print(f"\n{nombre}:")
        for param, value in r["params"].items():
            print(f"  {param:30s} = {value:12.6f}")

    print(f"\n{'='*70}")
    print("Todos los graficos y reportes guardados en:")
    print(f"  {OUT_DIR}")
    print(f"{'='*70}")

    return resultados


if __name__ == "__main__":
    resultados = main()
