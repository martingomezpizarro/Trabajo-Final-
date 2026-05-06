"""
Patch visualizador.html to add Simulator + Analysis tabs.
Inserts CSS, HTML structure, and JS engine for:
- SARIMA + GARCH time series simulation
- ADF & Phillips-Perron unit root tests
- ACF/PACF correlograms
- Interactive differencing
"""
import re, os

SRC = os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'visualizador.html')

# Read CSS patch
css_path = os.path.join(os.path.dirname(__file__), '_patch_css.txt')
html_path = os.path.join(os.path.dirname(__file__), '_patch_html.txt')
js_path = os.path.join(os.path.dirname(__file__), '_patch_js.txt')

with open(css_path, 'r', encoding='utf-8') as f:
    CSS_PATCH = f.read()
with open(html_path, 'r', encoding='utf-8') as f:
    HTML_PATCH = f.read()
with open(js_path, 'r', encoding='utf-8') as f:
    JS_PATCH = f.read()

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()

# 1) Insert CSS before </style>
html = html.replace('</style>', CSS_PATCH + '\n</style>', 1)

# 2) Wrap existing #main content: add tab bar, wrap explorer, add sim+analysis
# Find <div id="main"> and insert tab bar after it
html = html.replace(
    '<div id="main">',
    '<div id="main">\n' +
    ' <div id="main-tabs"><button class="mtab active" onclick="switchTab(\'explorer\')">📊 Explorador</button><button class="mtab" onclick="switchTab(\'simulator\')">🔧 Simulador</button><button class="mtab" onclick="switchTab(\'analysis\')">📐 Análisis</button></div>\n' +
    ' <div id="tab-explorer" class="tab-content active">',
    1
)

# Close the explorer tab div before </div> that closes #main, and add new tabs
# Find the closing </div> of #main (right before <script>)
html = html.replace(
    '</div>\n\n<script>',
    '</div>\n</div>\n' + HTML_PATCH + '\n</div>\n\n<script>',
    1
)

# 3) Insert JS before the closing </script>
html = html.replace('</script>\n</body></html>', JS_PATCH + '\n</script>\n</body></html>', 1)

# Backup and write
backup = SRC + '.bak'
if not os.path.exists(backup):
    import shutil
    shutil.copy2(SRC, backup)
    print(f"Backup: {backup}")

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Patch applied successfully!")
print(f"   File: {SRC}")
