---
description: Plan de acción y fases del trabajo final de grado sobre riesgo país argentino
---

# 📋 Plan de Acción - Trabajo Final de Grado

## Riesgo País Argentino: Análisis Econométrico y Predicción

**Estado:** 🟡 En progreso  
**Última actualización:** Abril 2026

---

## Fase 0: Preparación
- [ ] Releer todo lo anotado en el estudio
- [ ] Revisar el libro de Enders (Applied Econometric Time Series)
- [ ] Definir el alcance temporal del análisis (período de estudio)

---

## Fase 1: Base de Datos

### 1.1 Definición de Variables
- [ ] Definir lista completa de variables candidatas
- [ ] Documentar cada variable con su explicación y justificación teórica
- [ ] Clasificar variables en idiosincráticas vs. generales
- [ ] Identificar la fuente de datos para cada variable

### 1.2 Documentación y Acceso a APIs
- [ ] Conseguir documentación de cada API o fuente de datos
- [ ] Obtener API keys necesarias (FRED, etc.)
- [ ] Testear la descarga de cada serie temporal
- [ ] Documentar limitaciones de cada fuente (frecuencia, período disponible, etc.)

### 1.3 Inflación Breakeven
- [ ] Investigar cómo construir la inflación breakeven argentina
- [ ] Identificar los bonos necesarios (CER vs nominales)
- [ ] Implementar el cálculo
- [ ] Validar con datos de mercado

### 1.4 Procesamiento
- [ ] Armonizar frecuencias temporales
- [ ] Tratar valores faltantes
- [ ] Verificar consistencia de los datos
- [ ] Exportar base de datos limpia

---

## Fase 2: Modelización Econométrica

### 2.1 Repaso Teórico
- [ ] Repaso de modelos econométricos de serie de tiempo
- [ ] Revisión de literatura sobre determinantes del riesgo país
- [ ] Identificar modelos aplicados en trabajos similares

### 2.2 Definición de Modelos
- [ ] Definir los modelos a probar
- [ ] Justificar teóricamente la elección de cada modelo
- [ ] Definir hipótesis a testear
- [ ] Planificar la estrategia de estimación

### 2.3 Modelización en Python
- [ ] Tests de estacionariedad (ADF, KPSS) para cada variable
- [ ] Estimación OLS con errores HAC
- [ ] Estimación VAR y análisis de impulso-respuesta
- [ ] Test de cointegración y estimación VECM (si aplica)
- [ ] Estimación ARDL
- [ ] Modelos GARCH/EGARCH para volatilidad
- [ ] PCA para construcción del índice

### 2.4 Análisis de Resultados
- [ ] Evaluar cumplimiento del Objetivo 1 (índice > 70% explicación)
- [ ] Evaluar cumplimiento del Objetivo 2 (idiosincráticas vs. generales)
- [ ] Análisis de robustez
- [ ] Validación out-of-sample

### 2.5 Multimodelización
- [ ] Comparación de todos los modelos (AIC, BIC, R²)
- [ ] Análisis de sensibilidad
- [ ] Selección del modelo final
- [ ] Documentar resultados comparativos

---

## Fase 3: Red Neuronal

### 3.1 Investigación
- [ ] Repaso de redes neuronales para series temporales
- [ ] Investigar arquitecturas LSTM, GRU, Transformers
- [ ] Revisar trabajos similares en finanzas/economía
- [ ] Documentar hallazgos en documentacion_rn.md

### 3.2 Definición
- [ ] Definir las variables de entrada
- [ ] Definir la arquitectura de la red
- [ ] Definir hiperparámetros iniciales
- [ ] Planificar la estrategia de entrenamiento/validación/test

### 3.3 Desarrollo
- [ ] Preparación de datos (secuencias, normalización, train/val/test split)
- [ ] Implementación de la arquitectura
- [ ] Entrenamiento y ajuste de hiperparámetros
- [ ] Evaluación del modelo (RMSE, MAE, R²)
- [ ] Comparación con modelos econométricos
- [ ] Predicción del riesgo país LATAM (o argentino)

---

## Notas y Observaciones

> **Espacio para anotar ideas, cambios de plan, y ajustes sobre la marcha**

<!-- Agregar notas aquí -->
