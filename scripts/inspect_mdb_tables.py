"""
inspect_mdb_tables.py

Investiga TODAS las tablas disponibles en cada archivo .mdb del SIGADE
para identificar fuentes de diferencia con los graficos oficiales de:
  https://www.argentina.gob.ar/economia/finanzas/graficos-deuda

Para cada .mdb muestra:
  - Nombre de cada tabla
  - Numero de filas
  - Columnas de tipo saldo/dolares encontradas
  - Suma de la columna saldo en dolares
  - Comparacion con el total que extrajimos en build_saldo_sigade.py

Output: data/processed/inspeccion_mdb.csv
"""

import re
import warnings
from pathlib import Path
from datetime import date

import pandas as pd
import pyodbc

warnings.filterwarnings("ignore", category=UserWarning)

MDB_DIR     = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\basesingade deuda")
SIGADE_PATH = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed\saldo_deuda_sigade.xlsx")
OUTPUT_CSV  = Path(r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed\inspeccion_mdb.csv")

# These are the 3 table types we DO read in build_saldo_sigade
READ_KEYWORDS = [
    ["NORMAL"],
    ["REESTRUCTURAR"],
    ["CANJE"],
    ["SALDOS"],   # 2007-era aggregate table
]

SALDO_KEYWORDS = ["saldo", "dolares", "dólares", "monto"]

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


def is_table_we_read(table_name: str) -> bool:
    tu = table_name.upper()
    for kws in READ_KEYWORDS:
        if all(k in tu for k in kws):
            return True
    return False


def get_saldo_col(cols: list[str]) -> str | None:
    """Pick the best 'saldo en dolares' column."""
    for c in cols:
        cl = c.lower()
        if "saldo" in cl and ("dolar" in cl or "d\xf3lar" in cl):
            return c
    for c in cols:
        cl = c.lower()
        if "monto" in cl and "dolar" in cl:
            return c
    for c in cols:
        if any(k in c.lower() for k in SALDO_KEYWORDS):
            return c
    return None


def inspect_mdb(mdb_path: Path) -> list[dict]:
    conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};' + f'DBQ={mdb_path};'
    try:
        conn = pyodbc.connect(conn_str)
    except Exception as e:
        print(f"  [WARN] Cannot connect {mdb_path.name}: {e}")
        return []

    cursor = conn.cursor()
    all_tables = [r.table_name for r in cursor.tables(tableType="TABLE") if "~" not in r.table_name]

    records = []
    for table in all_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            row_count = cursor.fetchone()[0]
        except Exception:
            row_count = -1

        try:
            cursor.execute(f"SELECT * FROM [{table}] WHERE 1=0")
            cols = [d[0] for d in cursor.description]
        except Exception:
            cols = []

        saldo_col = get_saldo_col(cols)
        total_usd = None
        if saldo_col:
            try:
                cursor.execute(f"SELECT SUM([{saldo_col}]) FROM [{table}]")
                val = cursor.fetchone()[0]
                total_usd = float(val) if val is not None else None
            except Exception:
                total_usd = None

        we_read = is_table_we_read(table)
        records.append({
            "table":       table,
            "we_read":     we_read,
            "row_count":   row_count,
            "saldo_col":   saldo_col or "",
            "total_usd":   total_usd,
            "total_mmusd": round(total_usd / 1e6, 1) if total_usd else None,
            "all_cols":    "; ".join(cols),
        })

    conn.close()
    return records


def load_our_totals() -> dict[str, float]:
    """Returns dict: period (MM/YYYY) -> our extracted total in million USD."""
    try:
        df = pd.read_excel(SIGADE_PATH, sheet_name="A.1", skiprows=7, index_col=0)
    except Exception as e:
        print(f"[WARN] Could not read {SIGADE_PATH.name}: {e}")
        return {}

    total_row = None
    for label in df.index:
        if "DEUDA BRUTA TOTAL" in str(label):
            total_row = df.loc[label]
            break

    if total_row is None:
        return {}

    result = {}
    for col, val in total_row.items():
        c = str(col).strip()
        if re.match(r"^\d{2}/\d{4}$", c) and pd.notna(val):
            result[c] = float(val)
    return result


