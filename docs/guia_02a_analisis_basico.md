# Guía: 02a_analisis_basico — Análisis Básico de Modelos de Series de Tiempo

## Propósito

Este módulo implementa el pipeline completo de estimación econométrica para el trabajo final "Riesgo País Argentino". Toma un CSV de configuración de variables, carga las series temporales desde el CATALOG del visualizador, y estima tres familias de modelos de series de tiempo: ARDL, VAR estructural (Cholesky) y VECM.

**Script Python:** `02a_analisis_basico.py` (raíz del proyecto)
**Notebook original:** `notebooks/02a_analisis_basico.ipynb`
**Output:** `outputs/analisis_basico/` (gráficos PNG)

---

## Arquitectura del pipeline

```
CSV de análisis → CATALOG (HTML) → Carga series → Panel unificado
    ↓
Selección Y (auto-detect EMBI) → Dummy isolation → MAX_LAGS dinámico
    ↓
Tests estacionariedad (ADF+KPSS) → clasificación I(0)/I(1)/I(2)
    ↓
    ├── ARDL: BJ prewhitening → CCF → lags propuestos → estimación → control → Ljung-Box
    ├── VAR:  Permutaciones Cholesky (Y último) → IRF ortogonalizadas → Wald F-test
    └── VECM: Johansen → combinaciones × k_ar_diff → alpha/gamma → árbol decisión
    ↓
Consolidación → df_largo (coef correcto por modelo) → rankings → gráficos
```

---

## Secciones detalladas

### Sección 3: Configuración
Parámetros editables del análisis. Los más importantes:
- `CSV_ANALISIS`: nombre del CSV en `notebooks/Variables Regresivas/` (None = más reciente)
- `FRECUENCIA`: 'auto' detecta la más gruesa entre todas las series
- `FECHA_INICIO` / `FECHA_FIN`: rango temporal (default: 2007-01-01 a 2026-03-31)
- `MAX_VARS_POR_MODELO` / `MAX_COMBINACIONES`: limitar explosión combinatoria (None = todas)
- `CRITERIOS_SEL`: criterios de información para selección de lags (`['aic', 'bic', 'hqic']`)
- `NIVEL_SIG`: nivel de significancia (default: 0.05)

### Sección 4: Carga y construcción del panel
1. Lee el CSV de análisis (columnas: `Serie A`, `Deflactor A`, `Serie B`, `Operación`, `Log`, `Dif.`)
2. Valida que todas las series existan en el CATALOG (parseado de `visualizador_template.html`)
3. Detecta frecuencia automáticamente (filtra series con freq > mensual)
4. Construye cada variable: carga serie A → deflacta → carga serie B → opera → log → diff
5. Une todo en `df_panel` (intersection de fechas, dropna)

Deflactores disponibles: PBI, CER, TIP/IPC (TIPS ETF), MEP

### Sección 4.5: Selección de variable dependiente
- Auto-detecta EMBI/riesgo por keywords en los nombres de las series
- Mapea nombres largos a códigos seguros (`v00`, `v01`, ...) vía `COL_SAFE` / `COL_LABEL`
- Aísla variables con prefijo `Dummy_` como exógenas estrictas
- Calcula `MAX_LAGS` dinámicamente: `min(freq_cap, (T-1)/(K+1))`

### Sección 5: Estadísticos descriptivos
Resumen estadístico extendido (N, media, mediana, desvío, min, max, asimetría, curtosis, Jarque-Bera) + gráficos de todas las series del panel.

### Sección 6: Tests de estacionariedad
- **ADF** (H0: tiene raíz unitaria) + **KPSS** (H0: estacionaria) en niveles y primera diferencia
- Regla combinada: estacionaria si ADF rechaza Y KPSS no rechaza
- Clasificación: I(0) estacionaria, I(1) una diferencia, I(2)+ descartada
- Construye `df_safe_est` (versiones estacionarias donde I(1) → diff) y conjuntos:
  - `X_SAFE_EST`: para ARDL/VAR (incluye I(0) e I(1), excluye dummies)
  - `X_SAFE_I1`: para VECM (solo I(1), cointegrables)
  - `X_SAFE_I0`: estacionarias en nivel

### Sección 7: Modelos ARDL

**7.1 Box-Jenkins prewhitening:**
- Para cada X: ajusta ARMA(p,q) a X con `pmdarima.auto_arima`
- Aplica el filtro AR de X sobre Y (prewhitening correcto: X filtra a Y, no al revés)
- Calcula CCF entre X blanqueada (residuos ARMA) e Y filtrada (filtro AR de X)
- Lags con |CCF| > 1.96/√n → `_BJ_PROPOSED_LAGS[x] = [lag0, lag1, ...]`
- Estima AR(Y) global como mediana de los AR(residuos OLS) por variable

