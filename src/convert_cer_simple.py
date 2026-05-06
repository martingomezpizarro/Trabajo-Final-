import pandas as pd
import sys

print("START")
try:
    path = r'C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra\diar_cer.xls'
    out = r'C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra\cer.csv'
    
    # engine='xlrd' is default for .xls
    df = pd.read_excel(path, header=None)
    
    # User said: Column A is date, Column B is value
    # We clean it up
    df[0] = pd.to_datetime(df[0], errors='coerce')
    df = df.dropna(subset=[0])
    df = df[[0, 1]]
    df.columns = ['fecha', 'cer']
    df = df.sort_values('fecha')
    
    df.to_csv(out, index=False)
    print(f"DONE. Saved {len(df)} rows.")
except Exception as e:
    print(f"ERROR: {e}")
