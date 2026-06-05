"""
Construcción del "Sentimiento de Mercado Ajustado por Ciclo Político".

Genera dos variables explicativas para el modelo del Riesgo País (ARDL/VECM):

    X_t = D_t * (I_t - U)

donde:
    I_t = valor del índice en el mes t (ICG o ICC)
    U   = umbral crítico del índice (ICG: 2.0 ; ICC: 45)
    D_t = orientación del gobierno: +1 promercado, -1 antimercado, 0 sin clasificar

Frecuencia: mensual (la de los índices ICG/ICC).
La orientación se recalcula con las fechas REALES de asunción (10/12 del año
electoral), no con la victoria electoral como venía en dummy_gob.csv.
"""

import pandas as pd

DATA_DIR = "data/Variables Finales"

# --- Umbrales ---------------------------------------------------------------
UMBRAL_ICG = 2.0
UMBRAL_ICC = 45.0

# --- Períodos de gobierno por fecha de ASUNCIÓN (10/12) ---------------------
# (inicio_inclusive, orientacion). El intervalo va hasta el inicio del siguiente.
# +1 promercado | -1 antimercado | 0 no clasificado por el usuario.
PERIODOS = [
    ("1900-01-01", 0),   # Menem / De la Rúa / transición / Duhalde / Néstor
    ("2007-12-10", -1),  # Cristina Fernández de Kirchner
    ("2015-12-10", 1),   # Mauricio Macri
    ("2019-12-10", -1),  # Alberto Fernández
    ("2023-12-10", 1),   # Javier Milei
]


def asignar_orientacion(fechas: pd.DatetimeIndex) -> pd.Series:
    """Devuelve D_t para cada fecha. Usa el FIN de mes para que el mes de
    asunción (cambio el 10/12) ya quede asignado al gobierno entrante."""
    fin_de_mes = fechas + pd.offsets.MonthEnd(0)
    cortes = pd.to_datetime([p[0] for p in PERIODOS])
    valores = [p[1] for p in PERIODOS]
    # idx = índice del período cuyo inicio es <= fin_de_mes
    idx = pd.cut(
        fin_de_mes,
        bins=list(cortes) + [pd.Timestamp.max],
        labels=False,
        right=False,
    )
    return pd.Series([valores[int(i)] for i in idx], index=fechas, name="orientacion_gobierno")


def main() -> pd.DataFrame:
    col_icc = "Indice de Confianza del Consumidor (ICC) - Nacional"
    col_icg = "Indice de Confianza en el Gobierno (ICG) - Nivel General"

    raw = pd.read_csv(f"{DATA_DIR}/ICC.csv", usecols=["Date", col_icc, col_icg])
    raw["Date"] = pd.to_datetime(raw["Date"])
    df = (
        raw.rename(columns={"Date": "fecha", col_icc: "icc", col_icg: "icg"})
        .set_index("fecha")
        .sort_index()
    )

    # D_t con fechas de asunción reales (10/12)
    df["orientacion_gobierno"] = asignar_orientacion(df.index)

    # X_t = D_t * (I_t - U)   (el + 0.0 evita el cero negativo cuando D_t = 0)
    df["icg_transformado"] = df["orientacion_gobierno"] * (df["icg"] - UMBRAL_ICG) + 0.0
    df["icc_transformado"] = df["orientacion_gobierno"] * (df["icc"] - UMBRAL_ICC) + 0.0

    salida = df[["icg", "icc", "orientacion_gobierno", "icg_transformado", "icc_transformado"]]

    # --- Verificación -------------------------------------------------------
    pd.set_option("display.width", 140)
    pd.set_option("display.max_columns", None)
    print("Primeras filas con datos de ambos índices:")
    print(salida.dropna(subset=["icg", "icc"]).head(10), "\n")

    print("Meses de transición (asunción 10/12) — chequeo de signos:")
    for anio in (2015, 2019, 2023):
        ventana = salida.loc[f"{anio}-11-01":f"{anio}-12-31"]
        print(ventana[["orientacion_gobierno", "icg", "icg_transformado", "icc", "icc_transformado"]])
    print()

    print("Recuento de orientación asignada:")
    print(salida["orientacion_gobierno"].value_counts().sort_index(), "\n")

    out_path = f"{DATA_DIR}/sentimiento_ciclo_politico.csv"
    salida.to_csv(out_path)
    print(f"Guardado: {out_path}  ({len(salida)} filas)")
    return salida


if __name__ == "__main__":
    main()