**7.2 Estimación iterativa:**
- Genera todas las combinaciones de X_SAFE_EST (todos los tamaños) × 3 criterios
- Usa camino BJ (lags propuestos + AR(Y)) con fallback a `ardl_select_order`
- Dummies entran con lag 0 como exógenas
- Extrae:
  - Coeficientes de corto plazo: F-test conjunto sobre lags de cada X
  - **Coeficientes de largo plazo** θ = Σβ_x / (1 - Σα_y) con p-valor via **delta method** (propagación de covarianza con gradiente analítico)

**7.3 Control de calidad:** Filtros opcionales por R² mínimo y significancia

**7.4 Diagnóstico Ljung-Box (8 lags):** Retiene solo modelos cuyos residuos son ruido blanco (p > 0.05)

### Sección 8: Modelos VAR

**8.1 Selección de orden:** Muestra de 10 combinaciones de 3 variables para estimar lag óptimo por criterio de información

**8.2 Estimación con IRF estructural (Cholesky):**
- Genera permutaciones de X con **Y fijo en última posición** (más endógena en Cholesky)
- Cap a 1500 permutaciones para evitar explosión de RAM
- Para cada permutación: estima VAR → calcula IRF ortogonalizadas (0 a 12 horizontes) → p-valores asintóticos Z por horizonte
- Extrae coeficientes reducidos para ecuación Y: suma de coefs por lag + **Wald F-test** para significancia conjunta
- R² calculado manualmente para la ecuación Y

**8.3 Control de calidad:** Verificación de estabilidad (todas las raíces dentro del círculo unitario)

### Sección 9: Modelos VECM

**9.1 Cointegración de Johansen:** Test global con Trace y MaxEig al 5% sobre todas las variables I(1)

**9.2 Estimación:**
- Usa series en **NIVELES** (`df_safe`, NO `df_safe_est`) — VECM diferencia internamente
- Itera combinaciones × `k_ar_diff` ∈ [2, max(6, MAX_LAGS_VAR/2)]
- Solo estima si Johansen detecta cointegración (n_ci > 0)
- AIC/BIC/HQ calculados desde `sigma_u` (la clase VECM de statsmodels no los expone)
- Extrae:
  - **Alpha** (velocidad de ajuste al equilibrio de LP) con p-valor t-test
  - **Gamma** (efectos de corto plazo ΔX → ΔY)
- `reset_index(drop=True)` necesario porque statsmodels VECM no soporta DatetimeIndex

**9.3 Control de calidad:** Filtro por rango de cointegración mínimo

**9.4 Análisis Alpha:**
- Scatter alpha vs p-valor coloreado por variable
- Barras: % veces alpha NO significativo por variable (indica exogeneidad)
- **Árbol de decisión** (sklearn, max_depth=4): predice P(alpha sig.) según presencia/ausencia de cada variable → ranking de exogeneidad relativa

### Sección 10: Consolidación de resultados
- Une modelos aprobados de ARDL, VAR y VECM en `df_res`
- Construye `df_largo` con el **coeficiente correcto por tipo de modelo**:
  - ARDL → `lr_coef` / `lr_pval` (largo plazo, delta method)
  - VAR → `sum_coef` / `wald_pval` (reducido, Wald F-test)
  - VECM → `gamma_coef` / `gamma_pval` (corto plazo ECM)
- Gráficos: scatter coef vs p-valor por variable/modelo, barras % significancia
- Exporta a `notebooks/Variables Regresivas/resultados_iterativos.csv`

### Sección 11: Ranking y comparación
- Top 10 por R², AIC, BIC, HQ (sin duplicados por vars+modelo)
- Mejor modelo global: coeficientes detallados con estrellas (*** p<1%, ** p<5%, * p<10%)
- Box plots de criterios de información por modelo
- AIC por número de variables explicativas
- **Gráfico Real vs Ajustado** del mejor modelo (reconstruye Y_hat en niveles para VECM)

### Apéndice B: Diagnóstico de residuos completo
- Re-estima cada especificación única (mejor AIC por vars+modelo)
- Ljung-Box con 12 lags
- Resumen por tipo de modelo: % residuos ruido blanco
- Lista de modelos que NO pasan (autocorrelación residual detectada)

---

## Dependencias

