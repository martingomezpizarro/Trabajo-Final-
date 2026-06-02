"""
Convierte los 3 Excel del BCRA movidos a 'data/Variables Finales/' a los CSV
que consume el visualizador, reproduciendo columnas/formatos existentes:
  - ITCRMSerie.xlsx  -> data/Variables Finales/itcrm_diario.csv
  - diar_cer.xls     -> data/raw/bcra/cer.csv         (el generador lee CER de raw)
  - series.xlsm      -> depositos_usd_totales.csv / depositos_usd_residentes.csv /
                        depositos_usd_secprivnofin.csv / prestamos_privados_usd_q.csv
Sólo se usa la serie diaria ('D') de series.xlsm (hay también PM/VFM/VPM apiladas).
"""
import os, csv, warnings
import pandas as pd
warnings.filterwarnings('ignore')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VF   = os.path.join(ROOT, 'data', 'Variables Finales')
RAW  = os.path.join(ROOT, 'data', 'raw', 'bcra')


def fmt_date(s):
    return pd.to_datetime(s).dt.strftime('%Y-%m-%d')


# ── 1. ITCRM ───────────────────────────────────────────────
def conv_itcrm():
    src = os.path.join(VF, 'ITCRMSerie.xlsx')
    df = pd.read_excel(src, sheet_name='ITCRM y bilaterales', header=1)
    df = df.rename(columns={df.columns[0]: 'Periodo'})
    df = df[pd.to_datetime(df['Periodo'], errors='coerce').notna()].copy()
    df['Periodo'] = fmt_date(df['Periodo'])
    out = os.path.join(VF, 'itcrm_diario.csv')
    df.to_csv(out, index=False, encoding='utf-8')
    print(f"  [OK] itcrm_diario.csv          {len(df):>6} filas  ({df['Periodo'].iloc[0]} -> {df['Periodo'].iloc[-1]})")


# ── 2. CER ─────────────────────────────────────────────────
def conv_cer():
    src = os.path.join(VF, 'diar_cer.xls')
    rows = []
    import xlrd
    b = xlrd.open_workbook(src); s = b.sheet_by_index(0)
    for i in range(s.nrows):
        a = s.cell_value(i, 0); v = s.cell_value(i, 1)
        if a in ('', None):
            continue
        ct = s.cell_type(i, 0)
        try:
            if ct == 3:  # XL_CELL_DATE
                t = xlrd.xldate_as_tuple(a, b.datemode)
                ds = f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d}"
            else:
                d = None
                for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                    try:
                        from datetime import datetime
                        d = datetime.strptime(str(a).strip(), fmt); break
                    except ValueError:
                        continue
                if d is None:
                    continue
                ds = d.strftime('%Y-%m-%d')
            fv = float(v)
        except (ValueError, TypeError):
            continue
        rows.append((ds, fv))
    out = os.path.join(RAW, 'cer.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['fecha', 'cer']); w.writerows(rows)
    print(f"  [OK] raw/bcra/cer.csv          {len(rows):>6} filas  ({rows[0][0]} -> {rows[-1][0]})")


# ── 3. Depósitos y Préstamos USD (serie diaria 'D') ────────
def _load_d(sheet, tipo_idx):
    df = pd.read_excel(os.path.join(VF, 'series.xlsm'), sheet_name=sheet,
                       header=None, skiprows=9)
    df = df[pd.to_datetime(df[0], errors='coerce').notna()].copy()
    df = df[df[tipo_idx] == 'D'].copy()
    df[0] = fmt_date(df[0])
    return df


def conv_series_xlsm():
    dep = _load_d('DEPOSITOS', 30)   # tipo de serie en col AE (idx 30)
    specs = [
        ('depositos_usd_totales.csv',     'depositos_usd_z',             25),  # col Z  - Dólares Totales
        ('depositos_usd_residentes.csv',  'depositos_usd_residentes_aa', 26),  # col AA - Dólares Sector Privado
        ('depositos_usd_secprivnofin.csv','depositos_usd_aa',            26),  # col AA - idem (duplicado histórico)
    ]
    for fname, colname, idx in specs:
        sub = dep[[0, idx]].copy(); sub.columns = ['fecha', colname]
        sub = sub.dropna(subset=[colname])
        sub.to_csv(os.path.join(VF, fname), index=False, encoding='utf-8')
        print(f"  [OK] {fname:30s} {len(sub):>6} filas  (last {sub['fecha'].iloc[-1]}={sub[colname].iloc[-1]})")

    pre = _load_d('PRESTAMOS', 21)   # tipo de serie en col V (idx 21)
    sub = pre[[0, 16]].copy(); sub.columns = ['fecha', 'prestamos_privados_usd_q']  # col Q - Total Dólares
    sub = sub.dropna(subset=['prestamos_privados_usd_q'])
    sub.to_csv(os.path.join(VF, 'prestamos_privados_usd_q.csv'), index=False, encoding='utf-8')
    print(f"  [OK] {'prestamos_privados_usd_q.csv':30s} {len(sub):>6} filas  (last {sub['fecha'].iloc[-1]}={sub['prestamos_privados_usd_q'].iloc[-1]})")


if __name__ == '__main__':
    print("Convirtiendo Excels del BCRA...")
    conv_itcrm()
    conv_cer()
    conv_series_xlsm()
    print("Listo.")
