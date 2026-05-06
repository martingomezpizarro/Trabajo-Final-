import pandas as pd
import os

# Rutas de archivos
mep_path = r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec\tc_mep_2026-04-28.xlsx"
bcra_path = r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra\005_tc_mayorista_a3500.csv"
output_path = r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\processed\brecha_cambiaria.csv"

# Asegurar que el directorio de salida existe
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print("Cargando datos MEP...")
df_mep = pd.read_excel(mep_path)
df_mep['fecha'] = pd.to_datetime(df_mep['fecha'])
df_mep = df_mep.rename(columns={'valor': 'mep'})

print("Cargando datos BCRA Mayorista...")
df_bcra = pd.read_csv(bcra_path)
df_bcra['fecha'] = pd.to_datetime(df_bcra['fecha'])
df_bcra = df_bcra.rename(columns={'valor': 'bcra_a3500'})

print("Uniendo datasets...")
df_merged = pd.merge(df_mep, df_bcra, on='fecha', how='inner')

print("Calculando brecha...")
# Formula: (mep / bcra_a3500) - 1
df_merged['brecha_cambiaria'] = (df_merged['mep'] / df_merged['bcra_a3500']) - 1

# Seleccionar y ordenar columnas
df_final = df_merged[['fecha', 'mep', 'bcra_a3500', 'brecha_cambiaria']].sort_values('fecha')

print(f"Guardando resultado en {output_path}...")
df_final.to_csv(output_path, index=False)

print("Proceso completado con éxito.")
print(df_final.tail())
