"""
explore_bonos_cer_pesos.py

Fase 1: Muestra TODAS las columnas de la tabla vencimientos para 3 archivos muestra.
Fase 2: Escanea todos los .mdb y extrae un catálogo de:
  - Títulos Públicos / Bonos en pesos a tasa fija
  - Títulos Públicos / Bonos ajustados por CER (inflación)

Output:
  data/processed/catalogo_bonos_pesos_cer.xlsx
    - hoja "catalogo"  : lista única de instrumentos (Nombre, Moneda, Tasa, TipoDeuda)
    - hoja "detalle"   : todas las filas de vencimientos de esos instrumentos
    - hoja "columnas"  : schema de columnas por archivo (diagnóstico)
"""

import re
import warnings
from pathlib import Path
from datetime import date

import pandas as pd
import pyodbc

warnings.filterwarnings("ignore", category=UserWarning)

PYTHON_EXE = r"C:\Users\Usuario\AppData\Local\Programs\Python\Python313\python.exe"
MDB_DIR    = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\basesingade deuda")
OUTPUT     = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed\catalogo_bonos_pesos_cer.xlsx")

# ---------------------------------------------------------------------------
# Column aliases — amplios para cubrir variantes con/sin tildes
# ---------------------------------------------------------------------------

TIPO_DEUDA_ALIASES = [
    "Tipo de Deuda", "BOLETIN",
]
OPERACION_ALIASES = [
    "Nombre de la Operacion", "Nombre de la Operaci\xf3n", "Nombre de la Operación",
]
MONEDA_ALIASES = [
    "Moneda", "Moneda de Origen",
    "Descripción", "Descripcion", "Descripci\xf3n",
]
TASA_ALIASES = [
    "Tipo de Tasa", "Tipo de TAsa", "TAsa", "Tasa",
    "Tipo de tasa", "tipo de tasa",
]
FECHA_ALIASES  = ["Fecha de Servicio"]
PRINCIPAL_ALIASES = [
    "Principal en dolares", "Principal en Dolares",
    "Principal en d\xf3lares", "Principal en D\xf3lares",
    "Principal en dólares", "Principal en Dólares",
]
INTERES_ALIASES = [
    "Interes en dolares", "Interes en Dolares",
    "Interes en d\xf3lares", "Interes en D\xf3lares",
    "Interes en dólares", "Interes en Dólares",
]

# Columnas "extra" que quisieramos leer si existen (ISIN, acreedor, etc.)
EXTRA_ALIASES = {
    "isin":         ["ISIN", "Codigo ISIN", "Código ISIN"],
    "acreedor":     ["Acreedor", "Nombre del Acreedor"],
    "fecha_emis":   ["Fecha de Emisión", "Fecha de Emision", "Fecha Emision"],
    "fecha_vto":    ["Fecha de Vencimiento", "Fecha Vencimiento"],
    "instrumento":  ["Tipo de Instrumento", "Instrumento"],
}

# ---------------------------------------------------------------------------
# Filtros semánticos
# ---------------------------------------------------------------------------

TIPO_DEUDA_BONOS = [
    "TITULOS PUBLICOS", "TITULO PUBLICO", "TITULOS",
    "BONOS", "BONO",
    "LETRAS", "LETRA",
]

# Monedas "pesos nominales" (sin ajuste CER)
MONEDA_PESOS_NOMINAL = [
    "ARP",            # código SIGADE para Peso Argentino (2007-2012)
    "PESO ARGENTINO", # nombre completo (2008 Q2-Q3 transición)
    "PESO", "PESOS", "ARS", "$", "PESOS ARGENTINOS",
    "OCM",            # Otras monedas corrientes — posiblemente pesos
]

# Monedas CER-ajustadas
MONEDA_PESOS_CER = [
    "UCP",                 # Unidad de Conversión de Pesos = CER (código SIGADE)
    "PESO ARGENTINO + CER",  # nombre completo (2008 Q2-Q3)
    "CER",
]

# Unión para el filtro de "es peso de algún tipo"
MONEDA_PESOS = MONEDA_PESOS_NOMINAL + MONEDA_PESOS_CER

TASA_FIJA_KEYWORDS = [
    "FIJA", "TASA FIJA", "FIXED", "FIJO",
    "CERO",   # Tasa cero = también nominales (Letes, etc.)
]

