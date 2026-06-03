# GUÍA DE ACTUALIZACIÓN DE SERIES DE TIEMPO

> **Propósito.** Este documento es el manual operativo para **actualizar todas las series de tiempo** que alimentan `notebooks/visualizador.html` (y el resto del pipeline analítico). Está escrito para que una IA (o una persona) pueda, sin contexto previo, reproducir cada serie: de dónde sale (API / web / archivo manual / cálculo propio), con qué script se baja o se construye, dónde queda el archivo y qué columnas consume el visualizador.
>
> **Cómo se actualiza el dashboard, en una frase:** se (re)generan los CSV/Excel de cada fuente → se ejecuta `python notebooks/generar_visualizador.py`, que embebe todos los datos en un HTML standalone.
>
> Última revisión del documento: **2026-06-02**. Datos del proyecto al corte abril/2026.

---

## 0. Mapa mental: 3 tipos de series

| Tipo | Cómo se actualiza | Ejemplos |
|------|-------------------|----------|
| **A. API automática** | Correr un script de `scripts/download/` o `src/`. Reescribe el CSV solo. | BCRA, datos.gob.ar (INDEC/MECON), World Bank, Yahoo Finance, FRED, ArgentinaDatos, BCRP |
| **B. Archivo manual + parser** | Descargar a mano un Excel/.mdb desde la web oficial → correr un script que lo convierte. | SIGADE (.mdb deuda), Boletín de Deuda MECON, INDEC Oferta-Demanda (.xls), ITCRM/CER/depósitos USD (Excel BCRA), EMBI J.P.Morgan, INDEC CIN (deuda externa), UTDT (ICC/ICG) |
| **C. Cálculo propio (derivada)** | Correr el script que combina fuentes ya bajadas. No requiere descargar nada nuevo. | Brecha cambiaria, PBI USD MEP, resultado fiscal, resultado fiscal estructural, dummies, ratios, vencimientos 2Y |

> **Importante (rutas):** casi todos los scripts usan **rutas absolutas** con raíz
> `C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo`. Si se mueve el proyecto, hay que actualizarlas. Los scripts de `scripts/download/` usan rutas relativas (`parents[2]`) y son portables.

---

## 1. Secuencia maestra de actualización

Orden recomendado (las derivadas dependen de las fuentes, por eso van al final):

```powershell
# --- BLOQUE A: APIs automáticas (no requieren intervención manual) ---
python scripts/download/download_bcra.py          # BCRA v4.0 (~21 series monetarias/cambiarias)
python scripts/download/download_datos_gob.py     # INDEC + MECON vía CKAN
python scripts/download/download_worldbank.py     # World Bank (16 indicadores + 6 WGI), 7 países
python scripts/download/download_yfinance.py      # Yahoo Finance (commodities, índices, FX, ADRs)
python scripts/download/download_ofr.py           # OFR Financial Stress Index
python src/download_pending.py                    # FRED + ArgentinaDatos (MEP/Blue/CCL + Riesgo País) + ITCRM + dummies + ratios
python scripts/download/update_series_2026.py     # Refresca vix/dxy/ust* en Variables Finales + FRED

# --- BLOQUE B: archivos manuales ya descargados → parsers ---
#   (Primero descargar los archivos a mano: ver §3. Luego:)
python src/get_embi_latam.py                      # EMBI LATAM desde Excel J.P.Morgan
python scripts/convert_bcra_excels.py             # ITCRM, CER, depósitos USD, préstamos USD
python src/extract_pbi.py                         # Oferta-Demanda, PBI sectores, FBKF (INDEC .xls)
python scripts/build_deuda_externa_indec.py       # Deuda externa por sector/plazo (INDEC CIN .xls)
python scripts/build_calendario_deuda_externa_serie.py  # Calendario pagos deuda externa (descarga sola los CIN)
python scripts/build_saldo_sigade.py              # Saldo deuda 2007-2018 (.mdb SIGADE)
python scripts/build_vencimientos_2y.py           # Vencimientos forward 2 años (.mdb SIGADE)
python scripts/build_saldo_unificado.py           # Une SIGADE + Boletín Mensual MECON

# --- BLOQUE C: derivadas / cálculo propio ---
python scripts/calcular_brecha.py                 # Brecha cambiaria (MEP / A3500)
python src/pbi_usd_trimestral.py                  # PBI trimestral en USD MEP
python scripts/build_resultado_fiscal.py          # Resultado fiscal SPN/APN 1993-2026
python src/variables/resultado_fiscal_estructural.py  # Resultado fiscal estructural (Gay-Escudero)

# --- FINAL: regenerar el dashboard ---
python notebooks/generar_visualizador.py          # Embebe todo en visualizador.html
```

