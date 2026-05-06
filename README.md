# 🇦🇷 Trabajo Final de Grado - Riesgo País Argentino

## Análisis Econométrico de Series de Tiempo y Predicción con Redes Neuronales

**Autor:** Martín  
**Carrera:** Licenciatura en Economía  
**Universidad:** Universidad Nacional de Córdoba (UNC)  
**Inicio:** Abril 2026

---

## 📌 Descripción

Este proyecto busca identificar las principales variables explicativas del riesgo país argentino (EMBI+) mediante métodos econométricos de series de tiempo, construir un índice explicativo en tiempo real, y aplicar redes neuronales para la predicción del riesgo soberano latinoamericano.

## 📂 Estructura del Proyecto

```
Trabajo/
├── notebooks/
│   ├── 01_base_de_datos.ipynb      # Extracción y visualización de datos
│   ├── 02_modelos_regresion.ipynb   # Modelos econométricos
│   └── 03_red_neuronal.ipynb        # Red neuronal
│
├── src/
│   ├── data_loader.py               # Funciones de descarga de datos
│   ├── models.py                    # Wrappers de modelos econométricos
│   └── utils.py                     # Utilidades y tests estadísticos
│
├── docs/
│   ├── GOALS.md                     # Objetivos del proyecto
│   ├── documentacion_modelos.md     # Contexto para modelos econométricos
│   └── documentacion_rn.md          # Contexto para redes neuronales
│
├── data/
│   ├── raw/                         # Datos crudos descargados
│   └── processed/                   # Datos procesados y limpios
│
├── .agents/workflows/
│   └── plan_de_accion.md            # Plan de trabajo editable
│
├── requirements.txt                 # Dependencias Python
└── README.md                        # Este archivo
```

## 🎯 Objetivos

1. **Principal:** Identificar las principales variables explicativas del riesgo país argentino
2. **Índice:** Crear un índice que explique ≥70% del riesgo país, calculable en tiempo real
3. **Clasificación:** Distinguir variables idiosincráticas vs. generales
4. **Predicción:** Aplicar redes neuronales para predecir el riesgo país LATAM/Argentina

## 🚀 Cómo Empezar

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Abrir Jupyter
jupyter notebook

# 3. Empezar con notebooks/01_base_de_datos.ipynb
```

## 📚 Referencias

- **Enders, W.** - Applied Econometric Time Series
- Ver `docs/documentacion_modelos.md` y `docs/documentacion_rn.md` para más referencias
