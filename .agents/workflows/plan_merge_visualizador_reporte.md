---
description: Plan detallado para mergear visualizador.html + server.py + reporte.html + 02a_analisis_basico.py
last_updated: 2026-05-25
audience: agentes IA menos inteligentes (ejecutar paso por paso, no improvisar)
---

# Objetivo

Integrar la salida del análisis básico (`02a_analisis_basico.py` → `outputs/analisis_basico/reporte.html`) dentro de `notebooks/visualizador.html` como una **nueva pestaña** ("📈 Análisis Básico"). Además, en la pestaña **Análisis** ya existente, al guardar análisis y descargar el CSV, se debe poder marcar **una sola fila como variable dependiente** (radio button); esa marca se propaga al CSV y `02a_analisis_basico.py` la usa como Y en lugar de la auto-detección por keywords.

# Archivos en juego (rutas absolutas relativas a la raíz del repo)

- `notebooks/visualizador_template.html` (SOURCE — editar acá; visualizador.html se regenera)
- `notebooks/visualizador.html` (GENERADO — 9.7 MB con datos embebidos; regenerar al final con `generar_visualizador.py`)
- `notebooks/generar_visualizador.py` (build step: template + CSVs → visualizador.html)
- `notebooks/server.py` (servidor HTTP local — ya sirve `outputs/analisis_basico/reporte.html`)
- `notebooks/02a_analisis_basico.py` (script de análisis — produce `outputs/analisis_basico/reporte.html` y PNGs)
- `outputs/analisis_basico/reporte.html` (salida — no editar a mano, se regenera)
- `notebooks/Variables Regresivas/analisis_series_*.csv` (input del .py, output del visualizador)

---

# Restricciones críticas (NO IGNORAR)

1. **NO** modificar `visualizador.html` directamente — solo `visualizador_template.html`. Después correr `python notebooks/generar_visualizador.py` para regenerarlo.
2. Mantener compatibilidad con CSVs antiguos sin columna `Dependiente` (fallback: auto-detección por keywords).
3. No romper las funciones existentes `saveAnalysis()`, `renderSavedTable()`, `downloadAnalysesCSV()`, `clearAnalyses()`.
4. La variable global `window.ANALYSES` debe seguir siendo un array — solo se le agrega un campo `dep` (boolean).
5. La columna nueva en el CSV se llama exactamente `Dependiente` (valores `Sí` / `No` o vacío).
6. En el .py, la selección por columna `Dependiente` tiene **prioridad** sobre la auto-detección. Si hay más de una fila marcada, usar la primera; si ninguna, fallback a keywords.

---

# Paso 1 — Marcar variable dependiente al guardar análisis

**Archivo:** `notebooks/visualizador_template.html`

## 1.a — UI: agregar un radio "Dep." en la fila de la tabla guardada

En `renderSavedTable()` (~línea 2755) añadir una primera columna `dep` con un `<input type="radio" name="anl-dep">` por fila. Al cambiarse, debe actualizar `window.ANALYSES[i].dep = true` y poner `false` en todas las demás, luego volver a llamar `renderSavedTable()`.

Columnas finales: `#, Dep, Serie A, Deflactor A, Serie B, Deflactor B, Operación, Desde, Hasta, Frecuencia, Log, Dif., MM, Test UR, Estadístico, p-valor, Resultado`.

## 1.b — saveAnalysis(): inicializar `dep: false`

En `saveAnalysis()` (línea 2724) en el push a `window.ANALYSES`, agregar `dep: false`. Si es la **primera** análisis guardada (`window.ANALYSES.length === 0` antes del push), inicializar `dep: true` (default razonable: primer análisis = dependiente).

## 1.c — downloadAnalysesCSV(): incluir columna Dependiente

En `downloadAnalysesCSV()` (línea 2802):
- `cols`: insertar `'dep'` después de `'id'`
- `headers`: insertar `'Dependiente'` después de `'#'`
- Para cada fila, mapear `a.dep ? 'Sí' : 'No'`

---

# Paso 2 — Nueva pestaña "📈 Análisis Básico" en visualizador

**Archivo:** `notebooks/visualizador_template.html`

## 2.a — Botón de tab

En el div `#main-tabs` (~línea 178), añadir después del botón Análisis:
```html
<button class="mtab" onclick="switchTab('basico')">📈 Análisis Básico</button>
```

## 2.b — Contenido del tab

Después del `</div>` que cierra `tab-analysis` (~línea 406), insertar:

```html
<!-- ANÁLISIS BÁSICO (reporte de 02a) -->
<div id="tab-basico" class="tab-content">
  <div id="bb-bar" style="display:flex;gap:8px;padding:8px 12px;background:#1f2937;color:#fff;align-items:center">
    <button class="abtn" style="background:linear-gradient(135deg,#dc2626,#991b1b);padding:6px 14px;color:#fff;border:0;border-radius:4px;cursor:pointer;font-size:11px" onclick="ejecutarAnalisisBasico()">▶ Ejecutar Análisis Básico (con análisis guardados + variable dependiente)</button>
    <span id="bb-status" style="font-size:11px;opacity:.8">El reporte se cargará abajo al terminar.</span>
    <button class="abtn" style="margin-left:auto;background:#374151;padding:4px 10px;color:#fff;border:0;border-radius:4px;cursor:pointer;font-size:11px" onclick="recargarReporte()">↻ Recargar reporte</button>
  </div>
  <iframe id="bb-iframe" src="about:blank" style="flex:1;width:100%;border:0;min-height:600px"></iframe>
</div>
```

