# 📚 Variables del Modelo — Riesgo País Argentino

**Última actualización:** 2026-04-23
**Estado descarga:** ⬜ No iniciado · 🟡 En progreso · ✅ Obtenida · ⚠️ Requiere acción manual · ❌ No disponible · 🔧 Script listo (ejecutar `python src/build_dummies.py`)

---

## 0. Checklist — Lista Original de Variables Propuestas

> **Instrucciones:** completar la columna **¿Coincide?** con ✅ (sí, está como espero) / ❌ (no coincide / falta) / ❓ (dudoso). Usar la columna **Observaciones** para aclaraciones.
>
> **Faltantes conocidos (pre-check):** EMBI Latinoamericano (no descargado), CDS 5Y Argentina (fuente paga), Volumen BYMA, Encajes USD BCRA, Servicios de deuda 365d, TCRM BCRA, Inflación esperada REM 12m, Breakeven inflación AR, Credit ratings, Fraser EFW, WEF GCI, Doing Business, Resultado fiscal estructural, Reservas netas (cálculo), Deuda/PBI (cálculo), Brecha cambiaria (cálculo).

### 0.1 Variable dependiente (Y)

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 1 | EMBI+ Argentina (spread bps) — ArgentinaDatos | ✅ |C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
<!-- | 2 | CDS 5Y Argentina (alternativa) |  |  | -->

### 0.2 Globales — Push factors

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 3 | VIX |✅ | C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
| 4 | DXY (US Dollar Index) |✅ | C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
| 5 | UST 2Y |✅ | C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
| 6 | UST 5Y |✅ | C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
| 7 | UST 10Y |✅ | C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
| 8 | UST 30Y |✅ | C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
| 9 | EMBI Global |  |  |
| 10 | EMBI Latinoamericano | ✅ | C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
<!-- | 11 | Fed Funds |  |  | -->
<!-- | 12 | S&P 500 |  |  | -->
<!-- | 13 | MSCI EM |  |  | -->
| 14 | MOVE ("VIX de los bonos") |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
| 15 | OFR Financial Stress Index |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global |
<!-- | 16 | Petróleo WTI |  |  | -->
<!-- | 17 | Petróleo Brent |  |  | -->
<!-- | 18 | Oro |  |  | -->
| 19 | Soja |  |  |
| 20 | Maíz |  |  |
| 21 | Trigo |  |  |
<!-- | 22 | Cobre |  |  | -->
| 23 | BRL/USD |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\global-brl.csv|
<!-- | 24 | CLP/USD |  |  | -->
<!-- | 25 | MXN/USD |  |  | -->

### 0.3 Flujo de capitales — Local

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 26 | Volumen Merval con signo según subida o bajada (proxy con YPF y GGAL)/ PBI (será muy chino y espurio?)| ✅ |C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\local|
<!-- | 27 | Índice Merval (ARS) |  |  | -->
<!-- | 28 | Merval en USD |  |  | -->
<!-- | 29 | Galicia ADR (GGAL) |  |  | -->
<!-- | 30 | YPF ADR |  |  | -->
| 31 | Cuenta Capital / PBI (INDEC) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
| 32 | IED / PBI (World Bank) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec

### 0.4 Liquidez (BCRA + WB)

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 33 | Reservas Internacionales Brutas |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra
| 34 | Reservas Internacionales Netas (cálculo) |  |  |
| 35 | Depósitos en Dólares Residentes (AA) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra
<!-- | 36 | Encajes USD en BCRA |  |  | -->
<!-- | 37 | Base Monetaria |  |  | -->
<!-- | 38 | M2 |  |  | -->
| 39 | Depósitos en Dólares Totales (Z) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra
<!-- | 40 | Depósitos plazo fijo |  |  | -->
| 41 | Préstamos sector privado / PBI |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra
<!-- | 42 | LELIQ / NotaLiq |  |  | -->
<!-- | 43 | Pases pasivos |  |  | -->
<!-- | 44 | Broad Money / GDP (WB) |  |  | -->