> No todas las series cambian con la misma frecuencia. Para una actualización **diaria/semanal** suele bastar el BLOQUE A + regenerar. Para **mensual/trimestral** (INDEC, deuda, fiscal) hay que descargar los archivos manuales del BLOQUE B.

---

## 2. Fuentes tipo A — APIs automáticas

### 2.1 BCRA — API v4.0 Estadísticas Monetarias
- **Script:** `scripts/download/download_bcra.py`
- **Endpoint:** `https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{id}` — **público, sin API key**. Paginado (limit 3000, offset). `verify=False` (el cert del BCRA da problemas).
- **Salida:** `data/raw/bcra/{id:03d}_{slug}.csv` + `_index.csv`. Columnas: `fecha,valor`.
- **Series (id → slug):** 1 reservas_brutas · 4 tc_minorista · 5 tc_mayorista_a3500 · 7 tasa_badlar_privados · 8 tasa_tm20_privados · 12 tasa_dep_30d · 15 base_monetaria · 19 dep_cc_bcra · 21 dep_total · 22 dep_cc_privado · 23 dep_cajas_ahorro · 24 dep_plazo · 25 m2_var_anual · 26 prestamos_privado · 35 tasa_badlar_bp · 44 tasa_tamar · 109 m2 · 117 prest_total_privado · 152 pases_pasivos · 154 pases_activos · 155 leliq_notalq.
- **Nota:** los IDs de variable los lista la propia API (`/v4.0/monetarias` sin id). Si el BCRA renumera, revisar ahí.

### 2.2 datos.gob.ar (CKAN) — INDEC + MECON
- **Script:** `scripts/download/download_datos_gob.py`
- **Endpoint:** `https://datos.gob.ar/api/3/action/package_show?id={package_id}` → descarga cada recurso CSV/XLS del paquete. Sin key. User-Agent custom.
- **Salida:** `data/raw/indec/` y `data/raw/mecon/` (prefijo + slug del recurso) + `data/raw/_datos_gob_index.csv`.
- **Paquetes INDEC:** IPC nacional base dic-2016 · IPC variaciones · EMAE base 2004 · EMAE apertura sectorial · **ICA (intercambio comercial)** · **saldo comercial por países/regiones** · **balance de pagos MBP6** · cuenta corriente · **PBI en USD / per cápita / población** · indicadores oferta-demanda global precios constantes 2004 trimestral.
- **Paquetes MECON:** títulos públicos deuda · deuda externa bruta por sector residente · deuda externa privada (BCRA) · **IMIG SPNF** (resultado primario/financiero mensual) · esquemas AIF (SPN, Tesoro, APN, devengado) · **recursos tributarios** · subgrupos recaudación.
- **Nota:** los `package_id` cambian de nombre cuando MECON/INDEC reorganizan el portal. Si un paquete da "not found", buscar el nuevo slug en datos.gob.ar y actualizar la lista `PACKAGES`. Los nombres de archivo de salida (con su slug largo) son los que referencia el visualizador — **si cambian, romper­án el catálogo del template**.

