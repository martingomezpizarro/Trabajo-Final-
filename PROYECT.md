# PROYECT.md — Panorama General del Proyecto

## Identidad del Proyecto

- **Título**: Riesgo País Argentino: Análisis Econométrico de Series de Tiempo y Predicción con Redes Neuronales
- **Tipo**: Trabajo Final de Grado — Licenciatura en Economía, Universidad Nacional de Córdoba (UNC)
- **Autor**: Martín
- **Repositorio**: `github.com/martingomezpizarro/Trabajo-Final-` (branch `master`)
- **Lenguaje**: Python 3.10+ | JavaScript (dashboard)
- **Plataforma**: Windows (todos los paths son absolutos a `C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo`)

## Pregunta de Investigación

¿Qué variables explican el riesgo país argentino (spread EMBI+) y puede el aprendizaje automático predecirlo?

## Objetivos (de `docs/GOALS.md`)

1. Identificar variables explicativas del riesgo país argentino
2. Construir un índice en tiempo real que explique ≥70% de la variación del EMBI+
3. Distinguir factores idiosincráticos vs. globales (push factors)
4. Predicción con red neuronal (LSTM/GRU/Transformer) para LATAM y Argentina

---

## Arquitectura del Proyecto

```
Trabajo/
├── PROYECT.md                          ← este archivo
├── AGENTS.md                           ← guía git para agentes
├── README.md                           ← descripción del proyecto
├── requirements.txt                    ← dependencias Python
│
├── docs/                               ← documentación
│   ├── GOALS.md                        ← objetivos y alcance
│   ├── variables.md                    ← catálogo de ~100 variables con fuentes
│   ├── documentacion_modelos.md        ← referencias econométricas
│   └── documentacion_rn.md             ← referencias redes neuronales
│
├── src/                                ← módulos core (librería importable)
│   ├── data_loader.py                  ← cliente unificado APIs (Yahoo, FRED, BCRA, World Bank, ArgDatos)
│   ├── models.py                       ← wrappers OLS/VAR/VECM/ARDL/GARCH/PCA
│   ├── utils.py                        ← estacionariedad, causalidad Granger, transformaciones, métricas
│   ├── glosario.py                     ← registro de ~100 series con metadata (ID, fuente, ruta, freq, unidad)
│   ├── build_dummies.py                ← genera dummies: cepo, gobierno, elecciones, defaults
│   ├── download_pending.py             ← bulk download + auditoría de cobertura temporal
│   └── *.py                            ← extractores específicos (BCRA Excel, PBI, EMBI LATAM, CER, etc.)
│
├── scripts/                            ← procesamiento y construcción de datasets
│   ├── build_saldo_sigade.py           ← parsea ~70 archivos SIGADE .mdb → Excel deuda
│   ├── build_saldo_unificado.py        ← unifica SIGADE (2007-2018) + Boletín Mensual (2019-2026)
│   ├── build_vencimientos_2y.py        ← vencimientos forward 2 años desde SIGADE
│   ├── build_resultado_fiscal.py       ← serie resultado fiscal 1993-2026
│   ├── build_graficos_deuda.py         ← post-procesa saldo deuda en gráficos
│   ├── build_catalogo_bonos_pesos_breakeven.py  ← catálogo bonos CER/nominales
│   └── download/                       ← descargadores por fuente
│       ├── download_bcra.py            ← BCRA API v4.0 (~25 series)
│       ├── download_datos_gob.py       ← CKAN API (INDEC + Mecon)
│       ├── download_worldbank.py       ← World Bank API (22 indicadores + 6 WGI)
│       └── download_yfinance.py        ← Yahoo Finance
│
├── notebooks/                          ← notebooks Jupyter del pipeline analítico
│   ├── 01_base_de_datos.ipynb          ← extracción y visualización de datos
│   ├── 02_modelos_regresion.ipynb      ← modelos econométricos
│   ├── 03_red_neuronal.ipynb           ← red neuronal
│   ├── generar_visualizador.py         ← ensambla visualizador.html (datos CSV → JSON embebido)
│   ├── visualizador_template.html      ← dashboard interactivo (~2839 líneas JS/HTML)
│   ├── visualizador.html               ← dashboard generado (standalone, sin servidor)
│   └── Variables Regresivas/           ← CSVs de análisis de series candidatas
│
├── data/                               ← datos
│   ├── raw/                            ← datos crudos por fuente
│   │   ├── bcra/                       ← ~30 CSVs (reservas, TC, tasas, depósitos, CER, ITCRM)
│   │   ├── deuda_arg/                  ← deuda (A-J: boletín, SIGADE, externa, PBI, ratio, comparación)
│   │   ├── global/                     ← ~20 CSVs (VIX, DXY, UST, commodities, divisas, índices)
│   │   ├── indec/                      ← IPC, EMAE, ICA, Balanza Pagos, PBI
│   │   ├── mecon/                      ← AIF SPN/APN, deuda externa, recaudación
│   │   ├── riesgos pais/               ← EMBI LATAM, EMBI+ Argentina
│   │   └── worldbank/                  ← 22 indicadores + 6 WGI governance
│   ├── processed/                      ← datos procesados (PBI USD MEP, resultado fiscal, deuda SIGADE)
│   ├── Variables Finales/              ← ~45 CSVs/Excel finales consolidados (series listas para modelar)
│   ├── bonos/                          ← catálogo + vencimientos bonos soberanos USD (~77 bonos)
│   ├── basesingade deuda/              ← ~70 archivos .mdb trimestrales (2007-2025)
│   └── Bases Bonos/                    ← archivos .DAT de bonos
│
├── raw/                                ← datos alternativos
│   ├── global/                         ← FRED (fed funds, T10Y2Y, EMBI Global)
│   └── mep/                            ← TC Blue, MEP, CCL
│
└── scratch/                            ← pruebas y scripts auxiliares
```

