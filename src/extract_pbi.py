import pandas as pd
import os

def parse_indec_horizontal(df):
    year_row = 3
    q_row = 4
    data_start = 6
    q_months = ['01-01', '04-01', '07-01', '10-01']
    
    dates = []
    col_indices = []
    
    current_year = None
    for col in range(1, len(df.columns)):
        y_val = df.iloc[year_row, col]
        q_val = df.iloc[q_row, col]
        
        if pd.notna(y_val) and str(y_val).strip().isdigit():
            current_year = int(float(y_val))
            
        if current_year is not None and pd.notna(q_val) and 'trimestre' in str(q_val):
            try:
                q_num = int(str(q_val)[0])
                if 1 <= q_num <= 4:
                    date_str = f"{current_year}-{q_months[q_num-1]}"
                    dates.append(date_str)
                    col_indices.append(col)
            except:
                pass
                
    result_rows = []
    for row in range(data_start, len(df)):
        var_name = df.iloc[row, 0]
        if pd.isna(var_name) or str(var_name).strip() == '':
            continue
            
        var_name = str(var_name).strip()
        row_data = {'variable': var_name}
        valid_data = False
        
        for date, col in zip(dates, col_indices):
            val = df.iloc[row, col]
            if pd.notna(val) and val != '':
                try:
                    row_data[date] = float(val)
                    valid_data = True
                except:
                    pass
        if valid_data:
            result_rows.append(row_data)
            
    if not result_rows:
        return pd.DataFrame()
        
    res_df = pd.DataFrame(result_rows).set_index('variable').T
    res_df.index.name = 'fecha'
    res_df = res_df.reset_index()
    return res_df

def clean_cols(df):
    cols_map = {}
    for c in df.columns:
        if c == 'fecha': continue
        c_low = c.lower()
        if 'producto interno bruto' in c_low: cols_map[c] = 'pbi'
        elif 'importaciones' in c_low: cols_map[c] = 'impo'
        elif 'exportaciones' in c_low: cols_map[c] = 'expo'
        elif 'consumo privado' in c_low: cols_map[c] = 'consumo_priv'
        elif 'consumo p' in c_low: cols_map[c] = 'consumo_pub'
        elif 'capital fijo' in c_low: cols_map[c] = 'fbkf'
        elif 'oferta global' in c_low: cols_map[c] = 'oferta_global'
        elif 'demanda global' in c_low: cols_map[c] = 'demanda_global'
    
    df = df.rename(columns=cols_map)
    # keep only one of each column in case of duplicates
    df = df.loc[:,~df.columns.duplicated()]
    return df

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'Variables Finales', 'sh_oferta_demanda_03_26.xls')
    
    df1 = pd.read_excel(file_path, sheet_name='cuadro 1', header=None)
    df2 = pd.read_excel(file_path, sheet_name='cuadro 2', header=None)
    
    res1 = parse_indec_horizontal(df1)
    res2 = parse_indec_horizontal(df2)
    const = pd.merge(res1, res2, on='fecha', how='outer')
    const = clean_cols(const)
    
    df12 = pd.read_excel(file_path, sheet_name='cuadro 12', header=None)
    df8 = pd.read_excel(file_path, sheet_name='cuadro 8', header=None)
    
    res12 = parse_indec_horizontal(df12)
    res8 = parse_indec_horizontal(df8)
    corr = pd.merge(res12, res8, on='fecha', how='outer')
    corr = clean_cols(corr)
    
    const.to_csv(os.path.join(base_dir, 'data', 'Variables Finales', 'pbi_constante_2004.csv'), index=False)
    corr.to_csv(os.path.join(base_dir, 'data', 'Variables Finales', 'pbi_corriente.csv'), index=False)
    print("Guardados pbi_constante_2004.csv y pbi_corriente.csv limpiados.")

if __name__ == '__main__':
    main()