## 2.c — Funciones JS

Antes de `/* ── INIT ── */` (~línea 2837) agregar:

```js
function recargarReporte() {
  const iframe = document.getElementById('bb-iframe');
  iframe.src = 'reporte.html?ts=' + Date.now();
}

function ejecutarAnalisisBasico() {
  const status = document.getElementById('bb-status');
  if (!window.ANALYSES || window.ANALYSES.length === 0) {
    alert('Primero guardá al menos un análisis en la pestaña 📐 Análisis.');
    return;
  }
  if (!window.ANALYSES.some(a => a.dep)) {
    alert('Marcá una variable como Dependiente (radio) en la tabla de análisis guardados.');
    return;
  }
  // Construir CSV en memoria
  const cols = ['id','dep','s1','defl1','s2','defl2','op','from','to','freq','log','diff','ma'];
  const headers = ['#','Dependiente','Serie A','Deflactor A','Serie B','Deflactor B','Operación','Desde','Hasta','Frecuencia','Log','Dif.','MM'];
  let csv = headers.join(',') + '\n';
  window.ANALYSES.forEach(a => {
    const row = cols.map(c => {
      let v = a[c];
      if (c === 'dep') v = a.dep ? 'Sí' : 'No';
      return '"' + String(v).replace(/"/g, '""') + '"';
    });
    csv += row.join(',') + '\n';
  });

  status.textContent = '⏳ Ejecutando análisis…';
  fetch('/api/save-and-run', {
    method: 'POST',
    headers: {'Content-Type': 'text/csv;charset=utf-8'},
    body: csv
  })
  .then(r => r.json())
  .then(j => {
    status.textContent = j.ok ? '✅ Listo. Recargando reporte…' : '❌ Error: ' + (j.error || 'ver consola');
    if (j.ok) setTimeout(recargarReporte, 500);
  })
  .catch(e => { status.textContent = '❌ Fetch falló: ' + e + ' (¿servidor corriendo?)'; });
}

// Si se abre desde server.py, precargar el reporte vigente cuando se entra al tab
document.addEventListener('DOMContentLoaded', () => {
  const orig = window.switchTab;
  window.switchTab = function(t) {
    orig(t);
    if (t === 'basico') {
      const iframe = document.getElementById('bb-iframe');
      if (iframe.src === 'about:blank' || iframe.src.endsWith('blank')) {
        iframe.src = 'reporte.html?ts=' + Date.now();
      }
    }
  };
});
```

---

# Paso 3 — Extender `server.py`

**Archivo:** `notebooks/server.py`

## 3.a — Servir el visualizador como root

Cambiar el bloque `if u.path in ('/', '/index.html', '/reporte.html'):` para que:
- `/` y `/visualizador.html` sirvan `notebooks/visualizador.html`
- `/reporte.html` siga sirviendo `outputs/analisis_basico/reporte.html` (este es el que carga el iframe)

Añadir constante:
```python
_VIZ_HTML = _SCRIPT_DIR / 'visualizador.html'
```

Reescribir el handler de paths estáticos:
```python
if u.path in ('/', '/index.html', '/visualizador.html'):
    return self._send_file(_VIZ_HTML, 'text/html; charset=utf-8')
if u.path == '/reporte.html':
    return self._send_file(_REPORT_DIR / 'reporte.html', 'text/html; charset=utf-8')
```

## 3.b — Endpoint POST `/api/save-and-run`

Implementar `do_POST` en el Handler:
```python
def do_POST(self):
    u = urlparse(self.path)
    if u.path == '/api/save-and-run':
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8', errors='replace')
        # Guardar CSV en notebooks/Variables Regresivas/
        from datetime import datetime
        csv_dir = _PROJECT_ROOT / 'notebooks' / 'Variables Regresivas'
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_path = csv_dir / f'analisis_series_visualizador.csv'
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                f.write(body)
        except Exception as e:
            return self._send(500, json.dumps({'ok': False, 'error': f'No pude escribir CSV: {e}'}), 'application/json')

        # Invalidar todo el cache (porque cambió la dependiente y/o las series)
        if _run_lock.locked():
            return self._send(409, json.dumps({'ok': False, 'error': 'Ya hay un run en curso'}), 'application/json')
        with _run_lock:
            ok, log = _run_subprocess(['--invalidate', 'panel,ctx,est,ardl,var,vecm,consolidado',
                                       '--csv', csv_path.name])
        return self._send(200, json.dumps({'ok': ok, 'log_tail': log[-30:]}), 'application/json')
    self._send(404, f'POST no soportado: {u.path}')
```

## 3.c — Servir CSS/imágenes del reporte vía /reporte.html

