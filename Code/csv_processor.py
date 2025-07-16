import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from ui_components import get_theme_colors, apply_dark_mode_to_dialog
import re
import json
from typing import List, Dict, Tuple, Optional
from database import DatabaseManager
from utils import DataFormatter

class CSVProcessor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.disambiguation_cache = {} 
        
    def is_row_empty(self, row) -> bool:
        """Check if a row is essentially empty (all NaN or empty values)"""
        critical_fields = ['NRC', 'Materia', 'Departamento', 'Facultad ']
        
        for field in critical_fields:
            if field in row and not pd.isna(row[field]) and str(row[field]).strip() != '':
                return False
        return True

    def safe_strip(self, value) -> str:
        """Safely strip a value, handling null/float cases"""
        if pd.isna(value):
            return ''
        return str(value).strip()

    def parse_professors(self, prof_string) -> List[Dict]:
        """Parse the professor string and extract individual professors"""
        if pd.isna(prof_string) or prof_string == '':
            return []
        
        # Split by | to get individual professors
        professors = str(prof_string).split(' | ')
        parsed_profs = []
        
        for prof in professors:
            # Remove the (01), (02) etc. prefix and (Y) suffix
            clean_prof = re.sub(r'^\(\d+\)\s*', '', prof)
            clean_prof = re.sub(r'\(Y\)$', '', clean_prof).strip()
            
            if clean_prof:
                # Split name into parts
                name_parts = clean_prof.split()
                nombres, apellidos = self.intelligent_name_split_with_disambiguation(name_parts)
                
                if nombres or apellidos:  # Only add if we got valid names
                    parsed_profs.append({
                        'nombres': nombres,
                        'apellidos': apellidos,
                        'tipo': 'DEFAULT' 
                    })
        
        return parsed_profs
    
    def intelligent_name_split_with_disambiguation(self, name_parts: List[str]) -> Tuple[str, str]:
        """
        Intelligently split names with user disambiguation for ambiguous cases
        
        Args:
            name_parts: List of name parts
            
        Returns:
            Tuple of (nombres, apellidos)
        """
        if len(name_parts) == 1:
            return name_parts[0], ""
        elif len(name_parts) == 2:
            return name_parts[0], name_parts[1]
        elif len(name_parts) == 3:
            return self.resolve_three_part_ambiguity_interactive(name_parts)
        else:  # 4 or more parts
            # For 4+ parts, assume Colombian convention: last 2 are surnames
            nombres = ' '.join(name_parts[:-2])
            apellidos = ' '.join(name_parts[-2:])
            return nombres, apellidos

    def resolve_three_part_ambiguity_interactive(self, name_parts: List[str]) -> Tuple[str, str]:
        """
        Resolve three-part name ambiguity using automatic heuristics first, then user input
        
        Args:
            name_parts: List of exactly 3 name parts
            
        Returns:
            Tuple of (nombres, apellidos)
        """
        part1, part2, part3 = name_parts
        full_name = ' '.join(name_parts)
        
        # Check cache first to avoid asking the same question multiple times
        if full_name in self.disambiguation_cache:
            choice = self.disambiguation_cache[full_name]
            if choice == 1:
                return f"{part1} {part2}", part3
            else:
                return part1, f"{part2} {part3}"
        
        # Try automatic heuristics first
        auto_result = self.try_automatic_disambiguation(name_parts)
        if auto_result:
            nombres, apellidos = auto_result
            # Cache the automatic decision
            choice = 1 if ' ' in nombres else 2
            self.disambiguation_cache[full_name] = choice
            return nombres, apellidos
        
        # If automatic methods don't give a confident result, ask user
        choice = self.ask_user_for_name_split(name_parts)
        
        # Cache the user's decision
        self.disambiguation_cache[full_name] = choice
        
        if choice == 1:  # Two nombres + one apellido
            return f"{part1} {part2}", part3
        else:  # One nombre + two apellidos
            return part1, f"{part2} {part3}"

    def try_automatic_disambiguation(self, name_parts: List[str]) -> Optional[Tuple[str, str]]:
        """
        Try to automatically resolve three-part names using heuristics
        
        Returns:
            Tuple of (nombres, apellidos) if confident, None if uncertain
        """
        part1, part2, part3 = name_parts
        
        # Heuristic 1: Common compound first names (high confidence)
        compound_first_names = {
            'ANA MARIA', 'MARIA ELENA', 'JOSE LUIS', 'JUAN CARLOS', 'LUIS FERNANDO',
            'MARIA FERNANDA', 'ANA LUCIA', 'CARLOS ANDRES', 'JUAN PABLO', 'MARIA JOSE',
            'LUIS MIGUEL', 'JOSE ANTONIO', 'MARIA CRISTINA', 'ANA SOFIA', 'DIEGO ALEJANDRO',
            'SANDRA PATRICIA', 'CLAUDIA PATRICIA', 'MARTHA LUCIA', 'GLORIA ELENA'
        }
        
        potential_compound = f"{part1} {part2}".upper()
        if potential_compound in compound_first_names:
            return f"{part1} {part2}", part3
        
        # Heuristic 2: Surname particles/connectors (high confidence)
        surname_particles = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'VAN', 'VON', 'MC', 'MAC', 'D'}
        
        if part2.upper() in surname_particles:
            return part1, f"{part2} {part3}"
        
        # Heuristic 3: Very short third part likely indicates compound first name
        if len(part3) <= 3 and len(part2) > 4:
            return f"{part1} {part2}", part3
        
        # If none of the high-confidence heuristics apply, return None (ask user)
        return None

    def ask_user_for_name_split(self, name_parts: List[str]) -> int:
        """
        Ask user to disambiguate three-part names using a dialog
        
        Args:
            name_parts: List of exactly 3 name parts
            
        Returns:
            1 for option 1 (compound first name), 2 for option 2 (compound surname)
        """
        part1, part2, part3 = name_parts
        
        # Create disambiguation dialog
        dialog = NameDisambiguationDialog(name_parts)
        return dialog.get_choice()

    def format_time(self, time_value) -> Optional[str]:
        """Convert time from HHMM format to HH:MM"""
        if pd.isna(time_value):
            return None
        try:
            time_str = str(int(float(time_value))).zfill(4)
            return f"{time_str[:2]}:{time_str[2:]}"
        except (ValueError, TypeError):
            return None

    def get_days_string(self, row) -> str:
        """Get the days of the week when the session occurs"""
        days = []
        day_columns = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        day_abbrev = ['L', 'M', 'I', 'J', 'V', 'S', 'D']
        
        for i, day_col in enumerate(day_columns):
            if day_col in row and not pd.isna(row[day_col]) and str(row[day_col]).strip() != '':
                days.append(day_abbrev[i])
        
        return ','.join(days)

    def safe_int_convert(self, value, default=0) -> int:
        """Safely convert a value to integer"""
        if pd.isna(value):
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    def calculate_duration(self, hora_inicio: str, hora_fin: str) -> Optional[float]:
        """Calculate duration in hours between start and end time"""
        if not hora_inicio or not hora_fin:
            return None
            
        try:
            # Calculate duration in hours
            start_hour, start_min = map(int, hora_inicio.split(':'))
            end_hour, end_min = map(int, hora_fin.split(':'))
            # Add 10 minutes break and convert to hours
            duration_minutes = (end_hour * 60 + end_min) - (start_hour * 60 + start_min) + 10
            return duration_minutes / 60
        except ValueError:
            return None

    def process_csv_file(self, csv_file_path: str, progress_callback=None) -> Dict:
        """
        Main function to process CSV file and upload to database
        
        Args:
            csv_file_path: Path to the CSV file
            progress_callback: Optional callback function to report progress
            
        Returns:
            Dictionary with processing results and statistics
        """
        
        # Initialize result dictionary
        result = {
            'success': False,
            'processed_rows': 0,
            'skipped_rows': 0,
            'error_message': None,
            'statistics': {}
        }
        
        try:
            # Read CSV file and drop completely empty rows
            if progress_callback:
                progress_callback("Leyendo archivo CSV...")
            
            df = pd.read_csv(csv_file_path)
            df = df.dropna(how='all')  # Remove rows where all values are NaN
            
            if progress_callback:
                progress_callback(f"Archivo cargado: {len(df)} filas encontradas")
            
            # Initialize tracking variables
            inserted_departamentos = set()
            inserted_profesores = {}  # Key: (nombres, apellidos, departamento), Value: id
            inserted_materias = set()
            inserted_secciones = set()
            seccion_professors = {}  # Key: NRC, Value: set of professor_ids
            
            processed_rows = 0
            skipped_rows = 0
            
            # Process each row
            for index, row in df.iterrows():
                if progress_callback and index % 100 == 0:
                    progress_callback(f"Procesando fila {index + 1}/{len(df)}")
                
                # Check if row is empty
                if self.is_row_empty(row):
                    print(f"Skipping empty row {index + 1}")
                    skipped_rows += 1
                    continue
                
                processed_rows += 1
                
                # Process this row
                success = self._process_single_row(
                    row, index + 1,
                    inserted_departamentos, inserted_profesores, 
                    inserted_materias, inserted_secciones, seccion_professors
                )
                
                if not success:
                    skipped_rows += 1
                    processed_rows -= 1
            
            if progress_callback:
                progress_callback("Generando estadísticas...")
            
            # Get final statistics
            stats = self.db_manager.get_database_stats()
            
            result.update({
                'success': True,
                'processed_rows': processed_rows,
                'skipped_rows': skipped_rows,
                'statistics': stats
            })
            
            if progress_callback:
                progress_callback("¡Procesamiento completado!")
            
            return result
            
        except Exception as e:
            result['error_message'] = str(e)
            return result
    
    def _process_single_row(self, row, row_number: int, inserted_departamentos: set,
                           inserted_profesores: dict, inserted_materias: set,
                           inserted_secciones: set, seccion_professors: dict) -> bool:
        """Process a single row from the CSV"""
        
        try:
            # Get departamento for this row
            departamento_raw = self.safe_strip(row['Departamento'])
            
            departamento = DataFormatter.normalize_department_name(departamento_raw)
            if not departamento:
                print(f"Warning: Row {row_number} has no departamento, skipping")
                return False
            
            # Insert Departamento
            if departamento not in inserted_departamentos:
                self.db_manager.create_departamento(departamento)
                inserted_departamentos.add(departamento)
            
             # Parse and insert Profesores
            profesores = self.parse_professors(row['Profesor(es)'])
            profesor_ids = []
        
            for prof in profesores:
                # Key now only includes nombres and apellidos (not department)
                prof_key = (prof['nombres'], prof['apellidos'])
                
                if prof_key not in inserted_profesores:
                    # Create profesor with this department
                    profesor_id = self.db_manager.create_profesor(
                        prof['nombres'], prof['apellidos'], prof['tipo'], [departamento]
                    )
                    if profesor_id:
                        inserted_profesores[prof_key] = profesor_id
                        #print(f"  Created new professor: {prof['nombres']} {prof['apellidos']} (ID: {profesor_id}) in {departamento}")
                    else:
                        #print(f"  Failed to create professor: {prof['nombres']} {prof['apellidos']}")
                        continue
                else:
                    # Professor already exists, check if they need this department
                    profesor_id = inserted_profesores[prof_key]
                    
                    # Get current departments for this professor
                    current_depts = self.db_manager.get_profesor_departamentos(profesor_id)
                    
                    if departamento not in current_depts:
                        # Add this new department to the professor
                        new_depts = current_depts + [departamento]
                        success = self.db_manager.update_profesor_departamentos(profesor_id, new_depts)
                        #if success:
                            #print(f"  Added department {departamento} to existing professor {prof['nombres']} {prof['apellidos']} (ID: {profesor_id})")
                        #else:
                            #print(f"  Failed to add department {departamento} to professor {prof['nombres']} {prof['apellidos']} (ID: {profesor_id})")
                    #else:
                        #print(f"  Professor {prof['nombres']} {prof['apellidos']} (ID: {profesor_id}) already has department {departamento}")
            
                profesor_ids.append(profesor_id)
            
            # Insert Materia - belongs to departamento
            materia_codigo = self.safe_strip(row['Materia'])
            if materia_codigo and materia_codigo not in inserted_materias:
                success = self.db_manager.create_materia(
                    materia_codigo, 
                    self.safe_strip(row['Nombre largo curso']), 
                    self.safe_int_convert(row['Créditos']),
                    self.safe_strip(row['Nivel materia']), 
                    self.safe_strip(row['Modo calificación']), 
                    self.safe_strip(row['Campus']), 
                    self.safe_strip(row['Periodo']), 
                    departamento
                )
                if success:
                    inserted_materias.add(materia_codigo)
            
            # Get NRC
            nrc = self.safe_int_convert(row['NRC'])
            if nrc <= 0:
                print(f"Warning: Row {row_number} has invalid NRC, skipping")
                return False
            
            lista_cruzada = None
            lista_cruzada_value = self.safe_strip(row['Lista cruzada'])
            
            if lista_cruzada_value: 
                lista_cruzada = lista_cruzada_value 
            
            # Insert or update Seccion
            if nrc not in inserted_secciones:
                # First time seeing this section - insert it
                success = self.db_manager.create_seccion(
                    nrc, 
                    self.safe_strip(row['Secc']),
                    self.safe_int_convert(row['Cupo']),
                    materia_codigo, 
                    profesor_ids,
                    lista_cruzada
                )
                
                if success:
                    # Initialize the professors for this section
                    seccion_professors[nrc] = set(profesor_ids)
                    inserted_secciones.add(nrc)
                    
                    # Update inscritos if provided
                    inscritos = self.safe_int_convert(row['Inscritos'])
                    if inscritos > 0:
                        self.db_manager.update_seccion(
                            nrc, self.safe_strip(row['Secc']),
                            self.safe_int_convert(row['Cupo']), inscritos,
                            lista_cruzada
                        )
            else:
                # Section already exists - add new professors if they're not already there
                if nrc not in seccion_professors:
                    seccion_professors[nrc] = set()
                
                # Add new professors to the section
                new_professors = set(profesor_ids) - seccion_professors[nrc]
                if new_professors:
                    print(f"  Adding {len(new_professors)} new professors to section {nrc}")
                    seccion_professors[nrc].update(profesor_ids)
                    
                    # Update section professors in database
                    self._update_section_professors(nrc, list(seccion_professors[nrc]))
            
            # Insert Sesion
            success = self._create_session_from_row(row, nrc, profesor_ids)
            
            return success
            
        except Exception as e:
            print(f"Error processing row {row_number}: {e}")
            return False
    
    def _update_section_professors(self, nrc: int, profesor_ids: List[int]):
        """Update professors for a section"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get current professors
            cursor.execute("SELECT profesor_id FROM SeccionProfesor WHERE seccion_NRC = ?", (nrc,))
            current_profs = {row[0] for row in cursor.fetchall()}
            
            # Add new professors
            for prof_id in profesor_ids:
                if prof_id not in current_profs:
                    cursor.execute(
                        "INSERT INTO SeccionProfesor (seccion_NRC, profesor_id) VALUES (?, ?)",
                        (nrc, prof_id)
                    )
            
            # Update JSON field
            cursor.execute(
                "UPDATE Seccion SET profesor_ids = ? WHERE NRC = ?",
                (json.dumps(profesor_ids), nrc)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error updating section professors: {e}")
    
    def _create_session_from_row(self, row, nrc: int, profesor_ids: List[int]) -> bool:
        """Create a session from CSV row data"""
        try:
            hora_inicio = self.format_time(row['Hora inicio'])
            hora_fin = self.format_time(row['Hora fin'])
            duracion = self.calculate_duration(hora_inicio, hora_fin)
            dias = self.get_days_string(row)
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Insert Sesion
            cursor.execute('''
                INSERT INTO Sesion 
                (tipoHorario, horaInicio, horaFin, duracion, edificio, salon, 
                 atributoSalon, dias, seccion_NRC, profesor_ids) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.safe_strip(row['Tipo horario (franja)']), 
                hora_inicio, hora_fin, duracion,
                self.safe_strip(row['Edificio']), 
                self.safe_strip(row['Salón']), 
                self.safe_strip(row['Descripción atributo salón']),
                dias, nrc, json.dumps(profesor_ids)
            ))
            
            # Insert into SesionProfesor junction table
            sesion_id = cursor.lastrowid
            for profesor_id in profesor_ids:
                cursor.execute(
                    'INSERT INTO SesionProfesor (sesion_id, profesor_id) VALUES (?, ?)',
                    (sesion_id, profesor_id)
                )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def validate_csv_file(self, csv_file_path: str) -> Dict:
        """
        Validate CSV file structure and content
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'row_count': 0,
            'required_columns': []
        }
        
        required_columns = [
            'NRC', 'Materia', 'Departamento', 'Profesor(es)',
            'Nombre largo curso', 'Créditos', 'Secc', 'Cupo'
        ]
        
        try:
            # Try to read the file
            df = pd.read_csv(csv_file_path)
            result['row_count'] = len(df)
            
            # Check for required columns
            missing_columns = []
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                result['errors'].append(f"Faltan columnas requeridas: {', '.join(missing_columns)}")
            else:
                result['valid'] = True
                result['required_columns'] = required_columns
            
            # Check for empty critical data
            critical_fields = ['NRC', 'Materia', 'Departamento']
            for field in critical_fields:
                if field in df.columns:
                    empty_count = df[field].isna().sum()
                    if empty_count > 0:
                        result['warnings'].append(f"Campo '{field}' tiene {empty_count} valores vacíos")
            
            # Check for duplicate NRCs
            if 'NRC' in df.columns:
                nrc_counts = df['NRC'].value_counts()
                duplicates = nrc_counts[nrc_counts > 1]
                if len(duplicates) > 0:
                    result['warnings'].append(f"Se encontraron {len(duplicates)} NRCs duplicados")
            
        except Exception as e:
            result['errors'].append(f"Error al leer el archivo: {str(e)}")
        
        return result
    
    def preview_csv_data(self, csv_file_path: str, max_rows: int = 5) -> Dict:
        """
        Preview first few rows of CSV data
        
        Returns:
            Dictionary with preview data
        """
        result = {
            'success': False,
            'columns': [],
            'data': [],
            'total_rows': 0,
            'error_message': None
        }
        
        try:
            df = pd.read_csv(csv_file_path)
            result['total_rows'] = len(df)
            result['columns'] = df.columns.tolist()
            
            # Get preview data
            preview_df = df.head(max_rows)
            result['data'] = preview_df.values.tolist()
            result['success'] = True
            
        except Exception as e:
            result['error_message'] = str(e)
        
        return result
    
