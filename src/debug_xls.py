import xlrd
import os

filepath = r'C:\Users\Usuario\Desktop\MARTIN\ECONOMICS\TRABAJO FINAL\Trabajo\data\raw\bcra\diar_cer.xls'
try:
    book = xlrd.open_workbook(filepath)
    print("Sheets:", book.sheet_names())
    sheet = book.sheet_by_index(0)
    print("Rows:", sheet.nrows)
    for i in range(min(10, sheet.nrows)):
        print(f"Row {i}: {sheet.row_values(i)}")
except Exception as e:
    print("Error:", e)
