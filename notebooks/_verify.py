"""Quick verification of generated visualizador.html"""
import os, json, re

path = os.path.join(os.path.dirname(__file__), 'visualizador.html')
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

checks = {
    'EMBEDDED injected':          'const EMBEDDED={' in html,
    'loadFile patched':           'const cols = EMBEDDED[filename]' in html,
    'CER patched':                "EMBEDDED['__cer__']" in html,
    'TIP patched':                "EMBEDDED['__tip__']" in html,
    'Dummy patched':              'EMBEDDED[d.file]' in html,
    'Old loadFile XHR gone':      'const text = await xhrGet(path);\n  dataCache[path] = parseCSV(text)' not in html,
    'Old dummy XHR gone':         "const text = await xhrGet(path);\n  const parsed = parseCSV(text);" not in html,
    'parseCSV still present':     'function parseCSV' in html,
    'extractSeries still present':'function extractSeries' in html,
    'resample still present':     'function resample' in html,
    'CATALOG present':            'const CATALOG' in html,
    'DUMMIES present':            'const DUMMIES' in html,
}

print("=== HTML INTEGRITY CHECKS ===")
all_pass = True
for name, ok in checks.items():
    status = 'PASS' if ok else 'FAIL'
    if not ok: all_pass = False
    print(f'  [{status}] {name}')

size_mb = os.path.getsize(path) / 1024 / 1024
print(f'\n  File size: {size_mb:.1f} MB')

# Verify data integrity
m = re.search(r'const EMBEDDED=(\{.*?\});\n\n/\* ', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print(f'  Embedded files: {len(data)}')
    for k in sorted(data.keys()):
        cols = list(data[k].keys())
        n = len(data[k][cols[0]])
        print(f'    {k[:60]:60s} {n:>6} rows  cols={cols}')
else:
    print('  FAIL: Could not parse EMBEDDED data!')
    all_pass = False

print(f'\n{"ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED"}')
