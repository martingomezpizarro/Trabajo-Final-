# 🧠 Documentación y Contexto - Redes Neuronales

## Propósito
Este archivo sirve como repositorio de links, papers, documentación de librerías y notas
para tener contexto a la hora de desarrollar el modelo de red neuronal del trabajo final.

---

## Papers y Trabajos de Referencia

> **MARTÍN: Agregar aquí los links y referencias que vayas encontrando**

### Redes Neuronales para Series Temporales
<!-- Ejemplo:
- [Nombre del paper](URL) - Autor (Año) - Breve descripción
-->

### LSTM / GRU para Finanzas
<!-- Ejemplo:
- [Nombre del paper](URL) - Autor (Año) - Breve descripción
-->

### Predicción de Riesgo País con ML
<!-- Ejemplo:
- [Nombre del paper](URL) - Autor (Año) - Breve descripción
-->

### Transformers para Series Temporales
<!-- Ejemplo:
- [Nombre del paper](URL) - Autor (Año) - Breve descripción
-->

---

## Librerías de Python

### TensorFlow / Keras
- **Documentación oficial**: https://www.tensorflow.org/api_docs
- **Keras LSTM**: https://keras.io/api/layers/recurrent_layers/lstm/
- **Keras GRU**: https://keras.io/api/layers/recurrent_layers/gru/
- **Time Series Forecasting**: https://www.tensorflow.org/tutorials/structured_data/time_series

### PyTorch
- **Documentación oficial**: https://pytorch.org/docs/stable/index.html
- **nn.LSTM**: https://pytorch.org/docs/stable/generated/torch.nn.LSTM.html
- **Tutorial Series Temporales**: https://pytorch.org/tutorials/beginner/introyt/trainingyt.html

### Otras Librerías Útiles
- **tsai** (fastai para series temporales): https://timeseriesai.github.io/tsai/
- **darts** (forecasting): https://unit8co.github.io/darts/
- **pytorch-forecasting**: https://pytorch-forecasting.readthedocs.io/

---

## Arquitecturas a Considerar

| Arquitectura | Ventajas | Desventajas | Uso típico |
|---|---|---|---|
| LSTM | Captura dependencias largo plazo | Lento de entrenar | Series financieras |
| GRU | Más rápido que LSTM, similar performance | Menos capacidad | Series con menos datos |
| Transformer | Estado del arte, atención global | Requiere más datos | Series multivariadas |
| CNN-LSTM | Extrae features locales + temporales | Más complejo | Series con patrones locales |

---

## Notas y Observaciones

> **Espacio para anotar ideas, dudas y observaciones sobre las redes neuronales**

<!-- Agregar notas aquí -->