### 2.3 World Bank — wbgapi + REST (WGI)
- **Script:** `scripts/download/download_worldbank.py`
- **Fuente:** librería `wbgapi` (sin key) para 16 indicadores; los **WGI** (governance) vía REST `https://api.worldbank.org/v2/...?source=3`.
- **Países:** ARG, BRA, CHL, COL, MEX, PER, URY. **Años:** 1990-2025 (WGI 1996-2024).
- **Salida:** `data/raw/worldbank/{slug}.csv` (long: `economy,year,value`) + `_index.csv`.
- **Indicadores:** gdp_usd (NY.GDP.MKTP.CD), gdp_per_capita, gdp_growth, inflation_cpi, gov_debt_gdp, exports_gdp, imports_gdp, trade_gdp, cab_gdp, fdi_gdp, reserves, credit_private_gdp, market_cap_gdp, broad_money_gdp, unemployment, population. **WGI:** polstab, goveff, rol, regqual, control_corruption, voice_accountability.

### 2.4 Yahoo Finance — yfinance
- **Script:** `scripts/download/download_yfinance.py` (historia completa desde 2000) y `scripts/download/update_series_2026.py` (refresco rápido de vix/dxy/ust*).
- **Fuente:** `yfinance` (sin key).
- **Salida:** `data/raw/global/{slug}.csv` y `data/raw/local/{slug}.csv` (`fecha,Open,High,Low,Close,Adj Close,Volume`) + `_yfinance_index.csv`. `update_series_2026.py` además escribe `data/Variables Finales/{vix,dxy,ust2y,ust5y,ust10y,ust30y}.csv`.
- **Tickers (slug → ticker):** vix ^VIX · move ^MOVE · dxy DX-Y.NYB · ust2y ^IRX · ust5y ^FVX · ust10y ^TNX · ust30y ^TYX · sp500 ^GSPC · msci_em EEM · wti CL=F · brent BZ=F · soja ZS=F · maiz ZC=F · trigo ZW=F · oro GC=F · cobre HG=F · brl BRL=X · clp CLP=X · mxn MXN=X · merval ^MERV · merval_usd ARGT · ypf_adr YPF · gga_adr GGAL.
- **Nota:** `ust2y` usa `^IRX` (13 semanas) como proxy corto. Yahoo a veces falla por rate-limit; reintentar.

### 2.5 FRED — St. Louis Fed
- **Scripts:** `src/download_pending.py` y `scripts/download/update_series_2026.py` (ambos traen FRED).
- **Endpoint:** `https://api.stlouisfed.org/fred/series/observations` — **requiere API key**. Key en uso (hardcodeada en los scripts): `45b7109fba6ea6b87a614fa9ff67997c`. Si caduca, sacar otra gratis en https://fred.stlouisfed.org/docs/api/api_key.html.
- **Salida:** `raw/global/fred_*.csv` (ojo: carpeta `raw/` en la raíz, **no** `data/raw/`).
- **Series (FRED id → slug):** DFF → fred_fedfunds · BAMLEMCBPIOAS → fred_embi_global · BAMLHE00EHYIEY → fred_us_hy_oas · T10Y2Y → fred_t10y2y · DTWEXBGS → fred_tw_usd · VIXCLS → fred_vix.

### 2.6 ArgentinaDatos — Riesgo País, MEP/Blue/CCL
- **Script:** `src/download_pending.py`
- **Fuente:** `https://api.argentinadatos.com/v1/...` (sin key).
  - **Riesgo País (EMBI+ Argentina, variable dependiente Y):** `/v1/finanzas/indices/riesgo-pais` → `data/raw/global/riesgo_pais_arg.csv` (`fecha,embi_arg`, puntos básicos, desde 1999). **También** existe copia en `data/Variables Finales/riesgo_pais_arg.csv` que usa el visualizador.
  - **Dólares MEP/Blue/CCL:** `/v1/cotizaciones/dolares/{blue|bolsa|contadoconliqui}` → `data/raw/mep/tc_{blue,mep,ccl}.csv`.
- **Nota:** `tc_mep` se usa luego para `brecha_cambiaria.csv`. La carpeta `data/raw/mep/` puede estar vacía hasta correr este script.

### 2.7 OFR — Financial Stress Index
- **Script:** `scripts/download/download_ofr.py`
- **Fuente:** CSV directo `https://www.financialresearch.gov/financial-stress-index/data/fsi.csv`.
- **Salida:** `data/raw/global/ofr_fsi.csv` → copiado/usado como `data/Variables Finales/ofr_fsi.csv` (`Date,OFR FSI`).

