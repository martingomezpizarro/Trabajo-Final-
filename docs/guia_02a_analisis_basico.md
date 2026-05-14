# 📊 Guía — Notebook 02a: Análisis Básico Aislado

## Archivo: `notebooks/02a_analisis_basico.ipynb`

---

## Objetivo

Correr **todas las combinaciones posibles** de los 3 modelos (ARDL, VAR, VECM) con las variables explicativas del CSV de análisis, manteniendo siempre el **EMBI+ (riesgo país)** como variable dependiente. El propósito es:

1. **Identificar visualmente** qué variables son más explicativas mediante gráficos de p-value y coeficiente
2. **Identificar numéricamente** el mejor modelo por criterios de información (AIC, BIC, HQ, R²)
3. Generar un **ranking de variables** y un **ranking de modelos**

> Este análisis es "básico" porque cada modelo se estima de forma aislada — no se usan los resultados de un modelo para alimentar otro.

---

## Estructura de la Notebook

### Base Compartida (Secciones 1–6)

Copiar **celdas 0–14** del notebook `02_modelos_regresion.ipynb`:

| Sección | Contenido |
|---------|-----------|
| Título (Cell 0) | Adaptar: "Análisis Básico Aislado de Modelos — ARDL · VAR · VECM" |
| 1. Instalación e Imports (Cells 1-2) | Sin cambios |
| 2. Funciones Auxiliares (Cells 3-4) | Sin cambios — incluye parser de CATALOG, deflactores, carga de series |
| 3. Configuración (Cells 5-6) | Sin cambios — `CSV_ANALISIS`, `FRECUENCIA`, fechas, lags, semilla |
| 4. Carga del Panel (Cells 7-8) | Sin cambios — lee CSV, valida CATALOG, construye `df_panel` |
| 4.5. Variable Dependiente (Cells 9-10) | Sin cambios — auto-detecta riesgo país como `ETI_DEP` |
| 5. Estadísticos Descriptivos (Cells 11-12) | Sin cambios — tabla + gráficos |
| 6. Tests de Estacionariedad (Cells 13-14) | Sin cambios — ADF+KPSS, filtra `X_SAFE_EST` |

### Secciones Nuevas (post sección 6)

#### 7. Modelos ARDL

**7.1 Prewhitening Box-Jenkins**
- Para cada variable explicativa `X_i` en `X_SAFE_EST`:
  - Ajustar ARMA(p,q) a `X_i` (orden por AIC, max p=4, q=4)
  - Aplicar el filtro ARMA estimado a la variable dependiente `Y` (prewhitening)
  - Calcular la CCF (cross-correlation function) entre `X_i_filtrado` e `Y_filtrado`
  - Identificar lags significativos de la CCF → determinar lags óptimos para el ARDL
- Guardar los lags óptimos en un diccionario `{variable: [lags]}`
- Visualización: gráficos de CCF para cada variable

**7.2 Estimaciones iterativas ARDL**
- Generar todas las combinaciones posibles de variables en `X_SAFE_EST`
  - Tamaños de 1 a `MAX_VARS_POR_MODELO` (o `len(X_SAFE_EST)` si es None)
  - Limitar a `MAX_COMBINACIONES` si está configurado
- Para cada combinación:
  - Estimar ARDL con los lags determinados por prewhitening
  - Guardar: R² adj, AIC, BIC, HQ, coeficientes, p-values de cada variable
- Almacenar todo en `df_res_ardl` (DataFrame de resultados)

**7.3 Control de calidad ARDL**
- Filtrar modelos por:
  - R² mínimo configurable
  - Al menos una variable significativa (p < `NIVEL_SIG`)
- Resultado: `df_res_ardl_ok`

#### 8. Modelos VAR

**8.1 Selección del orden VAR**
- Evaluar sobre una muestra de combinaciones
- Criterios AIC/BIC/HQ para seleccionar el orden óptimo
- Rango: 1 a `MAX_LAGS_VAR`

**8.2 Estimaciones iterativas VAR**
- Mismas combinaciones que ARDL
- Para cada combinación:
  - Estimar VAR con orden seleccionado por AIC
  - Extraer coeficientes y p-values de la ecuación del EMBI
  - Guardar: R² adj, AIC, BIC, HQ, estabilidad (raíces < 1)
