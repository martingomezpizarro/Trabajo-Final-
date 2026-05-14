---
description: Guía para completar las notebooks 02a (análisis básico) y 02b (análisis completo) de modelos de regresión
---

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


# 🔬 Guía — Notebook 02b: Análisis Completo Integrado

## Archivo: `notebooks/02b_analisis_completo.ipynb`

---

## Objetivo

Establecer un **orden jerárquico de exogeneidad** entre las variables económicas usando los 3 modelos (ARDL, VAR, VECM) de forma **secuencial e integrada**, donde cada modelo verifica y complementa al anterior:

1. **ARDL exhaustivo** → Todas las variables como dependientes e independientes → Ranking de exogeneidad
2. **VAR** → Verificar el ranking con Granger, IRF y FEVD
3. **VECM** → Captar la dinámica de largo plazo

> A diferencia de la notebook 02a (análisis básico), aquí **no se fija** el EMBI como única variable dependiente. Todas las variables se prueban como dependientes para construir un mapa completo de relaciones causales.

---

## Estructura de la Notebook

### Base Compartida (Secciones 1–6)

Copiar **celdas 0–14** del notebook `02_modelos_regresion.ipynb`:

| Sección | Contenido |
|---------|-----------|
| Título (Cell 0) | Adaptar: "Análisis Completo Integrado — Jerarquía de Exogeneidad · ARDL → VAR → VECM" |
| 1. Instalación e Imports (Cells 1-2) | Sin cambios |
| 2. Funciones Auxiliares (Cells 3-4) | Sin cambios |
| 3. Configuración (Cells 5-6) | **Adaptar** — agregar pesos de exogeneidad y flag `TODAS_COMO_DEPENDIENTE` |
| 4. Carga del Panel (Cells 7-8) | Sin cambios |
| 4.5. Variable Dependiente (Cells 9-10) | **Adaptar** — se usa para referencia, pero no como única Y |
| 5. Estadísticos Descriptivos (Cells 11-12) | Sin cambios |
| 6. Tests de Estacionariedad (Cells 13-14) | Sin cambios |

### Configuración Adicional (agregar a Sección 3)

```python
# ── Pesos para score de exogeneidad ────────────────────────────────────────
W_PVALUE = 0.35   # Peso del p-value promedio como variable explicativa
W_R2INV  = 0.25   # Peso del R² invertido como variable dependiente
W_FREQ   = 0.25   # Peso de la frecuencia de significancia como X
W_BIC    = 0.15   # Peso de la parsimonia (BIC) de modelos donde participa

# ── ¿Probar todas las variables como dependientes? ─────────────────────────
TODAS_COMO_DEPENDIENTE = True   # True = completo (lento), False = solo EMBI como Y

# ── Lags máximos para prewhitening ─────────────────────────────────────────
MAX_AR_ORDER = 4   # Orden máximo AR para prewhitening
MAX_MA_ORDER = 4   # Orden máximo MA para prewhitening
```

---

### Secciones Nuevas (post sección 6)

#### 7. Análisis ARDL Exhaustivo — Jerarquía de Exogeneidad

**7.1 Prewhitening Box-Jenkins para TODAS las combinaciones Y/X**

Para cada par `(Y_i, X_j)` donde `i ≠ j`:
1. Ajustar ARMA(p,q) a `X_j` (orden por AIC, max AR=`MAX_AR_ORDER`, max MA=`MAX_MA_ORDER`)
2. Aplicar el filtro ARMA estimado a `Y_i` (prewhitening)
3. Calcular la CCF entre `X_j_filtrado` e `Y_i_filtrado`
4. Identificar lags significativos → almacenar en diccionario `{(Y_i, X_j): [lags]}`

```python
# Estructura de resultado del prewhitening
bj_lags = {}  # {(y_var, x_var): {'lags': [1,2,3], 'ccf_max': 0.35, 'arma_order': (2,1)}}
```

Visualización: matriz de CCF máximos (heatmap N×N)

