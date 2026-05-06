import pandas as pd
import os
import re

def clean_column_name(col):
    if not isinstance(col, str):
        return col
    # Quitar sufijos temporales como _2017, _2007_2014, _1993_2006
    col = re.sub(r'_(2017|2007_2014|1993_2006|1993_2000)$', '', col)
    return col

def main():
    base_path = r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo"
    mecon_path = os.path.join(base_path, "data", "raw", "mecon")
    
    # Archivos
    f_1993 = os.path.join(mecon_path, "aif_spn_sector_p_blico_nacional_valores_mensuales_1993_2006.csv")
    f_2007 = os.path.join(mecon_path, "aif_spn_sector_p_blico_nacional_valores_mensuales_2007_2014.csv")
    f_2017 = os.path.join(mecon_path, "aif_spn_sector_p_blico_nacional_valores_mensuales_2017.csv")
    
    # Para el encabezado de 1993-2006, usamos el anual como referencia
    f_header_ref = os.path.join(mecon_path, "aif_spn_sector_p_blico_nacional_valores_anuales_1993_2006.csv")
    header_ref_df = pd.read_csv(f_header_ref, nrows=0)
    cols_1993 = header_ref_df.columns.tolist()[:81] # El mensual tiene 81 columnas
    
    print(f"Cargando 1993-2006 (81 columnas)...")
    df_1993 = pd.read_csv(f_1993, names=cols_1993, header=None)
    
    print(f"Cargando 2007-2014...")
    df_2007 = pd.read_csv(f_2007)
    
    print(f"Cargando 2017+...")
    df_2017 = pd.read_csv(f_2017)
    
    # Limpiar encabezados
    df_1993.columns = [clean_column_name(c) for c in df_1993.columns]
    df_2007.columns = [clean_column_name(c) for c in df_2007.columns]
    df_2017.columns = [clean_column_name(c) for c in df_2017.columns]
    
    # Exportar a Excel en hojas separadas
    output_file = os.path.join(base_path, "Resultado fiscal.xlsx")
    print(f"Exportando a {output_file} en hojas separadas...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_1993.to_excel(writer, sheet_name="1993-2006", index=False)
        df_2007.to_excel(writer, sheet_name="2007-2014", index=False)
        df_2017.to_excel(writer, sheet_name="2017", index=False)
    
    print("¡Listo! El archivo se ha generado con éxito.")

if __name__ == "__main__":
    main()
