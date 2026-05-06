import pandas as pd
import os

def log(msg):
    print(msg)
    with open("extract_depositos.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def extraer_depositos_xlsm():
    if os.path.exists("extract_depositos.log"):
        os.remove("extract_depositos.log")
        
    log("Iniciando extracción de depósitos desde XLSM...")
    xlsm_file = "series (3).xlsm"
    output_path = os.path.join("data", "raw", "bcra")
    os.makedirs(output_path, exist_ok=True)
    
    if not os.path.exists(xlsm_file):
        log(f"❌ No se encontró el archivo {xlsm_file}")
        return

    log(f"Abriendo {xlsm_file} (este archivo es pesado, paciencia)...")
    try:
        # Intentamos con openpyxl que es el estándar para xlsm
        df = pd.read_excel(xlsm_file, sheet_name="PRESTAMOS", usecols="A, Q", header=0, engine='openpyxl')
        log(f"Hoja 'DEPOSITOS' leída. Columnas: {df.columns.tolist()}")
        
        # Renombrar columnas
        df.columns = ['fecha', 'prestamos_sector_privado_pbi']
        
        # Limpieza
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset=['fecha'])
        
        for col in ['depositos_usd_z', 'depositos_usd_aa']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.set_index('fecha').sort_index()
        
        # Guardar
        df[['prestamos_sector_privado_pbi']].dropna().to_csv(os.path.join(output_path, "prestamos_sector_privado_pbi.csv"))

        log(f"✅ ÉXITO: Archivos guardados en {output_path}")
        log(f"Muestra: {len(df)} filas. Desde {df.index.min()} hasta {df.index.max()}")
            
    except Exception as e:
        log(f"❌ ERROR CRÍTICO: {str(e)}")

if __name__ == "__main__":
    extraer_prestamos_xlsm()
