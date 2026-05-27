---
description: Plan de acción actualizado para completar el trabajo final — deadline 10/06/2026
last_updated: 2026-05-25
---

# Plan de Accion - Trabajo Final de Grado

## Riesgo Pais Argentino: Analisis Econometrico y Prediccion con Redes Neuronales

**Deadline:** 10 de junio de 2026 (16 dias desde hoy 25/05)
**Dedicacion estimada:** 2-3 h/dia base, 4-5 h/dia en dias clave
**Autor:** Martin Gomez Pizarro — Lic. en Economia, UNC

---

## Pasos del proyecto

| Paso | Descripcion | Estado |
|------|-------------|--------|
| 0.9 | Hacer que el codigo funcione y muestre lo relevante de cada modelo | EN CURSO |
| 1.0 | Conseguir todas las series temporales | PARCIAL (~45 listas, faltan 2-3) |
| 1.1 | Ver como se tratan los distintos tipos de series | PENDIENTE |
| 1.2 | Realizar el tratamiento, observar resultados para investigacion | PENDIENTE |
| 1.3 | Crear el modelo de RRNN | PENDIENTE |
| 2.0 | Escribir el documento final (max 6 pags) | PENDIENTE |

---

## Estado actual al 25/05/2026

### Lo que YA esta hecho:
- [x] Infraestructura de datos: ~100 variables, 10+ fuentes automatizadas
- [x] ~45 series en `data/Variables Finales/` listas
- [x] Dashboard interactivo standalone (`notebooks/visualizador.html`)
- [x] `02a_analisis_basico.py` creado (2172 lineas, pipeline ARDL/VAR/VECM completo)
- [x] Documentacion tecnica: `docs/guia_02a_analisis_basico.md`
- [x] CSV de configuracion de variables (`notebooks/Variables Regresivas/analisis_series_2026-05-22.csv`)
- [x] Tests de estacionariedad (ADF+KPSS) en `src/utils.py`
- [x] Dummies construidas (cepo, elecciones, gobierno)
- [x] Deflactores disponibles: PBI, CER, TIP/IPC, MEP

### Lo que FALTA:
- [ ] **Paso 0.9:** Ejecutar `02a_analisis_basico.py` y que corra sin errores
- [ ] **Paso 1.0:** Inflacion breakeven (~3 dias) + resultado fiscal estructural (~2 dias)
- [ ] **Paso 1.1-1.2:** Tratamiento de series y analisis de resultados
- [ ] **Paso 1.3:** 3 modelos de redes neuronales
- [ ] **Paso 2.0:** Documento final (max 6 paginas + tablas/anexos/biblio)

---

## PASO 0.9 — Hacer que el codigo funcione

**Objetivo:** Que `02a_analisis_basico.py` corra de punta a punta y muestre resultados relevantes de ARDL, VAR y VECM.

Instrucciones para el agente:
```
1. Ir a la raiz del proyecto: C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo
2. Ejecutar: python 02a_analisis_basico.py --hasta 6
   - Corre hasta tests de estacionariedad (sin modelos pesados)
   - Si hay errores, leer el traceback y corregir en el .py
3. Si pasa, ejecutar: python 02a_analisis_basico.py --seccion 7
   - Solo ARDL (el mas lento por combinaciones)
4. Luego: python 02a_analisis_basico.py --secciones 8,9
   - VAR y VECM
5. Finalmente: python 02a_analisis_basico.py
   - Corrida completa
   - Debe generar PNGs en outputs/analisis_basico/
   - Y resultados_iterativos.csv en notebooks/Variables Regresivas/
```

Errores probables y como solucionarlos:
- `FileNotFoundError` en visualizador_template.html → Esta en `notebooks/visualizador_template.html`
- `ModuleNotFoundError: pmdarima` → `pip install pmdarima`
- `MemoryError` en VAR permutaciones → Reducir `MAX_COMBINACIONES` en seccion 3
- `KeyError` en columnas CSV → Verificar columnas: `Serie A, Deflactor A, Serie B, Operacion, Log, Dif.`