### 2.8 BCRP (Perú) — EMBIG histórico LATAM (alternativo)
- **Script:** `scripts/build_embig_bcrp.py`
- **Fuente:** API REST del Banco Central de Reserva del Perú `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{cod}/json/{ini}/{fin}/ing` (spreads EMBIG diarios JPMorgan, en pbs, desde 1998).
- **Salida:** `data/raw/bcrp_embig/embig_<pais>.csv` + `embig_bcrp_wide.csv`.
- **Series:** américa_latina (PD04708XD), argentina (PD04710XD), brasil, chile, colombia, méxico, perú, ecuador, venezuela, emergentes, etc.
- **Uso:** fuente homogénea EMBI Global para todo el período (alternativa a empalmar EMBI+ con EMBIG). No siempre embebida en el visualizador; útil para robustez.

### 2.9 Heritage — Index of Economic Freedom (opcional)
- **Script:** `scripts/download/download_heritage.py`
- **Fuente:** `https://static.heritage.org/index/data/{year}/{year}_indexofeconomicfreedom_data.xlsx`. Anual.

---

## 3. Fuentes tipo B — Descarga manual + parser

> Para estas, **primero hay que bajar el archivo a mano** desde la web oficial y dejarlo en la ruta indicada; recién después corre el parser. Conviene renombrar manteniendo el patrón que el parser espera.

### 3.1 SIGADE — Saldo de deuda y vencimientos (.mdb)
- **Qué es:** ~70 bases Microsoft Access trimestrales (2007-2025) con el detalle de la deuda pública por instrumento/moneda/tasa y los vencimientos.
- **Dónde conseguirlas:** Secretaría de Finanzas, "Gráficos de la deuda" → https://www.argentina.gob.ar/economia/finanzas/graficos-deuda (descargar las bases SIGADE por período).
- **Dónde van:** `data/basesingade deuda/*.mdb`. **El nombre debe terminar en una fecha `YYYY-MM-DD`** (el parser la extrae con regex).
- **Requisitos técnicos:** Windows + **Microsoft Access Database Engine** + `pyodbc` (driver `Microsoft Access Driver (*.mdb, *.accdb)`).
- **Parsers:**
  - `scripts/build_saldo_sigade.py` → `data/Variables Finales/saldo_deuda.xlsx` (hojas A.1 por instrumento/situación, A.3 por moneda/tasa). Millones USD.
  - `scripts/build_vencimientos_2y.py` → `data/Variables Finales/vencimientos_2y_nuevo.xlsx` (vencimientos forward 2 años por tipo y moneda; el generador lo lee transpuesto).
  - `scripts/inspect_mdb_tables.py` → utilidad para inspeccionar nombres de tablas/columnas de un .mdb nuevo.
- **Cuidado con el encoding:** las columnas de los .mdb tienen acentos y nombres inconsistentes entre años. Los parsers tienen listas de **aliases** (`CLASIF_ALIASES`, `SALDO_USD_ALIASES`, etc.). Si aparece un .mdb nuevo con un encabezado no contemplado, hay que agregar el alias.

### 3.2 Boletín de Deuda Mensual (MECON) — saldo 2019-2026
- **Qué es:** Excel del Boletín de la deuda pública (SPN), mensual desde 2019.
- **Dónde:** Secretaría de Finanzas (mismo portal de deuda). Archivo actual en repo: `data/Variables Finales/boletin_mensual_31_03_2026_1.xlsx` (y copia en `data/raw/mecon/`).
- **Parser:** `scripts/build_saldo_unificado.py` une **SIGADE (2007-2018, Adm. Central)** + **Boletín (2019-2026, SPN)** → `data/Variables Finales/saldo_deuda_unificado.xlsx`. Misma estructura A.1 (TÍTULOS / LETRAS / PRÉSTAMOS).
- **Nota de cobertura:** hay un cambio de universo (Adm. Central → SPN) en 2019; documentado en el script.

