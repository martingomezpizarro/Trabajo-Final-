import sys, csv, json, shutil
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ── 1. Leer CSVs ────────────────────────────────────────────────────────────
def read_csv_columns(path, date_col, val_col):
    dates, vals = [], []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = row.get(date_col, '').strip()[:10]
            v = row.get(val_col, '').strip()
            if d and v:
                try:
                    vals.append(float(v))
                    dates.append(d)
                except ValueError:
                    pass
    return dates, vals

path_arg   = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\riesgos pais\riesgo_pais_arg.csv'
path_latam = r'c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\riesgos pais\embi_latam.csv'

dates_arg,   vals_arg   = read_csv_columns(path_arg,   'fecha', 'embi_arg')
dates_latam, vals_latam = read_csv_columns(path_latam, 'fecha', 'embi_latam')

print(f'ARG:   {len(dates_arg)} rows, {dates_arg[0]} → {dates_arg[-1]}')
print(f'LATAM: {len(dates_latam)} rows, {dates_latam[0]} → {dates_latam[-1]}')

# ── 2. Leer visualizador.html ────────────────────────────────────────────────
filepath = 'visualizador.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# ── 3. Encontrar exactamente dónde termina EMBEDDED ─────────────────────────
# The EMBEDDED object ends with }};  followed by \n\n/* ──
# From the diagnosis: EMBEDDED closes (};) at: 9483917
# Let's find the exact closing pattern
emb_idx   = content.find('const EMBEDDED')
cat_idx   = content.find('const CATALOG')

# The EMBEDDED section is between emb_idx and cat_idx
# It should end with }}; just before const CATALOG
# Find }};  right before const CATALOG
emb_section = content[emb_idx:cat_idx]
# The last character before /* ── ... const CATALOG should be }};\n\n
# Find the last }}; in the EMBEDDED section
last_close = emb_section.rfind('};')
print(f'Last "}};" in EMBEDDED section at offset {last_close} from EMBEDDED start')
print(f'Context: {repr(emb_section[last_close-10:last_close+10])}')

# Absolute position of the closing }; in content
abs_close = emb_idx + last_close + 2  # position right after the };
print(f'Insert point (after }}): absolute={abs_close}')
print(f'Content at insert: {repr(content[abs_close-5:abs_close+20])}')

# ── 4. Build new EMBEDDED entries ────────────────────────────────────────────
# Format: ,"filename":{"col1":[...],"col2":[...]}
emb_arg   = (f',\n"riesgo_pais_arg.csv":{{"fecha":{json.dumps(dates_arg, separators=(",",":"))}'
             f',"embi_arg":{json.dumps(vals_arg, separators=(",",":"))}}}')
emb_latam = (f',\n"embi_latam.csv":{{"fecha":{json.dumps(dates_latam, separators=(",",":"))}'
             f',"embi_latam":{json.dumps(vals_latam, separators=(",",":"))}}}')

# ── 5. Insert into EMBEDDED ─────────────────────────────────────────────────
# Insert BEFORE the closing }; of EMBEDDED
content = content[:abs_close-1] + emb_arg + emb_latam + content[abs_close-1:]

print(f'After EMBEDDED insert, length: {len(content)}')

# Verify the structure is intact
check_idx = content.find('const CATALOG')
check_emb = content.find('const EMBEDDED')
print(f'EMBEDDED still at: {check_emb}, CATALOG still at: {check_idx}')
print(f'Order OK: {check_emb < check_idx}')

# ── 6. Add CATALOG entries ──────────────────────────────────────────────────
catalog_block = """,

  /* ── RIESGO PAÍS ── */

  { grp:'Riesgo País (EMBI)', clr:'#f43f5e', subs:[
    { sub:'Argentina', items:[
      { id:'embi_arg', label:'EMBI Argentina (pb)', file:'riesgo_pais_arg.csv', dateCol:'fecha', valCol:'embi_arg', unit:'puntos básicos', freq:'D' }
    ]},
    { sub:'América Latina', items:[
      { id:'embi_latam', label:'EMBI LATAM (yield spread)', file:'embi_latam.csv', dateCol:'fecha', valCol:'embi_latam', unit:'%', freq:'D' }
    ]}
  ]}"""

# Find the CATALOG closing ];
cat_idx2 = content.find('const CATALOG')
# From the closing ];  — find ]; after catalog start
# The catalog ends with \n]; — find last ];\n before DUMMIES or next const
dummies_idx = content.find('const DUMMIES', cat_idx2)
if dummies_idx == -1:
    dummies_idx = content.find('\n];\n\n', cat_idx2)

print(f'DUMMIES/end at: {dummies_idx}')

# Find the ];\n just before DUMMIES
# Look for ];\n\n/* or ];\n\nconst
import re
# Find all occurrences of ];\n between catalog and dummies
pattern_end = content.rfind('\n];', cat_idx2, dummies_idx)
print(f'CATALOG ] close at: {pattern_end}')
print(f'Context: {repr(content[pattern_end-30:pattern_end+10])}')

# Insert catalog_block just before the final \n];
content = content[:pattern_end] + catalog_block + content[pattern_end:]

print(f'After CATALOG insert, length: {len(content)}')

# ── 7. Backup + save ────────────────────────────────────────────────────────
shutil.copy2(filepath, filepath + '.bak3')
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('\n✓ visualizador.html actualizado correctamente')
print('\nVerificación final:')
print(f'  "embi_arg" in CATALOG: {"embi_arg" in content[content.find("const CATALOG"):content.find("const DUMMIES")]}')
print(f'  "riesgo_pais_arg.csv" in EMBEDDED: {"riesgo_pais_arg.csv" in content[content.find("const EMBEDDED"):content.find("const CATALOG")]}')
print(f'  "embi_latam.csv" in EMBEDDED: {"embi_latam.csv" in content[content.find("const EMBEDDED"):content.find("const CATALOG")]}')