**Que debe mostrar cada modelo:**
- ARDL: coeficientes de largo plazo (delta method), R2, significancia de cada variable
- VAR: IRF ortogonalizadas, Wald F-test, descomposicion de varianza
- VECM: alpha (velocidad ajuste), gamma (corto plazo), rango de cointegracion

---

## PASO 1.0 — Conseguir todas las series temporales

### 1.0.1 Inflacion breakeven argentina
```
1. Leer: scripts/build_catalogo_bonos_pesos_breakeven.py
2. Datos disponibles:
   - data/catalogo_breakeven_bonos.xlsx
   - data/catalogo_bonos_pesos_cer.xlsx
   - data/raw/bcra/cer.csv
3. Calcular: breakeven = YTM_nominal - YTM_CER (pares de bonos similar maturity)
4. Guardar: data/Variables Finales/inflacion_breakeven.csv
5. Validacion: valores entre 5% y 200%+ en crisis
6. Alternativa: usar REM del BCRA (encuesta expectativas inflacion 12m)
```

### 1.0.2 Resultado fiscal estructural
```
1. Datos existentes:
   - data/processed/resultado_fiscal.xlsx
   - data/Variables Finales/Resultado fiscal-unificado.xlsx
   - scripts/build_resultado_fiscal.py
2. Calcular:
   - Output gap = (PBI_real - PBI_potencial) / PBI_potencial
   - PBI potencial: filtro HP (lambda=1600 trimestral)
   - RF_estructural = RF_primario - elasticidad * output_gap
   - Elasticidad fiscal: usar 1.0 (standard FMI)
3. Guardar: data/Variables Finales/resultado_fiscal_estructural.csv
4. Validacion: mayormente negativo (-1% a -8% del PBI)
```

**NOTA:** Si estas dos variables no se pueden construir a tiempo, el trabajo puede
presentarse SIN ellas. Son deseables pero no criticas.

---

## PASO 1.1 — Tratamiento de series

**Objetivo:** Entender como se tratan los distintos tipos de series y documentar decisiones.

```
1. Ejecutar 02a_analisis_basico.py --hasta 6 (si no se hizo en 0.9)
2. Revisar los resultados de estacionariedad:
   - Cuales son I(0)? (estacionarias en nivel)
   - Cuales son I(1)? (necesitan una diferencia)
   - Hay alguna I(2)? (se descarta)
3. Revisar las transformaciones aplicadas:
   - Que variables se logaritmizaron? Por que?
   - Que deflactores se usaron? (ver CSV de analisis)
   - Que operaciones entre Serie A y Serie B?
4. Documentar decisiones en un resumen para el documento final
```

---

## PASO 1.2 — Resultados para investigacion

**Objetivo:** Correr los modelos y extraer resultados interpretables.

```
1. Ejecutar pipeline completo: python 02a_analisis_basico.py
2. Leer resultados_iterativos.csv
3. Identificar:
   a. Top 5 variables mas significativas (menor p-valor promedio)
   b. Variables idiosincraticas vs generales — cual grupo explica mas?
   c. Mejor modelo por tipo (ARDL, VAR, VECM) segun AIC/BIC/R2
   d. Consistencia: las mismas variables son significativas en los 3 modelos?
4. Graficos criticos:
   a. Real vs Ajustado del mejor modelo
   b. Scatter coeficiente vs p-valor por variable
   c. Barras: % significancia por variable across modelos
5. Interpretar economicamente los coeficientes significativos
```

---

## PASO 1.3 — Redes neuronales

**IMPORTANTE:** Martin tiene poca experiencia con deep learning. Codigo simple,
bien comentado, con prints explicativos.

**Modelo 1: LSTM para EMBI LATAM (multivariate)**
```
Archivo: src/rn_latam.py
Objetivo: Predecir EMBI de 6 paises LATAM
Inputs: VIX, DXY, UST10Y, commodities, EMBI de cada pais
Arquitectura: LSTM(64) → Dropout(0.2) → LSTM(32) → Dense(6)
Loss: MSE, Optimizer: Adam(lr=0.001), EarlyStopping(patience=15)
Train/Val/Test: 70/15/15
Datos: data/Variables Finales/embi_latam.csv + vix.csv + dxy.csv + ust10y.csv
```