### 3.3 INDEC — Oferta y Demanda Global / PBI / FBKF / sectores (.xls)
- **Qué es:** cuadros de Cuentas Nacionales (oferta-demanda, PBI por sector, FBKF, deflactores).
- **Archivo fuente oficial:** `sh_oferta_demanda_03_26.xls` (INDEC). En repo: `data/Variables Finales/sh_oferta_demanda_03_26.xls`. Se descarga del INDEC (Cuentas Nacionales). Ver también `docs` de referencia: el archivo trae cuadros 1 (PBI constante), 8 (PBI corriente), 12, etc.
- **Parser:** `src/extract_pbi.py` → genera `oferta_demanda_constante.csv`, `oferta_demanda_corriente.csv`, `oferta_demanda_ipi.csv`, `pbi_sectores_*.csv`, `fbkf_*.csv`, `pbi_constante_2004.csv`, `pbi_corriente.csv` en `data/Variables Finales/`.
- **Estructura:** el lector asume año en fila 3, trimestre en fila 4, datos desde fila 6 (formato horizontal INDEC).
- **Términos de Intercambio (`ti_mensual.csv`):** del cuadro de TI del INDEC (precios/cantidades de expo e impo). Archivo `TI.xls` en `Variables Finales`.

### 3.4 INDEC — Deuda externa bruta (Cuentas Internacionales, CIN .xls)
- **Qué es:** deuda con **no residentes**, todos los sectores (concepto distinto al saldo de deuda MECON). Metodología BPM6.
- **Fuente:** INDEC, cuadros CIN. Descarga directa: `https://www.indec.gob.ar/ftp/cuadros/economia/cin_{ROMANO}_{ANIO}.xls` (ej. `cin_IV_2025.xls`).
- **Parsers:**
  - `scripts/build_deuda_externa_indec.py` (lee `cin_IV_2025.xls` en la raíz) → `deuda_externa_sectores.csv` (Cuadro 23: total + por sector institucional, aditivo), `deuda_externa_plazo.csv` (corto/largo plazo), `deuda_externa_calendario_pagos_2025T4.csv` (snapshot Cuadro 25). Millones USD, fin de trimestre.
  - `scripts/build_calendario_deuda_externa_serie.py` → **descarga sola** todos los `cin_*.xls` (a `raw/indec_cin/`) y arma la serie temporal del calendario de pagos: `deuda_externa_calendario_serie.csv` y `deuda_externa_calendario_panel.csv` (cobertura desde 2017T3, cuando empieza ese cuadro BPM6).
- **Para actualizar:** cambiar `XLS = "cin_IV_2025.xls"` al último trimestre publicado y volver a descargar ese archivo a la raíz.

### 3.5 BCRA — ITCRM, CER, Depósitos/Préstamos USD (Excel manuales)
- **Qué es:** series que el BCRA publica como descarga Excel (no siempre en la API monetaria v4).
- **Archivos a bajar a mano** y dejar en `data/Variables Finales/`:
  - `ITCRMSerie.xlsx` (BCRA, "Índices de Tipo de Cambio Real Multilateral", hoja `ITCRM y bilaterales`) → ITCRM multilateral + bilaterales por país.
  - `diar_cer.xls` (BCRA, CER diario).
  - `series (3).xlsm` (BCRA, "series" — planilla grande con depósitos/préstamos en USD; hojas `D` diaria).
- **Parser:** `scripts/convert_bcra_excels.py` →
  - `data/Variables Finales/itcrm_diario.csv` (col fecha = `Periodo`; cols `ITCRM `, `ITCRB <país>`).
  - `data/raw/bcra/cer.csv` (el generador lee CER de `raw/`, **no** de Variables Finales).
  - `depositos_usd_totales.csv`, `depositos_usd_residentes.csv`, `depositos_usd_secprivnofin.csv`, `prestamos_privados_usd_q.csv`.
