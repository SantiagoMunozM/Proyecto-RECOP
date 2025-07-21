

import tkinter as tk
from tkinter import filedialog, messagebox
import csv
import os

def process_files(input_path, output_path):
    with open(input_path, 'r') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        prof_headers = []
        for i in range(14, len(headers) - 1, 15):
            prof_headers.append(headers[i])
        dicc_secc_dedicacion = {}
        periodo = ''
        for row in reader:
            if periodo == '':
                periodo = row['PERIODO']
            seccion = row['CRN  ']
            empty_session = False
            i = 0
            while (not empty_session) and (i < 1):
                header = prof_headers[i]
                content = row[header]
                if content == '':
                    empty_session = True
                else:
                    prof_list = content.split('***')
                    for prof in prof_list:
                        prof_info = prof.split('|')
                        name = prof_info[1].strip()
                        dedicacion = prof_info[2].strip()
                        if name != '':
                            if seccion not in dicc_secc_dedicacion:
                                new_seccion = {name: dedicacion}
                                dicc_secc_dedicacion[seccion] = new_seccion
                            else:
                                seccion_dict = dicc_secc_dedicacion[seccion]
                                if name not in seccion_dict:
                                    seccion_dict[name] = dedicacion
                i += 1

    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['seccion', 'profesor', 'dedicacion', 'periodo']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for nrc in dicc_secc_dedicacion:
            seccion = dicc_secc_dedicacion[nrc]
            for prof in seccion:
                dedicacion = seccion[prof]
                writer.writerow({'seccion': nrc, 'profesor': prof, 'dedicacion': dedicacion, 'periodo': periodo})

    messagebox.showinfo("Success", f"Archivo guardado como {os.path.basename(output_path)}")

class SimpleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Dedicación Processor")
        self.input_path = None

        self.label = tk.Label(root, text="Bienvenido. Seleccione el archivo CSV a procesar.")
        self.label.pack(pady=10)

        self.select_button = tk.Button(root, text="Seleccionar archivo", command=self.select_file)
        self.select_button.pack(pady=5)

        self.process_button = tk.Button(root, text="Procesar y guardar", command=self.process, state=tk.DISABLED)
        self.process_button.pack(pady=5)

    def select_file(self):
        path = filedialog.askopenfilename(title="Seleccione archivo CSV", filetypes=[("CSV files", "*.csv")])
        if path:
            self.input_path = path
            filename = os.path.basename(path)
            self.label.config(text=f"Archivo seleccionado: {filename}")
            self.process_button.config(state=tk.NORMAL)

    def process(self):
        if not self.input_path:
            messagebox.showerror("Error", "Primero seleccione un archivo.")
            return
        output_path = filedialog.asksaveasfilename(title="Guardar archivo como...", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not output_path:
            return
        process_files(self.input_path, output_path)

def main():
    root = tk.Tk()
    app = SimpleApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()