# Resultado Fiscal Estructural (SE) — Guía Metodológica

**Variable**: `SE_pctPIB` en `data/Variables Finales/resultado_fiscal_estructural.csv`
**Script**: `src/variables/resultado_fiscal_estructural.py`
**Frecuencia**: trimestral, 2006Q1–2025Q4 (80 observaciones)

## 1. Marco teórico (Gay & Escudero, 2010)

El resultado fiscal estructural (SE) es el saldo presupuestario hipotético que se observaría si la economía estuviese en pleno empleo y los precios de los commodities en su nivel de tendencia. Filtra el componente cíclico del superávit primario observado (SP) y permite evaluar la posición fiscal subyacente.

### Descomposición

```
SP   = SE + componente_cíclico
SE   = T^S − G_CA
T^S  = T_CA · (TI*/TI)^γ        ← ajuste por términos de intercambio
T_CA = T   · (Y*/Y)^ε_T          ← ingresos ciclicamente ajustados
G_CA = G   · (Y*/Y)^ε_G          ← gastos ciclicamente ajustados
```

## 2. Insumos

| Insumo | Símbolo | Fuente | Frecuencia |
|---|---|---|---|
| PBI real | Y | `pbi_constante_2004.csv` | Trimestral |
| PBI nominal | Y_nom | `pbi_corriente.csv` | Trimestral (anualizado) |
| Ingresos primarios | T | `Resultado fiscal-unificado.xlsx` (`ing_primario_antes_figurativos`) | Mensual → Q |
| Gastos primarios | G | `Resultado fiscal-unificado.xlsx` (`gtos_primario_antes_figurativos`) | Mensual → Q |
| FBKF real | I | `fbkf_constante.csv` | Trimestral |
| Términos de Intercambio | TI | `ti_mensual.csv` (`ti_base100`) | Mensual → Q (promedio) |
| Tasa desempleo | u | `data/raw/worldbank/unemployment.csv` | Anual → Q (interp.) |
| Población | POP | `data/raw/worldbank/population.csv` | Anual → Q (interp.) |

## 3. PIB potencial Y* — Función de Producción Cobb-Douglas

Replica G&E ec. (12): `Y* = K^α · (LQ)^(1−α) · PTF`, con `α = 0.6`.

### Capital stock K (inventario perpetuo)
```
K_t = (1 − δ_q) · K_{t−1} + I_t
δ_q = 1 − (1 − 0.05)^(1/4) ≈ 0.0127  (5% anual)
K_0 = 2.5 × Y_0 × 4                   (ratio K/Y ≈ 2.5 PWT-style)
```

### Fuerza laboral L
- **L observado** = POP × 0.46 × (1 − u/100)
- **L pleno empleo** = POP × 0.46 × (1 − NAIRU/100)
- **NAIRU** = tendencia HP (λ=1600) de la tasa de desempleo

### PTF (productividad total de factores)
```
PTF_t          = Y_t / (K_t^0.6 · L_t^0.4)
PTF_suavizada  = exp(HP-trend(log PTF_t, λ=1600))
```

### Y* final
```
Y*_t = K_t^0.6 · L_pleno_t^0.4 · PTF_suavizada_t
GAP_t = (Y_t − Y*_t) / Y*_t
```

## 4. Términos de Intercambio largo plazo TI*

```
TI*_t = promedio móvil centrado de 10 años (40 trimestres) sobre TI
       = promedio simple muestral si la ventana queda fuera de la muestra
```

> **Limitación**: la muestra disponible empieza en 2004. Para 2006-2010, TI* queda atado al promedio muestral (~124), que es alto vs el TI observado (~98-117). Esto infla artificialmente la corrección de los primeros años. G&E no enfrentó este problema porque su muestra empezaba en 1983.

## 5. Elasticidades

Tomadas de Gay & Escudero (2010, Tabla 1), estimadas vía VAR cointegrado con quiebres:

| Elasticidad | Valor | Fuente |
|---|---|---|
| ε_T (recaudación/PIB) | **1.14** | G&E 2010; coincide con Perry & Servén (2003) |
| ε_G (gasto/PIB) | **0.43** | G&E 2010; difiere de OCDE (que asume ε_G ≈ 0) |
| γ (commodity) | **1.00** | G&E 2010 (asunción proporcional) |

## 6. Adaptaciones vs G&E original

| Aspecto | G&E 2010 | Este trabajo |
|---|---|---|
| Período | 1983Q1–2010Q2 | 2006Q1–2025Q4 |
| Y* | Cobb-Douglas con K, L, NAIRU, PTF | Idem (con K via inventario perpetuo desde FBKF) |
| Ajuste commodities | Precio soja (P*/P) | TI general (TI*/TI) |
| Definición fiscal | SPNF con corrección por privatizaciones | `ing/gtos_primario_antes_figurativos` (MECON) |

## 7. Validación

Solapamiento 2006-2010 con G&E Figura 5:

| Año | SP oficial (este trabajo) | SP G&E reportado | Match |
|---|---|---|---|
| 2006 | 3.24% | ~4% | ✓ |
| 2007 | 2.90% | ~2.5% | ✓ |
| 2008 | 2.83% | ~3% | ✓ |
| 2009 | 1.37% | ~1.5% | ✓ |
| 2010 | 1.50% | ~1.5% | ✓ |

El SP oficial coincide con G&E. El SE muestra divergencia en 2006-2008 por la limitación del TI* (ver §4).

## 8. Output

`data/Variables Finales/resultado_fiscal_estructural.csv` (80 filas × 25 columnas):

- `Y_real`, `Y_nom`, `Y_pot`, `GAP`
- `K`, `L`, `L_pleno`, `NAIRU`, `PTF_smooth`
- `TI`, `TI_star`
- `T_nom`, `G_nom`
- `T_CA`, `G_CA`, `T_estruct`
- `SP_observado`, `SP_oficial`, `SP_oficial_neto`, `SCA`, `SE`
- `SP_pctPIB`, `SP_oficial_pctPIB`, `SCA_pctPIB`, `SE_pctPIB`

**Variable de interés principal**: `SE_pctPIB` (resultado fiscal estructural como % del PBI).

## 9. Cómo regenerar

```bash
python src/variables/resultado_fiscal_estructural.py    # genera CSV
python src/variables/graficos_se.py                     # genera plot + tabla anual
```

## 10. Referencia

Gay, A. & Escudero, M. (2010). *El resultado fiscal estructural en la Argentina: 1983-2010*. UNC. PDF en `bibliografia contexto/`.
