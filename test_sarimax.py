import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

df = pd.read_csv('data/Variables Finales/deuda_externa_bruta_total_kalman.csv', index_col='fecha')
y = df['y_obs']

try:
    mod = SARIMAX(y, order=(4, 1, 0), seasonal_order=(1, 0, 1, 12), trend='c', enforce_stationarity=False, enforce_invertibility=False)
    res = mod.fit(disp=False, method='powell')
    pred = res.predict()
    print("Order (4, 1, 0) NaNs:", pred.isna().sum())
except Exception as e:
    print("Failed", e)
