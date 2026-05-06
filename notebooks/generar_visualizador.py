"""
Generador del Visualizador HTML con datos embebidos.
Lee visualizador_template.html, embebe los datos CSV, y genera visualizador.html.
Ejecutar: python notebooks/generar_visualizador.py
"""
import os, sys, json, re, csv as csv_mod

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.join(_HERE, '..')

VARS_DIR = os.path.join(ROOT, 'data', 'Variables Finales')
RAW_DIR  = os.path.join(ROOT, 'data', 'raw')
TEMPLATE = os.path.join(_HERE, 'visualizador_template.html')
OUTPUT   = os.path.join(_HERE, 'visualizador.html')

# ═══════════════════════════════════════════
# 1. LEER TEMPLATE
# ═══════════════════════════════════════════
print("Leyendo template...")
with open(TEMPLATE, 'r', encoding='utf-8') as f:
    html = f.read()

# ═══════════════════════════════════════════
# 2. EXTRAER ARCHIVOS DEL CATALOG Y DUMMIES
# ═══════════════════════════════════════════
print("Extrayendo archivos del catalogo...")

BLOCK_RE = re.compile(
    r"\{[^{}]*?file\s*:\s*'([^']*)'[^{}]*?dateCol\s*:\s*'([^']*)'[^{}]*?valCol\s*:\s*'([^']*)'",
    re.DOTALL
)

file_columns = {}  # filename → set of column names
for m in BLOCK_RE.finditer(html):
    fn, dc, vc = m.group(1), m.group(2), m.group(3)
    if fn not in file_columns:
        file_columns[fn] = set()
    file_columns[fn].add(dc)
    file_columns[fn].add(vc)

# PBI deflation uses 'periodo' and 'pbi_pesos_mm' from pbi_trimestral_usd_mep.csv
if 'pbi_trimestral_usd_mep.csv' in file_columns:
    file_columns['pbi_trimestral_usd_mep.csv'].add('periodo')
    file_columns['pbi_trimestral_usd_mep.csv'].add('pbi_pesos_mm')

# MEP deflation uses 'fecha' and 'mep' from brecha_cambiaria.csv (already in catalog)

print(f"  {len(file_columns)} archivos unicos encontrados en CATALOG/DUMMIES")

# ═══════════════════════════════════════════
# 3. LEER CSVs Y CONSTRUIR DATOS EMBEBIDOS
# ═══════════════════════════════════════════
print("\nLeyendo datos...")

def read_csv_cols(filepath, needed_cols):
    """Lee un CSV y devuelve datos columnares {col: [valores]}."""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv_mod.DictReader(f)
        # Strip whitespace from fieldnames (itcrm has trailing spaces)
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        # Match columns (also try stripped versions of needed_cols)
        col_map = {}
        for nc in needed_cols:
            nc_stripped = nc.strip()
            if nc_stripped in reader.fieldnames:
                col_map[nc] = nc_stripped
            elif nc in reader.fieldnames:
                col_map[nc] = nc

        if not col_map:
            print(f"    [!] Columnas no encontradas: {needed_cols}")
            print(f"    Disponibles: {reader.fieldnames[:10]}...")
            return None

        data = {nc: [] for nc in col_map}
        for row in reader:
            for orig_name, csv_name in col_map.items():
                val = row.get(csv_name, '')
                if val is None or val.strip() == '':
                    data[orig_name].append(None)
                    continue
                val = val.strip()
                try:
                    fval = float(val)
                    data[orig_name].append(round(fval, 4) if fval == fval else None)
                except (ValueError, TypeError):
                    data[orig_name].append(val)  # string value (e.g. gobierno_nombre)
    return data