---

## Stack Tecnológico

| Capa | Herramientas |
|------|-------------|
| **Lenguaje** | Python 3.10+, JavaScript (dashboard) |
| **Datos** | pandas, numpy, openpyxl, xlrd |
| **APIs** | yfinance, fredapi, wbgapi, requests (BCRA, datos.gob.ar, ArgentinaDatos) |
| **Bases de datos** | pyodbc (Microsoft Access .mdb/.accdb — SIGADE) |
| **Econometría** | statsmodels (OLS, VAR, VECM, ARDL), arch (GARCH), linearmodels |
| **ML** | scikit-learn (PCA) |
| **Deep Learning** | TensorFlow/Keras o PyTorch (LSTM, GRU, Transformer) — según notebooks |
| **Visualización** | matplotlib, seaborn, plotly (Python + JS 2.32.0 embebido), SheetJS |
| **Entorno** | Jupyter notebooks, ipywidgets, tqdm |

---

## Fuentes de Datos (10+ APIs y sistemas)

| Fuente | Series | Frecuencia |
|--------|--------|-----------|
| **BCRA API v4.0** | Reservas, TC, tasas, depósitos, préstamos, CER, ITCRM, agregados monetarios (~25 series) | Diaria/Mensual |
| **datos.gob.ar** (CKAN) | IPC, EMAE, ICA, Balanza de Pagos, deuda externa, resultado fiscal | Mensual/Trimestral |
| **Yahoo Finance** | S&P 500, MSCI EM, commodities (oro, petróleo, soja, maíz, trigo, cobre), divisas LATAM, Merval, ADRs | Diaria |
| **FRED** (St. Louis Fed) | Fed Funds, UST 2Y/5Y/10Y/30Y, T10Y2Y spread, VIX, HY OAS, EMBI Global, DXY, Trade-Weighted USD | Diaria |
| **World Bank API** | 22 indicadores desarrollo + 6 WGI governance para 7 países LATAM | Anual |
| **ArgentinaDatos API** | EMBI+ Argentina, TC Blue, MEP, CCL | Diaria |
| **SIGADE** (.mdb) | Saldo de deuda por instrumento/moneda/tasa, vencimientos forward | Trimestral |
| **Boletín Mensual** (Sec. Finanzas) | Deuda SPN 2019-2026 | Mensual/Trimestral |
| **INDEC** (.xls) | Oferta y demanda global, PBI trimestral | Trimestral |
| **J.P. Morgan** (Excel) | Serie histórica EMBI spread | Diaria |

---

## Flujos de Trabajo Principales

### 1. Adquisición de Datos
```
scripts/download/download_*.py  →  data/raw/<fuente>/  (CSVs crudos)
```