TASA_CER_KEYWORDS = [
    "CER", "AJUSTABLE", "INFLACION", "INFLACIÓN",
    "INDEXADA", "UVA",
]

# BADLAR es variable pero NO es CER — la incluimos como "variable nominal pesos"
TASA_BADLAR_KEYWORDS = ["BADLAR"]


def is_match_exact(value: str | None, keywords: list[str]) -> bool:
    """Match exacto del valor contra la lista de keywords (value IN keywords)."""
    if value is None:
        return False
    v = str(value).upper().strip()
    return v in [k.upper() for k in keywords]


def is_match(value: str | None, keywords: list[str]) -> bool:
    """Match parcial: alguna keyword está contenida en el valor."""
    if value is None:
        return False
    v = str(value).upper().strip()
    return any(k.upper() in v for k in keywords)


def classify_bond(moneda: str | None, tasa: str | None) -> str:
    """
    Devuelve el tipo de ajuste del bono:
    - 'CER'      : ajustado por inflación (UCP, PESO+CER, etc.)
    - 'NOMINAL'  : pesos a tasa fija (ARP + TASA FIJA/CERO)
    - 'BADLAR'   : pesos tasa variable (ARP + TASA BADLAR)
    - 'OTRO'     : resto
    """
    mon = str(moneda).upper().strip() if moneda else ""
    tas = str(tasa).upper().strip()   if tasa   else ""

    # Si la moneda ya indica CER → es CER independientemente de la tasa
    if is_match(mon, MONEDA_PESOS_CER):
        return "CER"

    if is_match(mon, MONEDA_PESOS_NOMINAL):
        if is_match(tas, TASA_BADLAR_KEYWORDS):
            return "BADLAR"
        if is_match(tas, TASA_FIJA_KEYWORDS):
            return "NOMINAL"
        if "DIVERSAS" in tas or "CAJA" in tas:
            return "NOMINAL_OTRO"
        return "OTRO"

    return "OTRO"


# ---------------------------------------------------------------------------
# Helpers MDB
# ---------------------------------------------------------------------------

def parse_file_date(stem: str) -> date | None:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})$", stem)
    if not m:
        return None
    y, a, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
    day, month = (a, b) if a > 12 else (b, a)
    try:
        return date(y, month, day)
    except ValueError:
        return None


def find_vencim_table(tables: list[str]) -> str | None:
    for t in tables:
        if "VENCIM" in t.upper() and "NORMAL" in t.upper():
            return t
    return None


def pick_col(cols: list[str], aliases: list[str]) -> str | None:
    col_map = {c.lower(): c for c in cols}
    for a in aliases:
        if a in cols:
            return a
        al = a.lower()
        if al in col_map:
            return col_map[al]
    return None


def connect_mdb(mdb_path: Path):
    conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' + f'DBQ={mdb_path};'
    return pyodbc.connect(conn_str)


# ---------------------------------------------------------------------------
# Fase 1: inspección de columnas
# ---------------------------------------------------------------------------

def inspect_columns(mdb_path: Path) -> dict:
    try:
        conn = connect_mdb(mdb_path)
    except Exception as e:
        return {"file": mdb_path.name, "error": str(e)}

    cursor = conn.cursor()
    tables = [r.table_name for r in cursor.tables(tableType="TABLE")]
    vtable = find_vencim_table(tables)
    if vtable is None:
        conn.close()
        return {"file": mdb_path.name, "vtable": "NOT FOUND", "columns": []}

    cursor.execute(f"SELECT * FROM [{vtable}] WHERE 1=0")
    cols = [d[0] for d in cursor.description]
    conn.close()
    return {"file": mdb_path.name, "vtable": vtable, "columns": cols}


# ---------------------------------------------------------------------------
# Fase 2: extracción de bonos pesos/CER
# ---------------------------------------------------------------------------

