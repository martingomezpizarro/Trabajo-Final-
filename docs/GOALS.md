# 🎯 Objetivos del Trabajo Final de Grado

## Riesgo País Argentino: Análisis Econométrico y Predicción

**Autor:** Martín  
**Carrera:** Licenciatura en Economía  
**Universidad:** Universidad Nacional de Córdoba (UNC)  
**Fecha de inicio:** Abril 2026

---

## Objetivo Principal

> **Identificar mediante la implementación de distintos métodos econométricos de serie de tiempo, las principales variables explicativas del riesgo país argentino.**

Se busca determinar qué factores económicos, financieros y político-institucionales tienen un impacto estadísticamente significativo sobre el spread soberano de Argentina (EMBI+), utilizando metodologías econométricas rigurosas y replicables.

---

## Objetivos Secundarios

### 1. 📊 Construcción de un Índice Explicativo

> **Crear un índice que explique al menos el 70% del riesgo país y pueda ser calculado en tiempo real.**

- El índice debe ser parsimonioso (pocas variables, alta capacidad explicativa)
- Debe poder actualizarse en tiempo real con datos disponibles públicamente
- Se evaluará mediante R² ajustado, criterios de información (AIC, BIC) y validación out-of-sample
- Potencial uso: herramienta de monitoreo para inversores y analistas

### 2. 🔍 Distinción entre Variables Idiosincráticas y Generales

> **Distinguir entre las variables de carácter idiosincrático y generales para la explicación del riesgo país.**

- **Variables idiosincráticas**: factores específicos de Argentina (política fiscal, reservas del BCRA, brecha cambiaria, inflación, resultado fiscal, etc.)
- **Variables generales**: factores globales que afectan a todos los emergentes (VIX, tasas de EEUU, precio de commodities, DXY, etc.)
- Metodología: descomposición de varianza, análisis factorial, regresiones con efectos fijos/aleatorios

### 3. 🤖 Modelo de Red Neuronal para Predicción

> **Aplicar un modelo de red neuronal para la predicción del riesgo país latinoamericano. Y en su defecto, argentino.**

- Implementación de arquitecturas de deep learning para series temporales (LSTM, GRU, Transformer)
- Predicción del riesgo país de múltiples países de LATAM (Brasil, México, Colombia, Chile, Perú, Argentina)
- Evaluación comparativa con modelos econométricos tradicionales
- Métricas: RMSE, MAE, MAPE, R² out-of-sample

---

## Hipótesis de Trabajo

1. Las variables idiosincráticas tienen mayor poder explicativo sobre el riesgo país argentino que las variables generales
2. Un modelo con pocas variables seleccionadas puede explicar más del 70% de la variación del EMBI+
3. Los modelos de redes neuronales superan a los modelos econométricos tradicionales en la predicción a corto plazo

---

## Contribución Esperada

- Herramienta cuantitativa para el análisis del riesgo soberano argentino
- Marco comparativo entre metodologías econométricas y de machine learning
- Índice replicable y actualizable en tiempo real
- Evidencia empírica sobre la descomposición del riesgo país en componentes idiosincráticos y sistémicos