### 0.5 Crecimiento y expectativas

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 45 | PBI real USD (WB) |  |  |
| 46 | PBI per cápita (WB) |  |  |
| 47 | PBI crecimiento (WB) |  |  |
| 48 | EMAE mensual (INDEC) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
| 49 | IPC general (INDEC) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
<!-- | 50 | Inflación CPI (WB) |  |  | -->

### 0.6 Endeudamiento

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 51 | Deuda externa bruta (Mecon) |  |  |
| 52 | Deuda externa privada (Mecon) |  |  |
| 53 | Títulos públicos de deuda (Mecon) |  |  |
| 54 | Deuda gobierno central / PBI (WB) |  |  |
| 55 | AIF SPN |  |  |
| 56 | AIF APN |  |  |
| 57 | AIF Tesoro |  |  |
| 58 | Servicios de deuda 365d |  |  |
| 59 | Deuda / PBI (cálculo) |  |  |

### 0.7 Sector externo

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 60 | ICA — Exportaciones + Importaciones (INDEC) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
<!-- | 61 | Saldo comercial por países (INDEC) |  |  | -->
| 62 | Exportaciones / PBI (WB) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
| 63 | Importaciones / PBI (WB) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
| 64 | Trade / PBI (apertura) (WB) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
| 65 | TCRM — Tipo de cambio real multilateral (BCRA) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra
| 66 | Cuenta Corriente / PBI (WB) (Trimestral) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
| 67 | Cuenta Corriente detallada (INDEC) |✅| C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
| 68 | Balance de Pagos MBP6 (INDEC) | ✅ |  |
<!-- | 69 | (X+M)/PBI — apertura (cálculo) |  |  | -->
<!-- | 70 | Reservas Internacionales (WB anual) |  |  | -->

### 0.8 Política fiscal

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
<!-- | 71 | IMIG — Ingresos y gastos SPNF (Mecon) |  |  | -->
<!-- | 72 | Recursos tributarios totales (Mecon) |  |  | -->
<!-- | 73 | Recaudación por subgrupos (Mecon) |  |  | -->
| 74 | AIF |  |  |
| 75 | Resultado Fiscal Estructural (cálculo / FMI) |  |  |

### 0.9 Apertura comercial y cambiaria

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 76 | Dummy Cepo cambiario |  |  |
| 77 | TC Oficial A3500 mayorista | ✅ |  |
<!-- | 78 | TC Oficial minorista |  |  | -->
<!-- | 79 | TC MEP (AL30) |  |  | -->
| 80 | TC CCL |  |  |
<!-- | 81 | TC Blue |  |  | -->
| 82 | Brecha cambiaria (CCL/Oficial − 1) (cálculo) |  |  |
| 83 | Heritage Index of Economic Freedom |  |  |

### 0.10 Volatilidad local e inflación

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 84 | TCN A3500 (volatilidad) || C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra
| 85 | IPC variaciones (INDEC) || C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec
<!-- | 86 | Inflación esperada REM 12m (BCRA) |  |  | -->
| 87 | Breakeven inflation AR (cálculo) |  |  |
<!-- | 88 | Tasa BADLAR |  |  | -->
<!-- | 89 | Tasa TM20 |  |  | -->
<!-- | 90 | Tasa depósitos 30d |  |  | -->

### 0.11 Sistema financiero

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
<!-- <!-- | 91 | Crédito sector privado / PBI (WB) |  |  | -->
| 92 | Capitalización bursátil / PBI (WB) |  |  |
<!-- | 93 | Préstamos totales sector privado (BCRA) |  |  |
| 94 | Spread tasas activa-pasiva (cálculo) |  |  |
| 95 | Desempleo (WB) |  |  |
| 96 | Población (WB) |  |  | --> -->

