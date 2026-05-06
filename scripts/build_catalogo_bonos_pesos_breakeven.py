"""
build_catalogo_bonos_pesos_breakeven.py

Catálogo consolidado de bonos argentinos en pesos (tasa fija nominal y CER)
que cotizaron desde 2019, útil para construir la serie de inflación breakeven.

Fuentes combinadas:
  - Boletín Mensual Secretaría de Finanzas (A.1) - 2019-2026
  - Base SIGADE .mdb - 2007-2018
  - Bonistas.com, Cohen.com.ar, argentina.gob.ar (información de mercado)

Output: data/processed/catalogo_breakeven_bonos.xlsx
  - hoja "cer"      : bonos ajustados por CER (inflación)
  - hoja "nominal"  : bonos tasa fija nominal en pesos
  - hoja "lecer"    : letras CER corto plazo (series X)
  - hoja "lecap"    : letras/bonos capitalizables nominales
  - hoja "notas"    : metodología y fuentes
"""

from pathlib import Path
import pandas as pd

OUTPUT = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed\catalogo_breakeven_bonos.xlsx")

# ---------------------------------------------------------------------------
# 1. BONOS CER — capital ajusta por inflación (CER)
# ---------------------------------------------------------------------------

bonos_cer = [
    # ── Reestructuración 2005 / Canje ────────────────────────────────────────
    {
        "ticker":       "DICP",
        "nombre":       "Discount en $ ajustado por CER",
        "familia":      "Canje 2005",
        "cupon_real":   5.83,
        "ajuste":       "CER",
        "fecha_emis":   "2005-06-02",
        "fecha_vto":    "2033-12-31",
        "cotiza_desde": "2005",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Reestructuración 2005 y 2010. Tasa escalonada: 5.83% desde 2013.",
    },
    {
        "ticker":       "PARP",
        "nombre":       "Par en $ ajustado por CER",
        "familia":      "Canje 2005",
        "cupon_real":   "escalera 0.5%->5.25%",
        "ajuste":       "CER",
        "fecha_emis":   "2005-06-02",
        "fecha_vto":    "2038-12-31",
        "cotiza_desde": "2005",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Tasa escalera: 0.5% (2005-2009), 1.0% (2010-2014), 2.0% (2015-2019), 5.25% (2020+).",
    },
    {
        "ticker":       "CUAP",
        "nombre":       "Cuasipar en $ ajustado por CER",
        "familia":      "Canje 2005",
        "cupon_real":   3.31,
        "ajuste":       "CER",
        "fecha_emis":   "2003-12-31",
        "fecha_vto":    "2045-12-31",
        "cotiza_desde": "2003",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Emitido en el canje 2003. Menor volumen de trading que DICP/PARP.",
    },

    # ── BONCER pre-2020 (del SIGADE, cotizaron en MAE/MERVAL) ───────────────
    {
        "ticker":       "BONCER 4.25% 2019-01",
        "nombre":       "BONCER/$/4,25%+CER/15-01-2019",
        "familia":      "BONCER (pre-2020)",
        "cupon_real":   4.25,
        "ajuste":       "CER",
        "fecha_emis":   None,
        "fecha_vto":    "2019-01-15",
        "cotiza_desde": "~2014",
        "cotiza_hasta": "2019-01",
        "mercado":      "MAE / MERVAL",
        "notas":        "Vencido en enero 2019. Del SIGADE (moneda UCP).",
    },
    {
        "ticker":       "BONCER 4.25% 2019-04",
        "nombre":       "BONCER/$/4,25%+CER/15-04-2019",
        "familia":      "BONCER (pre-2020)",
        "cupon_real":   4.25,
        "ajuste":       "CER",
        "fecha_emis":   None,
        "fecha_vto":    "2019-04-15",
        "cotiza_desde": "~2014",
        "cotiza_hasta": "2019-04",
        "mercado":      "MAE / MERVAL",
        "notas":        "Vencido en abril 2019.",
    },
    {
        "ticker":       "BONCER 2.25% 2020",
        "nombre":       "BONCER/$/2,25%+CER/28-04-2020",
        "familia":      "BONCER (pre-2020)",
        "cupon_real":   2.25,
        "ajuste":       "CER",
        "fecha_emis":   None,
        "fecha_vto":    "2020-04-28",
        "cotiza_desde": "~2016",
        "cotiza_hasta": "2020-04",
        "mercado":      "MAE / MERVAL",
        "notas":        "Vencido en abril 2020.",
    },
    {
        "ticker":       "BONCER 2.50% 2021",
        "nombre":       "BONCER/$/2,50%+CER/22-07-2021",
        "familia":      "BONCER (pre-2020)",
        "cupon_real":   2.50,
        "ajuste":       "CER",
        "fecha_emis":   None,
        "fecha_vto":    "2021-07-22",
        "cotiza_desde": "~2016",
        "cotiza_hasta": "2021-07",
        "mercado":      "MAE / MERVAL",
        "notas":        "Vencido julio 2021.",
    },
    {
        "ticker":       "BONCER 8.50% 2022",
        "nombre":       "BONCER/$/8,5%+CER/29-11-2022",
        "familia":      "BONCER (pre-2020)",
        "cupon_real":   8.50,
        "ajuste":       "CER",
        "fecha_emis":   None,
        "fecha_vto":    "2022-11-29",
        "cotiza_desde": "~2016",
        "cotiza_hasta": "2022-11",
        "mercado":      "MAE / MERVAL",
        "notas":        "Vencido noviembre 2022.",
    },
    {
        "ticker":       "BONCER 4.00% 2023",
        "nombre":       "BONCER/$/4%+CER/06-03-2023",
        "familia":      "BONCER (pre-2020)",
        "cupon_real":   4.00,
        "ajuste":       "CER",
        "fecha_emis":   None,
        "fecha_vto":    "2023-03-06",
        "cotiza_desde": "~2017",
        "cotiza_hasta": "2023-03",
        "mercado":      "MAE / MERVAL",
        "notas":        "Vencido marzo 2023.",
    },
    {
        "ticker":       "BONCER 4.00% 2025",
        "nombre":       "BONCER/$/4%+CER/27-04-2025",
        "familia":      "BONCER (pre-2020)",
        "cupon_real":   4.00,
        "ajuste":       "CER",
        "fecha_emis":   None,
        "fecha_vto":    "2025-04-27",
        "cotiza_desde": "~2017",
        "cotiza_hasta": "2025-04",
        "mercado":      "MAE / MERVAL",
        "notas":        "Vencido abril 2025.",
    },

    # ── BONCER Tesoro Nacional — Alberto Fernández (2020-2023) ────────────────
    {
        "ticker":       "TX21",
        "nombre":       "BONCER 1% vto 5/8/2021",
        "familia":      "BONCER (Tesoro Nacional)",
        "cupon_real":   1.00,
        "ajuste":       "CER",
        "fecha_emis":   "2020-01-31",
        "fecha_vto":    "2021-08-05",
        "cotiza_desde": "2020-01",
        "cotiza_hasta": "2021-08",
        "mercado":      "MERVAL / MAE",
        "notas":        "Emitido con Resolución Conjunta 8/2020. Primer BONCER del Tesoro.",
    },
    {
        "ticker":       "TX22",
        "nombre":       "BONCER 1.20% vto 18/3/2022",
        "familia":      "BONCER (Tesoro Nacional)",
        "cupon_real":   1.20,
        "ajuste":       "CER",
        "fecha_emis":   "2020-03",
        "fecha_vto":    "2022-03-18",
        "cotiza_desde": "2020-03",
        "cotiza_hasta": "2022-03",
        "mercado":      "MERVAL / MAE",
        "notas":        "Conversión a LECER+BONCER en 2022.",
    },
    {
        "ticker":       "TX24",
        "nombre":       "BONCER 1.50% vto 25/3/2024",
        "familia":      "BONCER (Tesoro Nacional)",
        "cupon_real":   1.50,
        "ajuste":       "CER",
        "fecha_emis":   "2021",
        "fecha_vto":    "2024-03-25",
        "cotiza_desde": "2021",
        "cotiza_hasta": "2024-03",
        "mercado":      "MERVAL / MAE",
        "notas":        "Vencido marzo 2024.",
    },
    {
        "ticker":       "T2X4",
        "nombre":       "BONCER 1.55% vto 26/7/2024",
        "familia":      "BONCER (Tesoro Nacional)",
        "cupon_real":   1.55,
        "ajuste":       "CER",
        "fecha_emis":   "2022",
        "fecha_vto":    "2024-07-26",
        "cotiza_desde": "2022",
        "cotiza_hasta": "2024-07",
        "mercado":      "MERVAL / MAE",
        "notas":        "Emitido en conversión del TX22 (30% LECER + 30% T2X4 + 40% TX26).",
    },
    {
        "ticker":       "TX26",
        "nombre":       "BONCER 2% vto 9/11/2026",
        "familia":      "BONCER (Tesoro Nacional)",
        "cupon_real":   2.00,
        "ajuste":       "CER",
        "fecha_emis":   "2020-09-04",
        "fecha_vto":    "2026-11-09",
        "cotiza_desde": "2020-09",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Uno de los más líquidos del mercado CER. Emitido junto con TX28.",
    },
    {
        "ticker":       "TX28",
        "nombre":       "BONCER 2.25% vto 9/11/2028",
        "familia":      "BONCER (Tesoro Nacional)",
        "cupon_real":   2.25,
        "ajuste":       "CER",
        "fecha_emis":   "2020-09-04",
        "fecha_vto":    "2028-11-09",
        "cotiza_desde": "2020-09",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Par con TX26 (mismo día emisión). Muy líquido.",
    },
    {
        "ticker":       "TX31",
        "nombre":       "BONCER 2.5% vto 30/11/2031",
        "familia":      "BONCER (Tesoro Nacional)",
        "cupon_real":   2.50,
        "ajuste":       "CER",
        "fecha_emis":   "2022-05-31",
        "fecha_vto":    "2031-11-30",
        "cotiza_desde": "2022-05",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Bono CER más largo del Tesoro. TIR actual ~8%.",
    },

    # ── BONCER Cero Cupón (Milei, 2023-2024) ─────────────────────────────────
    {
        "ticker":       "TZX25",
        "nombre":       "BONCER Cero Cupón vto 30/6/2025",
        "familia":      "BONCER Cero Cupón",
        "cupon_real":   0.00,
        "ajuste":       "CER",
        "fecha_emis":   "2023",
        "fecha_vto":    "2025-06-30",
        "cotiza_desde": "2023",
        "cotiza_hasta": "2025-06",
        "mercado":      "MERVAL / MAE",
        "notas":        "Zero coupon CER. Vencido junio 2025.",
    },
    {
        "ticker":       "TZX26",
        "nombre":       "BONCER Cero Cupón vto 30/6/2026",
        "familia":      "BONCER Cero Cupón",
        "cupon_real":   0.00,
        "ajuste":       "CER",
        "fecha_emis":   "2024-02-01",
        "fecha_vto":    "2026-06-30",
        "cotiza_desde": "2024-02",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "TIR actual ~-9.4%. Zero coupon CER.",
    },
    {
        "ticker":       "TZX27",
        "nombre":       "BONCER Cero Cupón vto 30/6/2027",
        "familia":      "BONCER Cero Cupón",
        "cupon_real":   0.00,
        "ajuste":       "CER",
        "fecha_emis":   "2024",
        "fecha_vto":    "2027-06-30",
        "cotiza_desde": "2024",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Zero coupon CER.",
    },
]

