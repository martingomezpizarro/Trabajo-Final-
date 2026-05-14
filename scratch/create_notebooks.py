"""
Script para crear las notebooks 02a y 02b a partir de las celdas 0-14
del notebook 02_modelos_regresion.ipynb.

- 02a_analisis_basico.ipynb: copia celdas 0-14 (base) + celdas 15-47 (modelos)
  con título adaptado.
- 02b_analisis_completo.ipynb: copia solo celdas 0-14 (base) con título adaptado
  + celda placeholder para las secciones nuevas.
"""
import json
import copy
import sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

NB_DIR = Path(__file__).parent.parent / 'notebooks'
SRC = NB_DIR / '02_modelos_regresion.ipynb'

with open(SRC, 'r', encoding='utf-8') as f:
    nb_orig = json.load(f)

cells_orig = nb_orig['cells']
metadata_orig = nb_orig.get('metadata', {})
nbformat = nb_orig.get('nbformat', 4)
nbformat_minor = nb_orig.get('nbformat_minor', 5)

# ── Celdas base: 0-14 ─────────────────────────────────────────────────────
base_cells = [copy.deepcopy(c) for c in cells_orig[:15]]  # cells 0..14

# ══════════════════════════════════════════════════════════════════════════
# NOTEBOOK A: Análisis Básico Aislado
# ══════════════════════════════════════════════════════════════════════════
cells_a = copy.deepcopy(base_cells)

# Adaptar título (Cell 0)
cells_a[0]['source'] = [
    "# 📊 Análisis Básico Aislado de Modelos de Series de Tiempo\n",
    "## Riesgo País Argentino — ARDL · VAR · VECM\n",
    "\n",
    "**Flujo de trabajo:**\n",
    "1. Leer `Variables Regresivas/analisis_series_*.csv` (generado desde el visualizador)\n",
    "2. Parsear el `CATALOG` de `visualizador_template.html` para obtener rutas y columnas de cada serie\n",
    "3. Cargar datos desde `data/Variables Finales/` con la misma lógica que el visualizador\n",
    "4. Ejecutar pre-tests (ADF/KPSS)\n",
    "5. Estimar ARDL · VAR · VECM sobre **todas las combinaciones posibles** de variables explicativas\n",
    "6. Visualizar coeficientes, p-values y significancia por variable y modelo\n",
    "7. Identificar el mejor modelo y las variables más explicativas\n",
    "\n",
    "---\n",
    "**Solo editar la Sección 3 (CONFIGURACIÓN).**\n",
    "\n",
    "> 📝 **Guía de referencia**: `docs/guia_02a_analisis_basico.md`"
]

# Copiar celdas 15-47 (secciones 7-Apéndice B) del original
cells_modelos = [copy.deepcopy(c) for c in cells_orig[15:48]]
cells_a.extend(cells_modelos)

nb_a = {
    'nbformat': nbformat,
    'nbformat_minor': nbformat_minor,
    'metadata': copy.deepcopy(metadata_orig),
    'cells': cells_a
}

out_a = NB_DIR / '02a_analisis_basico.ipynb'
with open(out_a, 'w', encoding='utf-8') as f:
    json.dump(nb_a, f, ensure_ascii=False, indent=1)
print(f'✅ Creado: {out_a}  ({len(cells_a)} celdas)')


# ══════════════════════════════════════════════════════════════════════════
# NOTEBOOK B: Análisis Completo Integrado
# ══════════════════════════════════════════════════════════════════════════
cells_b = copy.deepcopy(base_cells)

# Adaptar título (Cell 0)
cells_b[0]['source'] = [
    "# 🔬 Análisis Completo Integrado — Jerarquía de Exogeneidad\n",
    "## Riesgo País Argentino — ARDL → VAR → VECM\n",
    "\n",
    "**Enfoque:**\n",
    "1. Leer las variables del CSV de análisis\n",
    "2. **ARDL exhaustivo**: probar TODAS las variables como dependientes e independientes\n",
    "3. Construir un **ranking de exogeneidad** (p-values, BIC, R² adj)\n",
    "4. **VAR**: verificar el ranking con Granger, IRF y FEVD\n",
    "5. **VECM**: captar la dinámica de largo plazo (cointegración)\n",
    "6. Síntesis: identificar push factors vs pull factors idiosincráticos\n",
    "\n",
    "---\n",
    "**Solo editar la Sección 3 (CONFIGURACIÓN).**\n",
    "\n",
    "> 📝 **Guía de referencia**: `docs/guia_02b_analisis_completo.md`"
]