### 0.12 History matters

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 97 | N° de defaults soberanos desde 1990 |  |  |
| 98 | Años desde último default | ✅ |  |
<!-- | 99 | Credit rating S&P / Moody's / Fitch |  |  | -->

### 0.13 Riesgo / sesgo político

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
| 100 | Dummy gobierno (Menem → Milei) |  |  |
| 101 | Dummy ventana electoral (±60d) |  |  |
| 102 | WGI — Political Stability |  |  |
| 103 | WGI — Government Effectiveness |  |  |
| 104 | WGI — Rule of Law |  |  |
| 105 | WGI — Voice & Accountability |  |  |
| 106 | WGI — Control of Corruption |  |  |
| 107 | WGI — Regulatory Quality |  |  |

### 0.14 Reformas pendientes (propuesta)

| # | Variable | ¿Coincide? | Observaciones |
|---|---|---|---|
<!-- | 108 | Fraser Economic Freedom of the World |  |  | -->
<!-- | 109 | WEF Global Competitiveness Index |  |  | -->
<!-- | 110 | Doing Business (histórico, descontinuado 2021) |  |  | -->

---

## 1. Variable Dependiente (Target)

| Efecto | Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|---|
| Riesgo país (Y) | EMBI+ Argentina (spread, bps) | ArgentinaDatos API | Diaria | Sin key | ✅ | `descargar_argentinadatos('riesgo_pais')` vía `data_loader.py` |
| Riesgo país (Y, alternativa) | CDS 5Y Argentina | Refinitiv/Bloomberg (pago) · alternativa DB.nomics | Diaria | ⚠️ pago o limitado | ⬜ | — |

> **Nota:** Se implementó la descarga desde la API de ArgentinaDatos (`api.argentinadatos.com/v1/finanzas/indices/riesgo-pais`). Serie disponible desde 1999. Función `descargar_argentinadatos` en `src/data_loader.py`.

---

## 2. Flujo de Capitales

### 2.1 Globales (factores push)

| Variable | Descripción | Fuente | Ticker/Serie | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|---|---|
| VIX | Volatilidad implícita S&P500 (aversión al riesgo global) | Yahoo Finance | `^VIX` | Diaria | Sin key (yfinance) | ✅ | `raw/global/vix.csv` |
| DXY | US Dollar Index (fortaleza del dólar) | Yahoo Finance | `DX-Y.NYB` | Diaria | Sin key | ✅ | `raw/global/dxy.csv` |
| UST 2Y | Tesoro EEUU 2 años | Yahoo Finance | `^IRX` proxy | Diaria | Sin key | ✅ | `raw/global/ust2y.csv` |
| UST 5Y | Tesoro EEUU 5 años | Yahoo Finance | `^FVX` | Diaria | Sin key | ✅ | `raw/global/ust5y.csv` |
| UST 10Y | Tesoro EEUU 10 años | Yahoo Finance | `^TNX` | Diaria | Sin key | ✅ | `raw/global/ust10y.csv` |
| UST 30Y | Tesoro EEUU 30 años | Yahoo Finance | `^TYX` | Diaria | Sin key | ✅ | `raw/global/ust30y.csv` |
| EMBI Global | Spread soberano emergentes (control) | FRED | `BAMLEMCBPIOAS` | Diaria | ⚠️ FRED key | ⬜ | — |
| Fed Funds | Tasa de política FED | FRED | `DFF` | Diaria | ⚠️ FRED key | ⬜ | — |
| S&P 500 | Índice bursátil EEUU | Yahoo Finance | `^GSPC` | Diaria | Sin key | ✅ | `raw/global/sp500.csv` |
| MSCI EM | Índice mercados emergentes | Yahoo Finance | `EEM` | Diaria | Sin key | ✅ | `raw/global/msci_em.csv` |
| MOVE | Volatilidad treasuries | Yahoo Finance | `^MOVE` | Diaria | Sin key | ✅ | `raw/global/move.csv` |
| OFR FSI | Financial Stress Index | OFR (US Treasury) | — | Diaria | CSV público | ✅ | `raw/global/ofr_fsi.csv` |
| Petróleo WTI | Commodity energético | Yahoo Finance | `CL=F` | Diaria | Sin key | ✅ | `raw/global/wti.csv` |
| Petróleo Brent | Commodity energético | Yahoo Finance | `BZ=F` | Diaria | Sin key | ✅ | `raw/global/brent.csv` |
| Oro | Commodity refugio | Yahoo Finance | `GC=F` | Diaria | Sin key | ✅ | `raw/global/oro.csv` |
| Soja | Commodity clave Argentina | Yahoo Finance | `ZS=F` | Diaria | Sin key | ✅ | `raw/global/soja.csv` |
| Maíz | Commodity Argentina | Yahoo Finance | `ZC=F` | Diaria | Sin key | ✅ | `raw/global/maiz.csv` |
| Trigo | Commodity Argentina | Yahoo Finance | `ZW=F` | Diaria | Sin key | ✅ | `raw/global/trigo.csv` |
| Cobre | Commodity industrial | Yahoo Finance | `HG=F` | Diaria | Sin key | ✅ | `raw/global/cobre.csv` |
| BRL/USD | Real brasileño | Yahoo Finance | `BRL=X` | Diaria | Sin key | ✅ | `raw/global/brl.csv` |
| CLP/USD | Peso chileno | Yahoo Finance | `CLP=X` | Diaria | Sin key | ✅ | `raw/global/clp.csv` |
| MXN/USD | Peso mexicano | Yahoo Finance | `MXN=X` | Diaria | Sin key | ✅ | `raw/global/mxn.csv` |

