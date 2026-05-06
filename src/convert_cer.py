"""
Convertir diar_cer.xls a cer.csv
Columna A = fecha, Columna B = valor CER
"""
import sys, os

# Intentar con xlrd primero, luego pandas
input_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'bcra', 'diar_cer.xls')
output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'bcra', 'cer.csv')

input_path = os.path.normpath(input_path)
output_path = os.path.normpath(output_path)

print(f"Input: {input_path}")
print(f"Output: {output_path}")
print(f"File exists: {os.path.exists(input_path)}")
print(f"File size: {os.path.getsize(input_path)} bytes")

try:
    import xlrd
    print("Using xlrd...")
    book = xlrd.open_workbook(input_path)
    sheet = book.sheet_by_index(0)
    print(f"Sheet: {sheet.name}, Rows: {sheet.nrows}, Cols: {sheet.ncols}")
    
    # Show first 5 rows for debugging
    for i in range(min(5, sheet.nrows)):
        print(f"  Row {i}: {sheet.row_values(i)}")
    
    # Convert
    import csv
    from datetime import datetime
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['fecha', 'cer'])
        count = 0
        for i in range(sheet.nrows):
            vals = sheet.row_values(i)
            cell_type_0 = sheet.cell_type(i, 0)
            
            try:
                # Type 3 = XL_CELL_DATE
                if cell_type_0 == 3:
                    date_tuple = xlrd.xldate_as_tuple(vals[0], book.datemode)
                    date_str = f"{date_tuple[0]:04d}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"
                elif cell_type_0 == 1:  # XL_CELL_TEXT
                    # Try parsing text date
                    for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                        try:
                            dt = datetime.strptime(str(vals[0]).strip(), fmt)
                            date_str = dt.strftime('%Y-%m-%d')
                            break
                        except:
                            continue
                    else:
                        continue
                elif cell_type_0 == 2:  # XL_CELL_NUMBER (could be serial date)
                    try:
                        date_tuple = xlrd.xldate_as_tuple(vals[0], book.datemode)
                        date_str = f"{date_tuple[0]:04d}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"
                    except:
                        continue
                else:
                    continue
                
                # Get value
                val = vals[1] if len(vals) > 1 else None
                if val is None or val == '':
                    continue
                float_val = float(val)
                
                writer.writerow([date_str, float_val])
                count += 1
            except Exception as ex:
                if i < 10:
                    print(f"  Skip row {i}: {ex}")
                continue
    
    print(f"\nDONE! Wrote {count} rows to {output_path}")

except ImportError:
    print("xlrd not installed, trying pandas...")
    import pandas as pd
    df = pd.read_excel(input_path, header=None, engine='xlrd')
    print(f"Shape: {df.shape}")
    print(f"First 5 rows:\n{df.head()}")
    
    df.columns = ['fecha', 'cer'] + [f'col{i}' for i in range(2, len(df.columns))]
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df['cer'] = pd.to_numeric(df['cer'], errors='coerce')
    df = df.dropna(subset=['fecha', 'cer'])[['fecha', 'cer']]
    df = df.sort_values('fecha')
    df.to_csv(output_path, index=False)
    print(f"DONE! Wrote {len(df)} rows")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