- **Alternativa API:** `src/download_pending.py` también baja ITCRM por la API v2 del BCRA (variable 28) a `data/raw/bcra/itcrm.csv`, y `src/extract_depositos_bcra.py` / `src/download_cer_tip.py` cubren casos puntuales.
- **TIP ETF (deflactor IPC USA):** `data/raw/global/tip_etf.csv` — viene de Yahoo (ticker TIP) vía `src/download_cer_tip.py`.

### 3.6 J.P. Morgan — EMBI LATAM (Excel histórico)
- **Qué es:** serie histórica de spreads EMBI (incluye columna `LATINO`).
- **Archivo:** `data/raw/Serie_Historica_Spread_del_EMBI.xlsx` (planilla J.P.Morgan que circula públicamente; encabezados en fila 2).
- **Parser:** `src/get_embi_latam.py` → `data/raw/global/embi_latam.csv` (`fecha,embi_latam`). Copia consumida por el visualizador: `data/Variables Finales/embi_latam.csv`.

### 3.7 Dólar MEP para PBI USD (Excel)
- **Archivo:** `data/raw/indec/tc_mep_2026-04-28.xlsx` (serie MEP diaria; usada por `calcular_brecha.py` y `pbi_usd_trimestral.py`). Se puede regenerar el MEP desde ArgentinaDatos (§2.6) — verificar que la columna se llame `valor`/`fecha`.

### 3.8 UTDT — Confianza del Consumidor (ICC) y del Gobierno (ICG)
- **Qué es:** índices de la Universidad Torcuato Di Tella (mensuales).
- **Fuente:** UTDT — Centro de Investigación en Finanzas (https://www.utdt.edu/ → ICC / ICG). Se descargan a mano (o vía Alphacast; las columnas `*_current_prices_*` sugieren export de Alphacast).
- **Archivos (manuales, ya en repo):** `data/Variables Finales/ICC.csv` (col fecha `Date`) y `data/Variables Finales/ICG_utdt.csv` (`Date,ICG,Variacion_ICG`).
- **Actualización:** reemplazar el CSV agregando los meses nuevos, manteniendo nombres de columna.

---

## 4. Fuentes tipo C — Series derivadas (cálculo propio)

| Serie / archivo | Script | Insumos | Fórmula / nota |
|---|---|---|---|
| `brecha_cambiaria.csv` | `scripts/calcular_brecha.py` | `tc_mep_2026-04-28.xlsx` + `005_tc_mayorista_a3500.csv` | `brecha = mep / bcra_a3500 − 1`. Cols: `fecha,mep,bcra_a3500,brecha_cambiaria`. (El visualizador usa `mep`, `bcra_a3500` y `brecha_cambiaria` de este archivo.) |
| `pbi_trimestral_usd_mep.csv` | `src/pbi_usd_trimestral.py` | PBI corriente (cuadro 8 INDEC) + MEP diario | `PBI_usd = PBI_pesos / MEP_promedio_trimestral`. Cols: `periodo,pbi_pesos_mm,pbi_usd_mm`. Usado como **deflactor USD** en el dashboard. |
| `Resultado fiscal-unificado.xlsx` / `resultado_fiscal.xlsx` | `scripts/build_resultado_fiscal.py` | AIF SPN/APN (MECON, ya bajados por datos.gob) | Serie 1993-2026 (mensual/trim/anual): ingresos, gastos primarios, intereses, primario, financiero. |
| `resultado_fiscal_estructural.csv` | `src/variables/resultado_fiscal_estructural.py` | Resultado fiscal + PBI + FBKF + desempleo (WB) + TI | Metodología Gay-Escudero (2010): PIB potencial Cobb-Douglas, ajuste cíclico y por commodities. Cols `SE_pctPIB,SCA_pctPIB,SP_oficial_pctPIB`, 2006Q1+. |
| `dummy_cepo.csv`, `dummy_gob.csv`, `dummy_elec.csv`, `defaults_history.csv`, `years_since_default.csv` | `src/download_pending.py` (bloque 5) | fechas hardcodeadas | Cepo: 2011-10-28→2015-12-16 y 2019-09-01→2024-12-13. Gobiernos, elecciones (±60 días), defaults (2001/2014/2020). **Actualizar las listas al agregar eventos nuevos.** Hay `scripts/update_cepo.py` para el cepo. |
| `spread_tasas.csv`, `apertura_xm.csv`, `deuda_pbi.csv` | `src/download_pending.py` (bloque 7) | BCRA / World Bank | spread = BADLAR − tasa dep 30d; (X+M)/PBI y Deuda/PBI directos del WB. |
| `graficos_deuda.xlsx` | `scripts/build_graficos_deuda.py` | saldo deuda unificado | post-proceso para gráficos de composición. |

---

## 5. Regenerar el visualizador

```powershell
python notebooks/generar_visualizador.py
```

- Lee `notebooks/visualizador_template.html`, **extrae del catálogo (`CATALOG`/dummies) qué archivos y columnas** necesita (regex sobre `file:`, `dateCol:`, `valCol:`), lee esos CSV/XLSX desde `data/Variables Finales/` (y algunos de `data/raw/`), **embebe los datos como JSON** dentro del HTML y, si están presentes `plotly.min.js` y `xlsx.full.min.js`, los embebe también → `notebooks/visualizador.html` **standalone** (se abre sin servidor).
- Deflactores especiales que embebe aparte: `pbi_corriente.csv` (÷PBI ARS), `pbi_trimestral_usd_mep.csv` (÷PBI USD), `raw/bcra/cer.csv` (CER), `raw/global/tip_etf.csv` (IPC USA).
- **Regla de oro:** editar siempre **`visualizador_template.html`** (el `.html` final se regenera). Para **agregar una serie** al dashboard: 1) generar su CSV en `data/Variables Finales/`, 2) agregar su entrada `{ id, label, file, dateCol, valCol, unit, freq }` al `CATALOG` del template, 3) regenerar.