**Justificación teórica:** El canal de "push factors" (Calvo-Leiderman-Reinhart, 1993) sostiene que la liquidez global y el costo del capital en EEUU explican buena parte del spread soberano de emergentes. VIX y DXY capturan aversión al riesgo; UST captura el costo de oportunidad.

### 2.2 Locales

| Variable | Descripción | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|---|
| Volumen BYMA/PBI | Actividad del mercado local normalizada | BYMA (estadísticas) + INDEC CN | Diaria (volumen); Trimestral (PBI) | Scraping BYMA | ⬜ | `raw/local/byma_volumen.csv` |
| Índice Merval | Referencia de equity local | Yahoo `^MERV` | Diaria | Sin key | ✅ | `raw/local/merval.csv` |
| Merval en USD | Merval ajustado por TC | Yahoo `^MERV` / cálculo | Diaria | Sin key | ✅ | `raw/local/merval_usd.csv` |
| Galicia ADR | ADR banco Galicia | Yahoo `GGAL` | Diaria | Sin key | ✅ | `raw/local/gga_adr.csv` |
| YPF ADR | ADR YPF | Yahoo `YPF` | Diaria | Sin key | ✅ | `raw/local/ypf_adr.csv` |
| Cuenta Capital / PBI | Saldo financiero de la BP | INDEC — Balance de Pagos | Trimestral | CSV | ✅ | `raw/indec/balance_pagos_*.csv` |
| IED (Inversión Extranjera Directa) | Flujo de inversión productiva del exterior | World Bank | Anual | WB API | ✅ | `raw/worldbank/fdi_gdp.csv` |

---

## 3. Liquidez