embedded = {}
for filename, needed_cols in sorted(file_columns.items()):
    if filename.endswith(('.xlsx', '.xls')):
        continue  # handled after read_xlsx_cols is defined
    filepath = os.path.join(VARS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  [!] NO ENCONTRADO: {filename}")
        continue
    data = read_csv_cols(filepath, needed_cols)
    if data:
        n = len(next(iter(data.values())))
        embedded[filename] = data
        print(f"  [OK] {filename:60s} {n:>6} filas, {len(data)} cols")

# ── PBI (deflactor ÷PBI — se mantiene aunque el grupo PBI no esté en el catálogo) ──
pbi_path = os.path.join(VARS_DIR, 'pbi_constante_2004.csv')
if os.path.exists(pbi_path) and 'pbi_constante_2004.csv' not in embedded:
    data = read_csv_cols(pbi_path, {'fecha', 'pbi'})
    if data:
        embedded['pbi_constante_2004.csv'] = data
        print(f"  [OK] {'pbi_constante_2004.csv (deflector PBI)':60s} {len(data['fecha']):>6} filas")

# ── CER (deflactor) ──
cer_path = os.path.join(RAW_DIR, 'bcra', 'cer.csv')
if os.path.exists(cer_path):
    data = read_csv_cols(cer_path, {'fecha', 'cer'})
    if data:
        embedded['__cer__'] = data
        print(f"  [OK] {'CER (bcra/cer.csv)':60s} {len(data['fecha']):>6} filas")

# ── TIP ETF (deflactor IPC USA) ──
tip_path = os.path.join(RAW_DIR, 'global', 'tip_etf.csv')
if os.path.exists(tip_path):
    data = read_csv_cols(tip_path, {'fecha', 'tip_close'})
    if data:
        embedded['__tip__'] = data
        print(f"  [OK] {'TIP ETF (global/tip_etf.csv)':60s} {len(data['fecha']):>6} filas")

# ── XLSX con estructura tabular limpia ──
def read_xlsx_cols(filepath, needed_cols):
    """Lee un .xlsx/.xls con encabezados en fila 0 y devuelve datos columnares."""
    try:
        import pandas as pd
        fn = os.path.basename(filepath)
        # Elegir hoja según archivo
        if 'fiscal' in fn.lower():
            sheet = 'Unificado'
        else:
            xl = pd.ExcelFile(filepath)
            sheet = xl.sheet_names[0]
        df = pd.read_excel(filepath, sheet_name=sheet)
        available = list(df.columns)
        col_map = {nc: nc for nc in needed_cols if nc in available}
        if not col_map:
            print(f"    [!] Cols no encontradas en {fn}: {list(needed_cols)[:5]}")
            print(f"    Disponibles: {available[:8]}")
            return None
        data = {}
        for col in col_map:
            vals = []
            for v in df[col]:
                try:
                    import pandas as _pd
                    if _pd.isna(v):
                        vals.append(None)
                    elif hasattr(v, 'strftime'):
                        vals.append(str(v)[:10])
                    else:
                        fv = float(v)
                        vals.append(round(fv, 4) if fv == fv else None)
                except Exception:
                    vals.append(str(v) if v is not None else None)
            data[col] = vals
        return data
    except Exception as e:
        print(f"    [!] Error leyendo {os.path.basename(filepath)}: {e}")
        return None

# Procesar archivos xlsx referenciados en el CATALOG
xlsx_files = {fn for fn in file_columns if fn.endswith(('.xlsx', '.xls'))}
for filename in sorted(xlsx_files):
    filepath = os.path.join(VARS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  [!] NO ENCONTRADO: {filename}")
        continue
    data = read_xlsx_cols(filepath, file_columns[filename])
    if data:
        n = len(next(iter(data.values())))
        embedded[filename] = data
        print(f"  [OK] {filename:60s} {n:>6} filas, {len(data)} cols")

# ── Vencimientos 2Y desde xlsx transpuesto (filas=categorías, columnas=fechas) ──
venc_xlsx = os.path.join(VARS_DIR, 'vencimientos_2y_nuevo.xlsx')
if os.path.exists(venc_xlsx):
    try:
        import pandas as _pdv
        from datetime import datetime as _dtv
        df_v = _pdv.read_excel(venc_xlsx, sheet_name='Por Tipo y Moneda', header=None)
        raw_dates = [df_v.iloc[5, j] for j in range(1, df_v.shape[1]) if _pdv.notna(df_v.iloc[5, j])]
        n_d = len(raw_dates)

        def _parse_vdate(d):
            mm, yy = str(d).strip().split('/')
            return _dtv(int(yy), int(mm), 1)

        sidx = sorted(range(n_d), key=lambda i: _parse_vdate(str(raw_dates[i])))
        sdates = [_parse_vdate(str(raw_dates[i])).strftime('%Y-%m-%d') for i in sidx]

        def _venc_col(main, sub=None):
            t = str.maketrans('ÁÉÍÓÚáéíóúÑñ', 'AEIOUaeiouNn')
            s = re.sub(r'[^A-Z0-9\s]', ' ', main.strip().translate(t).upper())
            s = re.sub(r'_+', '_', re.sub(r'\s+', '_', s.strip())).lower()
            p = f'venc_{s}'
            if sub:
                if 'local' in sub.lower():     return f'{p}_local'
                if 'extranjera' in sub.lower(): return f'{p}_ext'
            return p

        vd = {'fecha': sdates}
        cur_main = None
        for ri in range(6, df_v.shape[0]):
            cell = df_v.iloc[ri, 0]
            if _pdv.isna(cell):
                continue
            lbl = str(cell)
            ml = lbl.strip()
            if not lbl.startswith('  '):
                cur_main = ml
                col = _venc_col(cur_main)
            else:
                col = _venc_col(cur_main, ml)
            rv = [df_v.iloc[ri, j + 1] for j in range(n_d)]
            cleaned = []
            for v in [rv[i] for i in sidx]:
                try:
                    cleaned.append(None if _pdv.isna(v) else (round(float(v), 4) if float(v) == float(v) else None))
                except Exception:
                    cleaned.append(None)
            vd[col] = cleaned

        embedded['vencimientos_2y_nuevo.csv'] = vd
        print(f"  [OK] {'vencimientos_2y_nuevo.xlsx (transpuesto)':60s} {len(sdates):>6} filas, {len(vd)-1} cols")
    except Exception as e:
        print(f"  [!] Error procesando vencimientos_2y_nuevo.xlsx: {e}")

print(f"\nTotal: {len(embedded)} archivos embebidos")

# ═══════════════════════════════════════════
# 4. SERIALIZAR DATOS
# ═══════════════════════════════════════════
print("Serializando datos...")
data_json = json.dumps(embedded, ensure_ascii=False, separators=(',', ':'))
print(f"  Payload JSON: {len(data_json) // 1024} KB")

# ═══════════════════════════════════════════
# 5. MODIFICAR EL HTML
# ═══════════════════════════════════════════
print("Parcheando HTML...")

# 5a. Inyectar EMBEDDED justo después de <script>
# Find the first <script> that contains PATHS
injection_point = "/* ── PATHS ── */"
inject_code = f"const EMBEDDED={data_json};\n\n/* ── PATHS ── */"
html = html.replace(injection_point, inject_code, 1)

# 5b-5e. El template ya maneja EMBEDDED directamente en loadFile/loadCER/loadTIP/loadDummy.
# No se requieren reemplazos de strings fragiles.

# ═══════════════════════════════════════════
# 6. EMBEBER DEPENDENCIAS (Plotly y SheetJS)
# ═══════════════════════════════════════════
print("Embebiendo librerias JS (si estan disponibles localmente)...")
plotly_path = os.path.join(_HERE, 'plotly.min.js')
if os.path.exists(plotly_path):
    with open(plotly_path, 'r', encoding='utf-8') as f:
        plotly_js = f.read()
    html = html.replace('<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>', f'<script>{plotly_js}</script>')
    print("  [OK] Plotly embebido.")

xlsx_path = os.path.join(_HERE, 'xlsx.full.min.js')
if os.path.exists(xlsx_path):
    with open(xlsx_path, 'r', encoding='utf-8') as f:
        xlsx_js = f.read()
    html = html.replace('<script src="https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js"></script>', f'<script>{xlsx_js}</script>')
    print("  [OK] SheetJS embebido.")

# ═══════════════════════════════════════════
# 7. ESCRIBIR OUTPUT
# ═══════════════════════════════════════════
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize(OUTPUT) // 1024
size_mb = size_kb / 1024
print(f"\n[OK] Visualizador generado: {OUTPUT}")
print(f"   {len(embedded)} archivos embebidos")
print(f"   Tamano: {size_kb} KB ({size_mb:.1f} MB)")
print(f"   Abrilo directo en el browser -- sin servidor necesario.")
