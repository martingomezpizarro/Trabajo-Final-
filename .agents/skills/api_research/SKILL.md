---
name: api_research
description: Skill para investigar documentaciones de APIs de datos económicos y financieros, identificar series temporales disponibles y documentar cómo acceder a ellas.
---

# 🔍 API Research Skill - Datos Económicos y Financieros

## Propósito
Este skill proporciona instrucciones para investigar y documentar APIs de datos económicos 
y financieros relevantes para el análisis del riesgo país argentino.

## Fuentes de Datos Principales

### 1. Yahoo Finance (vía `yfinance`)
- **Tipo**: Librería Python (sin API key)
- **Datos**: Precios de activos, índices, commodities, ETFs
- **Frecuencia**: Diaria (intradiaria disponible)
- **Doc**: https://github.com/ranaroussi/yfinance
- **Tickers útiles**:
  - `^VIX` - Índice de volatilidad
  - `DX-Y.NYB` - Dollar Index (DXY)
  - `CL=F` - Petróleo WTI
  - `GC=F` - Oro
  - `^GSPC` - S&P 500
  - `^MERV` - Merval
  - `GGAL` - Galicia ADR
  - `YPF` - YPF ADR
  - `BMA` - Macro ADR

### 2. FRED (Federal Reserve Economic Data)
- **Tipo**: API REST (requiere API key gratuita)
- **Datos**: Miles de series macroeconómicas de EEUU y globales
- **Frecuencia**: Variable (diaria a anual)
- **Doc**: https://fred.stlouisfed.org/docs/api/fred/
- **API Key**: https://fred.stlouisfed.org/docs/api/api_key.html
- **Series útiles**:
  - `DGS10` - Treasury 10Y yield
  - `DGS2` - Treasury 2Y yield
  - `T10Y2Y` - Spread 10Y-2Y
  - `VIXCLS` - VIX
  - `DTWEXBGS` - Trade Weighted Dollar Index
  - `BAMLHE00EHYIEY` - High Yield OAS
  - `BAMLEMHBHYCRPIEY` - EM High Yield OAS

### 3. BCRA (Banco Central de la República Argentina)
- **Tipo**: API REST (sin key, pero con rate limiting)
- **Datos**: Variables monetarias y cambiarias de Argentina
- **Frecuencia**: Diaria y mensual
- **Doc**: https://www.bcra.gob.ar/BCRAyVos/Catalogo_de_APIs_702.asp
- **Endpoint base**: `https://api.bcra.gob.ar/estadisticas/v2.0/`
- **Variables principales**: TC oficial, reservas, base monetaria, tasas

### 4. World Bank API
- **Tipo**: API REST (sin key)
- **Datos**: Indicadores macroeconómicos globales
- **Frecuencia**: Anual (algunas trimestrales)
- **Doc**: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

### 5. Ámbito Financiero / Riesgo País
- **Tipo**: Web scraping o datos manuales
- **Datos**: EMBI+ Argentina (riesgo país), dólar blue
- **Nota**: No tiene API pública estable. Alternativas:
  - J.P. Morgan EMBI+ vía Bloomberg/Reuters
  - Ámbito Financiero web
  - RAVA Bursátil API

### 6. INDEC
- **Tipo**: Descarga manual / web scraping
- **Datos**: IPC, actividad económica, balanza comercial
- **Doc**: https://www.indec.gob.ar/

## Instrucciones de Uso

### Cuando el usuario pida buscar una serie temporal:

1. **Identificar la variable**: Entender qué dato económico necesita
2. **Buscar en las fuentes**: Revisar cada API en orden de prioridad:
   - Yahoo Finance (más fácil, sin key)
   - FRED (amplia, requiere key)
   - BCRA (datos argentinos)
   - World Bank (macro global)
3. **Verificar disponibilidad**: 
   - Frecuencia temporal disponible
   - Rango de fechas
   - Calidad de los datos
4. **Documentar**: Agregar a la lista de variables en el notebook 01
5. **Testear**: Descargar una muestra y verificar

### Para investigar una API nueva:

1. Buscar la documentación oficial en GitHub o sitio web
2. Verificar si hay librería Python disponible
3. Probar un endpoint de ejemplo
4. Documentar: endpoint, parámetros, formato de respuesta, limitaciones
5. Crear función de descarga en `src/data_loader.py`

## Variables Candidatas para Riesgo País

| Variable | Categoría | Fuente Sugerida | Frecuencia |
|---|---|---|---|
| EMBI+ Argentina | Dependiente | Ámbito/Manual | Diaria |
| VIX | General | Yahoo/FRED | Diaria |
| Treasury 10Y | General | FRED | Diaria |
| DXY | General | Yahoo | Diaria |
| Spread HY | General | FRED | Diaria |
| Petróleo WTI | General | Yahoo | Diaria |
| S&P 500 | General | Yahoo | Diaria |
| TC Oficial | Idiosincrática | BCRA | Diaria |
| TC Blue | Idiosincrática | BCRA/Ámbito | Diaria |
| Brecha Cambiaria | Idiosincrática | Calculada | Diaria |
| Reservas BCRA | Idiosincrática | BCRA | Diaria |
| Base Monetaria | Idiosincrática | BCRA | Diaria |
| Tasa de Política | Idiosincrática | BCRA | Diaria |
| Inflación Breakeven | Idiosincrática | Calculada | Diaria |
| Merval en USD | Idiosincrática | Yahoo+BCRA | Diaria |
| Soja | General/Idio. | Yahoo (`ZS=F`) | Diaria |
