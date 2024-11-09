import openpyxl
from tabulate import tabulate

xlsx_dataframe = openpyxl.load_workbook("Sheet 3.xlsx")

dataframe = xlsx_dataframe.active

data = []

for row in range(1, dataframe.max_row):

    _row = [row,]

    for col in dataframe.iter_cols(1, dataframe.max_column):

        _row.append(col[row].value)
    
    data.append(_row)

print(tabulate(data, headers="firstrow", tablefmt="grid"))