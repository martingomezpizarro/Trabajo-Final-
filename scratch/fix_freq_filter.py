"""
Modifica 02a y 02b para que descarten series con frecuencia nativa
inferior a mensual (Q, A). Solo se aceptan D, W, M.

Se inyecta un bloque de filtro justo antes de la llamada a
construir_variable() en la celda de carga del panel (Sección 4).
"""
import json

FREQ_FILTER_BLOCK = [
    "        # ── Filtro: frecuencia mínima mensual ──────────────────────────────────\n",
    "        _FREQ_ORD = {'D': 0, 'W': 1, 'M': 2, 'Q': 3, 'A': 4}\n",
    "        _MAX_FREQ = 2  # M = máxima frecuencia aceptada (menor granularidad)\n",
    "        _nombre_a = str(_row.get('Serie A', '') or '').strip()\n",
    "        _nombre_b = str(_row.get('Serie B', '') or '').strip()\n",
    "        _skip_freq = False\n",
    "        for _sname in [_nombre_a, _nombre_b]:\n",
    "            if not _sname or _sname in ('', '\\u2014', '-', 'nan'):\n",
    "                continue\n",
    "            if _sname in CATALOG_VIZ:\n",
    "                _meta_f = CATALOG_VIZ[_sname]\n",
    "                _freq_native = _meta_f.get('freq', 'D')\n",
    "                if 'sources' in _meta_f:\n",
    "                    _freq_native = min(\n",
    "                        [s['freq'] for s in _meta_f['sources']],\n",
    "                        key=lambda f: _FREQ_ORD.get(f, 99)\n",
    "                    )\n",
    "                if _FREQ_ORD.get(_freq_native, 0) > _MAX_FREQ:\n",
    "                    print(f'  \\u23ed\\ufe0f [{_i+1}] {_sname}: freq={_freq_native} > mensual \\u2192 descartada')\n",
    "                    _skip_freq = True\n",
    "                    break\n",
    "        if _skip_freq:\n",
    "            continue\n",
    "\n",
]

# Línea que identifica dónde insertar el bloque (justo antes)
TRIGGER = "construir_variable(_row"

for nb_path in [
    'notebooks/02a_analisis_basico.ipynb',
    'notebooks/02b_analisis_completo.ipynb',
]:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    modified = False
    for c in nb['cells']:
        if c['cell_type'] != 'code':
            continue
        src = c['source']
        if not src:
            continue

        # Buscar la celda que contiene construir_variable(_row
        full = ''.join(src)
        if TRIGGER not in full:
            continue

        # Ya tiene el filtro inyectado?
        if '_skip_freq' in full:
            print(f'  {nb_path}: filtro ya presente, saltando.')
            continue

        # Encontrar la línea con construir_variable e insertar antes
        new_src = []
        for line in src:
            if TRIGGER in line:
                new_src.extend(FREQ_FILTER_BLOCK)
            new_src.append(line)
        c['source'] = new_src
        modified = True
        print(f'  {nb_path}: filtro de frecuencia inyectado.')
        break  # solo la primera celda que matchea

    if modified:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
    else:
        print(f'  {nb_path}: sin cambios.')

print('\nListo.')