# Adaptar sección de configuración (Cell 6) — agregar parámetros adicionales
# Encontrar la celda de configuración (Cell 6 en el original, index 6 en base_cells)
config_cell = cells_b[6]
config_src = ''.join(config_cell['source']) if isinstance(config_cell['source'], list) else config_cell['source']

# Agregar configuración adicional al final
extra_config = """
# ── Análisis de Exogeneidad (exclusivo de esta notebook) ──────────────────

# Pesos para el score de exogeneidad compuesto
W_PVALUE = 0.35   # Peso del p-value promedio cuando actúa como X
W_R2INV  = 0.25   # Peso del R² invertido cuando actúa como Y
W_FREQ   = 0.25   # Peso de la frecuencia de significancia como X
W_BIC    = 0.15   # Peso de la parsimonia (BIC) de modelos donde participa

# ¿Probar TODAS las variables como dependientes? (lento pero completo)
TODAS_COMO_DEPENDIENTE = True   # True = completo, False = solo EMBI como Y

# Lags para prewhitening
MAX_AR_ORDER = 4   # Orden máximo AR
MAX_MA_ORDER = 4   # Orden máximo MA

# Top N variables para VECM (usar las mejor rankeadas)
TOP_N_VECM = 5

print('✅ Configuración extendida guardada.')
"""

if isinstance(config_cell['source'], list):
    config_cell['source'].append(extra_config)
else:
    config_cell['source'] += extra_config