**7.2 Estimaciones ARDL — Todas las combinaciones posibles**

Para **cada variable `Y_i`** (si `TODAS_COMO_DEPENDIENTE=True`):
- Las demás variables son candidatas a `X`
- Generar combinaciones de 1 a `MAX_VARS_POR_MODELO`
- Para cada combinación:
  - Verificar estacionariedad de Y_i y las X
  - Estimar ARDL con lags de prewhitening
  - Guardar: `y_var`, `x_vars`, `coefs`, `pvalues`, `R2_adj`, `AIC`, `BIC`, `HQ`

```python
# DataFrame de resultados ARDL exhaustivo
df_ardl_full = pd.DataFrame(columns=[
    'y_var', 'x_vars', 'n_vars',
    'R2_adj', 'AIC', 'BIC', 'HQ',
    'coefs', 'pvalues', 'n_obs'
])
```

**7.3 Construcción de la Jerarquía de Exogeneidad**

Para cada variable `V_i`:

```python
def calcular_score_exogeneidad(df_ardl_full, variables, pesos):
    """
    Calcula el score de exogeneidad para cada variable.
    
    Una variable MÁS EXÓGENA:
      - Tiene bajo p-value cuando actúa como X (explica bien a las demás)
      - Tiene bajo R² cuando actúa como Y (las demás NO la explican bien)
      - Es frecuentemente significativa en los modelos donde participa como X
      - Los modelos donde participa como X tienen buen BIC
    
    Una variable MÁS ENDÓGENA:
      - Tiene alto p-value como X (no explica bien)
      - Tiene alto R² como Y (es fácilmente explicada por las demás)
    """
    scores = {}
    for v in variables:
        # 1. P-value promedio cuando V_i actúa como X
        mask_as_x = df_ardl_full['x_vars'].apply(lambda xv: v in xv)
        if mask_as_x.any():
            pvals_as_x = []
            for _, row in df_ardl_full[mask_as_x].iterrows():
                idx = list(row['x_vars']).index(v)
                pvals_as_x.append(row['pvalues'][idx])
            avg_pvalue_as_x = np.mean(pvals_as_x)
        else:
            avg_pvalue_as_x = 1.0  # No participa como X → penalizar
        
        # 2. R² promedio cuando V_i actúa como Y
        mask_as_y = df_ardl_full['y_var'] == v
        avg_r2_as_y = df_ardl_full.loc[mask_as_y, 'R2_adj'].mean() if mask_as_y.any() else 0
        
        # 3. Frecuencia de significancia como X (p < NIVEL_SIG)
        if mask_as_x.any():
            n_sig = sum(1 for p in pvals_as_x if p < NIVEL_SIG)
            freq_sig = n_sig / len(pvals_as_x)
        else:
            freq_sig = 0
        
        # 4. BIC promedio como X (normalizado)
        avg_bic_as_x = df_ardl_full.loc[mask_as_x, 'BIC'].mean() if mask_as_x.any() else 0
        
        # Score compuesto
        scores[v] = (
            pesos['pvalue'] * (1 - avg_pvalue_as_x) +
            pesos['r2inv']  * (1 - avg_r2_as_y) +
            pesos['freq']   * freq_sig +
            pesos['bic']    * (1 / (1 + abs(avg_bic_as_x)))  # normalizar BIC
        )
    
    return pd.Series(scores).sort_values(ascending=False)
```

Visualización:
- **Ranking de exogeneidad** con barras horizontales (más exógena arriba)
- **Tabla resumen**: Variable | Score | Avg p-val como X | Avg R² como Y | % sig.
- **Heatmap de p-values** N×N (Y en filas, X en columnas)

**7.4 Validación cruzada del ranking**
- Comparar ranking cuando Y=EMBI vs ranking global
- Test de Granger bidireccional para top 5 variables vs EMBI
- Scatter: score exogeneidad vs p-value en modelo EMBI

---