| Variable | Descripción | Fuente | Serie BCRA | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|---|---|
| Reservas Internacionales Brutas | Stock de reservas del BCRA | BCRA API | `1` | Diaria | Sin key | ✅ | `raw/bcra/001_reservas_brutas.csv` |
| Reservas Internacionales Netas | Brutas − swaps − encajes − Repo − DEGs | Cálculo propio | — | Diaria (reconstruida) | Cálculo | ⬜ | `processed/reservas_netas.csv` |
| Depósitos en Dólares Totales | Depósitos en usd (expresados en dolares) totales (1) | BCRA API | Dinámico | Diaria | Sin key | ✅ | `raw/bcra/depositos_usd.csv` |
| Encajes USD en BCRA | Fondos inmovilizados en moneda extranjera | BCRA — Informe Monetario | — | Mensual/Diaria | Scrape | ⬜ | — |
| Base Monetaria | BM en pesos | BCRA API | `15` | Diaria | Sin key | ✅ | `raw/bcra/015_base_monetaria.csv` |
| M2 | Agregado monetario | BCRA API | `109` | Diaria | Sin key | ✅ | `raw/bcra/109_m2.csv` |
| Depósitos totales | Dep. totales sistema financiero | BCRA API | `21` | Diaria | Sin key | ✅ | `raw/bcra/021_dep_total.csv` |
| Depósitos plazo fijo | Dep. a plazo | BCRA API | `24` | Diaria | Sin key | ✅ | `raw/bcra/024_dep_plazo.csv` |
| Préstamos sector privado | Préstamos al sector privado | BCRA API | `26` | Diaria | Sin key | ✅ | `raw/bcra/026_prestamos_privado.csv` |
| LELIQs / NotaLiq | Pasivos remunerados BCRA | BCRA API | `155` | Diaria | Sin key | ✅ | `raw/bcra/155_leliq_notalq.csv` |
| Pases pasivos | Pases pasivos BCRA | BCRA API | `152` | Diaria | Sin key | ✅ | `raw/bcra/152_pases_pasivos.csv` |
| Broad Money / GDP | Agregado monetario amplio | World Bank | Anual | WB API | ✅ | `raw/worldbank/broad_money_gdp.csv` |

**Justificación teórica:** La liquidez en divisas es determinante clave para la capacidad (no voluntad) de pago. Un nivel bajo de reservas netas eleva la probabilidad de default y, por ende, el spread (modelo de Eaton-Gersovitz).

---

## 4. Crecimiento y Expectativas

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| PBI real (USD) | World Bank | Anual | WB API | ✅ | `raw/worldbank/gdp_usd.csv` |
| PBI per cápita | World Bank | Anual | WB API | ✅ | `raw/worldbank/gdp_per_capita.csv` |
| PBI crecimiento | World Bank | Anual | WB API | ✅ | `raw/worldbank/gdp_growth.csv` |
| EMAE (proxy mensual de PBI) | INDEC (datos.gob.ar) | Mensual | CSV | ✅ | `raw/indec/emae_*.csv` |
| IPC general | INDEC (datos.gob.ar) | Mensual | CSV | ✅ | `raw/indec/ipc_nacional_*.csv` |
| Inflación CPI | World Bank | Anual | WB API | ✅ | `raw/worldbank/inflation_cpi.csv` |

---

## 5. Endeudamiento

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| Deuda externa bruta | Mecon (datos.gob.ar) | Trimestral | CSV | ✅ | `raw/mecon/deuda_externa_bruta_*.csv` |
| Deuda externa privada | Mecon (datos.gob.ar) | Trimestral | CSV | ✅ | `raw/mecon/deuda_externa_privada_*.csv` |
| Títulos públicos deuda | Mecon (datos.gob.ar) | — | CSV | ✅ | `raw/mecon/deuda_titulos_*.csv` |
| Gobierno central deuda/PBI | World Bank | Anual | WB API | ✅ | `raw/worldbank/gov_debt_gdp.csv` |
| AIF (Ahorro-Inversión-Financiamiento) SPN | Mecon (datos.gob.ar) | Mensual/Trimestral/Anual | CSV | ✅ | `raw/mecon/aif_spn_*.csv` |
| AIF APN | Mecon (datos.gob.ar) | Mensual/Trimestral/Anual | CSV | ✅ | `raw/mecon/aif_apn_*.csv` |
| AIF Tesoro | Mecon (datos.gob.ar) | Mensual/Trimestral/Anual | CSV | ✅ | `raw/mecon/aif_tesoro_*.csv` |
| Servicios deuda 365d | Secretaría de Finanzas — Perfil de Vencimientos | Mensual | Excel | ⬜ | — |
| Deuda / PBI | Cálculo propio | Trimestral | Cálculo | ⬜ | `processed/deuda_pbi.csv` |

