import pandas as pd
import os
import re

def clean_column_name(col):
    if not isinstance(col, str):
        return col
    # Quitar sufijos temporales (años)
    col = re.sub(r'_(2017|2007_2014|1993_2006|1993_2000)$', '', col)
    return col

def main():
    base_path = r"c:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo"
    input_file = os.path.join(base_path, "Resultado fiscal-nuevo.xlsx")
    
    print(f"Leyendo archivo: {input_file}")
    
    # Leer las hojas
    df_1993 = pd.read_excel(input_file, sheet_name="1993-2006")
    df_2007 = pd.read_excel(input_file, sheet_name="2007-2014")
    df_2017 = pd.read_excel(input_file, sheet_name="2017")
    
    # Limpiar columnas solo quitando años (y especificamente para la hoja 1993-2006 según instruccion, 
    # pero aplico la misma función segura a todas por si acaso, aunque solo pediste la de 1993-2006)
    df_1993.columns = [clean_column_name(c) for c in df_1993.columns]
    df_2007.columns = [clean_column_name(c) for c in df_2007.columns]
    df_2017.columns = [clean_column_name(c) for c in df_2017.columns]
    
    # Unificar haciendo coincidir columnas con el mismo nombre
    print("Unificando hojas...")
    # pd.concat por defecto alinea columnas con el mismo nombre. Si no existe, pone NaN. No inventa columnas.
    df_total = pd.concat([df_1993, df_2007, df_2017], ignore_index=True, sort=False)
    
    # Ordenar por tiempo si existe la columna indice_tiempo
    if 'indice_tiempo' in df_total.columns:
        df_total['indice_tiempo'] = pd.to_datetime(df_total['indice_tiempo'], errors='coerce')
        df_total = df_total.sort_values('indice_tiempo')
    
    # Exportar el resultado
    output_file = os.path.join(base_path, "Resultado fiscal-unificado.xlsx")
    print(f"Exportando a {output_file}...")
    
    df_total.to_excel(output_file, index=False, sheet_name="Unificado")
    
    print("¡Listo! El archivo unificado se ha generado.")

if __name__ == "__main__":
    main()