> El catálogo del template es la **fuente de verdad** de qué se muestra. El `src/glosario.py` es un catálogo paralelo (con metadata, fuente, rango) usado por el pipeline econométrico; conviene mantenerlos consistentes pero el visualizador sólo mira el template.

---

## 6. Inventario rápido: serie → fuente → archivo

| Grupo (en el árbol del visualizador) | Fuente | Archivo(s) en `Variables Finales/` salvo aclaración |
|---|---|---|
| EMBI+ Argentina (Y) | ArgentinaDatos API | `riesgo_pais_arg.csv` |
| VIX, MOVE, DXY, S&P500, MSCI EM, oro, WTI, Brent, soja, maíz, trigo, cobre, BRL/CLP/MXN | Yahoo Finance | `vix.csv`, `dxy.csv`, `data/raw/global/*.csv` |
| UST 2/5/10/30Y | Yahoo Finance | `ust2y.csv`…`ust30y.csv` |
| Fed Funds, T10Y2Y, US HY OAS, EMBI Global, TW USD, VIX FRED | FRED | `raw/global/fred_*.csv` |
| OFR FSI | OFR | `ofr_fsi.csv` |
| EMBI LATAM | J.P.Morgan (Excel) | `embi_latam.csv` |
| Reservas, depósitos ARS, base, M2, tasas, pases, LELIQ, préstamos | BCRA API v4 | `data/raw/bcra/*.csv`, `001_reservas_brutas.csv`, `021_dep_total.csv` |
| Depósitos/Préstamos USD | BCRA Excel (`series (3).xlsm`) | `depositos_usd_*.csv`, `prestamos_privados_usd_q.csv` |
| TC MEP / A3500 / Brecha | ArgentinaDatos + BCRA + cálculo | `brecha_cambiaria.csv` |
| ITCRM (multilateral + bilaterales) | BCRA Excel (`ITCRMSerie.xlsx`) | `itcrm_diario.csv` |
| IPC, EMAE | INDEC vía datos.gob | `data/raw/indec/*.csv` |
| CER (deflactor) | BCRA Excel (`diar_cer.xls`) | `data/raw/bcra/cer.csv` |
| ICA (intercambio comercial), saldo comercial por país | INDEC vía datos.gob | `ica_*.csv`, `saldo_comercial_paises_*.csv` |
| Términos de Intercambio | INDEC (`TI.xls`) | `ti_mensual.csv` |
| Balance de Pagos MBP6 | INDEC vía datos.gob | `balance_pagos_*.csv` |
| Oferta-Demanda, PBI sectores, FBKF, PBI const/corr | INDEC (`sh_oferta_demanda_03_26.xls`) → `extract_pbi.py` | `oferta_demanda_*.csv`, `pbi_sectores_*.csv`, `fbkf_*.csv`, `pbi_constante_2004.csv`, `pbi_corriente.csv` |
| PBI en USD MEP | cálculo propio | `pbi_trimestral_usd_mep.csv` |
| Saldo de deuda (total/moneda) | SIGADE .mdb + Boletín MECON | `saldo_deuda.csv`, `saldo_deuda_moneda.csv`, `saldo_deuda_unificado.xlsx` |
| Vencimientos 2Y | SIGADE .mdb | `vencimientos_2y_nuevo.xlsx` |
| Deuda externa (sectores/plazo/calendario) | INDEC CIN .xls | `deuda_externa_sectores.csv`, `deuda_externa_plazo.csv`, `deuda_externa_calendario_*.csv` |
| Resultado fiscal (SPN/APN) | MECON AIF | `Resultado fiscal-unificado.xlsx` |
| Resultado fiscal estructural | cálculo propio (Gay-Escudero) | `resultado_fiscal_estructural.csv` |
| ICC / ICG | UTDT (manual) | `ICC.csv`, `ICG_utdt.csv` |
| World Bank (PBI, deuda, comercio, WGI) | World Bank API | `data/raw/worldbank/*.csv` |
| Dummies (cepo, gobierno, elec, defaults) | cálculo propio | `dummy_*.csv`, `defaults_history.csv`, `years_since_default.csv` |