---

## 6. Sector Externo

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| ICA (Exportaciones + Importaciones) | INDEC (datos.gob.ar) | Mensual/Trimestral/Anual | CSV | ✅ | `raw/indec/ica_*.csv` |
| Saldo comercial por países | INDEC (datos.gob.ar) | Mensual/Trimestral/Anual | CSV | ✅ | `raw/indec/saldo_comercial_paises_*.csv` |
| Exportaciones / PBI | World Bank | Anual | WB API | ✅ | `raw/worldbank/exports_gdp.csv` |
| Importaciones / PBI | World Bank | Anual | WB API | ✅ | `raw/worldbank/imports_gdp.csv` |
| Trade / PBI (apertura comercial) | World Bank | Anual | WB API | ✅ | `raw/worldbank/trade_gdp.csv` |
| TCRM (Índice TC Real Multilateral) | BCRA | Diaria | BCRA API | ⬜ | `raw/bcra/itcrm.csv` |
| Cuenta Corriente / PBI | World Bank | Anual | WB API | ✅ | `raw/worldbank/cab_gdp.csv` |
| Cuenta Corriente (BP detallado) | INDEC (datos.gob.ar) | Trimestral | CSV | ✅ | `raw/indec/cuenta_corriente_*.csv` |
| Balance de Pagos (MBP6) | INDEC (datos.gob.ar) | Trimestral/Anual | CSV | ✅ | `raw/indec/balance_pagos_*.csv` |
| (X+M)/PBI (apertura) | Cálculo propio | Trimestral | Cálculo | ⬜ | `processed/apertura_xm.csv` |
| Reservas Internacionales | World Bank | Anual | WB API | ✅ | `raw/worldbank/reserves.csv` |

---

## 7. Política Fiscal

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| IMIG - Ingresos y Gastos SPNF | Mecon (datos.gob.ar) | Mensual | CSV | ✅ | `raw/mecon/imig_spnf_*.csv` |
| Recursos tributarios totales | Mecon (datos.gob.ar) | Mensual/Trimestral/Anual | CSV | ✅ | `raw/mecon/recursos_tributarios_*.csv` |
| Recaudación por subgrupos | Mecon (datos.gob.ar) | Mensual | CSV | ✅ | `raw/mecon/recaudacion_subgrupos_*.csv` |
| AIF devengado (varias instituciones) | Mecon (datos.gob.ar) | Anual | CSV | ✅ | `raw/mecon/aif_devengado_*.csv` |
| Resultado Fiscal Estructural | Estimación propia (filtro HP del output gap) o FMI Art. IV | Anual | Cálculo | ⬜ | `processed/resultado_estructural.csv` |

**Justificación:** El resultado estructural es la métrica de "voluntad de pago" propuesta porque abstrae del ciclo y refleja esfuerzo fiscal discrecional.

---

## 8. Apertura Comercial y Cambiaria

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| Dummy Cepo cambiario | Construcción manual (regímenes FX) | Diaria | Manual | 🔧 | `processed/dummy_cepo.csv` |
| (X+M)/PBI | Ver sección 6 | Trimestral | Cálculo | ⬜ | — |
| TC Oficial (A3500) mayorista | BCRA API | Diaria | Sin key | ✅ | `raw/bcra/005_tc_mayorista_a3500.csv` |
| TC Oficial minorista | BCRA API | Diaria | Sin key | ✅ | `raw/bcra/004_tc_minorista.csv` |
| TC MEP (AL30) | BYMA / Rava / Ámbito | Diaria | Scraping | ⬜ | `raw/mep/tc_mep.csv` |
| TC CCL | BYMA / Rava / Ámbito | Diaria | Scraping | ⬜ | `raw/mep/tc_ccl.csv` |
| TC Blue | Ámbito / dolarhoy | Diaria | Scraping | ⬜ | `raw/mep/tc_blue.csv` |
| Brecha cambiaria (CCL/Oficial − 1) | Cálculo propio | Diaria | Cálculo | ⬜ | `processed/brecha.csv` |
| Index of Economic Freedom | Heritage Foundation | Anual | CSV público | ✅ | `raw/heritage/20{24,25,26}_indexofeconomicfreedom_data.xlsx` |

