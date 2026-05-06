import pandas as pd
import os

def log(msg):
    print(msg)
    with open("extract_bcra_excel.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def extraer_todo_bcra_xlsm():
    if os.path.exists("extract_bcra_excel.log"):
        os.remove("extract_bcra_excel.log")
        
    log("🚀 Iniciando extracción masiva desde series (3).xlsm...")
    xlsm_file = "series (3).xlsm"
    output_path = os.path.join("data", "raw", "bcra")
    os.makedirs(output_path, exist_ok=True)
    
    if not os.path.exists(xlsm_file):
        log(f"❌ No se encontró el archivo {xlsm_file}")
        return

    try:
        # --- 1. EXTRACCIÓN DE DEPÓSITOS ---
        log("📂 Procesando hoja 'DEPOSITOS' (Columnas Z y AA)...")
        df_dep = pd.read_excel(xlsm_file, sheet_name="DEPOSITOS", usecols="A,Z,AA", header=0, engine='openpyxl')
        df_dep.columns = ['fecha', 'depositos_usd_totales_z', 'depositos_usd_residentes_aa']
        df_dep['fecha'] = pd.to_datetime(df_dep['fecha'], errors='coerce')
        df_dep = df_dep.dropna(subset=['fecha']).set_index('fecha').sort_index()
        
        for col in df_dep.columns:
            df_dep[col] = pd.to_numeric(df_dep[col], errors='coerce')
        
        df_dep[['depositos_usd_totales_z']].dropna().to_csv(os.path.join(output_path, "depositos_usd_z.csv"))
        df_dep[['depositos_usd_residentes_aa']].dropna().to_csv(os.path.join(output_path, "depositos_usd_aa.csv"))
        log(f"  ✅ Depósitos guardados. (Obs: {len(df_dep)})")

        # --- 2. EXTRACCIÓN DE PRÉSTAMOS ---
        log("📂 Procesando hoja 'PRESTAMOS' (Columna Q)...")
        df_pres = pd.read_excel(xlsm_file, sheet_name="PRESTAMOS", usecols="A,Q", header=0, engine='openpyxl')
        df_pres.columns = ['fecha', 'prestamos_privados_usd_q']
        df_pres['fecha'] = pd.to_datetime(df_pres['fecha'], errors='coerce')
        df_pres = df_pres.dropna(subset=['fecha']).set_index('fecha').sort_index()
        
        df_pres['prestamos_privados_usd_q'] = pd.to_numeric(df_pres['prestamos_privados_usd_q'], errors='coerce')
        
        df_pres[['prestamos_privados_usd_q']].dropna().to_csv(os.path.join(output_path, "prestamos_privados_usd_q.csv"))
        log(f"  ✅ Préstamos guardados. (Obs: {len(df_pres)})")
        
        log(f"✨ ÉXITO TOTAL: Todos los datos extraídos en {output_path}")
            
    except Exception as e:
        log(f"❌ ERROR CRÍTICO durante la extracción: {str(e)}")

if __name__ == "__main__":
    extraer_todo_bcra_xlsm()