---

## 7. Checklist y problemas frecuentes

- [ ] **Keys/credenciales:** sólo FRED requiere key (hardcodeada). El resto es público.
- [ ] **`package_id` de datos.gob** cambian de slug periódicamente → si falla, buscar el nuevo y mantener el **mismo nombre de archivo de salida** (lo referencia el template).
- [ ] **SIGADE .mdb:** requiere Windows + Access Database Engine + pyodbc; nombres de columna varían por año (agregar aliases). El nombre de archivo debe terminar en `YYYY-MM-DD`.
- [ ] **CIN INDEC:** para nuevo trimestre, actualizar `XLS=` en `build_deuda_externa_indec.py` y bajar el `cin_*.xls`.
- [ ] **Excel manuales BCRA** (ITCRM/CER/series.xlsm) y **UTDT** (ICC/ICG): no hay API estable; bajar a mano y respetar nombres de hoja/columna.
- [ ] **Rutas absolutas** en los scripts de `scripts/` y `src/` (no en `scripts/download/`). Si se mueve el repo, hay que reemplazarlas.
- [ ] **Dummies con fechas hardcodeadas:** al sumar elecciones/cambios de gobierno/cepo/default nuevos, editar las listas en `src/download_pending.py` (o `scripts/update_cepo.py`).
- [ ] **Después de cualquier cambio de datos:** correr `notebooks/generar_visualizador.py` y abrir `visualizador.html` para verificar que las series cargan (revisar la consola del script por `[!] NO ENCONTRADO` o columnas faltantes).
- [ ] **Auditoría de cobertura:** `src/download_pending.py` imprime al final un reporte de series que empiezan tarde o terminan temprano (`_download_log.txt`).

---

## 8. Referencias cruzadas dentro del repo
- `PROYECT.md` — panorama general y arquitectura.
- `src/glosario.py` — catálogo programático (id, fuente, ruta, freq, unidad, rango) para el pipeline econométrico.
- `docs/variables.md` — catálogo extendido de variables.
- `notebooks/visualizador_template.html` (`CATALOG`) — qué series muestra el dashboard (fuente de verdad del front).
- `notebooks/generar_visualizador.py` — ensamblador del HTML.