def read_bonos_pesos_cer(mdb_path: Path, file_date: date) -> pd.DataFrame | None:
    try:
        conn = connect_mdb(mdb_path)
    except Exception as e:
        print(f"  [WARN] No se puede conectar {mdb_path.name}: {e}")
        return None

    cursor = conn.cursor()
    tables = [r.table_name for r in cursor.tables(tableType="TABLE")]
    vtable = find_vencim_table(tables)
    if vtable is None:
        conn.close()
        return None

    cursor.execute(f"SELECT * FROM [{vtable}] WHERE 1=0")
    actual_cols = [d[0] for d in cursor.description]

    # Columnas obligatorias
    col_tipo  = pick_col(actual_cols, TIPO_DEUDA_ALIASES)
    col_op    = pick_col(actual_cols, OPERACION_ALIASES)
    col_mon   = pick_col(actual_cols, MONEDA_ALIASES)
    col_tasa  = pick_col(actual_cols, TASA_ALIASES)
    col_fecha = pick_col(actual_cols, FECHA_ALIASES)
    col_princ = pick_col(actual_cols, PRINCIPAL_ALIASES)
    col_int   = pick_col(actual_cols, INTERES_ALIASES)

    # Diagnóstico si faltan columnas clave
    for name, col in [("TipoDeuda", col_tipo), ("Operacion", col_op),
                      ("Moneda", col_mon), ("Tasa", col_tasa)]:
        if col is None:
            print(f"  [INFO] {mdb_path.name}: columna '{name}' no encontrada. Cols: {actual_cols}")

    # Construir lista de columnas a leer (sólo las que existan)
    wanted_cols = []
    wanted_labels = []
    for alias_list, label in [
        (TIPO_DEUDA_ALIASES, "tipo_deuda"),
        (OPERACION_ALIASES,  "operacion"),
        (MONEDA_ALIASES,     "moneda"),
        (TASA_ALIASES,       "tasa"),
        (FECHA_ALIASES,      "fecha_serv"),
        (PRINCIPAL_ALIASES,  "principal_usd"),
        (INTERES_ALIASES,    "interes_usd"),
    ]:
        c = pick_col(actual_cols, alias_list)
        if c:
            wanted_cols.append(c)
            wanted_labels.append(label)

    # Columnas extra opcionales
    for label, aliases in EXTRA_ALIASES.items():
        c = pick_col(actual_cols, aliases)
        if c:
            wanted_cols.append(c)
            wanted_labels.append(label)

    safe = ", ".join(f"[{c}]" for c in wanted_cols)
    try:
        df = pd.read_sql(f"SELECT {safe} FROM [{vtable}]", conn)
    except Exception as e:
        print(f"  [WARN] Error leyendo {mdb_path.name}: {e}")
        conn.close()
        return None
    conn.close()

    df.columns = wanted_labels

    # Añadir columnas faltantes como NaN
    for col in ["tipo_deuda", "operacion", "moneda", "tasa",
                "fecha_serv", "principal_usd", "interes_usd"]:
        if col not in df.columns:
            df[col] = None

    df["fecha_serv"]    = pd.to_datetime(df["fecha_serv"],    errors="coerce")
    df["principal_usd"] = pd.to_numeric(df["principal_usd"],  errors="coerce").fillna(0)
    df["interes_usd"]   = pd.to_numeric(df["interes_usd"],    errors="coerce").fillna(0)
    df["file_date"]     = file_date
    df["file_name"]     = mdb_path.name

    # --- Filtro 1: Títulos Públicos / Bonos / Letras ---
    mask_tipo = df["tipo_deuda"].apply(lambda v: is_match(v, TIPO_DEUDA_BONOS))

    # --- Filtro 2: Moneda pesos (nominal o CER) ---
    # Usamos match exacto para códigos cortos ("ARP", "UCP") y parcial para nombres largos
    def moneda_es_peso(v):
        if v is None:
            return False
        vs = str(v).upper().strip()
        # exact match con los códigos cortos
        if vs in [m.upper() for m in MONEDA_PESOS]:
            return True
        # o contiene substring "PESO" (cubre "PESO ARGENTINO", "PESO ARGENTINO + CER")
        return "PESO" in vs
    mask_mon = df["moneda"].apply(moneda_es_peso)

    # --- Clasificar tipo de ajuste ---
    df["tipo_ajuste"] = df.apply(
        lambda r: classify_bond(r["moneda"], r.get("tasa")), axis=1
    )

    # --- Filtro 3: Solo NOMINAL, CER o BADLAR (excluir "OTRO") ---
    mask_ajuste = df["tipo_ajuste"].isin(["CER", "NOMINAL", "BADLAR", "NOMINAL_OTRO"])

    filtered = df[mask_tipo & mask_mon & mask_ajuste].copy()
    return filtered if not filtered.empty else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    mdb_files = sorted(MDB_DIR.glob("*.mdb"))
    print(f"Encontrados {len(mdb_files)} archivos .mdb\n")

    # ---- Fase 1: schema de columnas (primeros 3 archivos) ----
    print("=" * 70)
    print("FASE 1 — Columnas disponibles en tabla Vencimientos (muestra)")
    print("=" * 70)
    schema_rows = []
    for mdb_path in mdb_files[:5]:
        info = inspect_columns(mdb_path)
        cols_str = " | ".join(info.get("columns", []))
        print(f"\n{info['file']}")
        print(f"  Tabla: {info.get('vtable', '?')}")
        print(f"  Columnas: {cols_str}")
        schema_rows.append({
            "file":    info["file"],
            "vtable":  info.get("vtable", ""),
            "columns": cols_str,
        })

    # ---- Fase 2: escaneo completo ----
    print("\n" + "=" * 70)
    print("FASE 2 — Extracción de bonos pesos / CER")
    print("=" * 70)

    all_dfs = []

    for mdb_path in mdb_files:
        file_date = parse_file_date(mdb_path.stem)
        if file_date is None:
            print(f"  [SKIP] No se puede parsear fecha: {mdb_path.name}")
            continue

        print(f"Procesando {mdb_path.name}  ->  {file_date.strftime('%m/%Y')}")
        df = read_bonos_pesos_cer(mdb_path, file_date)

        if df is not None and not df.empty:
            print(f"  -> {len(df)} filas encontradas")
            all_dfs.append(df)
        else:
            print(f"  -> Sin filas pesos/CER (o tabla vacía)")

    if not all_dfs:
        print("\n[ERROR] No se encontraron registros. Revisar filtros o archivos.")
        return

    detalle = pd.concat(all_dfs, ignore_index=True)
    print(f"\nTotal filas en detalle: {len(detalle)}")

    # --- Catálogo único de instrumentos ---
    catalogo_cols = ["operacion", "tipo_deuda", "moneda", "tasa", "tipo_ajuste"]
    extra_cols = [c for c in ["isin", "instrumento"] if c in detalle.columns]
    cat_cols = [c for c in catalogo_cols + extra_cols if c in detalle.columns]

    catalogo = (
        detalle[cat_cols]
        .drop_duplicates(subset=["operacion"])
        .sort_values("operacion")
        .reset_index(drop=True)
    )
    catalogo.columns = [c.title() for c in catalogo.columns]

    print(f"Instrumentos únicos: {len(catalogo)}")
    print("\nPrimeras filas del catálogo:")
    print(catalogo.head(20).to_string())

    # --- Estadísticas por tipo de tasa ---
    if "tasa" in detalle.columns:
        print("\nDistribución por Tasa:")
        print(detalle["tasa"].value_counts().to_string())

    if "tipo_deuda" in detalle.columns:
        print("\nDistribución por Tipo de Deuda:")
        print(detalle["tipo_deuda"].value_counts().to_string())

    # --- Guardar Excel ---
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Estadística de tipo_ajuste
    if "tipo_ajuste" in detalle.columns:
        print("\nDistribución por Tipo de Ajuste:")
        print(detalle.drop_duplicates("operacion")["tipo_ajuste"].value_counts().to_string())

    # Ordenar columnas del detalle
    priority = ["file_date", "file_name", "tipo_deuda", "operacion",
                "moneda", "tasa", "tipo_ajuste", "fecha_serv", "principal_usd", "interes_usd"]
    remaining = [c for c in detalle.columns if c not in priority]
    detalle = detalle[priority + remaining]

    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        catalogo.to_excel(writer, sheet_name="catalogo", index=False)
        detalle.to_excel(writer, sheet_name="detalle", index=False)
        pd.DataFrame(schema_rows).to_excel(writer, sheet_name="columnas", index=False)

    print(f"\nGuardado -> {OUTPUT}")
    print(f"  Hoja 'catalogo' : {len(catalogo)} instrumentos únicos")
    print(f"  Hoja 'detalle'  : {len(detalle)} filas de vencimientos")


if __name__ == "__main__":
    main()