# Agregar celdas placeholder para las secciones nuevas
nuevas_secciones = [
    # ── Sección 7: ARDL Exhaustivo ──
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            "## 7. Análisis ARDL Exhaustivo — Jerarquía de Exogeneidad\n",
            "\n",
            "### 7.1 Prewhitening Box-Jenkins (todas las combinaciones Y/X)\n",
            "\n",
            "> Para cada par `(Y_i, X_j)`: ajustar ARMA a X_j, filtrar Y_i, calcular CCF.\n",
            "> Esto genera los lags óptimos para cada combinación de variables."
        ]
    },
    {
        'cell_type': 'code',
        'metadata': {},
        'source': [
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "# 7.1  Prewhitening BJ: todas las combinaciones (Y_i, X_j)\n",
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "from statsmodels.tsa.arima.model import ARIMA\n",
            "from statsmodels.tsa.stattools import ccf\n",
            "\n",
            "print('═'*70)\n",
            "print('7.1  PREWHITENING BOX-JENKINS — TODAS LAS COMBINACIONES')\n",
            "print('═'*70)\n",
            "\n",
            "ALL_VARS = [Y_SAFE] + X_SAFE_EST if not TODAS_COMO_DEPENDIENTE else list(df_safe.columns)\n",
            "\n",
            "bj_lags = {}  # {(y_var, x_var): {'lags': [...], 'ccf_max': float, 'arma_order': (p,q)}}\n",
            "\n",
            "# TODO: Implementar loop de prewhitening para todas las combinaciones\n",
            "# Ver guía: docs/guia_02b_analisis_completo.md, Sección 7.1\n",
            "\n",
            "print(f'\\nPares analizados: {len(bj_lags)}')\n"
        ],
        'outputs': [],
        'execution_count': None
    },
    # ── 7.2 Estimaciones ARDL ──
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            "### 7.2 Estimaciones ARDL — Todas las combinaciones posibles\n",
            "\n",
            "> Cada variable se prueba como dependiente. Para cada Y_i, se estiman ARDL\n",
            "> con todas las combinaciones de las demás variables como explicativas."
        ]
    },
    {
        'cell_type': 'code',
        'metadata': {},
        'source': [
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "# 7.2  Estimaciones ARDL exhaustivas\n",
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "\n",
            "print('═'*70)\n",
            "print('7.2  ESTIMACIONES ARDL — TODAS LAS VARIABLES COMO DEPENDIENTES')\n",
            "print('═'*70)\n",
            "\n",
            "df_ardl_full = pd.DataFrame()\n",
            "\n",
            "# TODO: Implementar estimación ARDL exhaustiva\n",
            "# Ver guía: docs/guia_02b_analisis_completo.md, Sección 7.2\n",
            "\n",
            "print(f'\\nModelos estimados: {len(df_ardl_full)}')\n"
        ],
        'outputs': [],
        'execution_count': None
    },
    # ── 7.3 Jerarquía de Exogeneidad ──
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            "### 7.3 Construcción de la Jerarquía de Exogeneidad\n",
            "\n",
            "> Score compuesto: p-value promedio como X × R² invertido como Y × frecuencia de significancia × parsimonia BIC.\n",
            "> Mayor score = variable más exógena."
        ]
    },
    {
        'cell_type': 'code',
        'metadata': {},
        'source': [
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "# 7.3  Jerarquía de Exogeneidad\n",
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "\n",
            "def calcular_score_exogeneidad(df_ardl_full, variables, pesos):\n",
            "    \"\"\"\n",
            "    Calcula score de exogeneidad compuesto.\n",
            "    Mayor score = más exógena.\n",
            "    \"\"\"\n",
            "    scores = {}\n",
            "    for v in variables:\n",
            "        # 1. P-value promedio cuando actúa como X\n",
            "        mask_as_x = df_ardl_full['x_vars'].apply(lambda xv: v in xv if isinstance(xv, (list, tuple)) else False)\n",
            "        if mask_as_x.any():\n",
            "            pvals_as_x = []\n",
            "            for _, row in df_ardl_full[mask_as_x].iterrows():\n",
            "                xv = list(row['x_vars'])\n",
            "                if v in xv:\n",
            "                    idx = xv.index(v)\n",
            "                    pvs = row.get('pvalues', [])\n",
            "                    if isinstance(pvs, (list, tuple)) and idx < len(pvs):\n",
            "                        pvals_as_x.append(pvs[idx])\n",
            "            avg_pvalue_as_x = np.mean(pvals_as_x) if pvals_as_x else 1.0\n",
            "        else:\n",
            "            avg_pvalue_as_x = 1.0\n",
            "        \n",
            "        # 2. R² promedio como Y\n",
            "        mask_as_y = df_ardl_full['y_var'] == v\n",
            "        avg_r2_as_y = df_ardl_full.loc[mask_as_y, 'R2_adj'].mean() if mask_as_y.any() else 0\n",
            "        \n",
            "        # 3. Frecuencia de significancia como X\n",
            "        freq_sig = (sum(1 for p in pvals_as_x if p < NIVEL_SIG) / len(pvals_as_x)) if 'pvals_as_x' in dir() and pvals_as_x else 0\n",
            "        \n",
            "        # 4. BIC promedio como X\n",
            "        avg_bic = df_ardl_full.loc[mask_as_x, 'BIC'].mean() if mask_as_x.any() else 0\n",
            "        \n",
            "        scores[v] = (\n",
            "            pesos['pvalue'] * (1 - avg_pvalue_as_x) +\n",
            "            pesos['r2inv']  * (1 - avg_r2_as_y) +\n",
            "            pesos['freq']   * freq_sig +\n",
            "            pesos['bic']    * (1 / (1 + abs(avg_bic)))\n",
            "        )\n",
            "    return pd.Series(scores).sort_values(ascending=False)\n",
            "\n",
            "\n",
            "pesos = {'pvalue': W_PVALUE, 'r2inv': W_R2INV, 'freq': W_FREQ, 'bic': W_BIC}\n",
            "\n",
            "if not df_ardl_full.empty:\n",
            "    ranking_exogeneidad = calcular_score_exogeneidad(\n",
            "        df_ardl_full, list(df_safe.columns), pesos\n",
            "    )\n",
            "    print('\\n' + '═'*70)\n",
            "    print('  RANKING DE EXOGENEIDAD')\n",
            "    print('═'*70)\n",
            "    for i, (v, s) in enumerate(ranking_exogeneidad.items(), 1):\n",
            "        label = COL_LABEL.get(v, v)\n",
            "        print(f'  [{i:>2}]  {label:<55}  score={s:.4f}')\n",
            "    print('═'*70)\n",
            "    \n",
            "    # Gráfico de ranking\n",
            "    fig, ax = plt.subplots(figsize=(10, max(4, len(ranking_exogeneidad) * 0.4)))\n",
            "    labels = [COL_LABEL.get(v, v)[:40] for v in ranking_exogeneidad.index]\n",
            "    colors = ['#2196F3' if v != Y_SAFE else '#d62728' for v in ranking_exogeneidad.index]\n",
            "    ax.barh(range(len(labels)), ranking_exogeneidad.values, color=colors)\n",
            "    ax.set_yticks(range(len(labels)))\n",
            "    ax.set_yticklabels(labels, fontsize=8)\n",
            "    ax.set_xlabel('Score de Exogeneidad')\n",
            "    ax.set_title('Ranking de Exogeneidad (mayor = más exógena)')\n",
            "    ax.invert_yaxis()\n",
            "    plt.tight_layout()\n",
            "    plt.show()\n",
            "else:\n",
            "    print('⚠️  Sin resultados ARDL. Ejecutar sección 7.2 primero.')\n",
            "    ranking_exogeneidad = pd.Series(dtype=float)\n"
        ],
        'outputs': [],
        'execution_count': None
    },
    # ── 7.4 Validación cruzada ──
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            "### 7.4 Validación cruzada del ranking\n",
            "\n",
            "> Comparar ranking cuando Y=EMBI vs ranking global.\n",
            "> Test de Granger bidireccional para top variables."
        ]
    },
    {
        'cell_type': 'code',
        'metadata': {},
        'source': [
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "# 7.4  Validación cruzada del ranking\n",
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "\n",
            "# TODO: Implementar validación cruzada\n",
            "# Ver guía: docs/guia_02b_analisis_completo.md, Sección 7.4\n",
            "\n",
            "print('Sección 7.4 pendiente de implementación.')\n"
        ],
        'outputs': [],
        'execution_count': None
    },
    # ── Sección 8: VAR ──
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            "## 8. Verificación VAR del Orden Jerárquico\n",
            "\n",
            "### 8.1 Selección del orden del VAR\n",
            "\n",
            "> Evaluar criterios AIC/BIC/HQ para seleccionar el orden óptimo."
        ]
    },
    {
        'cell_type': 'code',
        'metadata': {},
        'source': [
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "# 8.1-8.6  Verificación VAR\n",
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "from statsmodels.tsa.api import VAR as _VAR\n",
            "\n",
            "print('═'*70)\n",
            "print('8.  VERIFICACIÓN VAR DEL ORDEN JERÁRQUICO')\n",
            "print('═'*70)\n",
            "\n",
            "# TODO: Implementar secciones 8.1 a 8.6\n",
            "# Ver guía: docs/guia_02b_analisis_completo.md, Secciones 8.1-8.6\n",
            "\n",
            "ranking_var = pd.Series(dtype=float)\n",
            "print('Sección 8 pendiente de implementación.')\n"
        ],
        'outputs': [],
        'execution_count': None
    },
    # ── Sección 9: VECM ──
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            "## 9. Dinámica de Largo Plazo — VECM\n",
            "\n",
            "### 9.1 Test de Cointegración de Johansen\n",
            "\n",
            "> Usar las top N variables del ranking confirmado + EMBI."
        ]
    },
    {
        'cell_type': 'code',
        'metadata': {},
        'source': [
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "# 9.1-9.3  VECM — Dinámica de Largo Plazo\n",
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "from statsmodels.tsa.vector_ar.vecm import coint_johansen, VECM as _VECM\n",
            "\n",
            "print('═'*70)\n",
            "print('9.  DINÁMICA DE LARGO PLAZO — VECM')\n",
            "print('═'*70)\n",
            "\n",
            "# TODO: Implementar secciones 9.1 a 9.3\n",
            "# Ver guía: docs/guia_02b_analisis_completo.md, Secciones 9.1-9.3\n",
            "\n",
            "print('Sección 9 pendiente de implementación.')\n"
        ],
        'outputs': [],
        'execution_count': None
    },
    # ── Sección 10: Síntesis ──
    {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            "## 10. Síntesis y Conclusiones\n",
            "\n",
            "> Tabla resumen final con ranking de exogeneidad, relaciones de largo plazo,\n",
            "> y clasificación push factors vs pull factors idiosincráticos."
        ]
    },
    {
        'cell_type': 'code',
        'metadata': {},
        'source': [
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "# 10.  SÍNTESIS Y CONCLUSIONES\n",
            "# ═══════════════════════════════════════════════════════════════════════════\n",
            "\n",
            "print('═'*70)\n",
            "print('10.  SÍNTESIS Y CONCLUSIONES')\n",
            "print('═'*70)\n",
            "\n",
            "# TODO: Implementar sección 10\n",
            "# Ver guía: docs/guia_02b_analisis_completo.md, Sección 10\n",
            "\n",
            "print('Sección 10 pendiente de implementación.')\n"
        ],
        'outputs': [],
        'execution_count': None
    },
]

cells_b.extend(nuevas_secciones)

nb_b = {
    'nbformat': nbformat,
    'nbformat_minor': nbformat_minor,
    'metadata': copy.deepcopy(metadata_orig),
    'cells': cells_b
}

out_b = NB_DIR / '02b_analisis_completo.ipynb'
with open(out_b, 'w', encoding='utf-8') as f:
    json.dump(nb_b, f, ensure_ascii=False, indent=1)
print(f'✅ Creado: {out_b}  ({len(cells_b)} celdas)')

print('\n' + '='*70)
print('  RESUMEN')
print('='*70)
print(f'  02a_analisis_basico.ipynb    : {len(cells_a)} celdas (base 0-14 + modelos 15-47)')
print(f'  02b_analisis_completo.ipynb  : {len(cells_b)} celdas (base 0-14 + estructura nueva)')
print(f'  guia_02a_analisis_basico.md  : ✅')
print(f'  guia_02b_analisis_completo.md: ✅')
print('='*70)