---

## 9. Volatilidad Local e Inflación

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| TCN — A3500 (volatilidad) | BCRA API | Diaria | Sin key | ✅ | `raw/bcra/005_tc_mayorista_a3500.csv` |
| IPC general | INDEC (datos.gob.ar) | Mensual | CSV | ✅ | `raw/indec/ipc_nacional_*.csv` |
| IPC variaciones | INDEC (datos.gob.ar) | Mensual | CSV | ✅ | `raw/indec/ipc_variaciones_*.csv` |
| Inflación esperada (REM 12m) | BCRA REM | Mensual | BCRA API | ⬜ | `raw/bcra/rem_ipc.csv` |
| Breakeven inflation AR | Cálculo propio: TIR CER vs nominal | Diaria | Cálculo (BYMA) | ⬜ | `processed/breakeven_ipc.csv` |
| Tasa BADLAR | BCRA API | Diaria | Sin key | ✅ | `raw/bcra/007_tasa_badlar_privados.csv` |
| Tasa TM20 | BCRA API | Diaria | Sin key | ✅ | `raw/bcra/008_tasa_tm20_privados.csv` |
| Tasa depósitos 30d | BCRA API | Diaria | Sin key | ✅ | `raw/bcra/012_tasa_dep_30d.csv` |

---

## 10. Sistema Financiero

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| Crédito sector privado / PBI | World Bank | Anual | WB API | ✅ | `raw/worldbank/credit_private_gdp.csv` |
| Capitalización bursátil / PBI | World Bank `CM.MKT.LCAP.GD.ZS` | Anual | WB API | ✅ | `raw/worldbank/market_cap_gdp.csv` |
| Depósitos totales | BCRA API | Diaria | Sin key | ✅ | `raw/bcra/021_dep_total.csv` |
| Préstamos totales sector privado | BCRA API | Diaria | Sin key | ✅ | `raw/bcra/117_prest_total_privado.csv` |
| Spread tasas activa-pasiva | Cálculo propio | Mensual | Cálculo | ⬜ | — |
| Desempleo | World Bank | Anual | WB API | ✅ | `raw/worldbank/unemployment.csv` |
| Población | World Bank | Anual | WB API | ✅ | `raw/worldbank/population.csv` |

**Propuesta:** Capitalización bursátil/PBI + Crédito al sector privado/PBI como proxy de desarrollo financiero (índice construido por PCA de ambas).

---

## 11. History Matters

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| N° de defaults soberanos desde 1990 | Construcción manual (Reinhart-Rogoff 2009, S&P) | Dummy constante | Manual | 🔧 | `processed/defaults_history.csv` |
| Años desde último default | Cálculo (2001, 2014, 2020) | Diaria | Cálculo | 🔧 | `processed/years_since_default.csv` |
| Credit rating S&P / Moody's / Fitch | Agencias | Evento | Manual | ⬜ | `processed/ratings.csv` |

---

## 12. Riesgo / Sesgo Político

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| Dummy gobierno (Menem → Milei) | Construcción manual | Diaria | Manual | 🔧 | `processed/dummy_gob.csv` |
| Ventana electoral (±60d alrededor de elecciones) | Calendario electoral CNE | Diaria | Manual | 🔧 | `processed/dummy_elec.csv` |
| WGI — Political Stability | World Bank Governance Indicators | Anual | WB API | ✅ | `raw/worldbank/wgi_polstab.csv` |
| WGI — Government Effectiveness | WB | Anual | WB API | ✅ | `raw/worldbank/wgi_goveff.csv` |
| WGI — Rule of Law | WB | Anual | WB API | ✅ | `raw/worldbank/wgi_rol.csv` |
| WGI — Voice & Accountability | WB | Anual | WB API | ✅ | `raw/worldbank/wgi_voice_accountability.csv` |
| WGI — Control of Corruption | WB | Anual | WB API | ✅ | `raw/worldbank/wgi_control_corruption.csv` |
| WGI — Regulatory Quality | WB | Anual | WB API | ✅ | `raw/worldbank/wgi_regqual.csv` |

