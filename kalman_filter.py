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

def preparar_datos() -> dict:
    """
    Carga todas las series, mensualiza las trimestrales y alinea fechas.
    Retorna un dict con DataFrames listos para cada modelo.
    """
    print("Cargando datos...")

    # -- Target variables (trimestrales) --
    se_q = cargar_se()
    pbi_nominal_q = cargar_pbi_nominal()
    pbi_real_q = cargar_pbi_constante()
    pbi_usd_q = cargar_pbi_usd()
    bp = cargar_balanza_pagos()
    deuda_q = cargar_deuda_externa()
    venc_2y_q = cargar_vencimientos_2y()
    venc_1y_q = cargar_vencimientos_1y()

    # -- Variables externas (mensuales) --
    sp = cargar_superavit_primario()
    emae = cargar_emae()
    sc = cargar_saldo_comercial()
    res = cargar_reservas_brutas()
    dummies = cargar_dummies()

    # -- Mensualizar targets --
    print("Mensualizando series trimestrales con NaNs...")
    se_m = trimestral_a_mensual_con_nan(se_q, es_flujo=True)
    pbi_nominal_m = trimestral_a_mensual_con_nan(pbi_nominal_q, es_flujo=True)
    pbi_real_m = trimestral_a_mensual_con_nan(pbi_real_q, es_flujo=True)
    pbi_usd_m = trimestral_a_mensual_con_nan(pbi_usd_q, es_flujo=True)
    cc_m = trimestral_a_mensual_con_nan(bp[["cuenta_corriente"]], es_flujo=True)
    cf_m = trimestral_a_mensual_con_nan(bp[["cuenta_financiera"]], es_flujo=True)
    deuda_m = trimestral_a_mensual_con_nan(deuda_q, es_flujo=False)
    venc_2y_m = trimestral_a_mensual_con_nan(venc_2y_q, es_flujo=False)
    venc_1y_m = trimestral_a_mensual_con_nan(venc_1y_q, es_flujo=False)

    # -- Reservas / PBI ratio (mensual) --
    # PBI tiene NaNs, interpolamos (forward fill) solo para el denominador de la variable exógena
    pbi_total_ffill = pbi_nominal_m.ffill().bfill()
    common = res.index.intersection(pbi_total_ffill.index)
    res_pbi = (res.loc[common].values.flatten() / pbi_total_ffill.loc[common].values.flatten())
    res_pbi_df = pd.DataFrame({"res_pbi": res_pbi}, index=common)

    # -- Construir datasets por modelo --
    # IMPORTANTE: Usamos dropna(subset=exog) para mantener los NaNs en la variable target
    datasets = {}

    def merge_dummies(df_main):
        if not dummies.empty:
            common_idx = df_main.index.intersection(dummies.index)
            df_merged = df_main.loc[common_idx].copy()
            df_merged["dummy_covid"] = dummies.loc[common_idx, "dummy_covid"]
            df_merged["dummy_cepo"] = dummies.loc[common_idx, "dummy_cepo"]
            return df_merged
        else:
            df_main["dummy_covid"] = 0
            df_main["dummy_cepo"] = 0
            return df_main

    # 1. SE ~ Superavit primario
    common_idx = se_m.index.intersection(sp.index)
    df_temp = pd.DataFrame({"se": se_m.loc[common_idx, "se"], "superavit_primario": sp.loc[common_idx, "superavit_primario"]})
    datasets["se"] = merge_dummies(df_temp).dropna(subset=["superavit_primario", "dummy_covid", "dummy_cepo"])

    # 2. PBI nominal ~ EMAE
    common_idx = pbi_nominal_m.index.intersection(emae.index)
    df_temp = pd.DataFrame({"pbi_nominal": pbi_nominal_m.loc[common_idx, "pbi_nominal"], "emae": emae.loc[common_idx, "emae"]})
    datasets["pbi_nominal"] = merge_dummies(df_temp).dropna(subset=["emae", "dummy_covid", "dummy_cepo"])

    # 2b. PBI constante ~ EMAE
    common_idx = pbi_real_m.index.intersection(emae.index)
    df_temp = pd.DataFrame({"pbi_real": pbi_real_m.loc[common_idx, "pbi_real"], "emae": emae.loc[common_idx, "emae"]})
    datasets["pbi_constante"] = merge_dummies(df_temp).dropna(subset=["emae", "dummy_covid", "dummy_cepo"])

    # 2c. PBI USD ~ EMAE
    common_idx = pbi_usd_m.index.intersection(emae.index)
    df_temp = pd.DataFrame({"pbi_usd": pbi_usd_m.loc[common_idx, "pbi_usd"], "emae": emae.loc[common_idx, "emae"]})
    datasets["pbi_usd"] = merge_dummies(df_temp).dropna(subset=["emae", "dummy_covid", "dummy_cepo"])

    # 3. Cuenta Corriente ~ Saldo Comercial
    common_idx = cc_m.index.intersection(sc.index)
    df_temp = pd.DataFrame({"cuenta_corriente": cc_m.loc[common_idx, "cuenta_corriente"], "saldo_comercial": sc.loc[common_idx, "saldo_comercial"]})
    datasets["cuenta_corriente"] = merge_dummies(df_temp).dropna(subset=["saldo_comercial", "dummy_covid", "dummy_cepo"])

    # 4. Cuenta Financiera ~ Saldo Comercial
    common_idx = cf_m.index.intersection(sc.index)
    df_temp = pd.DataFrame({"cuenta_financiera": cf_m.loc[common_idx, "cuenta_financiera"], "saldo_comercial": sc.loc[common_idx, "saldo_comercial"]})
    datasets["cuenta_financiera"] = merge_dummies(df_temp).dropna(subset=["saldo_comercial", "dummy_covid", "dummy_cepo"])

    # 5. Deuda Externa ~ Reservas/PBI
    common_idx = deuda_m.index.intersection(res_pbi_df.index)
    df_temp = pd.DataFrame({"deuda_externa": deuda_m.loc[common_idx, "deuda_externa"], "res_pbi": res_pbi_df.loc[common_idx, "res_pbi"]})
    datasets["deuda_externa"] = merge_dummies(df_temp).dropna(subset=["res_pbi", "dummy_covid", "dummy_cepo"])

    # 6. Vencimientos 1y
    datasets["venc_1y"] = merge_dummies(pd.DataFrame({"venc_1y": venc_1y_m["venc_1y"]})).dropna(subset=["dummy_covid", "dummy_cepo"])

    # 7. Vencimientos 2y
    datasets["venc_2y"] = merge_dummies(pd.DataFrame({"venc_2y": venc_2y_m["venc_2y"]})).dropna(subset=["dummy_covid", "dummy_cepo"])

    for k, v in datasets.items():
        print(f"  {k}: {len(v)} obs, {v.index[0].date()} --> {v.index[-1].date()}")

    return datasets


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
# 6. EJECUCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("FILTRO DE KALMAN - Variables Macroeconomicas Argentinas")
    print("=" * 70)

    # -- Preparar datos --
    datasets = preparar_datos()

    # -- Especificaciones --
    specs = {
        "SE - Nivel (Mill. ARS)": {
            "key": "se",
            "target": "se",
            "exog": ["superavit_primario", "dummy_covid", "dummy_cepo"],
            "order": (4, 0, 4),
            "seasonal_order": (1, 0, 1, 12),
        },
        "PBI Nominal": {
            "key": "pbi_nominal",
            "target": "pbi_nominal",
            "exog": ["emae", "dummy_covid", "dummy_cepo"],
            "order": (4, 1, 4),
            "seasonal_order": (1, 0, 1, 12),
        },
        "PBI Constante": {
            "key": "pbi_constante",
            "target": "pbi_real",
            "exog": ["emae", "dummy_covid", "dummy_cepo"],
            "order": (4, 1, 4),
            "seasonal_order": (1, 0, 1, 12),
        },
        "PBI USD": {
            "key": "pbi_usd",
            "target": "pbi_usd",
            "exog": ["emae", "dummy_covid", "dummy_cepo"],
            "order": (4, 1, 4),
            "seasonal_order": (1, 0, 1, 12),
        },
        "Total Cuenta Corriente": {
            "key": "cuenta_corriente",
            "target": "cuenta_corriente",
            "exog": ["saldo_comercial", "dummy_covid", "dummy_cepo"],
            "order": (4, 1, 1),
            "seasonal_order": (1, 0, 1, 12),
        },
        "Total Cuenta Financiera": {
            "key": "cuenta_financiera",
            "target": "cuenta_financiera",
            "exog": ["saldo_comercial", "dummy_covid", "dummy_cepo"],
            "order": (1, 1, 4),
            "seasonal_order": (1, 0, 1, 12),
        },
        "Deuda Externa Bruta Total": {
            "key": "deuda_externa",
            "target": "deuda_externa",
            "exog": ["res_pbi", "dummy_covid", "dummy_cepo"],
            "order": (4, 1, 0),
            "seasonal_order": (1, 0, 1, 12),
        },
        "Vencimientos USD 1 anio": {
            "key": "venc_1y",
            "target": "venc_1y",
            "exog": ["dummy_covid", "dummy_cepo"],
            "order": (0, 1, 4),
            "seasonal_order": (1, 0, 1, 12),
        },
        "Vencimientos USD 2 anios": {
            "key": "venc_2y",
            "target": "venc_2y",
            "exog": ["dummy_covid", "dummy_cepo"],
            "order": (0, 1, 4),
            "seasonal_order": (1, 0, 1, 12),
        },
    }

    resultados = {}

    for nombre, spec in specs.items():
        print(f"\n{'-'*60}")
        print(f"Estimando: {nombre}")
        print(f"  ARIMA{spec['order']} + exogena(s): {spec['exog'] if spec['exog'] else 'ninguna'}")

        df = datasets[spec["key"]]
        r = estimar_kalman(
            df,
            target=spec["target"],
            exog_cols=spec["exog"],
            order=spec["order"],
            seasonal_order=spec["seasonal_order"],
            nombre=nombre,
        )

        print(f"  AIC: {r['aic']:.1f}  |  BIC: {r['bic']:.1f}  |  RMSE: {r['rmse_in']:.2f}")
        print(f"  Ljung-Box p-value: {r['ljung_box_pval']:.4f}")

        # Guardar grafico
        fig = graficar_resultado(r)
        safe_name = nombre.lower().replace(" ", "_").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
        html_path = os.path.join(OUT_DIR, f"{safe_name}.html")
        fig.write_html(html_path)
        print(f"  Grafico: {html_path}")

        # Guardar CSV con observados y prediccion (in-sample)
        res_df = pd.DataFrame({
            "fecha": r["y_train"].index,
            "y_obs": r["y_train"].values,
            "y_pred": r["y_pred_in"].values
        }).set_index("fecha")
        out_var_path = os.path.join(VARS_DIR, f"{safe_name}_kalman.csv")
        res_df.to_csv(out_var_path)

        resultados[nombre] = r

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
