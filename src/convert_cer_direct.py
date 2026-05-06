import xlrd
import csv
import os
from datetime import datetime

print("STARTING DIRECT CONVERSION")
input_path = r'C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra\diar_cer.xls'
output_path = r'C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra\cer.csv'

try:
    book = xlrd.open_workbook(input_path)
    sheet = book.sheet_by_index(0)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['fecha', 'cer'])
        
        count = 0
        for i in range(sheet.nrows):
            row = sheet.row_values(i)
            # Row mapping: Column A is index 0, Column B is index 1
            date_val = row[0]
            value_val = row[1]
            
            try:
                # BCRA dates are often stored as numbers in Excel
                if isinstance(date_val, (int, float)):
                    date_tuple = xlrd.xldate_as_tuple(date_val, book.datemode)
                    date_str = datetime(*date_tuple[:3]).strftime('%Y-%m-%d')
                else:
                    # Try string parsing
                    date_str = datetime.strptime(str(date_val), '%Y-%m-%d').strftime('%Y-%m-%d')
                
                # Check if value is numeric
                float_val = float(value_val)
                writer.writerow([date_str, float_val])
                count += 1
            except:
                continue
    print(f"DONE. Converted {count} rows.")
except Exception as e:
    print(f"ERROR: {e}")
