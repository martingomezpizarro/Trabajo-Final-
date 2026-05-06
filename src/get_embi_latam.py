import pandas as pd
import os
import sys

def log(msg):
    print(msg)
    with open("get_embi.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def extraer_embi_latam_local():
    if os.path.exists("get_embi.log"):
        os.remove("get_embi.log")
        
    log("Iniciando extracción...")
    raw_path = os.path.join("data", "raw")
    excel_file = os.path.join(raw_path, "Serie_Historica_Spread_del_EMBI.xlsx")
    dest_path = os.path.join(raw_path, "global")
    dest_file = os.path.join(dest_path, "embi_latam.csv")
    
    os.makedirs(dest_path, exist_ok=True)
    
    if not os.path.exists(excel_file):
        log(f"❌ No se encontró el archivo: {excel_file}")
        return

    log(f"Abriendo Excel local: {excel_file}...")
    try:
        df = pd.read_excel(excel_file, header=1, engine='openpyxl')
        log(f"Excel leído. Columnas: {df.columns.tolist()[:10]}")
        
        if 'LATINO' in df.columns:
            date_col = df.columns[0]
            log(f"Extrayendo 'LATINO' y '{date_col}'...")
            
            embi_df = df[[date_col, 'LATINO']].dropna()
            embi_df.columns = ['fecha', 'embi_latam']
            embi_df['fecha'] = pd.to_datetime(embi_df['fecha'], errors='coerce')
            embi_df = embi_df.dropna(subset=['fecha'])
            embi_df['embi_latam'] = pd.to_numeric(embi_df['embi_latam'], errors='coerce')
            embi_df = embi_df.dropna(subset=['embi_latam'])
            
            embi_df = embi_df.set_index('fecha').sort_index()
            embi_df.to_csv(dest_file)
            log(f"✅ ÉXITO: {dest_file} guardado.")
            log(f"Cobertura: {embi_df.index.min()} a {embi_df.index.max()}")
        else:
            log("❌ ERROR: No está la columna 'LATINO'")
            
    except Exception as e:
        log(f"❌ ERROR CRÍTICO: {str(e)}")

if __name__ == "__main__":
    extraer_embi_latam_local()