# ---------------------------------------------------------------------------
# 2. BONOS TASA FIJA NOMINAL en $ (no ajustan por CER)
# ---------------------------------------------------------------------------

bonos_nominal = [
    # ── BONTE (Bonos del Tesoro Nacional en $, tasa fija) ───────────────────
    {
        "ticker":       "TO26",
        "nombre":       "BONTE 15.50% vto 17/10/2026",
        "familia":      "BONTE",
        "cupon_nominal": 15.50,
        "ajuste":       "Nominal $",
        "fecha_emis":   "2016-10-17",
        "fecha_vto":    "2026-10-17",
        "cotiza_desde": "2016",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Emitido en el período Macri. Paga cupón semestral.",
    },
    {
        "ticker":       "BONTE 16% 2023",
        "nombre":       "BOTE 16% vto 2023",
        "familia":      "BONTE",
        "cupon_nominal": 16.00,
        "ajuste":       "Nominal $",
        "fecha_emis":   "2018",
        "fecha_vto":    "2023",
        "cotiza_desde": "2018",
        "cotiza_hasta": "2023",
        "mercado":      "MERVAL / MAE",
        "notas":        "Emitido en 2018 (Macri). Vencido.",
    },
    {
        "ticker":       "BONTE 26% 2020",
        "nombre":       "BONTE 26% vto 21/11/2020",
        "familia":      "BONTE",
        "cupon_nominal": 26.00,
        "ajuste":       "Nominal $",
        "fecha_emis":   "2019",
        "fecha_vto":    "2020-11-21",
        "cotiza_desde": "2019",
        "cotiza_hasta": "2020-11",
        "mercado":      "MERVAL / MAE",
        "notas":        "Emitido Lacunza 2019 a tasa alta de mercado. Vencido.",
    },
    {
        "ticker":       "BONTE 26% 2021",
        "nombre":       "BONTE 26% vto 21/11/2021",
        "familia":      "BONTE",
        "cupon_nominal": 26.00,
        "ajuste":       "Nominal $",
        "fecha_emis":   "2019",
        "fecha_vto":    "2021-11-21",
        "cotiza_desde": "2019",
        "cotiza_hasta": "2021-11",
        "mercado":      "MERVAL / MAE",
        "notas":        "Emitido Lacunza 2019. Vencido.",
    },
    {
        "ticker":       "TMF30",  # ticker tentativo
        "nombre":       "BONTE 2030 (tasa fija ~31.7%)",
        "familia":      "BONTE",
        "cupon_nominal": 31.68,
        "ajuste":       "Nominal $",
        "fecha_emis":   "2025-06",
        "fecha_vto":    "2030-05-30",
        "cotiza_desde": "2025-06",
        "cotiza_hasta": "activo",
        "mercado":      "MERVAL / MAE",
        "notas":        "Emitido junio 2025 para inversores internacionales (suscripción en USD). Put ejercible mayo 2027. TIR corte: 31.68%.",
    },

    # ── BONAR en $ ───────────────────────────────────────────────────────────
    {
        "ticker":       "BONAR ARG $ V",
        "nombre":       "BONAR Argentino en Pesos V",
        "familia":      "BONAR",
        "cupon_nominal": None,
        "ajuste":       "Nominal $",
        "fecha_emis":   None,
        "fecha_vto":    None,
        "cotiza_desde": "~2010",
        "cotiza_hasta": "vencido",
        "mercado":      "MERVAL / MAE",
        "notas":        "Figura en SIGADE y boletín 2019 como remanente. Bajo volumen.",
    },

    # ── Otros nominales ──────────────────────────────────────────────────────
    {
        "ticker":       "BOGATO $",
        "nombre":       "BOGATO nominal (Bono Garantizado Total en $)",
        "familia":      "BOGATO",
        "cupon_nominal": None,
        "ajuste":       "Nominal $",
        "fecha_emis":   None,
        "fecha_vto":    "2020-03-06",
        "cotiza_desde": "~2015",
        "cotiza_hasta": "2020-03",
        "mercado":      "MAE",
        "notas":        "El nombre en SIGADE incluye 'CER+4%' pero la moneda registrada es ARP (nominal). Requiere verificación.",
    },
]