#### 8. Verificación VAR del Orden Jerárquico

**8.1 Selección del orden del VAR**
- Evaluar con criterios AIC/BIC/HQ
- Rango: 1 a `MAX_LAGS_VAR`
- Usar la muestra completa de variables disponibles

**8.2 Ordenamiento de Cholesky según jerarquía ARDL**
```python
# Ordenar variables de más exógena a más endógena
cholesky_order = ranking_exogeneidad.index.tolist()
# El EMBI debería quedar último o cerca del final (más endógeno)

# Crear el VAR con este orden
df_var = df_safe[cholesky_order]
model_var = VAR(df_var)
results_var = model_var.fit(optimal_lag)
```

**8.3 Test de causalidad de Granger dentro del VAR**
- Para cada par `(V_i, V_j)`:
  - Test de Granger: ¿V_i Granger-causa V_j?
  - Registrar dirección causal
- Comparar con la dirección implicada por el ranking ARDL
- Visualización: **grafo dirigido** de causalidad (o al menos una matriz)

**8.4 Funciones de Respuesta al Impulso (IRF)**
- Impulso en cada variable exógena → respuesta del EMBI
- Horizonte: 24 períodos
- Bandas de confianza (95%)
- Verificar que las variables más exógenas generen mayor respuesta

**8.5 Descomposición de Varianza del Error de Pronóstico (FEVD)**
- FEVD del EMBI a horizontes 1, 6, 12, 24
- Verificar que las variables top del ranking ARDL expliquen más varianza
- Tabla + gráfico de barras apiladas

**8.6 Comparación: ranking ARDL vs ranking VAR**
```python
# Ranking VAR basado en FEVD del EMBI a horizonte 12
ranking_var = fevd_embi_h12.sort_values(ascending=False)

# Comparar con ranking ARDL
from scipy.stats import spearmanr
rho, p = spearmanr(ranking_ardl.rank(), ranking_var.rank())
print(f'Correlación de Spearman: {rho:.3f} (p={p:.4f})')
```

Visualización:
- Tabla lado a lado: Variable | Rank ARDL | Rank VAR
- Scatter de posiciones (una debería dar pendiente positiva)

---

#### 9. Dinámica de Largo Plazo — VECM

**9.1 Test de Cointegración de Johansen**
- Usar las top N variables del ranking confirmado + EMBI
- Test de traza y test de valor propio máximo
- Determinar rango de cointegración `r`
- Si `r = 0`: no hay relación de largo plazo → reportar y terminar

```python
from statsmodels.tsa.vector_ar.vecm import coint_johansen
# Usar las top variables del ranking + EMBI
vars_vecm = ranking_final[:TOP_N_VECM].tolist() + [Y_SAFE]
result_joh = coint_johansen(df_safe[vars_vecm], det_order=0, k_ar_diff=optimal_lag)
```

**9.2 Estimación VECM**
```python
from statsmodels.tsa.vector_ar.vecm import VECM as _VECM
model = _VECM(df_safe[vars_vecm], k_ar_diff=optimal_lag, coint_rank=r)
results = model.fit()
```

Extraer e interpretar:
- **β (beta)**: vectores de cointegración → relaciones de largo plazo
  - "Un aumento de 1 unidad en VIX está asociado a X puntos de EMBI en equilibrio"
- **α (alpha)**: velocidad de ajuste al equilibrio
  - "El EMBI corrige el X% del desequilibrio por período"
- **Γ (gamma)**: efectos de corto plazo (matrices de coeficientes de los rezagos en diferencias)

**9.3 Interpretación Económica**
- Tabla de relaciones de largo plazo (β normalizado)
- Gráfico de la(s) relación(es) de cointegración a lo largo del tiempo
- Comparar signos de β con la teoría económica:
  - VIX ↑ → EMBI ↑ (✓ o ✗)
  - Reservas ↑ → EMBI ↓ (✓ o ✗)
  - UST 10Y ↑ → EMBI ↑ (✓ o ✗)
  - etc.

