import pandas as pd

mep_path = r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\indec\tc_mep_2026-04-28.xlsx"
df_mep = pd.read_excel(mep_path)
print("MEP Columns:", df_mep.columns.tolist())
print(df_mep.head())