# ---------------------------------------------------------------------------
# 3. LECER — Letras del Tesoro ajustadas por CER (corto plazo)
# ---------------------------------------------------------------------------
# Nota: se emitieron decenas de series X entre 2020 y 2023.
# Se listan las representativas. El ticker sigue el patrón X{DD}{MMM}{AA}.

lecer_series = [
    # Año 2021
    {"ticker": "X31D1",  "vto": "2021-12-31", "notas": "Activa en 2H2021"},
    # Año 2022
    {"ticker": "X16D2",  "vto": "2022-12-16", "notas": "Fue ofrecida en conversión TX22"},
    {"ticker": "X31E2",  "vto": "2022-01-31", "notas": ""},
    {"ticker": "X28F2",  "vto": "2022-02-28", "notas": ""},
    {"ticker": "X25MR2", "vto": "2022-03-25", "notas": ""},
    {"ticker": "X29A2",  "vto": "2022-04-29", "notas": ""},
    {"ticker": "X27MY2", "vto": "2022-05-27", "notas": ""},
    {"ticker": "X30J2",  "vto": "2022-06-30", "notas": ""},
    {"ticker": "X29L2",  "vto": "2022-07-29", "notas": ""},
    {"ticker": "X30G2",  "vto": "2022-08-30", "notas": ""},
    {"ticker": "X30S2",  "vto": "2022-09-30", "notas": ""},
    {"ticker": "X21O2",  "vto": "2022-10-21", "notas": ""},
    {"ticker": "X18N2",  "vto": "2022-11-18", "notas": ""},
    # Año 2023
    {"ticker": "X23F3",  "vto": "2023-02-23", "notas": ""},
    {"ticker": "X31MR3", "vto": "2023-03-31", "notas": ""},
    {"ticker": "X21A3",  "vto": "2023-04-21", "notas": ""},
    {"ticker": "X19MY3", "vto": "2023-05-19", "notas": ""},
    {"ticker": "X16J3",  "vto": "2023-06-16", "notas": ""},
    {"ticker": "X18L3",  "vto": "2023-07-18", "notas": ""},
    {"ticker": "X13G3",  "vto": "2023-08-13", "notas": ""},
    {"ticker": "X15S3",  "vto": "2023-09-15", "notas": ""},
    {"ticker": "X20O3",  "vto": "2023-10-20", "notas": ""},
]