class NameDisambiguationDialog:
    """Dialog for disambiguating three-part names with proper TTK styling"""
    
    def __init__(self, name_parts: List[str]):
        self.name_parts = name_parts
        self.choice = 2  # Default to option 2 (Colombian convention)
        self.dialog = None
        self.canvas = None
        self.scrollable_frame = None
        
    def get_choice(self) -> int:
        """Show dialog and get user choice"""
        try:
            # Import utilities
            from ui_components import get_theme_colors, setup_ttk_styles
            colors = get_theme_colors()
            
            # Create dialog window
            self.dialog = tk.Toplevel()
            self.dialog.title("Disambiguación de Nombre")
            self.dialog.geometry("900x700")
            self.dialog.resizable(True, True)
            
            # Configure dialog colors
            self.dialog.configure(bg=colors['bg'])
            
            # Setup TTK styles for this dialog
            self.style = setup_ttk_styles(self.dialog)
            
            # Make dialog modal
            self.dialog.transient()
            self.dialog.grab_set()
            
            # Center the dialog
            self.center_dialog()
            
            # Setup UI
            self.setup_ui(colors)
            
            # Wait for user to make a choice
            self.dialog.wait_window()
            
            return self.choice
            
        except Exception as e:
            print(f"Error in name disambiguation dialog: {e}")
            return 2
    
    def center_dialog(self):
        """Center dialog on screen"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_ui(self, colors):
        """Setup the dialog UI with proper styling"""
        # Main container
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_container, 
                               text="Nombre Ambiguo Encontrado", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Name display frame
        name_frame = ttk.LabelFrame(main_container, text="Nombre encontrado", padding="10")
        name_frame.pack(fill=tk.X, pady=(0, 20))
        
        name_label = ttk.Label(name_frame, 
                              text=' '.join(self.name_parts), 
                              font=("Arial", 14, "bold"))
        name_label.pack()
        
        # Instructions
        instruction_text = ("¿Cómo desea dividir este nombre?\n"
                           "Seleccione la opción que considere más apropiada:")
        instruction_label = ttk.Label(main_container, 
                                     text=instruction_text, 
                                     font=("Arial", 11),
                                     justify=tk.CENTER)
        instruction_label.pack(pady=(0, 20))
        
        # Options frame
        options_frame = ttk.Frame(main_container)
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Radio button variable
        self.choice_var = tk.IntVar(value=2)
        
        # Option 1: Compound first name
        self.create_option_frame(options_frame, 1, 
                                "Opción 1: Nombres compuestos",
                                f"Nombres: '{self.name_parts[0]} {self.name_parts[1]}'  |  Apellidos: '{self.name_parts[2]}'",
                                "(Ej: Ana María Rodríguez)")
        
        # Option 2: Compound surname  
        self.create_option_frame(options_frame, 2,
                                "Opción 2: Apellidos compuestos (Convención colombiana)",
                                f"Nombres: '{self.name_parts[0]}'  |  Apellidos: '{self.name_parts[1]} {self.name_parts[2]}'",
                                "(Ej: Santiago Muñoz Martínez)")
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_container)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Help text
        help_text = ("💡 Sugerencia: En Colombia es común usar dos apellidos (paterno y materno)\n"
                    "Si no está seguro, la Opción 2 suele ser la correcta.")
        help_label = ttk.Label(main_container, 
                              text=help_text, 
                              font=("Arial", 9),
                              justify=tk.CENTER,
                              foreground="gray")
        help_label.pack(pady=(10, 0))
        
        # Create buttons
        self.create_buttons(buttons_frame)
    
    def create_option_frame(self, parent, value, title, detail, example):
        """Create an option frame with TTK styling using theme colors"""
        # Option frame
        option_frame = ttk.LabelFrame(parent, text=title, padding="15")
        option_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Radio button
        radio = ttk.Radiobutton(option_frame,
                               text="Seleccionar esta opción",
                               variable=self.choice_var,
                               value=value)
        radio.pack(anchor=tk.W)
        
        # Detail text - USE THEME ACCENT COLOR for better visibility
        colors = get_theme_colors()
        
        detail_label = ttk.Label(option_frame,
                                text=detail,
                                font=("Arial", 11, "bold"),  # Made bold for better visibility
                                foreground=colors['accent'])  # Use theme accent color
        detail_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Example text - USE LIGHTER GRAY
        example_color = "#B0BEC5" if colors['bg'] != '#ffffff' else colors['comment']
        
        example_label = ttk.Label(option_frame,
                                 text=example,
                                 font=("Arial", 10, "italic"),
                                 foreground=example_color)
        example_label.pack(anchor=tk.W, pady=(2, 0))
    
    def create_buttons(self, parent):
        """Create action buttons using TTK"""
        # Default button (left side)
        default_btn = ttk.Button(parent,
                                text="⚡ Usar Opción 2 por Defecto",
                                command=self.use_default,
                                style="Gray.TButton")
        default_btn.pack(side=tk.LEFT)
        
        # Confirm button (right side)
        confirm_btn = ttk.Button(parent,
                                text="✓ Confirmar Selección",
                                command=self.confirm_choice,
                                style="Green.TButton")
        confirm_btn.pack(side=tk.RIGHT)
    
    def confirm_choice(self):
        """Confirm the user's choice"""
        self.choice = self.choice_var.get()
        self.dialog.destroy()
    
    def use_default(self):
        """Use default choice (option 2)"""
        self.choice = 2
        self.dialog.destroy()