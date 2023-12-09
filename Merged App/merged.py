import tkinter as tk
from tkinter import filedialog
import pandas as pd
import os
import openpyxl
import xlrd


def browse_file1():
    filename = filedialog.askopenfilename()
    file1_path_var.set(filename)

def browse_file2():
    filename = filedialog.askopenfilename()
    file2_path_var.set(filename)

def merge_files():
    try:
        if file1_path_var.get().endswith('.csv'):
            df1 = pd.read_csv(file1_path_var.get())
        elif file1_path_var.get().endswith(('.xlsx', '.xls')):
            df1 = pd.read_excel(file1_path_var.get())
        else:
            raise ValueError('Unsupported file format for File 1')

        if file2_path_var.get().endswith('.csv'):
            df2 = pd.read_csv(file2_path_var.get())
        elif file2_path_var.get().endswith(('.xlsx', '.xls')):
            df2 = pd.read_excel(file2_path_var.get())
        else:
            raise ValueError('Unsupported file format for File 2')

        merged_df = pd.merge(df1, df2, on=merge_column_var.get(), how='outer', indicator=True)
        merged_df['_sort'] = merged_df['_merge'].apply(lambda x: 0 if x == 'both' else 1)
        merged_df.sort_values('_sort', inplace=True)
        merged_df.drop(columns=['_merge', '_sort'], inplace=True)

        merged_df.to_csv(output_path_var.get(), index=False)
        status_label.config(text="Merge completed successfully.")
    except Exception as e:
        status_label.config(text=f"Error: {e}")


app = tk.Tk()
app.title("Merged")

file1_path_var = tk.StringVar()
file2_path_var = tk.StringVar()
merge_column_var = tk.StringVar()
output_path_var = tk.StringVar()

desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
default_output_file = os.path.join(desktop_path, "merged_output.csv")
output_path_var.set(default_output_file)

tk.Label(app, text="File 1 (excel or csv):").pack()
file1_path = tk.Entry(app, textvariable=file1_path_var, width=50)
file1_path.pack()
tk.Button(app, text="Browse", command=browse_file1).pack()

tk.Label(app, text="File 2 (excel or csv):").pack()
file2_path = tk.Entry(app, textvariable=file2_path_var, width=50)
file2_path.pack()
tk.Button(app, text="Browse", command=browse_file2).pack()

tk.Label(app, text="Column to Merge On (Common Column Name):").pack()
merge_column = tk.Entry(app, textvariable=merge_column_var)
merge_column.pack()

tk.Label(app, text="Output File Path:").pack()
output_path = tk.Entry(app, textvariable=output_path_var, width=50)
output_path.pack()

merge_button = tk.Button(app, text="Merge Files", command=merge_files)
merge_button.pack()

# Reminder label
reminder_label = tk.Label(app, text="Reminder: Please close all open files before merging.")
reminder_label.pack(side=tk.LEFT, padx=10)

status_label = tk.Label(app, text="")
status_label.pack()

app.mainloop()