| Paquete | Uso |
|---------|-----|
| `statsmodels` | ARDL, VAR, VECM, Johansen, Ljung-Box, ADF, KPSS |
| `pmdarima` | auto_arima para prewhitening BJ |
| `sklearn` | DecisionTreeClassifier (análisis alpha VECM) |
| `scipy` | delta method (norm), t-test |
| `pandas` / `numpy` | manipulación de datos |
| `matplotlib` | gráficos (backend Agg por defecto) |

---

## Archivos de entrada

| Archivo | Descripción |
|---------|-------------|
| `notebooks/Variables Regresivas/analisis_series_*.csv` | CSV de configuración de variables |
| `visualizador_template.html` | CATALOG de series (parseado con regex) |
| `data/Variables Finales/*.csv` | Series temporales finales (~45 archivos) |
| `data/raw/*.csv` | Series crudas (fallback) |
| `src/utils.py` | Funciones: `test_estacionariedad`, `test_causalidad_granger`, `resumen_estadistico` |

## Archivos de salida

| Archivo | Descripción |
|---------|-------------|
| `outputs/analisis_basico/*.png` | Gráficos por sección |
| `notebooks/Variables Regresivas/resultados_iterativos.csv` | Resultados consolidados (df_largo) |

---

## Uso desde línea de comandos

```bash
# Ejecutar todo
python 02a_analisis_basico.py

# Solo ARDL
python 02a_analisis_basico.py --seccion 7

# ARDL + VAR
python 02a_analisis_basico.py --secciones 7,8

# Hasta estacionariedad (sin modelos)
python 02a_analisis_basico.py --hasta 6

# Con ventana de gráficos interactiva
python 02a_analisis_basico.py --backend TkAgg
```

---

## Decisiones técnicas clave

1. **Prewhitening BJ correcto**: el filtro AR de X se aplica a Y (no al revés). La CCF se calcula entre residuos_ARMA(X) e Y_filtrada_por_AR(X). Esto evita correlación espuria por autocorrelación compartida.

2. **ARDL largo plazo via delta method**: θ = Σβ_x / (1 - Σα_y). El p-valor se calcula propagando la matriz de covarianza con el gradiente analítico ∂θ/∂β = 1/(1-Σα), ∂θ/∂α = Σβ/(1-Σα)².

3. **VAR Cholesky con Y último**: al fijar Y_SAFE en la última posición, se asume que es la variable más endógena (absorbe shocks contemporáneos de todas las X). Las permutaciones varían solo el orden de las X entre sí.

4. **VECM en niveles con reset_index**: usa `df_safe` (no `df_safe_est`). `reset_index(drop=True)` es un workaround necesario porque `statsmodels.tsa.vector_ar.vecm.VECM` no soporta DatetimeIndex.

5. **Alpha como indicador de exogeneidad**: si alpha(Y) es significativo y negativo, Y converge al equilibrio LP. El árbol de decisión identifica qué combinaciones de variables producen alpha significativo, revelando la estructura de exogeneidad del sistema.

6. **MAX_LAGS dinámico**: `min(freq_cap, (T-1)/(K+1))` evita sobreparametrización con pocas observaciones o muchas variables.

---

## Fallas corregidas del notebook original

| Problema | Corrección |
|----------|-----------|
| ~35 líneas duplicadas de header "7.1 Análisis BJ" (cell 16) | Eliminadas |
| Encoding roto en cell 25 (`?? Par?metros ???`) | Caracteres Unicode corregidos |
| `%matplotlib inline` (magic de IPython) | `matplotlib.use('Agg')` configurable via `--backend` |
| `display()` de IPython | `print(df.to_string())` |
| `globals()` para `_BJ_PROPOSED_LAGS` y `_BJ_AR_Y` | Parámetros explícitos pasados a funciones |
| Paths relativos desde directorio de notebooks | Resolución absoluta desde `Path(__file__).resolve().parent` |
| Sin guardado de gráficos | `_save_fig()` guarda PNG en `outputs/analisis_basico/` |
| Funciones monolíticas en cells gigantes | Refactorizado en funciones por sección con contexto explícito |

---

## Contexto para agentes futuros

- La variable dependiente es siempre el **EMBI+ Argentina spread** (riesgo país)
- El CSV de análisis define qué variables usar, con qué deflactor, y qué operación entre Serie A y Serie B
- Las dummies (prefijo `Dummy_`) se tratan como exógenas estrictas (no entran en combinaciones, solo como control)
- Los tres modelos capturan diferentes aspectos: ARDL → relación de largo plazo, VAR → dinámica estructural (Cholesky), VECM → corrección de error y velocidad de ajuste
- `df_largo` es la tabla clave para análisis posterior: contiene el coeficiente "correcto" según cada tipo de modelo
- El script es idempotente: se puede re-ejecutar cambiando solo el CSV de análisis
