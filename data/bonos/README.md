# Vencimientos de Deuda Soberana Argentina en USD — Ventana Forward 2 Años

## Objetivo
Construir una serie temporal mensual que mida la **cantidad de deuda soberana argentina en USD con vencimientos dentro de los próximos 2 años**. Esta variable captura la **presión de refinanciamiento** — un determinante clave del riesgo país.

## Metodología

### Enfoque
Para cada mes `t` desde enero 2006 hasta hoy, se calcula:
```
Venc_forward(t) = Σ Amortización_i  para todo bono_i activo en t, 
                  donde fecha_pago_i ∈ [t, t + 24 meses]
```

### Catálogo de bonos
Se construyó un catálogo exhaustivo de **todos los instrumentos de deuda soberana argentina en USD** organizados por era:

1. **BODEN (Post-crisis 2001)**: BODEN 2012 (RG12), BODEN 2015 (RO15)
2. **Post-restructuración 2005/2010**: Discount USD (DICY/DICA), Par USD (PARY/PARA), Global 2017 (GJ17)
3. **GDP Warrants (TVPY/TVPA)**: Pagos contingentes atados al crecimiento del PBI (2007-2012)
4. **Club de París**: Acuerdo 2014, ~USD 9,700 MM en cuotas semestrales (2014-2019)
5. **FMI — SBA 2018**: Stand-By por ~USD 44,000 MM desembolsados, repagos 2021-2031 (refinanciado via EFF 2022)
6. **FMI — EFF 2025**: Facilidades Extendidas por USD 20,000 MM, repagos 2030-2035 (gracia 4.5 años)
7. **Emisiones 2016–2019**: AO20, AY24, AA25, AC17, A2E7, AN19, AA21, AA22, AA23, AA36, AA46, AA48
8. **Post-restructuración 2020**: GD29, AL29, GD30, AL30, GD35, AL35, GD38, GD41, AL41, GD46
9. **Letras del Tesoro en USD (LETES)**: Stock trimestral rolling 2016-2019 (zero-coupon, corto plazo)
10. **BOPREAL del BCRA**: Series 1 (BPO27), 2 (BPJ25), 3 (BPY26), 4 (BPO28) — bonos en USD del Banco Central (2024+)
11. **LEBAC USD del BCRA**: Stock anual proxy 2006-2017 (instrumentos de corto plazo)

### Restructuraciones incorporadas
- **Sep 2020**: Todos los bonos de las eras 1 y 2 se marcan como "inactivos" a partir del 4/9/2020, reemplazados por los bonos Step-Up de la era 3.

## Archivos

| Archivo | Descripción |
|---|---|
| `01_download_boletin.py` | Descarga el boletín mensual de Finanzas (para validación) |
| `02_catalogo_bonos_usd.py` | Genera el catálogo JSON con todos los bonos y flujos |
| `03_calcular_vencimientos_forward.py` | Calcula la serie temporal de vencimientos forward 2Y |
| `catalogo_bonos_usd.json` | Catálogo maestro (generado por script 02) |
| `catalogo_bonos_resumen.csv` | Resumen tabular del catálogo |
| `vencimientos_usd_2y_forward.csv` | **Serie final** (generada por script 03) |

## Ejecución
```bash
# Paso 1: Generar catálogo de bonos
python data/bonos/02_catalogo_bonos_usd.py

# Paso 2: Calcular serie de vencimientos
python data/bonos/03_calcular_vencimientos_forward.py

# Opcional: Descargar boletín oficial para validación
python data/bonos/01_download_boletin.py
```

## Fuentes
- Prospectos de emisión (SEC EDGAR — "Republic of Argentina")
- Secretaría de Finanzas — Datos mensuales de la deuda
- Oficina de Presupuesto del Congreso (OPC)
- Información de mercado (BYMA, Invertir Online, Allaria)

## Advertencias
- Los montos emitidos son **aproximados** basados en fuentes públicas.
- No incluye deuda con organismos multilaterales (FMI, BM, BID).
- No incluye Letras del Tesoro (corto plazo, renovación constante).
- El catálogo no está exhaustivamente completo para 2006–2016 (faltan algunos bonos menores).
- Los cupones step-up no se incluyen en el cálculo de la ventana forward (solo capital).