# ---------------------------------------------------------------------------

def main():
    our_totals = load_our_totals()
    print(f"Loaded our totals for {len(our_totals)} periods from {SIGADE_PATH.name}")

    mdb_files = sorted(MDB_DIR.glob("*.mdb"))
    print(f"Inspecting {len(mdb_files)} .mdb files...\n")

    all_records = []
    comparison_rows = []

    for mdb_path in mdb_files:
        file_date = parse_file_date(mdb_path.stem)
        if file_date is None:
            continue
        period = file_date.strftime("%m/%Y")

        print(f"--- {mdb_path.name}  ({period}) ---")
        records = inspect_mdb(mdb_path)

        sum_read    = 0.0
        sum_unread  = 0.0
        sum_all     = 0.0

        for r in records:
            r["file"]   = mdb_path.name
            r["period"] = period
            all_records.append(r)

            usd_str = f"  {r['total_mmusd']:>10,.1f} M" if r["total_mmusd"] is not None else ""
            read_flag = "[READ]  " if r["we_read"] else "[SKIP]  "
            print(f"  {read_flag}{r['table']:<60} rows={r['row_count']:>5}{usd_str}")

            if r["total_usd"] is not None:
                val_m = r["total_usd"] / 1e6
                sum_all += val_m
                if r["we_read"]:
                    sum_read += val_m
                else:
                    sum_unread += val_m

        our = our_totals.get(period)
        our_str = f"{our:,.1f}" if our is not None else "N/A"
        print(f"  -> Sum of READ tables (saldo cols): {sum_read:,.1f} M")
        print(f"  -> Sum of SKIP tables (saldo cols): {sum_unread:,.1f} M")
        print(f"  -> Our extracted total (A.1):       {our_str} M")
        if our is not None:
            diff = sum_read - our
            print(f"  -> Diff (read - ours):              {diff:,.1f} M")
        print()

        comparison_rows.append({
            "period":            period,
            "file":              mdb_path.name,
            "sum_read_mmusd":    round(sum_read,   1),
            "sum_unread_mmusd":  round(sum_unread, 1),
            "our_total_mmusd":   round(our, 1) if our else None,
            "diff_mmusd":        round(sum_read - our, 1) if our else None,
        })

    # Save full table inspection
    df_all = pd.DataFrame(all_records)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Full inspection saved -> {OUTPUT_CSV}")

    # Print comparison summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"{'Period':<10} {'Sum_Read':>12} {'Sum_Skip':>12} {'Our_Total':>12} {'Diff':>10}")
    print("-"*60)
    for row in sorted(comparison_rows, key=lambda r: col_to_date_str(r["period"])):
        p  = row["period"]
        sr = f"{row['sum_read_mmusd']:,.1f}" if row["sum_read_mmusd"] else "N/A"
        ss = f"{row['sum_unread_mmusd']:,.1f}" if row["sum_unread_mmusd"] is not None else "N/A"
        ou = f"{row['our_total_mmusd']:,.1f}" if row["our_total_mmusd"] else "N/A"
        di = f"{row['diff_mmusd']:,.1f}" if row["diff_mmusd"] is not None else "N/A"
        print(f"{p:<10} {sr:>12} {ss:>12} {ou:>12} {di:>10}")

    # Print tables found in SKIP that have significant saldo
    print("\nTables NOT READ that have significant saldo (> 100 M USD):")
    df_skip = df_all[(df_all["we_read"] == False) & (df_all["total_mmusd"].notna()) & (df_all["total_mmusd"] > 100)]
    if df_skip.empty:
        print("  None found.")
    else:
        for _, r in df_skip.iterrows():
            print(f"  {r['period']}  {r['table']:<60}  {r['total_mmusd']:,.1f} M")


def col_to_date_str(c: str) -> date:
    try:
        mm, yyyy = c.split("/")
        return date(int(yyyy), int(mm), 1)
    except Exception:
        return date(1900, 1, 1)


if __name__ == "__main__":
    main()
