"""
Rellena los trimestres faltantes en vencimientos_2y_sigade.xlsx usando el
archivo SIGADE del trimestre anterior: descarta vencimientos caidos en los
3 meses de diferencia y aplica la ventana de 2 años desde la fecha imputada.
"""

import warnings
from datetime import date
from pathlib import Path

import pandas as pd
import pyodbc

warnings.filterwarnings("ignore", category=UserWarning)

MDB_DIR    = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\basesingade deuda")
EXCEL_PATH = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed\vencimientos_2y_sigade.xlsx")

TIPO_DEUDA_ALIASES = ["Tipo de Deuda", "BOLETIN"]
FECHA_ALIASES      = ["Fecha de Servicio"]
PRINCIPAL_ALIASES  = [
    "Principal en dolares", "Principal en Dolares",
    "Principal en dólares", "Principal en Dólares", "Principal en D\xf3lares",
]
INTERES_ALIASES = [
    "Interes en dolares", "Interes en Dolares",
    "Interes en dólares", "Interes en Dólares", "Interes en D\xf3lares",
]

# Missing quarters: (col_label, source_mdb, imputed_date)
MISSING = [
    ("03/2009", MDB_DIR / "basesigade 2008-12-30.mdb",  date(2009, 3, 31)),
    ("03/2014", MDB_DIR / "basesigade 2013-31-12.mdb",  date(2014, 3, 31)),
    ("09/2014", MDB_DIR / "basesigade 2014-06-30.mdb",  date(2014, 9, 30)),
]


def pick_col(cols: list[str], aliases: list[str]) -> str | None:
    col_map = {c.lower(): c for c in cols}
    for a in aliases:
        if a in cols:
            return a
        if a.lower() in col_map:
            return col_map[a.lower()]
    return None


def find_vencim_table(tables: list[str]) -> str | None:
    for t in tables:
        if "VENCIM" in t.upper() and "NORMAL" in t.upper():
            return t
    return None


def read_raw_vencimientos(mdb_path: Path) -> pd.DataFrame | None:
    conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' + f'DBQ={mdb_path};'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    tables = [row.table_name for row in cursor.tables(tableType="TABLE")]
    vtable = find_vencim_table(tables)
    if vtable is None:
        print(f"  [WARN] No vencimientos table in {mdb_path.name}")
        conn.close()
        return None

    cursor.execute(f"SELECT * FROM [{vtable}] WHERE 1=0")
    actual_cols = [d[0] for d in cursor.description]

    col_tipo  = pick_col(actual_cols, TIPO_DEUDA_ALIASES)
    col_fecha = pick_col(actual_cols, FECHA_ALIASES)
    col_princ = pick_col(actual_cols, PRINCIPAL_ALIASES)
    col_int   = pick_col(actual_cols, INTERES_ALIASES)

    missing_c = [n for n, c in [("TipoDeuda", col_tipo), ("Fecha", col_fecha),
                                  ("Principal", col_princ), ("Interes", col_int)] if c is None]
    if missing_c:
        print(f"  [WARN] Missing cols {missing_c} in {mdb_path.name}. Available: {actual_cols}")
        conn.close()
        return None

    safe_cols = ", ".join(f"[{c}]" for c in [col_tipo, col_fecha, col_princ, col_int])
    df = pd.read_sql(f"SELECT {safe_cols} FROM [{vtable}]", conn)
    conn.close()

    df.columns = ["tipo_deuda", "fecha_serv", "principal_usd", "interes_usd"]
    df["fecha_serv"]    = pd.to_datetime(df["fecha_serv"], errors="coerce")
    df["principal_usd"] = pd.to_numeric(df["principal_usd"], errors="coerce").fillna(0)
    df["interes_usd"]   = pd.to_numeric(df["interes_usd"],   errors="coerce").fillna(0)
    return df


def compute_imputed_column(mdb_path: Path, imputed_date: date) -> dict[str, float]:
    """
    Reads source .mdb and returns aggregated Principal+Interest per Tipo de Deuda,
    keeping only vencimientos in [imputed_date, imputed_date + 2 years].
    """
    df = read_raw_vencimientos(mdb_path)
    if df is None or df.empty:
        return {}

    start  = pd.Timestamp(imputed_date)
    cutoff = start + pd.DateOffset(years=2)
    mask = (df["fecha_serv"] >= start) & (df["fecha_serv"] <= cutoff)
    df = df[mask].copy()

    if df.empty:
        return {}

    df["total_usd"] = df["principal_usd"] + df["interes_usd"]
    return df.groupby("tipo_deuda")["total_usd"].sum().to_dict()


def col_to_date(col: str) -> date:
    mm, yyyy = col.split("/")
    return date(int(yyyy), int(mm), 1)


def main():
    result = pd.read_excel(EXCEL_PATH, index_col=0)
    # Drop TOTAL row before adding columns; re-add at end
    has_total = "TOTAL" in result.index
    if has_total:
        result = result.drop("TOTAL")

    for col_label, mdb_path, imputed_date in MISSING:
        print(f"Computing {col_label} from {mdb_path.name} (imputed date: {imputed_date})")
        tipo_map = compute_imputed_column(mdb_path, imputed_date)

        # Add new tipos that don't yet exist as rows
        for tipo in tipo_map:
            if tipo not in result.index:
                result.loc[tipo] = 0.0

        col_data = pd.Series(0.0, index=result.index)
        for tipo, val in tipo_map.items():
            col_data[tipo] = val

        result[col_label] = col_data

    # Re-sort columns chronologically
    all_cols_sorted = sorted(result.columns, key=col_to_date)
    result = result[all_cols_sorted].fillna(0)
    result = result.sort_index()

    # Re-add TOTAL row
    result.loc["TOTAL"] = result.sum()

    result.to_excel(EXCEL_PATH)
    print(f"\nSaved -> {EXCEL_PATH}")
    print(f"Shape: {result.shape}")
    print("Columns:", list(result.columns))
    # Spot-check the 3 new columns
    for col_label, _, _ in MISSING:
        print(f"\n  {col_label}:")
        nonzero = result[col_label][result[col_label] > 0].sort_values(ascending=False)
        print(nonzero.to_string())


if __name__ == "__main__":
    main()