---

## 13. Reformas Pendientes (propuesta)

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| Fraser Economic Freedom of the World | Fraser Institute | Anual | ⚠️ CSV requiere descarga manual | ⬜ | `raw/fraser/efw.csv` |
| Index of Economic Freedom (Heritage) | Heritage Foundation | Anual | CSV público | ✅ | `raw/heritage/*.xlsx` |
| WEF Global Competitiveness | World Economic Forum | Anual | CSV (histórico ≤2019) | ⬜ | — |
| Doing Business (Descontinuado 2021) | World Bank | Anual | Archivo histórico | ⬜ | — |

---

## 14. Índices de Estrés Financiero (controles adicionales)

| Variable | Fuente | Frecuencia | Acceso | Estado | Archivo |
|---|---|---|---|---|---|
| OFR Financial Stress Index | Office of Financial Research (US Treasury) | Diaria | CSV público | ✅ | `raw/global/ofr_fsi.csv` |
| MOVE Index (vol. treasuries) | Yahoo `^MOVE` | Diaria | Sin key | ✅ | `raw/global/move.csv` |

---

## Resumen de Accesos y Autenticación

| Fuente | Auth | Registro |
|---|---|---|
| **ArgentinaDatos** | No requiere | — |
| **BCRA** | No requiere | — |
| **INDEC (datos.gob.ar)** | No requiere | — |
| **Mecon (datos.gob.ar)** | No requiere | — |
| **Yahoo Finance (yfinance)** | No requiere | — |
| **World Bank (wbgapi)** | No requiere | — |
| **Heritage Foundation** | No requiere (CSV público) | — |
| **Fraser Institute** | ⚠️ Requiere descarga manual | — |
| **OFR Financial Stress** | No requiere | — |
| **FRED (St. Louis Fed)** | ⚠️ API key gratis | https://fredaccount.stlouisfed.org/apikeys |
| **BYMA / Rava (para MEP/CCL)** | Scraping (sin key) | — |
| **Bloomberg / Refinitiv** | ❌ Paga | — |

---

## Resumen de Estado

| Categoría | ✅ Obtenidas | 🔧 Script listo | ⬜ Pendientes |
|---|---|---|---|
| **Yahoo Finance (global)** | 20 series | — | — |
| **World Bank** | 22 series | — | — |
| **BCRA** | 21 series | — | — |
| **INDEC (datos.gob.ar)** | 25 archivos | — | — |
| **Mecon (datos.gob.ar)** | 42 archivos | — | — |
| **Heritage Foundation** | 3 años (xlsx) | — | — |
| **OFR** | 1 serie | — | — |
| **Dummies/History** | — | 5 archivos | — |
| **FRED** | — | — | Necesita API key |
| **MEP/CCL/Blue** | — | — | Necesita scraping |
| **Cálculos derivados** | — | — | 6+ variables |

---

## Próximos pasos

1. ⏳ **Ejecutar** `python src/build_dummies.py` para generar dummies (cepo, gobiernos, electoral, defaults)
2. ⚠️ **Registrar FRED API key** para obtener Fed Funds, EMBI Global
3. 🔧 **Implementar scraping** para TC MEP, CCL, Blue (o buscar API alternativa)
4. 🔧 **Construir series derivadas**: reservas netas, brecha, breakeven, resultado estructural
5. 🔧 **Armonización de frecuencias** y exportación de base consolidada