- Almacenar en `df_res_var`

**8.3 Control de calidad VAR**
- Filtrar por estabilidad del sistema
- R² mínimo
- Resultado: `df_res_var_ok`

#### 9. Modelos VECM

**9.1 Test de cointegración de Johansen**
- Ejecutar Johansen sobre todas las variables disponibles
- Determinar rango de cointegración global
- Filtrar combinaciones sin cointegración

**9.2 Estimaciones iterativas VECM**
- Solo combinaciones con cointegración
- Estimar VECM para cada combinación
- Guardar: coeficientes de largo plazo (β), velocidad de ajuste (α), R²

**9.3 Control de calidad VECM**
- Rango de cointegración mínimo
- R² mínimo
- Resultado: `df_res_vecm_ok`

#### 10. Resultados Consolidados

- Unir `df_res_ardl_ok` + `df_res_var_ok` + `df_res_vecm_ok` → `df_res`
- Construir formato largo `df_largo` para análisis visual:
  - Columnas: `modelo`, `variables`, `variable`, `coef`, `pvalue`, `R2_adj`, `AIC`, `BIC`, `HQ`

#### 11. Gráficos de Coeficientes, P-valores y Significancia

- **Scatter coef vs p-value** por variable y modelo (colores: ARDL=azul, VAR=naranja, VECM=verde)
- **Barras de % de significancia** por variable (en cuántos modelos es significativa al nivel `NIVEL_SIG`)
- **Heatmap de p-values** (variables × modelos)

#### 12. Ranking y Comparación de Modelos

- **Top 10** modelos por cada criterio (R², AIC, BIC, HQ)
- Mejor modelo global
- Gráficos de comparación entre tipos de modelo

#### 13. Mejor VAR y VECM

- Gráfico ajustado vs real para el mejor VAR y VECM
- **Funciones de Respuesta al Impulso (IRF)** del mejor VAR
- IRF del mejor VECM

#### Apéndice A — Explorador Interactivo
- Tabla interactiva con `itables` para explorar `df_largo`

#### Apéndice B — Diagnóstico de Residuos
- Test Ljung-Box sobre residuos de los mejores modelos

---

## Variables Clave del Código

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `df_panel` | DataFrame | Panel unificado con todas las series |
| `ETI_DEP` | str | Etiqueta de la variable dependiente (EMBI+) |
| `X_SAFE_EST` | list[str] | Variables explicativas estacionarias (safe names) |
| `COL_LABEL` | dict | Mapeo safe_name → etiqueta legible |
| `df_res_ardl` | DataFrame | Resultados brutos de todas las estimaciones ARDL |
| `df_res_ardl_ok` | DataFrame | Modelos ARDL que pasan control de calidad |
| `df_res_var` / `df_res_var_ok` | DataFrame | Ídem para VAR |
| `df_res_vecm` / `df_res_vecm_ok` | DataFrame | Ídem para VECM |
| `df_res` | DataFrame | Consolidación de los 3 modelos aprobados |
| `df_largo` | DataFrame | Formato largo para gráficos (1 fila = 1 variable × 1 modelo) |

---

## Funciones de `src/utils.py` Utilizadas

- `test_estacionariedad(serie, nombre)` — Test ADF + KPSS
- `test_causalidad_granger(df, y, x, max_lag)` — Test de Granger
- `resumen_estadistico(df)` — Estadísticos descriptivos

## Funciones Definidas en la Notebook

- `_parse_catalog()` — Parsea CATALOG del visualizador
- `detectar_frecuencia(df_csv)` — Detecta frecuencia más gruesa
- `construir_variable(row, freq, fi, ff)` — Construye serie desde fila CSV
- `extraer_ardl(...)` — Estima un ARDL y extrae resultados
- `extraer_var(...)` — Estima un VAR y extrae resultados
- `extraer_vecm(...)` — Estima un VECM y extrae resultados

---

## Colores por Modelo

```python
_COLORS = {'ARDL': '#2196F3', 'VAR': '#FF9800', 'VECM': '#4CAF50'}
```