El iframe carga `/reporte.html`, y las imágenes en `outputs/analisis_basico/` (e.g. `sec05_series_panel.png`) son referenciadas relativas. El handler existente ya sirve archivos de `_REPORT_DIR` por path, así que **funcionará** si el iframe usa `src="reporte.html"` y luego pide `sec05_*.png` relativos a `/`. Verificar que el fallback al final del `do_GET` (`target = _REPORT_DIR / u.path.lstrip('/')`) cubre estos casos — **ya lo hace**, ok.

---

# Paso 4 — Modificar `02a_analisis_basico.py`

**Archivo:** `notebooks/02a_analisis_basico.py`

## 4.a — Aceptar `--csv` para forzar nombre de CSV

En `main()` (~línea 2868):
```python
parser.add_argument('--csv', type=str, default=None, help='Nombre del CSV en notebooks/Variables Regresivas/')
```
Pasar al config como `config['CSV_ANALISIS'] = args.csv if args.csv else None` después de `config = seccion_3_configuracion()`.

## 4.b — Leer columna `Dependiente` en `seccion_4_carga_panel`

En el bloque que normaliza columnas del CSV (~línea 864), añadir `Dependiente` a la lista. Después de cargar `df_csv`, NO usar la columna acá — solo conservarla.

Pasar `df_csv` a `seccion_45_seleccion_dependiente` o pasar un mapa de etiqueta → dep. Forma simple: en `seccion_4_carga_panel`, construir y devolver además un set `DEPENDIENTE_LABELS` con las etiquetas marcadas como dependiente, derivado de `df_csv['Dependiente']`:

```python
_dep_labels = set()
if 'Dependiente' in df_csv.columns:
    for _i, _row in df_csv.iterrows():
        _flag = str(_row.get('Dependiente', '') or '').strip().lower()
        if _flag in ('sí', 'si', 'yes', 'true', '1', 'x'):
            _eti = _eti_map.get(_i)
            if _eti:
                _dep_labels.add(_eti)
```

Devolver tupla extendida: `return df_panel, df_csv, _LISTA_SERIES, FRECUENCIA_USADA, _dep_labels`.

## 4.c — Usar `DEPENDIENTE_LABELS` en `seccion_45_seleccion_dependiente`

Cambiar firma para aceptar `dep_labels=None`. Lógica:
```python
if dep_labels:
    for i, c in enumerate(_LISTA_SERIES, 1):
        if c in dep_labels:
            VARIABLE_DEPENDIENTE = i
            break
    else:
        # marcado pero no en panel — fallback a keywords
        ...
else:
    # fallback existente: keywords
    ...
```

Y en `main()` ajustar el desempaquetado:
```python
df_panel, df_csv, _LISTA_SERIES, FRECUENCIA_USADA, _DEP_LABELS = seccion_4_carga_panel(config, CATALOG_VIZ)
...
ctx = seccion_45_seleccion_dependiente(df_panel, _LISTA_SERIES, FRECUENCIA_USADA, config, dep_labels=_DEP_LABELS)
```

Actualizar también el bloque de caché para guardar `_DEP_LABELS` en el panel cache:
```python
_cache_save('panel', {..., '_DEP_LABELS': _DEP_LABELS})
```

---

# Paso 5 — Regenerar visualizador.html

Correr en la raíz del repo:
```bash
python notebooks/generar_visualizador.py
```
Esto recrea `notebooks/visualizador.html` con los cambios del template + datos embebidos.

---

# Paso 6 — Probar end-to-end

1. `python notebooks/server.py` (sirve en http://localhost:8765/)
2. Abrir el navegador → tab "📐 Análisis" → configurar y "💾 Guardar Análisis" 2-3 veces
3. En la tabla guardada, marcar el radio "Dep" de la fila que querés como Y
4. Ir a tab "📈 Análisis Básico" → click "▶ Ejecutar Análisis Básico"
5. Esperar ~1-3 min (ver `bb-status`). Al terminar, el iframe muestra `reporte.html` con la Y elegida.

---

# Notas de seguridad / fallbacks

- Si `server.py` no está corriendo y se abre `visualizador.html` directo desde el filesystem, el fetch `/api/save-and-run` fallará — eso es esperable; mostrar mensaje claro al usuario.
- El CSV se sobrescribe en `notebooks/Variables Regresivas/analisis_series_visualizador.csv`. Si se quiere historial, cambiar a fechado, pero entonces `02a.py` debe recibir el nombre vía `--csv` (ya implementado en paso 4.a).
- Si el usuario marca 0 o múltiples dependientes en el CSV: `02a.py` toma la **primera** marcada o cae a keywords. No falla.

# Checklist final

- [ ] Paso 1.a/b/c (template: radio + saveAnalysis + downloadCSV)
- [ ] Paso 2.a/b/c (template: nuevo tab + funciones JS)
- [ ] Paso 3.a/b (server.py: root + POST endpoint)
- [ ] Paso 4.a/b/c (02a.py: --csv + Dependiente)
- [ ] Paso 5 (regenerar visualizador.html)
- [ ] Paso 6 (test manual)
