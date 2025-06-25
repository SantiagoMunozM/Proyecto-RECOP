import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, List, Dict
from database import DatabaseManager
from ui_components import setup_ttk_styles

class BaseDialog:
    """Base class for all CRUD dialogs"""
    def __init__(self, parent, db_manager: DatabaseManager, title: str, callback: Callable = None):
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        self.style = setup_ttk_styles(self.dialog)
        
        # Center dialog
        self.center_dialog()
        
    def center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def on_cancel(self):
        """Handle dialog cancel"""
        self.result = None
        self.dialog.destroy()
    
    def on_success(self, result=True):
        """Handle successful operation"""
        self.result = result
        self.dialog.destroy()
        if self.callback:
            self.callback()

class CreateDepartamentoDialog(BaseDialog):
    """Dialog for creating departamento"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        super().__init__(parent, db_manager, "Crear Departamento", callback)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI"""
        self.dialog.geometry("400x200")
        
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Crear Nuevo Departamento", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Name entry
        ttk.Label(main_frame, text="Nombre del Departamento:").pack(anchor=tk.W)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        name_entry.pack(pady=(5, 20), fill=tk.X)
        name_entry.focus()
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Cancelar", command=self.on_cancel, style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(btn_frame, text="Crear", command=self.create_departamento, style="Green.TButton").pack(side=tk.RIGHT)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.create_departamento())
        
    def create_departamento(self):
        """Create the departamento"""
        nombre = self.name_var.get().strip().upper()
        
        if not nombre:
            messagebox.showerror("Error", "El nombre del departamento es requerido.")
            return
            
        if self.db_manager.departamento_exists(nombre):
            messagebox.showerror("Error", f"El departamento '{nombre}' ya existe.")
            return
            
        if self.db_manager.create_departamento(nombre):
            messagebox.showinfo("Éxito", f"Departamento '{nombre}' creado exitosamente.")
            self.on_success()
        else:
            messagebox.showerror("Error", "Error al crear el departamento.")


