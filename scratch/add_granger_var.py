import json

NB_PATH = 'notebooks/02b_analisis_completo.ipynb'

with open(NB_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find where to insert (after 8.2 code cell)
insert_idx = None
for i, c in enumerate(nb['cells']):
    src = ''.join(c.get('source', []))
    if '8.2  FEVD' in src and c['cell_type'] == 'code':
        insert_idx = i + 1
        break

if insert_idx is None:
    raise RuntimeError("Could not find cell 8.2 FEVD code")

# ── CELDA 8.3: Markdown ──
md_cell = {
    'cell_type': 'markdown',
    'metadata': {},
    'source': [
"### 8.3 Test de Causalidad de Granger en VAR\n",
"\n",
"> Para los mejores modelos VAR significativos (ruido blanco + estables + BIC < media),\n",
"> analizamos la causalidad de Granger bidireccional entre las variables explicativas y el EMBI."
    ]
}

# ── CELDA 8.3: Code ──
code_cell = {
    'cell_type': 'code',
    'metadata': {},
    'outputs': [],
    'execution_count': None,
    'source': [
"# ═══════════════════════════════════════════════════════════════════════════\n",
"# 8.3  TEST DE CAUSALIDAD DE GRANGER — TOP MODELOS VAR\n",
"# ═══════════════════════════════════════════════════════════════════════════\n",
"import pandas as pd\n",
"\n",
"print('═'*70)\n",
"print('8.3  TEST DE CAUSALIDAD DE GRANGER EN VAR (BIDIRECCIONAL)')\n",
"print('═'*70)\n",
"\n",
"if 'df_var_full' not in globals() or df_var_full.empty:\n",
"    print('⚠️  Sin modelos VAR. Ejecutar sección 8.1.')\n",
"else:\n",
"    # ── Filtrar: ruido blanco + estable + BIC < media ──────────────────\n",
"    _df_ok = df_var_full[\n",
"        (df_var_full['resid_ruido_blanco'] == True) &\n",
"        (df_var_full['stable'] == True)\n",
"    ].copy()\n",
"\n",
"    if not _df_ok.empty:\n",
"        _bic_mean = _df_ok['BIC'].mean()\n",
"        _df_good = _df_ok[_df_ok['BIC'] < _bic_mean].copy()\n",
"        if _df_good.empty:\n",
"            _df_good = _df_ok.copy()\n",
"        # Top 5 por BIC\n",
"        _df_good = _df_good.sort_values('BIC').head(5).reset_index(drop=True)\n",
"\n",
"        print(f'Evaluando {len(_df_good)} mejores modelos VAR estables con ruido blanco...\\n')\n",
"\n",
"        for _rank, _row in _df_good.iterrows():\n",
"            _ordered = list(_row['ordered_vars'])\n",
"            _p = int(_row['p_selected'])\n",
"            _df_v = df_safe[_ordered].dropna()\n",
"            \n",
"            _fit = _VAR_est(_df_v).fit(_p)\n",
"            \n",
"            print(f'\\n── Modelo {_rank+1}: BIC={_row[\"BIC\"]:.1f}  p={_p} ──')\n",
"            _granger_rows = []\n",
"            \n",
"            for _x in _row['x_vars']:\n",
"                _x_lbl = COL_LABEL.get(_x, _x)[:30]\n",
"                _y_lbl = COL_LABEL.get(Y_SAFE, Y_SAFE)[:30]\n",
"                \n",
"                # X causa a Y (Null: X NO causa Y)\n",
"                try:\n",
"                    _res_xy = _fit.test_causality(caused=Y_SAFE, causing=_x, kind='wald')\n",
"                    _pval_xy = _res_xy.pvalue\n",
"                    _sig_xy = '✅ Sí' if _pval_xy < 0.05 else '❌ No'\n",
"                except:\n",
"                    _pval_xy = np.nan\n",
"                    _sig_xy = 'Error'\n",
"                    \n",
"                # Y causa a X (Null: Y NO causa X)\n",
"                try:\n",
"                    _res_yx = _fit.test_causality(caused=_x, causing=Y_SAFE, kind='wald')\n",
"                    _pval_yx = _res_yx.pvalue\n",
"                    _sig_yx = '✅ Sí' if _pval_yx < 0.05 else '❌ No'\n",
"                except:\n",
"                    _pval_yx = np.nan\n",
"                    _sig_yx = 'Error'\n",
"                \n",
"                _granger_rows.append({\n",
"                    'Variable': _x_lbl,\n",
"                    'X → Y (p-val)': _pval_xy,\n",
"                    'Causa a Y?': _sig_xy,\n",
"                    'Y → X (p-val)': _pval_yx,\n",
"                    'Es causada por Y?': _sig_yx\n",
"                })\n",
"                \n",
"            _df_g = pd.DataFrame(_granger_rows)\n",
"            display(_df_g.round(4))\n",
"            \n",
"    else:\n",
"        print('⚠️  Ningún modelo VAR estable con ruido blanco disponible para Granger.')\n"
    ]
}

nb['cells'].insert(insert_idx, md_cell)
nb['cells'].insert(insert_idx + 1, code_cell)

with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Inserted Section 8.3 Granger Causality.")