**Modelo 2: LSTM para Argentina (features locales)**
```
Archivo: src/rn_argentina.py
Objetivo: Predecir EMBI Argentina con variables locales
Inputs: top 5 variables de resultados_iterativos.csv (por significancia)
Arquitectura: LSTM(32) → Dropout(0.3) → Dense(16) → Dense(1)
Lookback: 6 periodos
```

**Modelo 3: Random Forest (benchmark ML)**
```
Archivo: src/rn_tree.py
Objetivo: Benchmark no-lineal, interpretable (feature importance)
RandomForestRegressor(n_estimators=200, max_depth=10)
Features: mismas 5 variables + lags 1-6 (usar crear_rezagos de utils.py)
Train/Test: 80/20 (tabular, sin secuencias)
```

**Script controlador:**
```
Archivo: 03_redes_neuronales.py (raiz)
argparse: --modelo latam/argentina/tree/todos
Genera tabla comparativa: LSTM vs RF vs mejor modelo econometrico
Guarda en: outputs/redes_neuronales/
```

Dependencias:
```
pip install tensorflow  # LSTM
pip install xgboost     # Opcional para Modelo 3
```

---

## PASO 2.0 — Documento final

REGLAS:
- MAXIMO 6 paginas de texto
- Tablas, graficos, anexos y bibliografia NO cuentan
- Formato: Word (.docx)

```
1. PRIMERO leer la guia del seminario:
   "Trabajo Final/Guia_Actividad_Final_Seminario_Completa.docx"
   - Seguir EXACTAMENTE el formato que pide la UNC

2. Estructura sugerida (adaptar segun guia):
   Pag 1: Introduccion y motivacion
   Pag 2: Marco teorico + literatura (5-8 referencias)
   Pag 3: Metodologia (datos, modelos, tests)
   Pag 4-5: Resultados + interpretacion economica
   Pag 6: Conclusiones + limitaciones

3. DESPUES del texto: tablas, anexos, bibliografia

4. Guardar: "Trabajo Final/Gomez_Pizarro_Trabajo_Final.docx"
```

---

## ARCHIVOS CLAVE

| Archivo | Que es | Estado |
|---------|--------|--------|
| `02a_analisis_basico.py` | Pipeline ARDL/VAR/VECM | Creado, falta testear |
| `docs/guia_02a_analisis_basico.md` | Documentacion tecnica | Completo |
| `src/utils.py` | Tests, transformaciones, metricas | Completo |
| `notebooks/Variables Regresivas/analisis_series_2026-05-22.csv` | Config variables | Listo |
| `data/Variables Finales/` | ~45 series temporales | Listo |
| `notebooks/visualizador_template.html` | CATALOG de series | Listo |
| `docs/GOALS.md` | 3 objetivos + hipotesis | Listo |
| `Trabajo Final/Guia_Actividad_Final_Seminario_Completa.docx` | Guia UNC | Leer antes de escribir |

---

## NOTAS PARA AGENTES

1. **Prioridad absoluta:** que el codigo CORRA. No importa si el resultado no es perfecto.
2. **Si algo falla:** no reescribir todo. Leer el error, corregir solo lo necesario.
3. **Variables faltantes (breakeven, fiscal):** no son criticas. Si no se logran, seguir adelante.
4. **Redes neuronales:** codigo simple, bien comentado, con prints explicativos.
5. **Documento:** leer la guia del seminario PRIMERO.
6. **No tocar:** `data/Variables Finales/`, `notebooks/visualizador.html`, `src/utils.py`.
7. **Paths:** proyecto en `C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo`.
   Bash sandbox: `/sessions/pensive-happy-hopper/mnt/Trabajo`.
   visualizador_template.html en `notebooks/` (NO en raiz).
8. **Contexto tecnico:** leer `docs/guia_02a_analisis_basico.md` antes de tocar modelos.
9. **NO desarrollar 02b_analisis_completo.** Ese notebook se descarta del plan.