class CreateProfesorDialog(BaseDialog):
    """Multi-step dialog for creating profesor with multiple departments"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        super().__init__(parent, db_manager, "Crear Profesor", callback)
        self.current_step = 0
        self.selected_departamentos = []  # Changed to list
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI"""
        self.dialog.geometry("500x400")
        
        # Main container
        self.main_frame = ttk.Frame(self.dialog, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress indicator
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_label = ttk.Label(self.progress_frame, text="Paso 1 de 2: Seleccionar Departamentos",
                                       font=("Arial", 12, "bold"))
        self.progress_label.pack()
        
        # Content frame (will change based on step)
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Start with step 1
        self.show_step_1()
    
    def show_step_1(self):
        """Step 1: Select departments (multiple selection)"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 1 de 2: Seleccionar Departamentos")
        
        # Instructions
        ttk.Label(self.content_frame, 
                 text="Seleccione uno o más departamentos para el profesor:",
                 font=("Arial", 10)).pack(pady=(0, 15))
        
        # Department selection with checkboxes
        ttk.Label(self.content_frame, text="Departamentos:").pack(anchor=tk.W)
        
        # Create frame for checkboxes
        self.dept_frame = ttk.Frame(self.content_frame)
        self.dept_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 20))
        
        # Load departamentos
        departamentos = self.db_manager.get_departamentos()
        self.dept_vars = {}  # Dictionary to store checkbox variables
        
        if not departamentos:
            ttk.Label(self.dept_frame, 
                     text="No hay departamentos disponibles. Debe crear un departamento primero.",
                     foreground="red").pack(pady=20)
            
            # Show create departamento button
            ttk.Button(self.dept_frame, text="Crear Departamento",
                      command=self.create_departamento_first, style = "Orange.TButton").pack(pady=10)
        else:
            # Create scrollable frame for departments
            canvas = tk.Canvas(self.dept_frame, height=150)
            scrollbar = ttk.Scrollbar(self.dept_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Add checkboxes for each department
            for dept in departamentos:
                var = tk.BooleanVar()
                self.dept_vars[dept] = var
                
                check = ttk.Checkbutton(
                    scrollable_frame,
                    text=dept,
                    variable=var,
                    onvalue=True,
                    offvalue=False
                )
                check.pack(anchor=tk.W, pady=2)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        
        # Setup buttons
        self.setup_buttons_step_1()
    
    def create_departamento_first(self):
        """Create departamento from within this dialog"""
        def refresh_departamentos():
            self.show_step_1()  # Refresh the step
            
        CreateDepartamentoDialog(self.dialog, self.db_manager, refresh_departamentos)
        
    def setup_buttons_step_1(self):
        """Setup buttons for step 1"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        ttk.Button(self.btn_frame, text="Cancelar", command=self.on_cancel, style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(self.btn_frame, text="Siguiente", command=self.go_to_step_2, style="Blue.TButton").pack(side=tk.RIGHT)
    
    def go_to_step_2(self):
        """Go to step 2 - validate that at least one department is selected"""
        if not hasattr(self, 'dept_vars'):
            messagebox.showerror("Error", "Debe crear al menos un departamento primero.")
            return
        
        # Get selected departments
        self.selected_departamentos = [
            dept for dept, var in self.dept_vars.items() if var.get()
        ]
        
        if not self.selected_departamentos:
            messagebox.showerror("Error", "Debe seleccionar al menos un departamento.")
            return
            
        self.current_step = 1
        self.show_step_2()
    
    def show_step_2(self):
        """Step 2: Enter profesor details"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 2 de 2: Información del Profesor")
        
        # Show selected departments
        info_frame = ttk.LabelFrame(self.content_frame, text="Departamentos Seleccionados", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        dept_text = ", ".join(self.selected_departamentos)
        if len(dept_text) > 80:  # Truncate if too long
            dept_text = dept_text[:77] + "..."
        
        ttk.Label(info_frame, text=dept_text, font=("Arial", 9)).pack()
        ttk.Label(info_frame, text=f"Total: {len(self.selected_departamentos)} departamento(s)", 
                 font=("Arial", 8), foreground="gray").pack()
        
        # Profesor details form
        form_frame = ttk.LabelFrame(self.content_frame, text="Datos del Profesor", padding="15")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Names
        ttk.Label(form_frame, text="Nombres:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.nombres_var = tk.StringVar()
        nombres_entry = ttk.Entry(form_frame, textvariable=self.nombres_var, width=40)
        nombres_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        nombres_entry.focus()
        
        # Surnames
        ttk.Label(form_frame, text="Apellidos:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.apellidos_var = tk.StringVar()
        apellidos_entry = ttk.Entry(form_frame, textvariable=self.apellidos_var, width=40)
        apellidos_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Type
        ttk.Label(form_frame, text="Tipo:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.tipo_var = tk.StringVar(value="PRINCIPAL")
        tipo_combo = ttk.Combobox(form_frame, textvariable=self.tipo_var,
                                 values=["PRINCIPAL", "AUXILIAR", "INVITADO"], state="readonly", width=37)
        tipo_combo.grid(row=2, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
        # Setup buttons
        self.setup_buttons_step_2()
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.create_profesor())
        
    def setup_buttons_step_2(self):
        """Setup buttons for step 2"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        ttk.Button(self.btn_frame, text="Atrás", command=self.go_back_to_step_1, style="Gray.TButton").pack(side=tk.LEFT)
        ttk.Button(self.btn_frame, text="Cancelar", command=self.on_cancel, style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(self.btn_frame, text="Crear Profesor", command=self.create_profesor, style="Green.TButton").pack(side=tk.RIGHT)
        
    def go_back_to_step_1(self):
        """Go back to step 1"""
        self.current_step = 0
        self.show_step_1()
        
    def create_profesor(self):
        """Create the profesor with multiple departments"""
        nombres = self.nombres_var.get().strip()
        apellidos = self.apellidos_var.get().strip()
        tipo = self.tipo_var.get()
        
        if not nombres or not apellidos:
            messagebox.showerror("Error", "Nombres y apellidos son requeridos.")
            return
        
        # Create profesor with multiple departments
        profesor_id = self.db_manager.create_profesor(nombres, apellidos, tipo, self.selected_departamentos)
        
        if profesor_id:
            dept_list = ", ".join(self.selected_departamentos)
            messagebox.showinfo("Éxito", 
                               f"Profesor '{nombres} {apellidos}' creado exitosamente.\n"
                               f"Departamentos: {dept_list}")
            self.on_success()
        else:
            messagebox.showerror("Error", "Error al crear el profesor.")

class CreateMateriaDialog(BaseDialog):
    """Multi-step dialog for creating materia"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        super().__init__(parent, db_manager, "Crear Materia", callback)
        self.current_step = 0
        self.selected_departamento = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI"""
        self.dialog.geometry("550x500")
        
        # Main container
        self.main_frame = ttk.Frame(self.dialog, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress indicator
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_label = ttk.Label(self.progress_frame, text="Paso 1 de 2: Seleccionar Departamento",
                                       font=("Arial", 12, "bold"))
        self.progress_label.pack()
        
        # Content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Start with step 1
        self.show_step_1()
        
    def show_step_1(self):
        """Step 1: Select departamento"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 1 de 2: Seleccionar Departamento")
        
        ttk.Label(self.content_frame, 
                 text="Seleccione el departamento al que pertenecerá la materia:",
                 font=("Arial", 10)).pack(pady=(0, 15))
        
        ttk.Label(self.content_frame, text="Departamento:").pack(anchor=tk.W)
        
        self.dept_var = tk.StringVar()
        self.dept_combo = ttk.Combobox(self.content_frame, textvariable=self.dept_var,
                                      state="readonly", width=50)
        
        departamentos = self.db_manager.get_departamentos()
        if not departamentos:
            ttk.Label(self.content_frame, 
                     text="No hay departamentos disponibles. Debe crear un departamento primero.",
                     foreground="red").pack(pady=20)
            ttk.Button(self.content_frame, text="Crear Departamento",
                      command=self.create_departamento_first, style="Orange.TButton").pack(pady=10)
        else:
            self.dept_combo['values'] = departamentos
            self.dept_combo.pack(pady=(5, 20), fill=tk.X)
        
        self.setup_buttons_step_1()
        
    def create_departamento_first(self):
        """Create departamento from within this dialog"""
        def refresh_departamentos():
            self.show_step_1()
            
        CreateDepartamentoDialog(self.dialog, self.db_manager, refresh_departamentos)
        
    def setup_buttons_step_1(self):
        """Setup buttons for step 1"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        ttk.Button(self.btn_frame, text="Cancelar", command=self.on_cancel, style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(self.btn_frame, text="Siguiente", command=self.go_to_step_2, style="Blue.TButton").pack(side=tk.RIGHT)
        
    def go_to_step_2(self):
        """Go to step 2"""
        if not hasattr(self, 'dept_combo') or not self.dept_var.get():
            messagebox.showerror("Error", "Debe seleccionar un departamento.")
            return
            
        self.selected_departamento = self.dept_var.get()
        self.current_step = 1
        self.show_step_2()
        
    def show_step_2(self):
        """Step 2: Enter materia details"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 2 de 2: Información de la Materia")
        
        # Show selected departamento
        info_frame = ttk.LabelFrame(self.content_frame, text="Departamento Seleccionado", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(info_frame, text=self.selected_departamento, font=("Arial", 10, "bold")).pack()
        
        # Materia details form
        form_frame = ttk.LabelFrame(self.content_frame, text="Datos de la Materia", padding="15")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Código
        ttk.Label(form_frame, text="Código:*").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.codigo_var = tk.StringVar()
        codigo_entry = ttk.Entry(form_frame, textvariable=self.codigo_var, width=40)
        codigo_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        codigo_entry.focus()
        
        # Nombre
        ttk.Label(form_frame, text="Nombre:*").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.nombre_var = tk.StringVar()
        nombre_entry = ttk.Entry(form_frame, textvariable=self.nombre_var, width=40)
        nombre_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Créditos
        ttk.Label(form_frame, text="Créditos:*").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.creditos_var = tk.StringVar(value="3")
        creditos_spinbox = tk.Spinbox(form_frame, textvariable=self.creditos_var, 
                                     from_=1, to=10, width=37)
        creditos_spinbox.grid(row=2, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Nivel
        ttk.Label(form_frame, text="Nivel:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.nivel_var = tk.StringVar(value="PREGRADO")
        nivel_combo = ttk.Combobox(form_frame, textvariable=self.nivel_var,
                                  values=["PREGRADO", "POSTGRADO", "ESPECIALIZACION"], 
                                  state="readonly", width=37)
        nivel_combo.grid(row=3, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Calificación
        ttk.Label(form_frame, text="Modo Calificación:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        self.calificacion_var = tk.StringVar(value="NUMERICO")
        cal_combo = ttk.Combobox(form_frame, textvariable=self.calificacion_var,
                                values=["NUMERICO", "CONCEPTUAL", "PASS/FAIL"], 
                                state="readonly", width=37)
        cal_combo.grid(row=4, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Campus
        ttk.Label(form_frame, text="Campus:").grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        self.campus_var = tk.StringVar(value="BOGOTA")
        campus_combo = ttk.Combobox(form_frame, textvariable=self.campus_var,
                                   values=["BOGOTA", "MEDELLIN", "BARRANQUILLA"], 
                                   state="readonly", width=37)
        campus_combo.grid(row=5, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Período
        ttk.Label(form_frame, text="Período:").grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        self.periodo_var = tk.StringVar(value="2025-1")
        periodo_entry = ttk.Entry(form_frame, textvariable=self.periodo_var, width=40)
        periodo_entry.grid(row=6, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
        # Required fields note
        ttk.Label(form_frame, text="* Campos requeridos", font=("Arial", 8), 
                 foreground="gray").grid(row=7, column=0, columnspan=2, pady=(10, 0))
        
        self.setup_buttons_step_2()
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.create_materia())
        
    def setup_buttons_step_2(self):
        """Setup buttons for step 2"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        ttk.Button(self.btn_frame, text="Atrás", command=self.go_back_to_step_1, style="Gray.TButton").pack(side=tk.LEFT)
        ttk.Button(self.btn_frame, text="Cancelar", command=self.on_cancel, style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(self.btn_frame, text="Crear Materia", command=self.create_materia, style="Green.TButton").pack(side=tk.RIGHT)
        
    def go_back_to_step_1(self):
        """Go back to step 1"""
        self.current_step = 0
        self.show_step_1()
        
    def create_materia(self):
        """Create the materia"""
        codigo = self.codigo_var.get().strip().upper()
        nombre = self.nombre_var.get().strip()
        
        if not codigo or not nombre:
            messagebox.showerror("Error", "Código y nombre son requeridos.")
            return
            
        try:
            creditos = int(self.creditos_var.get())
        except ValueError:
            messagebox.showerror("Error", "Los créditos deben ser un número válido.")
            return
            
        if self.db_manager.materia_codigo_exists(codigo):
            messagebox.showerror("Error", f"Ya existe una materia con el código '{codigo}'.")
            return
            
        nivel = self.nivel_var.get()
        calificacion = self.calificacion_var.get()
        campus = self.campus_var.get()
        periodo = self.periodo_var.get().strip()
        
        if self.db_manager.create_materia(codigo, nombre, creditos, nivel, calificacion, 
                                         campus, periodo, self.selected_departamento):
            messagebox.showinfo("Éxito", 
                               f"Materia '{codigo} - {nombre}' creada exitosamente en {self.selected_departamento}.")
            self.on_success()
        else:
            messagebox.showerror("Error", "Error al crear la materia.")

class CreateSeccionDialog(BaseDialog):
    """Multi-step dialog for creating seccion"""
    def __init__(self, parent, db_manager: DatabaseManager, callback: Callable = None):
        super().__init__(parent, db_manager, "Crear Sección", callback)
        self.current_step = 0
        self.selected_departamento = None
        self.selected_materia = None
        self.available_profesores = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI"""
        self.dialog.geometry("600x550")
        
        # Main container
        self.main_frame = ttk.Frame(self.dialog, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Progress indicator
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_label = ttk.Label(self.progress_frame, text="Paso 1 de 3: Seleccionar Departamento",
                                       font=("Arial", 12, "bold"))
        self.progress_label.pack()
        
        # Content frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Start with step 1
        self.show_step_1()
        
    def show_step_1(self):
        """Step 1: Select departamento"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 1 de 3: Seleccionar Departamento")
        
        ttk.Label(self.content_frame, 
                 text="Seleccione el departamento:",
                 font=("Arial", 10)).pack(pady=(0, 15))
        
        ttk.Label(self.content_frame, text="Departamento:").pack(anchor=tk.W)
        
        self.dept_var = tk.StringVar()
        self.dept_combo = ttk.Combobox(self.content_frame, textvariable=self.dept_var,
                                      state="readonly", width=50)
        
        departamentos = self.db_manager.get_departamentos()
        if departamentos:
            self.dept_combo['values'] = departamentos
            self.dept_combo.pack(pady=(5, 20), fill=tk.X)
        else:
            ttk.Label(self.content_frame, 
                     text="No hay departamentos disponibles.",
                     foreground="red").pack(pady=20)
        
        self.setup_buttons_step_1()
        
    def setup_buttons_step_1(self):
        """Setup buttons for step 1"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        ttk.Button(self.btn_frame, text="Cancelar", command=self.on_cancel, style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(self.btn_frame, text="Siguiente", command=self.go_to_step_2, style="Blue.TButton").pack(side=tk.RIGHT)
        
    def go_to_step_2(self):
        """Go to step 2"""
        if not self.dept_var.get():
            messagebox.showerror("Error", "Debe seleccionar un departamento.")
            return
            
        self.selected_departamento = self.dept_var.get()
        self.current_step = 1
        self.show_step_2()
        
    def show_step_2(self):
        """Step 2: Select materia"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 2 de 3: Seleccionar Materia")
        
        # Show selected departamento
        info_frame = ttk.LabelFrame(self.content_frame, text="Departamento Seleccionado", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(info_frame, text=self.selected_departamento, font=("Arial", 10, "bold")).pack()
        
        ttk.Label(self.content_frame, text="Seleccione la materia:").pack(anchor=tk.W)
        
        self.materia_var = tk.StringVar()
        self.materia_combo = ttk.Combobox(self.content_frame, textvariable=self.materia_var,
                                         state="readonly", width=60)
        
        # Load materias for this departamento
        materias = self.db_manager.get_materias_by_departamento(self.selected_departamento)
        if materias:
            materia_options = [f"{m['codigo']} - {m['nombre']}" for m in materias]
            self.materia_combo['values'] = materia_options
            self.materia_combo.pack(pady=(5, 20), fill=tk.X)
        else:
            ttk.Label(self.content_frame, 
                     text="No hay materias disponibles en este departamento.",
                     foreground="red").pack(pady=20)
            ttk.Button(self.content_frame, text="Crear Materia",
                      command=self.create_materia_first, style="Orange.TButton").pack(pady=10)
        
        self.setup_buttons_step_2()
        
    def create_materia_first(self):
        """Create materia from within this dialog"""
        def refresh_materias():
            self.show_step_2()
            
        CreateMateriaDialog(self.dialog, self.db_manager, refresh_materias)
        
    def setup_buttons_step_2(self):
        """Setup buttons for step 2"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        ttk.Button(self.btn_frame, text="Atrás", command=self.go_back_to_step_1, style="Gray.TButton").pack(side=tk.LEFT)
        ttk.Button(self.btn_frame, text="Cancelar", command=self.on_cancel, style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(self.btn_frame, text="Siguiente", command=self.go_to_step_3, style="Blue.TButton").pack(side=tk.RIGHT)
        
    def go_back_to_step_1(self):
        """Go back to step 1"""
        self.current_step = 0
        self.show_step_1()
        
    def go_to_step_3(self):
        """Go to step 3"""
        if not self.materia_var.get():
            messagebox.showerror("Error", "Debe seleccionar una materia.")
            return
            
        # Extract materia codigo from selection
        self.selected_materia = self.materia_var.get().split(' - ')[0]
        self.current_step = 2
        self.show_step_3()
        
    def show_step_3(self):
        """Step 3: Enter seccion details"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            
        self.progress_label.config(text="Paso 3 de 3: Información de la Sección")
        
        # Show selections
        info_frame = ttk.LabelFrame(self.content_frame, text="Selecciones", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(info_frame, text=f"Departamento: {self.selected_departamento}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Materia: {self.materia_var.get()}").pack(anchor=tk.W)
        
        # Seccion details form
        form_frame = ttk.LabelFrame(self.content_frame, text="Datos de la Sección", padding="15")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # NRC
        ttk.Label(form_frame, text="NRC:*").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.nrc_var = tk.StringVar()
        nrc_entry = ttk.Entry(form_frame, textvariable=self.nrc_var, width=20)
        nrc_entry.grid(row=0, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        nrc_entry.focus()
        
        # Indicator
        ttk.Label(form_frame, text="Indicador:*").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.indicador_var = tk.StringVar(value="01")
        indicador_entry = ttk.Entry(form_frame, textvariable=self.indicador_var, width=20)
        indicador_entry.grid(row=1, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        
        # Cupo
        ttk.Label(form_frame, text="Cupo:*").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.cupo_var = tk.StringVar(value="30")
        cupo_spinbox = tk.Spinbox(form_frame, textvariable=self.cupo_var, 
                                 from_=1, to=200, width=18)
        cupo_spinbox.grid(row=2, column=1, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        
        # Profesores (optional for now)
        ttk.Label(form_frame, text="Profesores\n(opcional):").grid(row=3, column=0, sticky=tk.W+tk.N, pady=(0, 5))
        
        prof_frame = ttk.Frame(form_frame)
        prof_frame.grid(row=3, column=1, sticky=tk.W+tk.E, pady=(0, 5), padx=(10, 0))
        
        # Load available profesores
        self.available_profesores = self.db_manager.get_profesores_by_departamento(self.selected_departamento)
        
        # Listbox for profesor selection
        prof_listbox_frame = ttk.Frame(prof_frame)
        prof_listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(prof_listbox_frame, text="Profesores disponibles:").pack(anchor=tk.W)
        
        self.prof_listbox = tk.Listbox(prof_listbox_frame, selectmode=tk.MULTIPLE, height=6)
        scrollbar = ttk.Scrollbar(prof_listbox_frame, orient=tk.VERTICAL, command=self.prof_listbox.yview)
        self.prof_listbox.config(yscrollcommand=scrollbar.set)
        
        self.prof_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate listbox
        for prof in self.available_profesores:
            self.prof_listbox.insert(tk.END, prof['full_name'])
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
        # Required fields note
        ttk.Label(form_frame, text="* Campos requeridos", font=("Arial", 8), 
                 foreground="gray").grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        # Bind NRC validation
        nrc_entry.bind('<FocusOut>', self.validate_nrc)
        
        self.setup_buttons_step_3()
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.create_seccion())
        
    def validate_nrc(self, event=None):
        """Validate NRC uniqueness"""
        try:
            nrc = int(self.nrc_var.get())
            if self.db_manager.nrc_exists(nrc):
                messagebox.showwarning("Advertencia", f"El NRC {nrc} ya existe. Debe usar un NRC único.")
                event.widget.focus()
        except ValueError:
            pass  # Not a valid number yet
            
    def setup_buttons_step_3(self):
        """Setup buttons for step 3"""
        for widget in self.btn_frame.winfo_children():
            widget.destroy()
            
        ttk.Button(self.btn_frame, text="Atrás", command=self.go_back_to_step_2, style="Gray.TButton").pack(side=tk.LEFT)
        ttk.Button(self.btn_frame, text="Cancelar", command=self.on_cancel, style="Gray.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(self.btn_frame, text="Crear Sección", command=self.create_seccion, style="Green.TButton").pack(side=tk.RIGHT)
        
    def go_back_to_step_2(self):
        """Go back to step 2"""
        self.current_step = 1
        self.show_step_2()
        
    def create_seccion(self):
        """Create the seccion"""
        try:
            nrc = int(self.nrc_var.get())
        except ValueError:
            messagebox.showerror("Error", "El NRC debe ser un número válido.")
            return
            
        indicador = self.indicador_var.get().strip()
        
        try:
            cupo = int(self.cupo_var.get())
        except ValueError:
            messagebox.showerror("Error", "El cupo debe ser un número válido.")
            return
            
        if not indicador:
            messagebox.showerror("Error", "El indicador es requerido.")
            return
            
        if self.db_manager.nrc_exists(nrc):
            messagebox.showerror("Error", f"El NRC {nrc} ya existe.")
            return
            
        # Get selected profesores
        selected_indices = self.prof_listbox.curselection()
        profesor_ids = [self.available_profesores[i]['id'] for i in selected_indices]
        
        if self.db_manager.create_seccion(nrc, indicador, cupo, self.selected_materia, profesor_ids):
            prof_count = len(profesor_ids)
            prof_text = f" con {prof_count} profesor(es)" if prof_count > 0 else " sin profesores asignados"
            messagebox.showinfo("Éxito", 
                               f"Sección {nrc} creada exitosamente para {self.selected_materia}{prof_text}.")
            self.on_success()
        else:
            messagebox.showerror("Error", "Error al crear la sección.")

# Utility function to open dialogs
def open_create_dialog(dialog_type: str, parent, db_manager: DatabaseManager, callback: Callable = None):
    """Open the appropriate create dialog"""
    dialogs = {
        'departamento': CreateDepartamentoDialog,
        'profesor': CreateProfesorDialog,
        'materia': CreateMateriaDialog,
        'seccion': CreateSeccionDialog,
    }
    
    if dialog_type in dialogs:
        dialogs[dialog_type](parent, db_manager, callback)
    else:
        messagebox.showerror("Error", f"Tipo de diálogo desconocido: {dialog_type}")
        
# Add this new class at the end of the file:

