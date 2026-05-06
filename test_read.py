import pandas as pd
import os

excel_file = r"data\raw\Serie_Historica_Spread_del_EMBI.xlsx"
print(f"Checking {excel_file}...")
try:
    df = pd.read_excel(excel_file, header=1, engine='openpyxl')
    print("Columns found:")
    print(df.columns.tolist())
    if 'LATINO' in df.columns:
        print("LATINO column found!")
except Exception as e:
    print(f"Error: {e}")