---

#### 10. Síntesis y Conclusiones

**10.1 Tabla resumen final**

| Variable | Rank ARDL | Rank VAR (FEVD) | Rank Final | Relación LP (β) | Signo esperado | ¿Coincide? |
|----------|-----------|-----------------|------------|------------------|----------------|------------|
| VIX      | 1         | 2               | 1          | +0.45            | +              | ✓          |
| UST 10Y  | 2         | 1               | 2          | +0.32            | +              | ✓          |
| ...      | ...       | ...             | ...        | ...              | ...            | ...        |

**10.2 Variables más explicativas del riesgo país**
- Top 5 con interpretación económica

**10.3 Factores idiosincráticos vs push factors**
- Clasificar las top variables en:
  - **Push factors** (globales): VIX, DXY, UST, EMBI Global, etc.
  - **Pull factors** (idiosincráticos): reservas, TC, fiscal, deuda, etc.
- Calcular % de varianza explicada por cada grupo

**10.4 Gráfico resumen final**
- Diagrama de barras: contribución de cada variable al EMBI
- O diagrama radar con las dimensiones principales

---

## Funciones Nuevas Necesarias

```python
def estimar_ardl_todas_y(df_safe, variables, bj_lags, max_lags_dep, max_lags_ind, criterio):
    """
    Estima ARDL con CADA variable como dependiente.
    Devuelve DataFrame con todos los resultados.
    """
    pass

def calcular_score_exogeneidad(df_ardl_full, variables, pesos):
    """
    Calcula score de exogeneidad compuesto para cada variable.
    Mayor score = más exógena.
    """
    pass

def ordenamiento_cholesky(ranking_exogeneidad):
    """
    Genera el orden de variables para la descomposición de Cholesky
    del VAR, basado en el ranking de exogeneidad.
    """
    pass

def comparar_rankings(rank_ardl, rank_var):
    """
    Compara dos rankings y calcula correlación de Spearman.
    Genera visualización comparativa.
    """
    pass

def interpretar_vecm(results_vecm, col_labels):
    """
    Extrae e interpreta los vectores de cointegración (β),
    velocidades de ajuste (α) y genera tablas legibles.
    """
    pass
```

---

## Variables Clave del Código

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `df_ardl_full` | DataFrame | Resultados ARDL con TODAS las Y posibles |
| `ranking_exogeneidad` | Series | Score de exogeneidad por variable (desc.) |
| `bj_lags` | dict | Lags óptimos por par (Y, X) del prewhitening |
| `cholesky_order` | list | Orden de variables para el VAR |
| `ranking_var` | Series | Ranking basado en FEVD del VAR |
| `ranking_final` | Series | Ranking consenso ARDL + VAR |
| `beta_vecm` | array | Vectores de cointegración |
| `alpha_vecm` | array | Velocidades de ajuste |

---

## Advertencias Computacionales

> **⚠️ COSTO COMPUTACIONAL**: Con N variables y `TODAS_COMO_DEPENDIENTE=True`:
> - Pares prewhitening: N×(N-1)
> - Combinaciones ARDL: N × Σ(k=1..M) C(N-1, k) donde M = MAX_VARS_POR_MODELO
> - Para N=10, M=4: ~10 × 255 = 2550 modelos ARDL
> - Para N=10, M=None: ~10 × 511 = 5110 modelos ARDL
> - Para N=15, M=None: ~15 × 16383 ≈ 245000 modelos ARDL
>
> **Recomendación**: Empezar con `MAX_VARS_POR_MODELO = 3` o `4` para pruebas iniciales.

---

## Dependencias

Mismas que `02_modelos_regresion.ipynb`:
- `statsmodels` (ARDL, VAR, VECM, Johansen, Granger)
- `scipy` (spearmanr, stats)
- `numpy`, `pandas`, `matplotlib`
- `src/utils.py` (test_estacionariedad, test_causalidad_granger, resumen_estadistico)