### 2. Procesamiento y Construcción de Variables
```
scripts/build_*.py              →  data/processed/ + data/Variables Finales/
src/build_dummies.py            →  dummies (cepo, gobierno, elecciones, defaults)
src/download_pending.py         →  bulk download + ratios (brecha, deuda/PBI, (X+M)/PBI)
```

### 3. Análisis Econométrico
```
notebooks/01_base_de_datos.ipynb    →  exploración y visualización
notebooks/02_modelos_regresion.ipynb →  OLS, VAR, VECM, ARDL, GARCH, PCA
```

### 4. Red Neuronal
```
notebooks/03_red_neuronal.ipynb     →  LSTM/GRU/Transformer
```

### 5. Dashboard Interactivo
```
notebooks/generar_visualizador.py   →  lee template + embebe CSVs → visualizador.html
```
El dashboard resultante es un archivo HTML standalone (sin servidor) con:
- Árbol lateral de variables colapsable
- Doble área de gráficos (c1/c2)
- Controles de media móvil, normalización (índice, log, %, z-score), rango de ejes
- Modo comparación y exportación a Excel

---

## Series Clave (de `src/glosario.py` y `docs/variables.md`)

### Variable Dependiente
- **EMBI+ Argentina** (spread en puntos básicos, diario desde 1999, ~7599 obs)

### Categorías de Variables Explicativas (~100 series)

| Categoría | Ejemplos |
|-----------|---------|
| **Push Factors Globales** | VIX, DXY, UST 10Y, Fed Funds, EMBI Global, HY OAS, MOVE, OFR FSI |
| **Commodities** | Oro, Petróleo WTI, Soja, Maíz, Trigo, Cobre |
| **Flujos de Capital** | MSCI EM, S&P 500, Merval, ADRs Galicia/YPF |
| **Liquidez y Monetario** | Reservas BCRA, M2, M3, Depósitos USD, Tasa Badlar, LELIQ |
| **Tipo de Cambio** | Oficial, Blue, MEP, CCL, Brecha Cambiaria, ITCRM |
| **Inflación y Actividad** | IPC, CER, EMAE, ICA |
| **Deuda Soberana** | Saldo deuda total/en USD/ARS, Vencimientos 2Y forward, Composición por moneda |
| **Sector Externo** | Cuenta Corriente, Balanza Comercial, Términos de Intercambio |
| **Fiscal** | Resultado Primario/Financiero SPN/APN, Recaudación |
| **Institucional/Historia** | Dummies: Cepo Cambiario, Gobierno, Elecciones, Defaults, Años desde Default |
| **Riesgo LATAM** | EMBI LATAM, EMBI Brasil/Colombia/México |

---

## Convenciones del Proyecto

- **Todos los paths son absolutos** con raíz en `C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo`. Si se traslada el proyecto, deben actualizarse.
- **Idioma**: documentación, comentarios y nombres de archivos en español.
- **Encoding**: las columnas de SIGADE .mdb tienen acentos y codificaciones inconsistentes entre años; los scripts de parsing normalizan aliases.
- **El archivo `requirements.txt`** contiene todas las dependencias. Instalar con:
  ```
  pip install -r requirements.txt
  ```
- **Archivos de log**: `extract_bcra_excel.log`, `extract_depositos.log`, `get_embi.log` registran resultados de extracciones.
- **Archivos auxiliares `tmp_*.py`** en la raíz son scripts de prueba/desarrollo; no forman parte del pipeline principal.
- **Visualizador**: para regenerar el dashboard ejecutar `notebooks/generar_visualizador.py`.
- **SIGADE**: los archivos .mdb requieren Microsoft Access Database Engine y pyodbc.
- **AGENTS.md** contiene información de git. Hacer commits en español con mensajes descriptivos.

---

## Estado Actual del Proyecto (Mayo 2026)

- Datos actualizados hasta abril 2026
- ~100 variables consolidadas en `data/Variables Finales/`
- Pipeline de descarga y procesamiento automatizado para la mayoría de las fuentes
- Saldo de deuda unificado (SIGADE 2007-2018 + Boletín Mensual 2019-2026) completado
- Vencimientos forward 2 años calculados
- Catálogo de bonos USD (77 bonos, 8 eras históricas) completado
- Dashboard interactivo standalone funcional
- **Pendiente**: ejecución final de modelos econométricos y red neuronal sobre el dataset consolidado
