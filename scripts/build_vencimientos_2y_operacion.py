"""
Serie historica de vencimientos a 2 anos por Operacion + Moneda (SIGADE .mdb)
Output: DataFrame con filas = (Nombre de la Operacion, Moneda), columnas = MM/AAAA
Incluye imputacion de trimestres faltantes: 03/2009, 03/2014, 09/2014.
"""

import re
import warnings
from pathlib import Path
from datetime import date

import pandas as pd
import pyodbc

warnings.filterwarnings("ignore", category=UserWarning)

MDB_DIR     = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\basesingade deuda")
OUTPUT_PATH = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed\vencimientos_2y_sigade_operacion.xlsx")

# ---------------------------------------------------------------------------
# Column aliases
# ---------------------------------------------------------------------------

OPERACION_ALIASES = [
    "Nombre de la Operacion", "Nombre de la Operaci\xf3n",
    "Nombre de la Operación",
]
MONEDA_ALIASES = [
    "Moneda", "Moneda de Origen",
]
FECHA_ALIASES = ["Fecha de Servicio"]
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

# Trimestres a imputar: (col_label, source_mdb_name, imputed_date)
MISSING_QUARTERS = [
    ("03/2009", "basesigade 2008-12-30.mdb",  date(2009, 3, 31)),
    ("03/2014", "basesigade 2013-31-12.mdb",  date(2014, 3, 31)),
    ("09/2014", "basesigade 2014-06-30.mdb",  date(2014, 9, 30)),
]

# ---------------------------------------------------------------------------
# Helpers
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


def col_to_date(col: str) -> date:
    mm, yyyy = col.split("/")
    return date(int(yyyy), int(mm), 1)


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
        if a.lower() in col_map:
            return col_map[a.lower()]
    return None


def read_raw(mdb_path: Path) -> pd.DataFrame | None:
    """Read vencimientos table returning (operacion, moneda, fecha, principal_usd, interes_usd)."""
    conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' + f'DBQ={mdb_path};'
    try:
        conn = pyodbc.connect(conn_str)
    except Exception as e:
        print(f"  [WARN] Cannot connect {mdb_path.name}: {e}")
        return None

    cursor = conn.cursor()
    tables = [row.table_name for row in cursor.tables(tableType="TABLE")]
    vtable = find_vencim_table(tables)
    if vtable is None:
        print(f"  [WARN] No vencimientos table in {mdb_path.name}")
        conn.close()
        return None

    cursor.execute(f"SELECT * FROM [{vtable}] WHERE 1=0")
    actual_cols = [d[0] for d in cursor.description]

    col_op    = pick_col(actual_cols, OPERACION_ALIASES)
    col_mon   = pick_col(actual_cols, MONEDA_ALIASES)
    col_fecha = pick_col(actual_cols, FECHA_ALIASES)
    col_princ = pick_col(actual_cols, PRINCIPAL_ALIASES)
    col_int   = pick_col(actual_cols, INTERES_ALIASES)

    missing = [n for n, c in [("Operacion", col_op), ("Moneda", col_mon),
                               ("Fecha", col_fecha), ("Principal", col_princ),
                               ("Interes", col_int)] if c is None]
    if missing:
        print(f"  [WARN] Missing cols {missing} in {mdb_path.name}. Available: {actual_cols}")
        conn.close()
        return None

    safe = ", ".join(f"[{c}]" for c in [col_op, col_mon, col_fecha, col_princ, col_int])
    try:
        df = pd.read_sql(f"SELECT {safe} FROM [{vtable}]", conn)
    except Exception as e:
        print(f"  [WARN] Error reading {mdb_path.name}: {e}")
        conn.close()
        return None
    conn.close()

    df.columns = ["operacion", "moneda", "fecha_serv", "principal_usd", "interes_usd"]
    df["fecha_serv"]    = pd.to_datetime(df["fecha_serv"], errors="coerce")
    df["principal_usd"] = pd.to_numeric(df["principal_usd"], errors="coerce").fillna(0)
    df["interes_usd"]   = pd.to_numeric(df["interes_usd"],   errors="coerce").fillna(0)
    return df


def aggregate(df: pd.DataFrame, from_date: date) -> dict[tuple, float]:
    """Filter to 2-year window from from_date and aggregate by (operacion, moneda)."""
    start  = pd.Timestamp(from_date)
    cutoff = start + pd.DateOffset(years=2)
    mask = (df["fecha_serv"] >= start) & (df["fecha_serv"] <= cutoff)
    df = df[mask].copy()
    if df.empty:
        return {}
    df["total_usd"] = df["principal_usd"] + df["interes_usd"]
    return df.groupby(["operacion", "moneda"])["total_usd"].sum().to_dict()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    mdb_files = sorted(MDB_DIR.glob("*.mdb"))
    print(f"Found {len(mdb_files)} .mdb files")

    records: dict[str, dict[tuple, float]] = {}

    for mdb_path in mdb_files:
        file_date = parse_file_date(mdb_path.stem)
        if file_date is None:
            print(f"  [SKIP] Cannot parse date: {mdb_path.name}")
            continue

        col_label = file_date.strftime("%m/%Y")
        print(f"Processing {mdb_path.name}  ->  {col_label}")

        df = read_raw(mdb_path)
        if df is None or df.empty:
            records[col_label] = {}
            continue

        records[col_label] = aggregate(df, file_date)

    # --- Impute missing quarters ---
    for col_label, mdb_name, imputed_date in MISSING_QUARTERS:
        mdb_path = MDB_DIR / mdb_name
        print(f"Imputing {col_label} from {mdb_name} (date: {imputed_date})")
        df = read_raw(mdb_path)
        records[col_label] = aggregate(df, imputed_date) if df is not None else {}

    # --- Build output DataFrame ---
    all_keys = sorted({k for col in records.values() for k in col})
    all_cols = sorted(records.keys(), key=col_to_date)

    index = pd.MultiIndex.from_tuples(all_keys, names=["Operacion", "Moneda"])
    result = pd.DataFrame(0.0, index=index, columns=all_cols)

    for col, key_map in records.items():
        for (op, mon), val in key_map.items():
            result.loc[(op, mon), col] = val

    result = result.fillna(0).sort_index()

    # TOTAL row
    total = pd.DataFrame(
        [result.sum()],
        index=pd.MultiIndex.from_tuples([("TOTAL", "")], names=["Operacion", "Moneda"]),
        columns=all_cols,
    )
    result = pd.concat([result, total])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_excel(OUTPUT_PATH)
    print(f"\nSaved -> {OUTPUT_PATH}")
    print(f"Shape: {result.shape}  ({result.shape[0]-1} operaciones x {result.shape[1]} trimestres)")


if __name__ == "__main__":
    main()
