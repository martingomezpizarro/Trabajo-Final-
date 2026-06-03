import pandas as pd
import numpy as np

# Define the date range
dates = pd.date_range(start='2000-01-01', end='2030-12-01', freq='MS')
df = pd.DataFrame({'fecha': dates})

# Dummy COVID: March 2020 to March 2021
df['dummy_covid'] = np.where((df['fecha'] >= '2020-03-01') & (df['fecha'] <= '2021-03-01'), 1, 0)

# Save to Variables Finales
out_path = r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\Variables Finales\dummy_covid.csv"
df.to_csv(out_path, index=False)
print(f"Dummy covid creada y guardada en {out_path}")
