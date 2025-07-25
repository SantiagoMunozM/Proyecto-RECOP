import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from database import DatabaseManager
from ui_components import DatabaseViewer, ProgressDialog, SearchProfessorDialog, ProfessorSessionsDialog, setup_ttk_styles, get_theme_colors
from crud_dialogs import open_create_dialog
from csv_processor import CSVProcessor
from utils import FileHelpers, UIHelpers, Constants

class RECOPSimulator:
    def __init__(self, root):
        self.root = root
        self.csv_file_path = None
        self.db_manager = DatabaseManager()
        self.csv_processor = CSVProcessor(self.db_manager)
        self.style = setup_ttk_styles(self.root)
        self.setup_ui()
        self.apply_dark_mode_to_widgets()
        self.check_existing_database()
    
    def setup_ui(self):
        """Setup the main user interface"""
        self.root.title("Simulador RECOP - Sistema de Gestión de Horarios")
        self.root.geometry(f"{Constants.DEFAULT_WINDOW_WIDTH}x{Constants.DEFAULT_WINDOW_HEIGHT}")
        
        # Create menu bar
        self.create_menu()
        
        # Main content
        self.create_main_interface()
        
        # Status bar
        self.create_status_bar()
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cargar CSV...", command=self.select_csv_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Procesar Archivo", command=self.process_csv, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Database menu
        db_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Base de Datos", menu=db_menu)
        db_menu.add_command(label="Ver Tablas", command=self.view_database_tables)
        db_menu.add_command(label="Estadísticas", command=self.show_database_stats)
        db_menu.add_separator()
        db_menu.add_command(label="Respaldar BD", command=self.backup_database)
        db_menu.add_command(label="Recrear BD", command=self.reset_database)
        
        # Create menu
        create_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Crear", menu=create_menu)
        create_menu.add_command(label="Departamento", command=lambda: self.create_entity('departamento'))
        create_menu.add_command(label="Profesor", command=lambda: self.create_entity('profesor'))
        create_menu.add_command(label="Materia", command=lambda: self.create_entity('materia'))
        create_menu.add_command(label="Sección", command=lambda: self.create_entity('seccion'))
        
        # Search menu - UPDATED
        search_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Consultas", menu=search_menu)
        search_menu.add_command(label="Buscar Profesor", command=self.search_professor)
        search_menu.add_command(label="Sesiones de Profesor", command=self.query_professor_sessions)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-o>', lambda e: self.select_csv_file())
        self.root.bind('<Control-p>', lambda e: self.process_csv())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        
    def create_main_interface(self):
        """Create the main interface content"""
        # Main container with padding
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Welcome section
        self.create_welcome_section(main_container)
        
        # File operations section
        self.create_file_upload_section(main_container)
        
        # Database operations section
        self.create_database_section(main_container)
        
        # Quick actions section
        self.create_quick_actions_section(main_container)
        
        #Recop
        self.create_recop_section(main_container)
    
    def create_welcome_section(self, parent):
        """Create welcome section"""
        welcome_frame = ttk.LabelFrame(parent, text="Bienvenido al Simulador RECOP", padding="15")
        welcome_frame.pack(fill=tk.X, pady=(0, 15))
        
        welcome_text = (
            "Sistema de Gestión de Horarios Universitarios\n"
            "Cargue un archivo CSV de cartelera para comenzar o gestione los datos existentes"
        )
        
        welcome_label = ttk.Label(
            welcome_frame,
            text=welcome_text,
            font=("Arial", 11),
            justify=tk.CENTER
        )
        welcome_label.pack()
    
    
        # Replace the create_file_upload_section method in app.py:
    
    def create_file_upload_section(self, parent):
        """Create file upload section"""
        upload_frame = ttk.LabelFrame(parent, text="Cargar Datos", padding="15")
        upload_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Instructions
        instructions = ttk.Label(upload_frame, 
                               text="Cargue archivos CSV con datos académicos, vincule datos personales o actualice dedicaciones:",
                               font=("Arial", 11))
        instructions.pack(pady=(0, 10))
        
        # Sub-instructions for each button - Updated for three columns
        sub_instructions_frame = tk.Frame(upload_frame)
        sub_instructions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Left side - Academic data
        left_frame = tk.Frame(sub_instructions_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Label(left_frame, text="📄 CSV Académico:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        tk.Label(left_frame, text="Datos de materias, secciones, profesores y sesiones", 
                 font=("Arial", 8), fg="gray").pack(anchor=tk.W)
        
        # Middle - Personal data
        middle_frame = tk.Frame(sub_instructions_frame)
        middle_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Label(middle_frame, text="👥 Datos Personales:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        tk.Label(middle_frame, text="Información adicional de empleados", 
                 font=("Arial", 8), fg="gray").pack(anchor=tk.W)
        
        # Right side - Dedication data (NEW)
        right_frame = tk.Frame(sub_instructions_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(right_frame, text="📊 Dedicaciones:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        tk.Label(right_frame, text="Porcentajes de dedicación por sección", 
                 font=("Arial", 8), fg="gray").pack(anchor=tk.W)
        
        # Buttons container
        buttons_container = tk.Frame(upload_frame)
        buttons_container.pack(fill=tk.X)
        
        # Academic CSV buttons - separate select and process
        self.select_csv_btn = ttk.Button(
            buttons_container,
            text="📁 Seleccionar CSV",
            command=self.select_csv_file,
            style="Blue.TButton"
        )
        self.select_csv_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Process CSV button (initially disabled)
        self.process_csv_btn = ttk.Button(
            buttons_container,
            text="⚙️ Procesar CSV",
            command=self.process_csv,
            state="disabled",
            style="Green.TButton"
        )
        self.process_csv_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # Personal data upload button
        self.upload_personal_btn = ttk.Button(
            buttons_container,
            text="👥 Vincular Datos Personales",
            command=self.upload_personal_data,
            state="disabled",
            style="Teal.TButton"
        )
        self.upload_personal_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # NEW: Dedication data upload button
        self.upload_dedication_btn = ttk.Button(
            buttons_container,
            text="📊 Actualizar Dedicaciones",
            command=self.upload_dedication_data,
            state="disabled",
            style="Orange.TButton"
        )
        self.upload_dedication_btn.pack(side=tk.LEFT)
        
        # File info display
        self.file_info_var = tk.StringVar(value="Ningún archivo seleccionado")
        file_info_label = ttk.Label(upload_frame, textvariable=self.file_info_var, 
                                   font=("Arial", 10), foreground="gray")
        file_info_label.pack(pady=(15, 0))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(upload_frame, variable=self.progress_var, 
                                           maximum=100, style="Blue.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        self.progress_bar.pack_forget()  # Initially hidden     
        
    def create_database_section(self, parent):
        """Create database operations section"""
        db_frame = ttk.LabelFrame(parent, text="Operaciones de Base de Datos", padding="15")
        db_frame.pack(fill=tk.X, pady=(0, 15))
        
        # First row of buttons
        row1 = ttk.Frame(db_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        
        self.view_tables_btn = ttk.Button(
            row1,
            text="📊 Ver Tablas",
            command=self.view_database_tables,
            state="disabled",
            style="Blue.TButton"
        )
        self.view_tables_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stats_btn = ttk.Button(
            row1,
            text="📈 Estadísticas",
            command=self.show_database_stats,
            state="disabled",
            style="Blue.TButton"
        )
        self.stats_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.view_dedication_btn = ttk.Button(
            row1,
            text="📊 Ver Dedicaciones",
            command=self.view_dedication_data,
            state="disabled",
            style="Teal.TButton"
        )
        self.view_dedication_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.backup_btn = ttk.Button(
            row1,
            text="💾 Respaldar",
            command=self.backup_database,
            state="disabled",
            style="Orange.TButton"
        )
        self.backup_btn.pack(side=tk.LEFT)
        
        # Second row of buttons
        row2 = ttk.Frame(db_frame)
        row2.pack(fill=tk.X)
        
        self.search_btn = ttk.Button(
            row2,
            text="🔍 Buscar Profesor",
            command=self.search_professor,
            state="disabled",
            style="Blue.TButton"
        )
        self.search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_btn = ttk.Button(
            row2,
            text="🔄 Recrear BD",
            command=self.reset_database,
            state="disabled",
            style="Red.TButton"
        )
        self.reset_btn.pack(side=tk.LEFT)
    
    def create_quick_actions_section(self, parent):
        """Create quick actions section"""
        actions_frame = ttk.LabelFrame(parent, text="Acciones Rápidas", padding="15")
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Create entities row
        create_row = ttk.Frame(actions_frame)
        create_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(create_row, text="Crear:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        create_buttons = [
            ("👥 Departamento", 'departamento'),
            ("👨‍🏫 Profesor", 'profesor'),
            ("📚 Materia", 'materia'),
            ("📝 Sección", 'seccion')
        ]
        
        for text, entity_type in create_buttons:
            btn = ttk.Button(
                create_row,
                text=text,
                command=lambda t=entity_type: self.create_entity(t),
                state="disabled",
                style="Orange.TButton"
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))
            # Store reference to enable/disable later
            setattr(self, f"create_{entity_type}_btn", btn)
        
        # Query row
        query_row = ttk.Frame(actions_frame)
        query_row.pack(fill=tk.X)
        
        ttk.Label(query_row, text="Consultar:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.prof_sessions_btn = ttk.Button(
            query_row,
            text="📅 Sesiones de Profesor",
            command=self.query_professor_sessions,
            state="disabled",
            style="Green.TButton"
        )
        self.prof_sessions_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.prof_sections_btn = ttk.Button(
            query_row,
            text="📚 Secciones de Profesor",
            command=self.query_professor_sections,
            state="disabled",
            style="Green.TButton"
        )
        self.prof_sections_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.prof_materias_btn = ttk.Button(
            query_row,
            text="📖 Materias de Profesor",
            command=self.query_professor_materias,
            state="disabled",
            style="Green.TButton"
        )
        self.prof_materias_btn.pack(side=tk.LEFT, padx=(0, 5))  
        
        self.materia_sections_btn = ttk.Button(
            query_row,
            text="📖 Secciones de Materia",
            command=self.query_materia_sections,
            state="disabled",
            style="Green.TButton"
        )
        self.materia_sections_btn.pack(side=tk.LEFT, padx=(0, 5))
    
        self.dept_professors_btn = ttk.Button(
            query_row,
            text="🏢 Profesores por Departamento",
            command=self.query_department_professors,
            state="disabled",
            style="Green.TButton"
        )
        self.dept_professors_btn.pack(side=tk.LEFT, padx=(0, 5))    
        
    
    def create_recop_section(self, parent):
        """Create RECOP operations section"""
        recop_frame = ttk.LabelFrame(parent, text="RECOP", padding="15")
        recop_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Instructions
        instructions = ttk.Label(recop_frame, 
                               text="Herramientas para cálculos automáticos del sistema RECOP:",
                               font=("Arial", 11))
        instructions.pack(pady=(0, 10))
        
        # Button container
        button_container = tk.Frame(recop_frame)
        button_container.pack(fill=tk.X)
        
        # First row - PER calculations (levels 1-2)
        per_row = tk.Frame(button_container)
        per_row.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(per_row, text="PER (Niveles 1-2):", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        # Calculate PER button
        self.calculate_per_btn = ttk.Button(
            per_row,
            text="⚙️ Calcular PER",
            command=self.calculate_per_automatic,
            state="disabled",
            style="Green.TButton"
        )
        self.calculate_per_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # View PER statistics button
        self.view_per_stats_btn = ttk.Button(
            per_row,
            text="📊 Estadísticas PER",
            command=self.view_per_statistics,
            state="disabled",
            style="Blue.TButton"
        )
        self.view_per_stats_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Reset PER button
        self.reset_per_btn = ttk.Button(
            per_row,
            text="🔄 Resetear PER",
            command=self.reset_per_values,
            state="disabled",
            style="Orange.TButton"
        )
        self.reset_per_btn.pack(side=tk.LEFT)
        
        # Second row - Tamaño Estándar calculations (levels 3-4)
        tamano_row = tk.Frame(button_container)
        tamano_row.pack(fill=tk.X)
        
        ttk.Label(tamano_row, text="Tamaño Estándar (Niveles 3-4):", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        # Calculate Tamaño Estándar button
        self.calculate_tamano_btn = ttk.Button(
            tamano_row,
            text="📐 Calcular Tamaño Estándar",
            command=self.calculate_tamano_estandar_automatic,
            state="disabled",
            style="Green.TButton"
        )
        self.calculate_tamano_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # View Tamaño Estándar statistics button
        self.view_tamano_stats_btn = ttk.Button(
            tamano_row,
            text="📊 Ver Tamaño Estándar",
            command=self.view_tamano_estandar_statistics,
            state="disabled",
            style="Blue.TButton"
        )
        self.view_tamano_stats_btn.pack(side=tk.LEFT)
        
            # Third row - PER calculations (levels 3-4) - NEW
        per_34_row = tk.Frame(button_container)
        per_34_row.pack(fill=tk.X)
        
        ttk.Label(per_34_row, text="PER (Niveles 3-4):", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        # Calculate PER for levels 3-4 button
        self.calculate_per_34_btn = ttk.Button(
            per_34_row,
            text="⚙️ Calcular PER con Tamaño Estándar",
            command=self.calculate_per_levels_3_4_automatic,
            state="disabled",
            style="Green.TButton"
        )
        self.calculate_per_34_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Reset PER for levels 3-4 button
        self.reset_per_34_btn = ttk.Button(
            per_34_row,
            text="🔄 Resetear PER (3-4)",
            command=self.reset_per_values_34,
            state="disabled",
            style="Orange.TButton"
        )
        self.reset_per_34_btn.pack(side=tk.LEFT)
        
            # Fourth row - Horas Promedio por Sección (NEW)
        horas_row = tk.Frame(button_container)
        horas_row.pack(fill=tk.X)
        
        ttk.Label(horas_row, text="Horas Promedio por Sección y Secciones a Tamaño Estándar:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        # Calculate Horas Promedio button
        self.calculate_horas_btn = ttk.Button(
            horas_row,
            text="⏱️ Calcular Hr. Promedio y Secc. a TS",
            command=self.calculate_horas_promedio_automatic,
            state="disabled",
            style="Green.TButton"
        )
        self.calculate_horas_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # View Horas Promedio statistics button
        self.view_horas_stats_btn = ttk.Button(
            horas_row,
            text="📊 Ver Dashboard",
            command=self.view_unified_recop_dashboard,
            state="disabled",
            style="Blue.TButton"
        )
        self.view_horas_stats_btn.pack(side=tk.LEFT)
        
    
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Separator
        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        # Status label
        self.status_var = tk.StringVar(value="Listo - Seleccione un archivo CSV para comenzar")
        self.status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Arial", 9),
            padding="5"
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Database status
        self.db_status_var = tk.StringVar(value="BD: No conectada")
        self.db_status_label = ttk.Label(
            status_frame,
            textvariable=self.db_status_var,
            font=("Arial", 9),
            padding="5"
        )
        self.db_status_label.pack(side=tk.RIGHT)
    
    def check_existing_database(self):
        """Check if database already exists and enable buttons if it does"""
        try:
            stats = self.db_manager.get_database_stats()
            total_records = sum(stats.values())
            
            if total_records > 0:
                # Clean up any duplicate professor-department relationships
                cleanup_result = self.db_manager.cleanup_duplicate_professor_departments()
                '''
                if cleanup_result['removed'] > 0:
                    print(f"Database cleanup: removed {cleanup_result['removed']} duplicate relationships")
                '''
                self.enable_database_buttons()
                self.status_var.set(f"Base de datos existente - {total_records} registros totales")
                self.db_status_var.set("BD: Conectada")
            else:
                self.db_status_var.set("BD: Vacía")
                
        except Exception as e:
            self.db_status_var.set("BD: Error")
            print(f"Error checking database: {e}")
    
    def enable_database_buttons(self):
        """Enable all database operation buttons"""
        buttons = [
            'view_tables_btn', 'stats_btn', 'backup_btn', 'search_btn', 'reset_btn',
            'prof_sessions_btn', 'prof_sections_btn', 'materia_sections_btn', 'dept_professors_btn', 'prof_materias_btn',
            'create_departamento_btn', 'create_profesor_btn', 'create_materia_btn', 'create_seccion_btn',
            'upload_personal_btn', 'calculate_per_btn', 'view_per_stats_btn', 'reset_per_btn',
            'calculate_tamano_btn', 'view_tamano_stats_btn',
            'calculate_per_34_btn', 'reset_per_34_btn',
            'upload_personal_btn', 'upload_dedication_btn', 'view_dedication_btn',
            'calculate_horas_btn', 'view_horas_stats_btn'
        ]
        
        for btn_name in buttons:
            if hasattr(self, btn_name):
                getattr(self, btn_name).config(state="normal")
    
    def disable_database_buttons(self):
        """Disable all database operation buttons"""
        buttons = [
            'view_tables_btn', 'stats_btn', 'backup_btn', 'search_btn',
            'prof_sessions_btn', 'prof_sections_btn','materia_sections_btn', 'dept_professors_btn', 'prof_materias_btn',
            'create_departamento_btn', 'create_profesor_btn', 'create_materia_btn', 'create_seccion_btn',
            'upload_personal_btn', 'calculate_per_btn', 'view_per_stats_btn', 'reset_per_btn',
            'calculate_tamano_btn', 'view_tamano_stats_btn',
            'calculate_per_34_btn', 'reset_per_34_btn',
            'upload_personal_btn', 'upload_dedication_btn', 'view_dedication_btn',
            'calculate_horas_btn', 'view_horas_stats_btn'
        ]
        
        for btn_name in buttons:
            if hasattr(self, btn_name):
                getattr(self, btn_name).config(state="disabled")
    
    
    def select_csv_file(self):
        """Open file dialog to select CSV file"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de cartelera",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialdir=os.path.expanduser("~")
        )
        
        if file_path:
            # Validate CSV file
            if not FileHelpers.validate_csv_file(file_path):
                UIHelpers.show_error(
                    self.root,
                    "Archivo inválido",
                    "El archivo seleccionado no es un CSV válido."
                )
                return
            
            self.csv_file_path = file_path
            filename = os.path.basename(file_path)
            file_size = FileHelpers.get_file_size_mb(file_path)
            
            # Update file info display
            self.file_info_var.set(f"📄 {filename} ({file_size:.1f} MB) - Listo para procesar")
            
            # Enable process button
            self.process_csv_btn.config(state="normal")
            
            # Update status
            self.status_var.set("Archivo CSV seleccionado - Listo para procesar")
    
    
        # In the process_csv method, update the processing section:
    
    def process_csv(self):
        """Process the selected CSV file"""
        if not hasattr(self, 'csv_file_path') or not self.csv_file_path:
            UIHelpers.show_error(self.root, "Error", "Por favor seleccione un archivo CSV primero")
            return
        
        # Validate file first
        validation_result = self.csv_processor.validate_csv_file(self.csv_file_path)
        
        if not validation_result['valid']:
            error_msg = "Errores en el archivo CSV:\n" + "\n".join(validation_result['errors'])
            UIHelpers.show_error(self.root, "Archivo CSV inválido", error_msg)
            return
        
        if validation_result['warnings']:
            warning_msg = "Advertencias:\n" + "\n".join(validation_result['warnings'])
            if not UIHelpers.confirm_action(
                self.root, 
                "Advertencias encontradas", 
                f"{warning_msg}\n\n¿Desea continuar con el procesamiento?"
            ):
                return
        
        # Show information about interactive disambiguation
        info_msg = (
            "Durante el procesamiento, es posible que aparezcan diálogos para "
            "disambiguar nombres de profesores con tres partes.\n\n"
            "Estos diálogos le permitirán decidir cómo dividir nombres como:\n"
            "• 'Ana María González' (¿nombres compuestos o apellidos compuestos?)\n\n"
            "El procesamiento puede tomar más tiempo debido a esta interacción."
        )
        
        if not UIHelpers.confirm_action(
            self.root,
            "Procesamiento Interactivo",
            f"{info_msg}\n\n¿Desea continuar?"
        ):
            return
        
        # Show progress bar
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        self.progress_var.set(0)
        
        # Disable buttons during processing
        self.select_csv_btn.config(state="disabled")
        self.process_csv_btn.config(state="disabled")
        
        # Create progress dialog - Modified to allow user interaction
        progress = ProgressDialog(self.root, "Procesando archivo CSV", 
                                 "Iniciando procesamiento...\n(Pueden aparecer diálogos de confirmación)")
        
        try:
            def update_progress(message):
                if not progress.is_cancelled():
                    progress.update_message(message)
                    self.root.update()
            
            # Process file - This may now include user interaction
            result = self.csv_processor.process_csv_file(self.csv_file_path, update_progress)
            
            progress.close()
            
            if result['success']:
                stats = result['statistics']
                
                # Show disambiguation summary if any occurred
                disambiguation_count = len(getattr(self.csv_processor, 'disambiguation_cache', {}))
                
                success_msg = (
                    f"¡Archivo procesado exitosamente!\n\n"
                    f"Registros procesados: {result['processed_rows']}\n"
                    f"Registros omitidos: {result['skipped_rows']}\n"
                )
                
                if disambiguation_count > 0:
                    success_msg += f"Nombres disambiguados: {disambiguation_count}\n"
                
                success_msg += (
                    f"\nEstadísticas de la base de datos:\n"
                    f"• Departamentos: {stats.get('departamento', 0)}\n"
                    f"• Profesores: {stats.get('profesor', 0)}\n"
                    f"• Materias: {stats.get('materia', 0)}\n"
                    f"• Secciones: {stats.get('seccion', 0)}\n"
                    f"• Sesiones: {stats.get('sesion', 0)}"
                )
                
                UIHelpers.show_info(self.root, "Procesamiento completado", success_msg)
                
                self.enable_database_buttons()
                self.status_var.set("Archivo procesado exitosamente")
                self.db_status_var.set("BD: Actualizada")
                
                # Update file info
                self.file_info_var.set(f"Base de datos activa - {sum(stats.values())} registros totales")
                
                # Reset for next file
                self.csv_file_path = None
                self.process_csv_btn.config(state="disabled")
                
            else:
                UIHelpers.show_error(
                    self.root, 
                    "Error en procesamiento", 
                    f"Error al procesar el archivo:\n{result['error_message']}"
                )
                
        except Exception as e:
            progress.close()
            UIHelpers.show_error(self.root, "Error", f"Error inesperado: {str(e)}")
        
        finally:
            # Re-enable buttons and hide progress bar
            self.select_csv_btn.config(state="normal")
            if hasattr(self, 'csv_file_path') and self.csv_file_path:
                self.process_csv_btn.config(state="normal")
            self.progress_bar.pack_forget()
    
    def view_database_tables(self):
        """Open database viewer window"""
        try:
            DatabaseViewer(self.root, self.db_manager)
        except Exception as e:
            UIHelpers.show_error(self.root, "Error", f"Error al abrir el visor: {str(e)}")
    
    def show_database_stats(self):
        """Show database statistics"""
        try:
            stats = self.db_manager.get_database_stats()
            
            stats_msg = "Estadísticas de la Base de Datos:\n\n"
            for table, count in stats.items():
                stats_msg += f"• {table.capitalize()}: {count} registros\n"
            
            total = sum(stats.values())
            stats_msg += f"\nTotal de registros: {total}"
            
            UIHelpers.show_info(self.root, "Estadísticas de BD", stats_msg)
            
        except Exception as e:
            UIHelpers.show_error(self.root, "Error", f"Error al obtener estadísticas: {str(e)}")
    
    def backup_database(self):
        """Create database backup"""
        try:
            backup_path = FileHelpers.backup_database(self.db_manager.db_path)
            UIHelpers.show_info(
                self.root, 
                "Respaldo creado", 
                f"Respaldo de la base de datos creado exitosamente:\n{backup_path}"
            )
        except Exception as e:
            UIHelpers.show_error(self.root, "Error", f"Error al crear respaldo: {str(e)}")
    
    def reset_database(self):
        """Reset/recreate the database"""
        if not UIHelpers.confirm_action(
            self.root,
            "Confirmar recreación",
            "¿Está seguro de que desea recrear la base de datos?\n\n"
            "Se perderán todos los datos existentes.\n"
            "Se recomienda crear un respaldo antes de continuar."
        ):
            return
        
        try:
            # Create backup first
            backup_path = FileHelpers.backup_database(self.db_manager.db_path)
            
            # Remove existing database
            if os.path.exists(self.db_manager.db_path):
                os.remove(self.db_manager.db_path)
            
            # Create new database
            self.db_manager = DatabaseManager()
            self.csv_processor = CSVProcessor(self.db_manager)
            
            # Update UI
            self.disable_database_buttons()
            self.status_var.set("Base de datos recreada - Seleccione un archivo CSV")
            self.db_status_var.set("BD: Vacía")
            
            UIHelpers.show_info(
                self.root,
                "Base de datos recreada",
                f"Base de datos recreada exitosamente.\nRespaldo guardado en: {backup_path}"
            )
            
        except Exception as e:
            UIHelpers.show_error(self.root, "Error", f"Error al recrear la base de datos: {str(e)}")
    
    def create_entity(self, entity_type):
        """Open create dialog for specified entity type"""
        def refresh_callback():
            self.check_existing_database()
            self.status_var.set(f"{entity_type.capitalize()} creado exitosamente")
        
        open_create_dialog(entity_type, self.root, self.db_manager, refresh_callback)
    
    def search_professor(self):
        """Open professor search dialog"""
        def search_callback():
            self.status_var.set("Búsqueda de profesor completada")
        
        SearchProfessorDialog(self.root, self.db_manager, search_callback)
    
    def query_professor_sessions(self):
        """Open professor sessions query dialog"""
        def query_callback():
            self.status_var.set("Consulta de sesiones completada")
        
        ProfessorSessionsDialog(self.root, self.db_manager, query_callback)
        
        # Add this method to the RECOPSimulator class:
    
    def query_professor_sections(self):
        """Open professor sections query dialog"""
        try:
            from ui_components import ProfessorSectionsDialog
            ProfessorSectionsDialog(self.root, self.db_manager)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir diálogo de secciones: {str(e)}")
    
    # Add this method to the RECOPSimulator class:
    
    def query_materia_sections(self):
        """Open materia sections query dialog"""
        try:
            from ui_components import MateriaSectionsDialog
            MateriaSectionsDialog(self.root, self.db_manager)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir diálogo de secciones de materia: {str(e)}")
            
        # Add this method to the RECOPSimulator class:
    
    def query_department_professors(self):
        """Open department professors query dialog"""
        try:
            from ui_components import DepartmentProfessorsDialog
            DepartmentProfessorsDialog(self.root, self.db_manager)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir diálogo de profesores por departamento: {str(e)}")
            
        # Add this method to the RECOPSimulator class in app.py:
    
    def query_professor_materias(self):
        """Open professor materias query dialog"""
        try:
            from ui_components import ProfessorMateriasDialog
            ProfessorMateriasDialog(self.root, self.db_manager)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir diálogo de materias de profesor: {str(e)}")
       
    def show_about(self):
        """Show about dialog"""
        about_text = (
            "Simulador RECOP v2.0\n"
            "Sistema de Gestión de Horarios Universitarios\n\n"
            "Desarrollado para el curso de Ingeniería de Software\n"
            "Universidad de los Andes - 2025\n\n"
            "Características:\n"
            "• Importación de datos desde CSV\n"
            "• Gestión completa de entidades académicas\n"
            "• Consultas avanzadas de información\n"
            "• Interfaz intuitiva y moderna"
        )
        
        UIHelpers.show_info(self.root, "Acerca del Simulador RECOP", about_text)
        
    def calculate_per_automatic(self):
        """Calculate PER values automatically for nivel 1 and 2 materias"""
        try:
            # Get sessions that need PER calculation
            sessions = self.db_manager.get_sessions_for_per_calculation()
            
            if not sessions:
                messagebox.showinfo("Sin datos", "No se encontraron sesiones de nivel 1 o 2 para calcular PER.")
                return
            
            # Calculate new PER values
            updates = []
            grouped_count = 0
            individual_count = 0
            
            for session in sessions:
                new_per = self.calculate_per_formula(session['tipo_horario'], session['inscritos'])
                
                # Track grouping statistics
                if 'grouped_with' in session:
                    grouped_count += 1
                else:
                    individual_count += 1
                
                # Only update if PER changed
                if new_per != session['current_per']:
                    updates.append({
                        'sesion_id': session['sesion_id'],
                        'new_per': new_per,
                        'old_per': session['current_per'],
                        'materia': session['materia_codigo'],
                        'tipo_horario': session['tipo_horario'],
                        'inscritos': session['inscritos'],
                        'original_inscritos': session.get('original_inscritos', session['inscritos']),
                        'grouped_with': session.get('grouped_with', None),
                        'group_size': session.get('group_size', 1)
                    })
            
            if not updates:
                messagebox.showinfo("Sin cambios", "Todos los valores PER ya están actualizados según la fórmula.")
                return
            
            # Show confirmation with summary including grouping info
            confirm_msg = (
                f"¿Aplicar cálculo automático de PER con agrupación por Lista Cruzada?\n\n"
                f"Se actualizarán {len(updates)} sesiones de {len(sessions)} totales.\n"
                f"• Sesiones agrupadas: {grouped_count}\n"
                f"• Sesiones individuales: {individual_count}\n\n"
                f"Ejemplo de cambios:\n"
            )
            
            # Show first 3 examples with grouping info
            for i, update in enumerate(updates[:3]):
                if update.get('grouped_with'):
                    confirm_msg += (f"• {update['materia']}: {update['old_per']} → {update['new_per']} "
                                  f"(Agrupado: {update['grouped_with']}, PE combinado: {update['inscritos']})\n")
                else:
                    confirm_msg += f"• {update['materia']}: {update['old_per']} → {update['new_per']}\n"
            
            if len(updates) > 3:
                confirm_msg += f"  ... y {len(updates) - 3} más"
            
            if not messagebox.askyesno("Confirmar Cálculo", confirm_msg):
                return
            
            # Apply updates
            updated_count = self.db_manager.bulk_update_per_values(updates)
            
            if updated_count > 0:
                messagebox.showinfo("Cálculo Completado", 
                                   f"Se actualizaron {updated_count} valores PER exitosamente.\n"
                                   f"Se utilizó agrupación por Lista Cruzada para combinar estudiantes.")
                self.status_var.set(f"PER calculado con agrupación - {updated_count} sesiones actualizadas")
            else:
                messagebox.showerror("Error", "No se pudieron actualizar los valores PER.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular PER: {str(e)}")
    
    def calculate_per_formula(self, tipo_horario: str, inscritos: int) -> int:
        """
        Calculate PER value based on tipo_horario and inscritos
        
        Args:
            tipo_horario: Type of schedule (e.g., 'Magistral', 'Laboratorio')
            inscritos: Number of enrolled students
            
        Returns:
            int: Calculated PER value
        """
        # PLACEHOLDER - Replace with your actual formula
        # This is just a simple example
        
        if not tipo_horario:
            return 1
        
        tipo_upper = tipo_horario.upper()
        per = 0
        # Base PER calculation (example logic)
        if tipo_upper == 'MAGISTRAL' or tipo_upper == 'TEORICA':
            if inscritos <= 10:
                per = 10
            elif 10 < inscritos <= 60:
                per = inscritos
            elif 60 < inscritos <= 120:
                per = 60 + ((inscritos - 60)/2)
            elif 120 < inscritos:
                per = 90
        elif tipo_upper == 'LABORATORIO' or tipo_upper == 'TALLER Y PBL':
            if inscritos <= 6:
                per = 6
            elif 6 < inscritos <= 25:
                per = inscritos
            elif 25 < inscritos:
                per = 90
    
        
        return per
    
    def view_per_statistics(self):
        """View PER statistics"""
        try:
            stats = self.db_manager.get_per_statistics()
            
            if not stats:
                messagebox.showinfo("Estadísticas PER", "No hay datos PER disponibles.")
                return
            
            # Create statistics window
            stats_window = tk.Toplevel(self.root)
            stats_window.title("Estadísticas PER")
            stats_window.geometry("500x400")
            stats_window.transient(self.root)
            stats_window.grab_set()
            
            # Main frame
            main_frame = ttk.Frame(stats_window, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title
            ttk.Label(main_frame, text="Estadísticas de PER", 
                     font=("Arial", 16, "bold")).pack(pady=(0, 20))
            
            # Statistics display
            stats_text = tk.Text(main_frame, wrap=tk.WORD, height=15, width=50)
            scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=stats_text.yview)
            stats_text.configure(yscrollcommand=scrollbar.set)
            
            # Calculate statistics
            total_sessions = sum(stats.values())
            
            stats_content = f"Total de sesiones: {total_sessions}\n\n"
            stats_content += "Distribución por valor PER:\n"
            stats_content += "=" * 30 + "\n"
            
            for per_value, count in sorted(stats.items()):
                percentage = (count / total_sessions) * 100
                stats_content += f"PER {per_value}: {count:>6} sesiones ({percentage:>5.1f}%)\n"
            
            stats_text.insert(tk.END, stats_content)
            stats_text.config(state=tk.DISABLED)
            
            # Pack text widget and scrollbar
            stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Close button
            ttk.Button(main_frame, text="Cerrar", 
                      command=stats_window.destroy).pack(pady=(20, 0))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener estadísticas: {str(e)}")
    
    def reset_per_values(self):
        """Reset PER values to 0 for levels 1 and 2"""
        if not messagebox.askyesno("Confirmar Reset", 
                                  "¿Está seguro de que desea resetear todos los valores PER "
                                  "a 0 para materias de nivel 1 y 2?\n\n"
                                  "Esta acción no se puede deshacer."):
            return
        
        try:
            count = self.db_manager.reset_per_values_for_levels([1, 2])
            
            if count > 0:
                messagebox.showinfo("Reset Completado", 
                                   f"Se resetearon {count} valores PER a 0 para materias de nivel 1 y 2.")
                self.status_var.set(f"PER reseteado - {count} sesiones actualizadas")
            else:
                messagebox.showinfo("Sin cambios", "No se encontraron sesiones para resetear.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al resetear valores PER: {str(e)}")
    
    def calculate_tamano_estandar_automatic(self):
        """Calculate Tamaño Estándar automatically for nivel 3 and 4 materias"""
        try:
            # Get sessions for calculation
            sessions = self.db_manager.get_sessions_for_tamano_estandar_calculation()
            
            if not sessions:
                messagebox.showinfo("Sin datos", "No se encontraron sesiones de nivel 3 o 4 para calcular Tamaño Estándar.")
                return
            
            # Calculate Tamaño Estándar
            results = self.db_manager.calculate_tamano_estandar_by_department()
            
            if not results:
                messagebox.showinfo("Sin resultados", "No se pudieron calcular valores de Tamaño Estándar.")
                return
            
            # Show confirmation with summary
            total_departments = len(results)
            total_sections = sum(
                dept_data['TEORICO']['total_sections'] + dept_data['PRACTICO']['total_sections']
                for dept_data in results.values()
            )
            
            confirm_msg = (
                f"¿Proceder con el cálculo de Tamaño Estándar?\n\n"
                f"Se analizarán {total_sections} secciones en {total_departments} departamentos.\n\n"
                f"El cálculo se realizará por:\n"
                f"• Departamento\n"
                f"• Tipo de curso (Teórico/Práctico)\n"
                f"• Promedio de estudiantes por sección"
            )
            
            if not messagebox.askyesno("Confirmar Cálculo", confirm_msg):
                return
            
            # Show results immediately
            self.show_tamano_estandar_results(results)
            
            self.status_var.set(f"Tamaño Estándar calculado - {total_departments} departamentos analizados")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular Tamaño Estándar: {str(e)}")

    def show_tamano_estandar_results(self, results):
        """Show Tamaño Estándar calculation results in a window"""
        # Create results window
        results_window = tk.Toplevel(self.root)
        results_window.title("Resultados - Tamaño Estándar")
        results_window.geometry("800x600")
        results_window.transient(self.root)
        results_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(results_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Tamaño Estándar por Departamento", 
                font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(title_frame, text="✕ Cerrar", 
                command=results_window.destroy, style="Red.TButton").pack(side=tk.RIGHT)
        
        # Results table
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview
        columns = ('Departamento', 'Tipo', 'Tamaño Estándar', 'Secciones', 'Total Estudiantes')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Define columns
        tree.heading('Departamento', text='Departamento')
        tree.heading('Tipo', text='Tipo Curso')
        tree.heading('Tamaño Estándar', text='Tamaño Estándar')
        tree.heading('Secciones', text='Secciones')
        tree.heading('Total Estudiantes', text='Total Estudiantes')
        
        tree.column('Departamento', width=200)
        tree.column('Tipo', width=100)
        tree.column('Tamaño Estándar', width=120)
        tree.column('Secciones', width=100)
        tree.column('Total Estudiantes', width=130)
        
        # Add data
        for dept, dept_data in sorted(results.items()):
            for course_type in ['TEORICO', 'PRACTICO']:
                data = dept_data[course_type]
                if data['total_sections'] > 0:
                    tree.insert('', tk.END, values=(
                        dept,
                        course_type,
                        f"{data['tamano_estandar']:.2f}",
                        data['total_sections'],
                        data['total_inscritos']
                    ))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Export button
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(export_frame, text="📄 Exportar a Consola", 
                command=lambda: self.export_tamano_estandar_results(results),
                style="Blue.TButton").pack(side=tk.LEFT)

    def view_tamano_estandar_statistics(self):
        """View Tamaño Estándar statistics"""
        try:
            stats = self.db_manager.get_tamano_estandar_statistics()
            
            if not stats['department_details']:
                messagebox.showinfo("Estadísticas Tamaño Estándar", "No hay datos disponibles para niveles 3 y 4.")
                return
            
            # Show current calculations
            self.show_tamano_estandar_results(stats['department_details'])
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener estadísticas: {str(e)}")

    def export_tamano_estandar_results(self, results):
        """Export Tamaño Estándar results to console"""
        try:
            print("\n" + "="*80)
            print("TAMAÑO ESTÁNDAR POR DEPARTAMENTO (NIVELES 3 Y 4)")
            print("="*80)
            
            # Calculate overall statistics
            total_teorico_sections = 0
            total_practico_sections = 0
            total_teorico_students = 0
            total_practico_students = 0
            teorico_values = []
            practico_values = []
            
            print(f"{'DEPARTAMENTO':<30} {'TIPO':<10} {'TAMAÑO EST.':<12} {'SECCIONES':<10} {'ESTUDIANTES':<12}")
            print("-" * 80)
            
            for dept, dept_data in sorted(results.items()):
                for course_type in ['TEORICO', 'PRACTICO']:
                    data = dept_data[course_type]
                    if data['total_sections'] > 0:
                        print(f"{dept:<30} {course_type:<10} {data['tamano_estandar']:>8.2f} {data['total_sections']:>8} {data['total_inscritos']:>10}")
                        
                        if course_type == 'TEORICO':
                            total_teorico_sections += data['total_sections']
                            total_teorico_students += data['total_inscritos']
                            teorico_values.append(data['tamano_estandar'])
                        else:
                            total_practico_sections += data['total_sections']
                            total_practico_students += data['total_inscritos']
                            practico_values.append(data['tamano_estandar'])
            
            print("=" * 80)
            print("RESUMEN GENERAL:")
            print(f"• Departamentos analizados: {len(results)}")
            print(f"• Cursos teóricos: {total_teorico_sections} secciones, {total_teorico_students} estudiantes")
            print(f"• Cursos prácticos: {total_practico_sections} secciones, {total_practico_students} estudiantes")
            
            if teorico_values:
                avg_teorico = sum(teorico_values) / len(teorico_values)
                print(f"• Promedio Tamaño Estándar Teórico: {avg_teorico:.2f}")
            
            if practico_values:
                avg_practico = sum(practico_values) / len(practico_values)
                print(f"• Promedio Tamaño Estándar Práctico: {avg_practico:.2f}")
            
            print("=" * 80)
            
            messagebox.showinfo("Exportado", "Los resultados han sido exportados a la consola.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
            
    def calculate_per_levels_3_4_automatic(self):
        """Calculate PER values automatically for nivel 3 and 4 materias using Tamaño Estándar"""
        try:
            # Calculate PER using Tamaño Estándar
            result = self.db_manager.calculate_per_for_levels_3_4_with_tamano_estandar()
            
            updates = result['updates']
            tamano_estandar_used = result['tamano_estandar_used']
            
            if not updates:
                messagebox.showinfo("Sin cambios", 
                                   "No se encontraron sesiones de nivel 3 o 4 para calcular PER, "
                                   "o todos los valores ya están actualizados.")
                return
            
            # Count grouping statistics
            grouped_updates = [u for u in updates if u.get('grouped_with')]
            individual_updates = [u for u in updates if not u.get('grouped_with')]
            
            # Show confirmation with detailed summary including grouping
            confirm_msg = (
                f"¿Aplicar cálculo automático de PER para niveles 3 y 4 con Lista Cruzada?\n\n"
                f"Se actualizarán {len(updates)} sesiones.\n"
                f"• Sesiones agrupadas: {len(grouped_updates)}\n"
                f"• Sesiones individuales: {len(individual_updates)}\n\n"
                f"El cálculo usa Tamaño Estándar y agrupa por Lista Cruzada.\n\n"
                f"Ejemplo de cambios:\n"
            )
            
            # Show first 3 examples with more detail including grouping
            for i, update in enumerate(updates[:3]):
                if update.get('grouped_with'):
                    confirm_msg += (f"• {update['materia']} ({update['course_type']}): "
                                  f"{update['old_per']} → {update['new_per']} "
                                  f"(TE: {update['tamano_estandar']:.1f}, PE combinado: {update['inscritos']}, "
                                  f"Grupo: {update['grouped_with']})\n")
                else:
                    confirm_msg += (f"• {update['materia']} ({update['course_type']}): "
                                  f"{update['old_per']} → {update['new_per']} "
                                  f"(TE: {update['tamano_estandar']:.1f}, PE: {update['inscritos']})\n")
            
            if len(updates) > 3:
                confirm_msg += f"  ... y {len(updates) - 3} más"
            
            # Add Tamaño Estándar summary
            if tamano_estandar_used:
                confirm_msg += f"\n\nTamaño Estándar utilizados:\n"
                for dept, types in list(tamano_estandar_used.items())[:3]:
                    confirm_msg += f"• {dept}: "
                    type_info = []
                    for course_type, te_value in types.items():
                        type_info.append(f"{course_type}={te_value:.1f}")
                    confirm_msg += ", ".join(type_info) + "\n"
            
            if not messagebox.askyesno("Confirmar Cálculo", confirm_msg):
                return
            
            # Apply updates
            updates_for_db = [
                {
                    'sesion_id': update['sesion_id'],
                    'new_per': update['new_per']
                }
                for update in updates
            ]
            
            updated_count = self.db_manager.bulk_update_per_values(updates_for_db)
            
            if updated_count > 0:
                # Show detailed results
                self.show_per_34_calculation_results(updates, tamano_estandar_used)
                
                messagebox.showinfo("Cálculo Completado", 
                                   f"Se actualizaron {updated_count} valores PER para niveles 3 y 4 exitosamente.\n"
                                   f"Se utilizó agrupación por Lista Cruzada y Tamaño Estándar.")
                self.status_var.set(f"PER niveles 3-4 calculado con agrupación - {updated_count} sesiones actualizadas")
            else:
                messagebox.showerror("Error", "No se pudieron actualizar los valores PER.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al calcular PER para niveles 3-4: {str(e)}")
    
    def show_per_34_calculation_results(self, updates, tamano_estandar_used):
        """Show detailed results of PER calculation for levels 3-4"""
        # Create results window
        results_window = tk.Toplevel(self.root)
        results_window.title("Resultados - PER Niveles 3 y 4")
        results_window.geometry("1000x700")
        results_window.transient(self.root)
        results_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(results_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Cálculo de PER - Niveles 3 y 4", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(title_frame, text="✕ Cerrar", 
                  command=results_window.destroy, style="Red.TButton").pack(side=tk.RIGHT)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Changes made
        changes_frame = ttk.Frame(notebook)
        notebook.add(changes_frame, text="Cambios Realizados")
        
        # Changes table
        changes_table_frame = ttk.Frame(changes_frame)
        changes_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Materia', 'Departamento', 'Tipo', 'PE', 'TE', 'PER Anterior', 'PER Nuevo')
        tree = ttk.Treeview(changes_table_frame, columns=columns, show='headings', height=15)
        
        # Define columns
        tree.heading('Materia', text='Materia')
        tree.heading('Departamento', text='Departamento')
        tree.heading('Tipo', text='Tipo Curso')
        tree.heading('PE', text='PE')
        tree.heading('TE', text='Tamaño Est.')
        tree.heading('PER Anterior', text='PER Anterior')
        tree.heading('PER Nuevo', text='PER Nuevo')
        
        tree.column('Materia', width=100)
        tree.column('Departamento', width=150)
        tree.column('Tipo', width=80)
        tree.column('PE', width=50)
        tree.column('TE', width=80)
        tree.column('PER Anterior', width=80)
        tree.column('PER Nuevo', width=80)
        
        # Add changes data
        for update in updates:
            tree.insert('', tk.END, values=(
                update['materia'],
                update['departamento'],
                update['course_type'],
                update['inscritos'],
                f"{update['tamano_estandar']:.1f}",
                update['old_per'],
                update['new_per']
            ))
        
        # Scrollbar for changes table
        scrollbar1 = ttk.Scrollbar(changes_table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar1.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 2: Tamaño Estándar used
        te_frame = ttk.Frame(notebook)
        notebook.add(te_frame, text="Tamaño Estándar Utilizado")
        
        # TE table
        te_table_frame = ttk.Frame(te_frame)
        te_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        te_columns = ('Departamento', 'Tipo Curso', 'Tamaño Estándar', 'Sesiones Afectadas')
        te_tree = ttk.Treeview(te_table_frame, columns=te_columns, show='headings', height=15)
        
        # Define TE columns
        for col in te_columns:
            te_tree.heading(col, text=col)
            te_tree.column(col, width=150)
        
        # Add TE data
        for dept, types in tamano_estandar_used.items():
            for course_type, te_value in types.items():
                # Count affected sessions
                affected_count = len([u for u in updates 
                                    if u['departamento'] == dept and u['course_type'] == course_type])
                
                te_tree.insert('', tk.END, values=(
                    dept,
                    course_type,
                    f"{te_value:.2f}",
                    affected_count
                ))
        
        # Scrollbar for TE table
        scrollbar2 = ttk.Scrollbar(te_table_frame, orient=tk.VERTICAL, command=te_tree.yview)
        te_tree.configure(yscrollcommand=scrollbar2.set)
        
        te_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Export button
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(export_frame, text="📄 Exportar a Consola", 
                  command=lambda: self.export_per_34_results(updates, tamano_estandar_used),
                  style="Blue.TButton").pack(side=tk.LEFT)
    
    def export_per_34_results(self, updates, tamano_estandar_used):
        """Export PER 3-4 calculation results to console"""
        try:
            print("\n" + "="*100)
            print("CÁLCULO DE PER PARA NIVELES 3 Y 4 CON TAMAÑO ESTÁNDAR")
            print("="*100)
            
            # Print Tamaño Estándar used
            print("\nTAMAÑO ESTÁNDAR UTILIZADO:")
            print("-" * 60)
            print(f"{'DEPARTAMENTO':<30} {'TIPO':<10} {'TAMAÑO EST.':<12} {'SESIONES':<10}")
            print("-" * 60)
            
            for dept, types in tamano_estandar_used.items():
                for course_type, te_value in types.items():
                    affected_count = len([u for u in updates 
                                        if u['departamento'] == dept and u['course_type'] == course_type])
                    print(f"{dept:<30} {course_type:<10} {te_value:>8.2f} {affected_count:>8}")
            
            # Print changes made
            print(f"\nCAMBIOS REALIZADOS ({len(updates)} sesiones):")
            print("-" * 100)
            print(f"{'MATERIA':<12} {'DEPARTAMENTO':<25} {'TIPO':<10} {'PE':<4} {'TE':<6} {'PER ANT':<8} {'PER NUEVO':<10}")
            print("-" * 100)
            
            for update in updates:
                print(f"{update['materia']:<12} {update['departamento']:<25} {update['course_type']:<10} "
                      f"{update['inscritos']:<4} {update['tamano_estandar']:>5.1f} {update['old_per']:>7} {update['new_per']:>9}")
            
            # Summary statistics
            print("\n" + "="*100)
            print("RESUMEN:")
            total_departments = len(tamano_estandar_used)
            total_teorico = len([u for u in updates if u['course_type'] == 'TEORICO'])
            total_practico = len([u for u in updates if u['course_type'] == 'PRACTICO'])
            
            print(f"• Total de departamentos procesados: {total_departments}")
            print(f"• Sesiones teóricas actualizadas: {total_teorico}")
            print(f"• Sesiones prácticas actualizadas: {total_practico}")
            print(f"• Total de sesiones actualizadas: {len(updates)}")
            
            if updates:
                avg_per_change = sum(u['new_per'] - u['old_per'] for u in updates) / len(updates)
                print(f"• Cambio promedio de PER: {avg_per_change:+.2f}")
            
            print("="*100)
            
            messagebox.showinfo("Exportado", "Los resultados han sido exportados a la consola.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {str(e)}")
    
    def reset_per_values_34(self):
        """Reset PER values to 0 for levels 3 and 4"""
        if not messagebox.askyesno("Confirmar Reset", 
                                  "¿Está seguro de que desea resetear todos los valores PER "
                                  "a 0 para materias de nivel 3 y 4?\n\n"
                                  "Esta acción no se puede deshacer."):
            return
        
        try:
            count = self.db_manager.reset_per_values_for_levels([3, 4])
            
            if count > 0:
                messagebox.showinfo("Reset Completado", 
                                   f"Se resetearon {count} valores PER a 0 para materias de nivel 3 y 4.")
                self.status_var.set(f"PER reseteado - {count} sesiones actualizadas (niveles 3-4)")
            else:
                messagebox.showinfo("Sin cambios", "No se encontraron sesiones para resetear.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al resetear valores PER: {str(e)}")
            
    def calculate_horas_promedio_automatic(self):
        """Calculate both Horas Promedio and Secciones a Tamaño Estándar in unified calculation"""
        try:
            # Show information about the unified calculation
            info_msg = (
                "El cálculo unificado procesará AMBOS métricas simultáneamente:\n\n"
                "📊 HORAS PROMEDIO POR SECCIÓN:\n"
                "• Promedio de horas por dependencia, nivel, tipo profesor y tipo sesión\n\n"
                "📐 SECCIONES A TAMAÑO ESTÁNDAR:\n"
                "• Total PER dividido por Tamaño Estándar correspondiente\n"
                "• Básico e Intermedio: Teórico=30, Práctico=20\n"
                "• Avanzado: Usa valores calculados de Tamaño Estándar\n\n"
                "🔧 PROCESAMIENTO:\n"
                "• Sesiones: MAGISTRAL, TEORICA, LABORATORIO, TALLER Y PBL\n"
                "• Niveles: Básico e intermedio (1,2) / Avanzado (3,4)\n"
                "• Incluye dedicaciones de profesores por sección\n"
                "• Evita duplicación de PER por profesor-sección\n\n"
                "¿Desea continuar con el cálculo unificado?"
            )
            
            if not messagebox.askyesno("Cálculo Unificado RECOP", info_msg):
                return
            
            # Show progress dialog
            progress = ProgressDialog(self.root, "Calculando Métricas RECOP", 
                                     "Procesando estructura unificada...")
            
            try:
                # Get unified statistics
                stats = self.db_manager.get_unified_recop_statistics()
                
                progress.close()
                
                if not stats or stats['total_secciones'] == 0:
                    messagebox.showinfo("Sin datos", "No se encontraron datos para el cálculo unificado.")
                    return
                
                # Show confirmation with summary
                confirm_msg = (
                    f"✅ Cálculo Unificado RECOP completado.\n\n"
                    f"📈 ESTADÍSTICAS PROCESADAS:\n"
                    f"• Dependencias: {stats['total_dependencias']}\n"
                    f"• Niveles académicos: {stats['total_niveles']}\n"
                    f"• Tipos de profesor: {stats['total_tipos_profesor']}\n"
                    f"• Tipos de sesión: {stats['total_tipos_sesion']}\n"
                    f"• Secciones procesadas: {stats['total_secciones']}\n\n"
                    f"🎯 NIVELES: {', '.join(stats['niveles_found'])}\n"
                    f"👥 PROFESORES: {', '.join(stats['tipos_profesor_found'])}\n"
                    f"📚 SESIONES: {', '.join(stats['tipos_sesion_found'])}\n\n"
                    f"¿Desea ver el dashboard unificado con ambas métricas?"
                )
                
                if messagebox.askyesno("Cálculo Completado", confirm_msg):
                    self.show_unified_recop_dashboard(stats)
                
                self.status_var.set(f"RECOP Unificado calculado - {stats['total_secciones']} secciones procesadas")
                
            except Exception as e:
                progress.close()
                raise e
                
        except Exception as e:
            messagebox.showerror("Error", f"Error en cálculo unificado: {str(e)}")
    
    def show_unified_recop_dashboard(self, stats):
        """Show unified dashboard with both Horas Promedio and Secciones a Tamaño Estándar"""
        # Create dashboard window
        dashboard_window = tk.Toplevel(self.root)
        dashboard_window.title("Dashboard RECOP - Horas Promedio y Secciones a Tamaño Estándar")
        dashboard_window.geometry("1600x1000")  # Larger size for combined view
        dashboard_window.transient(self.root)
        dashboard_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(dashboard_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="🎯 Dashboard RECOP Unificado", 
                 font=("Arial", 18, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(title_frame, text="✕ Cerrar", 
                  command=dashboard_window.destroy, style="Red.TButton").pack(side=tk.RIGHT)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Combined Metrics Table
        combined_frame = ttk.Frame(notebook)
        notebook.add(combined_frame, text="📊 Métricas Combinadas")
        
        self.create_combined_metrics_tab(combined_frame, stats)
        
        # Tab 2: Summary by Dependencia
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="📈 Resumen por Dependencia")
        
        self.create_dependencia_summary_tab(summary_frame, stats)
        
        # Tab 3: Detailed Analysis
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="🔍 Análisis Detallado")
        
        self.create_detailed_analysis_tab(analysis_frame, stats)
        
        # Export button
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(export_frame, text="📄 Exportar Dashboard Completo", 
                  command=lambda: self.export_unified_dashboard(stats),
                  style="Blue.TButton").pack(side=tk.LEFT)
    
    def create_combined_metrics_tab(self, parent, stats):
        """Create the combined metrics table tab"""
        # Instructions
        instructions = ttk.Label(parent, 
                               text="Vista combinada de ambas métricas RECOP por dependencia, nivel, tipo profesor y tipo sesión",
                               font=("Arial", 11))
        instructions.pack(pady=(10, 15))
        
        # Combined table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Columns for combined view
        columns = ('Dependencia', 'Nivel', 'Tipo Profesor', 'Tipo Sesión', 
                   'Horas Promedio', 'Secciones/TE', 'Horas', 'Profesores u HC', 'Secciones', 'Profesores', 'TE Usado')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # Define columns
        tree.heading('Dependencia', text='Dependencia')
        tree.heading('Nivel', text='Nivel')
        tree.heading('Tipo Profesor', text='Tipo Profesor')
        tree.heading('Tipo Sesión', text='Tipo Sesión')
        tree.heading('Horas Promedio', text='Horas Promedio')
        tree.heading('Secciones/TE', text='Secciones/TE')
        tree.heading('Horas', text='Horas')
        tree.heading('Profesores u HC', text='Profesores u HC')
        tree.heading('Secciones', text='Secciones')
        tree.heading('Profesores', text='Profesores')
        tree.heading('TE Usado', text='TE Usado')
        
        # Column widths
        tree.column('Dependencia', width=400, stretch=False, anchor='w')
        tree.column('Nivel', width=150, stretch=False, anchor='w')
        tree.column('Tipo Profesor', width=180, stretch=False, anchor='w')
        tree.column('Tipo Sesión', width=100, stretch=False, anchor='w')
        tree.column('Horas Promedio', width=110, stretch=False, anchor='center')
        tree.column('Secciones/TE', width=100, stretch=False, anchor='center')
        tree.column('Horas', width=80, stretch=False, anchor='center')
        tree.column('Profesores u HC', width = 120, stretch=False, anchor='center')
        tree.column('Secciones', width=80, stretch=False, anchor='center')
        tree.column('Profesores', width=80, stretch=False, anchor='center')
        tree.column('TE Usado', width=80, stretch=False, anchor='center')
        
        # Add combined data
        for dependencia, niveles in stats['combined_metrics'].items():
            for nivel, tipos_prof in niveles.items():
                for tipo_prof, tipos_sesion in tipos_prof.items():
                    for tipo_sesion, data in tipos_sesion.items():
                        if tipo_prof != 'CÁTEDRA':
                            tree.insert('', tk.END, values=(
                                dependencia,
                                nivel,
                                tipo_prof,
                                tipo_sesion,
                                f"{data['promedio_horas']:.2f}",
                                f"{data['secciones_tamano_estandar']:.2f}",
                                f"{data['horas']:.2f}",
                                f"{data['profesores']:.2f}",
                                data['num_secciones'],
                                data['num_profesores'],
                                f"{data['tamano_estandar_usado']:.1f}"
                            ))
                        else:
                            tree.insert('', tk.END, values=(
                                dependencia,
                                nivel,
                                tipo_prof,
                                tipo_sesion,
                                f"{data['promedio_horas']:.2f}",
                                f"{data['secciones_tamano_estandar']:.2f}",
                                f"{data['horas']:.2f}",
                                f"{data['horas']:.2f}",
                                data['num_secciones'],
                                data['num_profesores'],
                                f"{data['tamano_estandar_usado']:.1f}"
                            ))
        
        # Scrollbar
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Grid layout for proper scrollbar positioning
        tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights for resizing
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
    
    def create_dependencia_summary_tab(self, parent, stats):
        """Create the dependencia summary tab"""
        # Summary table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        summary_columns = ('Dependencia', 'Nivel', 'Tipos Prof.', 'Total Horas', 'Total PER', 'Secciones')
        summary_tree = ttk.Treeview(table_frame, columns=summary_columns, show='headings', height=15)
        
        # Define summary columns
        for col in summary_columns:
            summary_tree.heading(col, text=col)
            if col == 'Dependencia':
                summary_tree.column(col, width=250)
            elif col == 'Nivel':
                summary_tree.column(col, width=150)
            else:
                summary_tree.column(col, width=100)
        
        # Add summary data
        for dependencia, nivel_data in stats['dependencia_summary'].items():
            for nivel, summary_data in nivel_data.items():
                if nivel != 'TOTAL':  # Skip total rows for this view
                    summary_tree.insert('', tk.END, values=(
                        dependencia,
                        nivel,
                        summary_data.get('tipos_profesor', 0),
                        f"{summary_data['total_horas']:.2f}",
                        f"{summary_data['total_per']:.2f}",
                        summary_data['total_secciones']
                    ))
        
        # Scrollbar for summary table
        summary_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=summary_tree.yview)
        summary_tree.configure(yscrollcommand=summary_scrollbar.set)
        
        summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_detailed_analysis_tab(self, parent, stats):
        """Create detailed analysis tab with statistics"""
        # Statistics container
        stats_container = ttk.Frame(parent, padding="20")
        stats_container.pack(fill=tk.BOTH, expand=True)
        
        # Statistics display
        stats_text = tk.Text(stats_container, wrap=tk.WORD, height=30, width=100)
        stats_scrollbar = ttk.Scrollbar(stats_container, orient=tk.VERTICAL, command=stats_text.yview)
        stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        # Generate detailed analysis content
        analysis_content = self.generate_detailed_analysis_content(stats)
        stats_text.insert(tk.END, analysis_content)
        stats_text.config(state=tk.DISABLED)
        
        stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def generate_detailed_analysis_content(self, stats) -> str:
        """Generate detailed analysis content for the dashboard"""
        content = "🎯 ANÁLISIS DETALLADO DEL DASHBOARD RECOP\n"
        content += "=" * 80 + "\n\n"
        
        # General statistics
        content += "📊 ESTADÍSTICAS GENERALES:\n"
        content += f"• Total de dependencias procesadas: {stats['total_dependencias']}\n"
        content += f"• Niveles académicos analizados: {stats['total_niveles']}\n"
        content += f"• Tipos de profesor encontrados: {stats['total_tipos_profesor']}\n"
        content += f"• Tipos de sesión procesados: {stats['total_tipos_sesion']}\n"
        content += f"• Secciones totales procesadas: {stats['total_secciones']}\n\n"
        
        # Level breakdown
        content += "📚 NIVELES ACADÉMICOS:\n"
        for nivel in stats['niveles_found']:
            content += f"• {nivel}\n"
        content += "\n"
        
        # Professor types breakdown
        content += "👥 TIPOS DE PROFESOR:\n"
        for tipo in stats['tipos_profesor_found']:
            content += f"• {tipo}\n"
        content += "\n"
        
        # Session types breakdown
        content += "🎓 TIPOS DE SESIÓN:\n"
        for tipo in stats['tipos_sesion_found']:
            content += f"• {tipo}\n"
        content += "\n"
        
        # Metrics analysis by dependencia
        content += "📈 ANÁLISIS POR DEPENDENCIA:\n"
        content += "-" * 80 + "\n"
        
        for dependencia, nivel_data in stats['dependencia_summary'].items():
            content += f"\n🏢 {dependencia}:\n"
            for nivel, data in nivel_data.items():
                if nivel != 'TOTAL':
                    content += f"  📍 {nivel}:\n"
                    content += f"    • Tipos de profesor: {data.get('tipos_profesor', 0)}\n"
                    content += f"    • Total horas: {data['total_horas']:.2f}\n"
                    content += f"    • Total PER: {data['total_per']:.2f}\n"
                    content += f"    • Secciones: {data['total_secciones']}\n"
        
        # Top performers analysis
        content += "\n\n🏆 ANÁLISIS DE RENDIMIENTO:\n"
        content += "-" * 80 + "\n"
        
        # Find top dependencies by hours and PER
        dep_totals = []
        for dep, nivel_data in stats['dependencia_summary'].items():
            if 'TOTAL' in nivel_data:
                total_data = nivel_data['TOTAL']
                dep_totals.append((dep, total_data['total_horas'], total_data['total_per'], total_data['total_secciones']))
        
        # Sort by total hours
        dep_totals_by_hours = sorted(dep_totals, key=lambda x: x[1], reverse=True)
        content += "\n🔥 TOP 5 DEPENDENCIAS POR HORAS TOTALES:\n"
        for i, (dep, hours, per, sections) in enumerate(dep_totals_by_hours[:5], 1):
            content += f"{i}. {dep}: {hours:.2f} horas ({sections} secciones)\n"
        
        # Sort by total PER
        dep_totals_by_per = sorted(dep_totals, key=lambda x: x[2], reverse=True)
        content += "\n📊 TOP 5 DEPENDENCIAS POR PER TOTAL:\n"
        for i, (dep, hours, per, sections) in enumerate(dep_totals_by_per[:5], 1):
            content += f"{i}. {dep}: {per:.2f} PER ({sections} secciones)\n"
        
        content += "\n" + "=" * 80 + "\n"
        
        return content
    
    def export_unified_dashboard(self, stats):
        """Export complete unified dashboard to console"""
        try:
            print("\n" + "="*150)
            print("🎯 DASHBOARD RECOP UNIFICADO - HORAS PROMEDIO Y SECCIONES A TAMAÑO ESTÁNDAR")
            print("="*150)
            
            # Print general statistics
            print(f"\n📊 ESTADÍSTICAS GENERALES:")
            print(f"• Total de dependencias: {stats['total_dependencias']}")
            print(f"• Niveles académicos: {stats['total_niveles']}")
            print(f"• Tipos de profesor: {stats['total_tipos_profesor']}")
            print(f"• Tipos de sesión: {stats['total_tipos_sesion']}")
            print(f"• Secciones procesadas: {stats['total_secciones']}")
            
            # Print combined metrics table
            print(f"\n📈 MÉTRICAS COMBINADAS:")
            print("-" * 150)
            print(f"{'DEPENDENCIA':<35} {'NIVEL':<20} {'TIPO PROF':<12} {'TIPO SES':<12} {'HORAS PROM':<12} {'SECC/TE':<10} {'SECCIONES':<10} {'PROFS':<8} {'TE USADO':<8}")
            print("-" * 150)
            
            for dependencia, niveles in stats['combined_metrics'].items():
                for nivel, tipos_prof in niveles.items():
                    for tipo_prof, tipos_sesion in tipos_prof.items():
                        for tipo_sesion, data in tipos_sesion.items():
                            print(f"{dependencia:<35} {nivel:<20} {tipo_prof:<12} {tipo_sesion:<12} "
                                  f"{data['promedio_horas']:>10.2f} {data['secciones_tamano_estandar']:>8.2f} "
                                  f"{data['num_secciones']:>8} {data['num_profesores']:>6} {data['tamano_estandar_usado']:>6.1f}")
            
            # Print summary by dependencia
            print(f"\n📋 RESUMEN POR DEPENDENCIA:")
            print("-" * 100)
            print(f"{'DEPENDENCIA':<35} {'NIVEL':<20} {'TOTAL HORAS':<15} {'TOTAL PER':<12} {'SECCIONES':<10}")
            print("-" * 100)
            
            for dependencia, nivel_data in stats['dependencia_summary'].items():
                for nivel, summary_data in nivel_data.items():
                    if nivel != 'TOTAL':
                        print(f"{dependencia:<35} {nivel:<20} {summary_data['total_horas']:>12.2f} "
                              f"{summary_data['total_per']:>10.2f} {summary_data['total_secciones']:>8}")
            
            print("="*150)
            
            messagebox.showinfo("Exportado", "El dashboard completo ha sido exportado a la consola.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar dashboard: {str(e)}")
    
        
        # Add this method to the RECOPSimulator class:
    
    def view_unified_recop_dashboard(self):
        """View the unified RECOP dashboard with both metrics"""
        try:
            # Get unified statistics
            stats = self.db_manager.get_unified_recop_statistics()
            
            if not stats or stats['total_secciones'] == 0:
                messagebox.showinfo("Dashboard RECOP", "No hay datos disponibles para el dashboard unificado.\n\nPrimero debe ejecutar el cálculo unificado.")
                return
            
            # Show the unified dashboard
            self.show_unified_recop_dashboard(stats)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener datos del dashboard: {str(e)}")
            
    def upload_dedication_data(self):
        """Upload and process dedication data CSV file"""
        if not self.db_manager:
            messagebox.showerror("Error", "No hay una base de datos activa.")
            return
        
        try:
            from ui_components import DedicationDataLinkingDialog
            
            def dedication_callback():
                self.status_var.set("Dedicaciones actualizadas exitosamente")
                # Refresh database connection status
                self.check_existing_database()
            
            # Open the dedication data linking dialog
            DedicationDataLinkingDialog(self.root, self.db_manager, dedication_callback)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar datos de dedicación: {str(e)}")
            
    def view_dedication_data(self):
        """Open dedication data viewer dialog"""
        try:
            from ui_components import DedicationViewerDialog
            DedicationViewerDialog(self.root, self.db_manager)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir visor de dedicaciones: {str(e)}")
    
    def apply_dark_mode_to_widgets(self, parent=None):
        """Apply dark mode colors to regular tkinter widgets"""
        if parent is None:
            parent = self.root
        
        colors = get_theme_colors()  # Import this from ui_components
        
        # Configure root window
        if parent == self.root:
            self.root.configure(bg=colors['bg'])
        
        # Recursively update all child widgets
        for child in parent.winfo_children():
            widget_class = child.winfo_class()
            
            if widget_class == 'Frame':
                child.configure(bg=colors['bg'])
            elif widget_class == 'Label':
                child.configure(bg=colors['bg'], fg=colors['fg'])
            elif widget_class == 'Entry':
                child.configure(bg=colors['entry_bg'], fg=colors['entry_fg'],
                              insertbackground=colors['fg'], borderwidth=1,
                              relief='solid')
            elif widget_class == 'Button':
                # Only update if it's not a styled button
                if not hasattr(child, '_custom_styled'):
                    child.configure(bg=colors['button_bg'], fg=colors['fg'],
                                  activebackground=colors['select_bg'],
                                  activeforeground=colors['select_fg'])
            elif widget_class == 'Text':
                child.configure(bg=colors['entry_bg'], fg=colors['entry_fg'],
                              insertbackground=colors['fg'])
            elif widget_class == 'Listbox':
                child.configure(bg=colors['tree_bg'], fg=colors['tree_fg'],
                              selectbackground=colors['tree_select'],
                              selectforeground=colors['select_fg'])
            elif widget_class == 'Canvas':
                child.configure(bg=colors['bg'])
            elif widget_class == 'Toplevel':
                child.configure(bg=colors['bg'])
            
            # Recursively apply to children
            self.apply_dark_mode_to_widgets(child)
    
    
    # Add this new method to the RECOPSimulator class in app.py:
    
    def upload_personal_data(self):
        """Upload and process personal data CSV file"""
        if not self.db_manager:
            messagebox.showerror("Error", "No hay una base de datos activa.")
            return
        
        try:
            from ui_components import PersonalDataLinkingDialog
            
            def linking_callback():
                # Refresh database status after linking
                self.check_existing_database()
                self.status_var.set("Datos personales procesados exitosamente")
                
                # Update file info display
                try:
                    stats = self.db_manager.get_database_stats()
                    with_personal = stats['total_profesores'] - len(self.db_manager.get_professors_without_personal_data())
                    self.file_info_var.set(f"Base de datos activa - {with_personal}/{stats['total_profesores']} profesores con datos personales")
                except:
                    self.file_info_var.set("Base de datos activa - Datos personales actualizados")
            
            # Open the personal data linking dialog
            PersonalDataLinkingDialog(self.root, self.db_manager, linking_callback)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar datos personales: {str(e)}")

def main():
    """Main function to run the application"""
    root = tk.Tk()
    
    # Configure ttk styles
    style = ttk.Style()
    
    # Try to set a modern theme
    try:
        style.theme_use('clam')  # Modern looking theme
    except:
        pass  # Use default theme if clam is not available
    
    # Configure custom styles
    style.configure('Accent.TButton', foreground='blue')
    
    # Create and run application
    app = RECOPSimulator(root)
    
    # Center window on screen
    UIHelpers.center_window(root)
    
    # Run main loop
    root.mainloop()

if __name__ == "__main__":
    main()