df_lecer = pd.DataFrame(lecer_series)
df_lecer["ajuste"]       = "CER"
df_lecer["cupon_real"]   = 0.0
df_lecer["familia"]      = "LECER"
df_lecer["cotiza_desde"] = df_lecer["vto"].str[:4].astype(str)
df_lecer["cotiza_hasta"] = df_lecer["vto"]
df_lecer["mercado"]      = "MERVAL / MAE"

# ---------------------------------------------------------------------------
# 4. LECAP / BONCAP — Letras y Bonos capitalizables en $ (tasa fija nominal)
# ---------------------------------------------------------------------------

lecap_series = [
    # ── ERA MACRI (2018-2019) — todos vencidos ───────────────────────────────
    # El naming era S{DD}{MES}{AA}. Se listan los que cotizaron en 2019.
    {"ticker": "S29Y6_2019",  "vto": "2019-01-29", "era": "Macri 2018-2019", "notas": "Último año Macri"},
    {"ticker": "S22F9",       "vto": "2019-02-22", "era": "Macri 2018-2019", "notas": ""},
    {"ticker": "S29MR9",      "vto": "2019-03-29", "era": "Macri 2018-2019", "notas": ""},
    {"ticker": "S30A9",       "vto": "2019-04-30", "era": "Macri 2018-2019", "notas": ""},
    {"ticker": "S31MY9",      "vto": "2019-05-31", "era": "Macri 2018-2019", "notas": ""},
    {"ticker": "S30J9",       "vto": "2019-06-28", "era": "Macri 2018-2019", "notas": ""},
    {"ticker": "S31L9",       "vto": "2019-07-31", "era": "Macri 2018-2019", "notas": ""},
    {"ticker": "S14G9",       "vto": "2019-08-14", "era": "Macri 2018-2019", "notas": "Última LECAP Lacunza; default técnico post-PASO"},
    # ── ERA MILEI (2024+) — actuales ────────────────────────────────────────
    {"ticker": "S30A6",  "vto": "2026-04-30", "era": "Milei 2024+", "notas": "51 días al vto (ref. mayo 2026)"},
    {"ticker": "S29Y6",  "vto": "2026-05-29", "era": "Milei 2024+", "notas": "80 días al vto"},
    {"ticker": "S31L6",  "vto": "2026-07-31", "era": "Milei 2024+", "notas": "143 días al vto"},
    {"ticker": "S31G6",  "vto": "2026-08-31", "era": "Milei 2024+", "notas": "174 días al vto"},
    {"ticker": "S30O6",  "vto": "2026-10-30", "era": "Milei 2024+", "notas": "234 días al vto"},
    {"ticker": "S30N6",  "vto": "2026-11-30", "era": "Milei 2024+", "notas": "265 días al vto"},
    # BONCAP (>1 año, misma mecánica capitalizable)
    {"ticker": "T30J6",  "vto": "2026-06-30", "era": "Milei 2024+ (BONCAP)", "notas": "112 días al vto"},
    {"ticker": "T15E7",  "vto": "2027-01-15", "era": "Milei 2024+ (BONCAP)", "notas": "311 días al vto"},
    {"ticker": "T30A7",  "vto": "2027-04-30", "era": "Milei 2024+ (BONCAP)", "notas": "416 días al vto"},
    {"ticker": "T31Y7",  "vto": "2027-05-31", "era": "Milei 2024+ (BONCAP)", "notas": "447 días al vto"},
    {"ticker": "T30J7",  "vto": "2027-06-30", "era": "Milei 2024+ (BONCAP)", "notas": "477 días al vto"},
]

df_lecap = pd.DataFrame(lecap_series)
df_lecap["ajuste"]     = "Nominal $"
df_lecap["cupon"]      = "capitalizable (TNA mensual)"
df_lecap["mercado"]    = "MERVAL / MAE"
df_lecap["familia"]    = df_lecap["era"].apply(
    lambda e: "BONCAP" if "BONCAP" in e else "LECAP"
)

# ---------------------------------------------------------------------------
# 5. Construir DataFrames y guardar
# ---------------------------------------------------------------------------

df_cer     = pd.DataFrame(bonos_cer)
df_nominal = pd.DataFrame(bonos_nominal)

# Columnas ordenadas
cer_cols = ["ticker","nombre","familia","cupon_real","ajuste",
            "fecha_emis","fecha_vto","cotiza_desde","cotiza_hasta","mercado","notas"]
nom_cols = ["ticker","nombre","familia","cupon_nominal","ajuste",
            "fecha_emis","fecha_vto","cotiza_desde","cotiza_hasta","mercado","notas"]
lecer_cols = ["ticker","familia","ajuste","cupon_real","vto",
              "cotiza_desde","cotiza_hasta","mercado","notas"]
lecap_cols = ["ticker","familia","ajuste","cupon","era","vto","mercado","notas"]

# Notas metodológicas
notas = pd.DataFrame([
    {"sección": "CER",
     "descripción": "Bonos cuyo capital ajusta diariamente por el índice CER (BCRA). "
                    "La tasa real es el spread sobre CER. Para el breakeven: "
                    "TIR_nominal / TIR_real - 1 ~ inflacion implicita."},
    {"sección": "Nominal",
     "descripción": "Bonos en pesos con tasa fija sin ajuste inflacionario. "
                    "Para breakeven se necesita una duration similar al bono CER comparable."},
    {"sección": "LECER",
     "descripción": "Letras del Tesoro ajustadas por CER, corto plazo (<1 año). "
                    "Cero cupón. Ticker X{DD}{MMM}{AA}. Activas 2020-2023."},
    {"sección": "LECAP/BONCAP",
     "descripción": "Letras (<1 año) y Bonos (>1 año) capitalizables nominales. "
                    "Pagan TNA mensual capitalizada, sin cupones periódicos. "
                    "Dos epocas: Macri (2018-2019) y Milei (2024+)."},
    {"sección": "Fuentes",
     "descripción": "Boletín Mensual Secretaría de Finanzas (hoja A.1, 2019-2026); "
                    "base SIGADE .mdb (2007-2018); Bonistas.com; "
                    "Cohen.com.ar; IOL invertironline; argentina.gob.ar licitaciones."},
    {"seccion": "Breakeven metodologia",
     "descripcion": "Breakeven inflation ~ (1 + TIR_nominal) / (1 + TIR_CER) - 1. "
                    "Parear por duration similar. Para series historicas se requieren "
                    "precios diarios/semanales de cada bono y el CER diario del BCRA."},
])

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
    df_cer[cer_cols].to_excel(writer, sheet_name="cer", index=False)
    df_nominal[nom_cols].to_excel(writer, sheet_name="nominal", index=False)
    df_lecer[lecer_cols].to_excel(writer, sheet_name="lecer", index=False)
    df_lecap[lecap_cols].to_excel(writer, sheet_name="lecap_boncap", index=False)
    notas.to_excel(writer, sheet_name="notas", index=False)

print(f"Guardado -> {OUTPUT}")
print(f"  CER     : {len(df_cer)} instrumentos")
print(f"  Nominal : {len(df_nominal)} instrumentos")
print(f"  LECER   : {len(df_lecer)} series")
print(f"  LECAP   : {len(df_lecap)} series")

# Resumen en pantalla
print("\n=== RESUMEN BONOS CER (para breakeven) ===")
print(df_cer[["ticker","cupon_real","fecha_vto","cotiza_desde","cotiza_hasta"]].to_string(index=False))

print("\n=== RESUMEN BONOS NOMINALES ===")
print(df_nominal[["ticker","cupon_nominal","fecha_vto","cotiza_desde","cotiza_hasta"]].to_string(index=False))
