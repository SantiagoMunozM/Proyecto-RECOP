import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from database import DatabaseManager
from ui_components import DatabaseViewer, ProgressDialog, SearchProfessorDialog, ProfessorSessionsDialog, setup_ttk_styles
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
                               text="Cargue archivos CSV con datos académicos o vincule datos personales de profesores:",
                               font=("Arial", 11))
        instructions.pack(pady=(0, 10))
        
        # Sub-instructions for each button
        sub_instructions_frame = tk.Frame(upload_frame)
        sub_instructions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Left side - Academic data
        left_frame = tk.Frame(sub_instructions_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Label(left_frame, text="📄 CSV Académico:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        tk.Label(left_frame, text="Datos de materias, secciones, profesores y sesiones", 
                 font=("Arial", 8), fg="gray").pack(anchor=tk.W)
        
        # Right side - Personal data
        right_frame = tk.Frame(sub_instructions_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(right_frame, text="👥 Datos Personales:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        tk.Label(right_frame, text="Información adicional de empleados (requiere DB existente)", 
                 font=("Arial", 8), fg="gray").pack(anchor=tk.W)
        
        # Buttons container
        buttons_container = tk.Frame(upload_frame)
        buttons_container.pack(fill=tk.X)
        
        # FIXED: Academic CSV buttons - separate select and process
        # Select CSV button
        self.select_csv_btn = ttk.Button(
            buttons_container,
            text="� Seleccionar CSV",
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
        self.upload_personal_btn.pack(side=tk.LEFT)
        
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
            'prof_sessions_btn', 'prof_sections_btn', 'materia_sections_btn', 'dept_professors_btn',
            'create_departamento_btn', 'create_profesor_btn', 'create_materia_btn', 'create_seccion_btn',
            'upload_personal_btn'
        ]
        
        for btn_name in buttons:
            if hasattr(self, btn_name):
                getattr(self, btn_name).config(state="normal")
    
    def disable_database_buttons(self):
        """Disable all database operation buttons"""
        buttons = [
            'view_tables_btn', 'stats_btn', 'backup_btn', 'search_btn',
            'prof_sessions_btn', 'prof_sections_btn','materia_sections_btn', 'dept_professors_btn',
            'create_departamento_btn', 'create_profesor_btn', 'create_materia_btn', 'create_seccion_btn',
            'upload_personal_btn'
        ]
        
        for btn_name in buttons:
            if hasattr(self, btn_name):
                getattr(self, btn_name).config(state="disabled")
    
        # Replace the select_csv_file method in app.py:
    
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
        
        # Show progress bar
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        self.progress_var.set(0)
        
        # Disable buttons during processing
        self.select_csv_btn.config(state="disabled")
        self.process_csv_btn.config(state="disabled")
        
        # Create progress dialog
        progress = ProgressDialog(self.root, "Procesando archivo CSV", "Iniciando procesamiento...")
        
        try:
            def update_progress(message):
                if not progress.is_cancelled():
                    progress.update_message(message)
                    self.root.update()
            
            # Process file
            result = self.csv_processor.process_csv_file(self.csv_file_path, update_progress)
            
            progress.close()
            
            if result['success']:
                stats = result['statistics']
                success_msg = (
                    f"¡Archivo procesado exitosamente!\n\n"
                    f"Registros procesados: {result['processed_rows']}\n"
                    f"Registros omitidos: {result['skipped_rows']}\n\n"
                    f"Estadísticas de la base de datos:\n"
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