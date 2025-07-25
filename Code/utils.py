import re
import json
import pandas as pd
from datetime import datetime, time
from typing import Any, List, Dict, Optional, Union, Tuple
import tkinter as tk
from tkinter import messagebox

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class DataValidator:
    """Class for data validation functions"""
    
    @staticmethod
    def validate_nrc(nrc: Union[int, str]) -> int:
        """
        Validate NRC format and return as integer
        
        Args:
            nrc: NRC value to validate
            
        Returns:
            int: Valid NRC as integer
            
        Raises:
            ValidationError: If NRC is invalid
        """
        try:
            nrc_int = int(nrc)
            if nrc_int <= 0:
                raise ValidationError("NRC debe ser un número positivo")
            if nrc_int > 99999:
                raise ValidationError("NRC no puede tener más de 5 dígitos")
            return nrc_int
        except (ValueError, TypeError):
            raise ValidationError("NRC debe ser un número válido")
    
    @staticmethod
    def validate_codigo_materia(codigo: str) -> str:
        """
        Validate materia code format
        
        Args:
            codigo: Materia code to validate
            
        Returns:
            str: Valid materia code
            
        Raises:
            ValidationError: If code is invalid
        """
        if not codigo or not isinstance(codigo, str):
            raise ValidationError("Código de materia es requerido")
            
        codigo = codigo.strip().upper()
        
        # Basic format validation (adjust as needed)
        if len(codigo) < 4 or len(codigo) > 12:
            raise ValidationError("Código de materia debe tener entre 4 y 12 caracteres")
            
        # Check for valid characters (letters, numbers, hyphens)
        if not re.match(r'^[A-Z0-9-]+$', codigo):
            raise ValidationError("Código de materia solo puede contener letras, números y guiones")
            
        return codigo
    
    @staticmethod
    def validate_creditos(creditos: Union[int, str]) -> int:
        """
        Validate credits number
        
        Args:
            creditos: Credits to validate
            
        Returns:
            int: Valid credits number
            
        Raises:
            ValidationError: If credits are invalid
        """
        try:
            creditos_int = int(creditos)
            if creditos_int < 0 or creditos_int > 12:
                raise ValidationError("Créditos deben estar entre 0 y 12")
            return creditos_int
        except (ValueError, TypeError):
            raise ValidationError("Créditos deben ser un número válido")
    
    @staticmethod
    def validate_cupo(cupo: Union[int, str]) -> int:
        """
        Validate section capacity
        
        Args:
            cupo: Capacity to validate
            
        Returns:
            int: Valid capacity
            
        Raises:
            ValidationError: If capacity is invalid
        """
        try:
            cupo_int = int(cupo)
            if cupo_int <= 0:
                raise ValidationError("Cupo debe ser un número positivo")
            if cupo_int > 500:
                raise ValidationError("Cupo no puede ser mayor a 500")
            return cupo_int
        except (ValueError, TypeError):
            raise ValidationError("Cupo debe ser un número válido")
    
    @staticmethod
    def validate_name(name: str, field_name: str = "Nombre") -> str:
        """
        Validate person name
        
        Args:
            name: Name to validate
            field_name: Name of the field for error messages
            
        Returns:
            str: Valid name
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError(f"{field_name} es requerido")
            
        name = name.strip()
        
        if len(name) < 2:
            raise ValidationError(f"{field_name} debe tener al menos 2 caracteres")
            
        if len(name) > 50:
            raise ValidationError(f"{field_name} no puede tener más de 50 caracteres")
            
        # Allow letters, spaces, apostrophes, and hyphens
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]+$', name):
            raise ValidationError(f"{field_name} solo puede contener letras, espacios, apostrofes y guiones")
            
        return name
    
    @staticmethod
    def validate_departamento_name(name: str) -> str:
        """
        Validate departamento name
        
        Args:
            name: Departamento name to validate
            
        Returns:
            str: Valid departamento name
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValidationError("Nombre del departamento es requerido")
            
        name = name.strip().upper()
        
        if len(name) < 3:
            raise ValidationError("Nombre del departamento debe tener al menos 3 caracteres")
            
        if len(name) > 100:
            raise ValidationError("Nombre del departamento no puede tener más de 100 caracteres")
            
        return name
    
    @staticmethod
    def validate_time_format(time_str: str) -> str:
        """
        Validate time format (HH:MM)
        
        Args:
            time_str: Time string to validate
            
        Returns:
            str: Valid time string
            
        Raises:
            ValidationError: If time format is invalid
        """
        if not time_str:
            raise ValidationError("Hora es requerida")
            
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
            raise ValidationError("Formato de hora debe ser HH:MM (24 horas)")
            
        return time_str
    
    @staticmethod
    def validate_days_string(days: str) -> str:
        """
        Validate days string format
        
        Args:
            days: Days string to validate (e.g., "L,M,I,J,V")
            
        Returns:
            str: Valid days string
            
        Raises:
            ValidationError: If days format is invalid
        """
        if not days:
            return ""
            
        valid_days = {'L', 'M', 'I', 'J', 'V', 'S', 'D'}
        day_list = [d.strip().upper() for d in days.split(',')]
        
        for day in day_list:
            if day not in valid_days:
                raise ValidationError(f"Día inválido: {day}. Use L,M,I,J,V,S,D")
                
        return ','.join(day_list)
    
    @staticmethod
    def validate_semanas(semanas: Union[int, str]) -> int:
        """
        Validate semanas (weeks) value
        
        Args:
            semanas: Semanas value to validate
            
        Returns:
            int: Valid semanas value (8 or 16)
            
        Raises:
            ValidationError: If semanas value is invalid
        """
        try:
            semanas_int = int(semanas)
            if semanas_int not in [8, 16]:
                raise ValidationError("Semanas debe ser 8 o 16")
            return semanas_int
        except (ValueError, TypeError):
            raise ValidationError("Semanas debe ser un número válido (8 o 16)")
    
    @staticmethod
    def validate_parte_pdo(parte_pdo: str) -> str:
        """
        Validate Parte pdo format
        
        Args:
            parte_pdo: Parte pdo value to validate
            
        Returns:
            str: Valid parte_pdo value
            
        Raises:
            ValidationError: If parte_pdo format is invalid
        """
        if not parte_pdo:
            return "16"  # Default value
        
        parte_pdo_clean = str(parte_pdo).strip().upper()
        
        # Common valid values
        valid_values = ['1', '2', '3', '4', '5', '6', '7', '8', '8A', '8B', '9', '10', '11', '12']
        
        if parte_pdo_clean not in valid_values:
            raise ValidationError(f"Valor de Parte pdo no reconocido: {parte_pdo_clean}")
        
        return parte_pdo_clean

class DataFormatter:
    """Class for data formatting functions"""
    
    @staticmethod
    def calculate_semanas_from_parte_pdo(parte_pdo: Any) -> int:
        """
        Calculate semanas from Parte pdo value
        
        Args:
            parte_pdo: Parte pdo value from CSV
            
        Returns:
            int: 8 if parte_pdo is "8A" or "8B", otherwise 16
        """
        if pd.isna(parte_pdo) or parte_pdo is None:
            return 16
        
        parte_pdo_str = str(parte_pdo).strip().upper()
        
        if parte_pdo_str in ['8A', '8B']:
            return 8
        else:
            return 16
    
    @staticmethod
    def format_semanas_display(semanas: int) -> str:
        """
        Format semanas for display
        
        Args:
            semanas: Number of weeks
            
        Returns:
            str: Formatted display string
        """
        if semanas == 8:
            return "8 semanas (Medio período)"
        elif semanas == 16:
            return "16 semanas (Período completo)"
        else:
            return f"{semanas} semanas"
    
    @staticmethod
    def format_time_from_excel(time_value: Any) -> Optional[str]:
        """
        Convert time from Excel format to HH:MM string
        
        Args:
            time_value: Time value from Excel (various formats)
            
        Returns:
            str or None: Formatted time string or None if invalid
        """
        if pd.isna(time_value):
            return None
            
        try:
            # Handle different input formats
            if isinstance(time_value, str):
                # Already a string, validate format
                if re.match(r'^\d{1,2}:\d{2}$', time_value):
                    return time_value
                # Try to parse as HHMM
                if time_value.isdigit():
                    time_value = int(time_value)
                else:
                    return None
            
            if isinstance(time_value, (int, float)):
                # Convert from HHMM format
                time_str = str(int(time_value)).zfill(4)
                if len(time_str) == 4:
                    return f"{time_str[:2]}:{time_str[2:]}"
                    
            return None
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def format_days_from_columns(row: pd.Series) -> str:
        """
        Extract days from DataFrame row columns
        
        Args:
            row: Pandas Series representing a row
            
        Returns:
            str: Comma-separated days string
        """
        days = []
        day_columns = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        day_abbrev = ['L', 'M', 'I', 'J', 'V', 'S', 'D']
        
        for i, day_col in enumerate(day_columns):
            if day_col in row and not pd.isna(row[day_col]) and str(row[day_col]).strip() != '':
                days.append(day_abbrev[i])
        
        return ','.join(days)
    
    @staticmethod
    def format_days_for_display(days_str: str) -> str:
        """
        Convert days abbreviation to full display format
        
        Args:
            days_str: Days string (e.g., "L,M,I,J,V")
            
        Returns:
            str: Full days display (e.g., "Lunes, Martes, Miércoles, Jueves, Viernes")
        """
        if not days_str:
            return ""
            
        day_map = {
            'L': 'Lunes',
            'M': 'Martes',
            'I': 'Miércoles',
            'J': 'Jueves',
            'V': 'Viernes',
            'S': 'Sábado',
            'D': 'Domingo'
        }
        
        day_list = [d.strip() for d in days_str.split(',')]
        full_days = [day_map.get(d, d) for d in day_list if d in day_map]
        
        return ', '.join(full_days)
    
    @staticmethod
    def format_time_range(start_time: str, end_time: str) -> str:
        """
        Format time range for display
        
        Args:
            start_time: Start time (HH:MM)
            end_time: End time (HH:MM)
            
        Returns:
            str: Formatted time range
        """
        if not start_time or not end_time:
            return "Horario no definido"
            
        return f"{start_time} - {end_time}"
    
    @staticmethod
    def format_duration(duration_hours: float) -> str:
        """
        Format duration in hours to readable format
        
        Args:
            duration_hours: Duration in hours
            
        Returns:
            str: Formatted duration string
        """
        if not duration_hours or duration_hours <= 0:
            return "No definido"
            
        hours = int(duration_hours)
        minutes = int((duration_hours - hours) * 60)
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"
    
    @staticmethod
    def format_professor_name(nombres: str, apellidos: str) -> str:
        """
        Format professor name for display
        
        Args:
            nombres: First names
            apellidos: Last names
            
        Returns:
            str: Formatted full name
        """
        nombres = nombres.strip() if nombres else ""
        apellidos = apellidos.strip() if apellidos else ""
        
        if nombres and apellidos:
            return f"{nombres} {apellidos}"
        elif apellidos:
            return apellidos
        elif nombres:
            return nombres
        else:
            return "Sin nombre"
    
    @staticmethod
    def format_capacity_info(cupo: int, inscritos: int) -> str:
        """
        Format capacity information for display
        
        Args:
            cupo: Total capacity
            inscritos: Enrolled students
            
        Returns:
            str: Formatted capacity info
        """
        disponible = cupo - inscritos
        return f"{inscritos}/{cupo} (Disponible: {disponible})"
    
    @staticmethod
    def safe_string_conversion(value: Any, default: str = "") -> str:
        """
        Safely convert any value to string
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            str: String representation of value
        """
        if pd.isna(value) or value is None:
            return default
        return str(value).strip()
    
    @staticmethod
    def safe_int_conversion(value: Any, default: int = 0) -> int:
        """
        Safely convert value to integer
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            int: Integer value
        """
        if pd.isna(value) or value is None:
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
        
        # Add this new function to the DataFormatter class in utils.py:
    
    @staticmethod
    def normalize_department_name(name: str) -> str:
        """
        Normalize department name to handle spacing inconsistencies
        
        Args:
            name: Department name to normalize
            
        Returns:
            str: Normalized department name with consistent spacing
        """
        if not name or pd.isna(name):
            return "DECANATURA DE INGENIERIA"  # Updated default
        
        # Convert to string and strip
        normalized = str(name).strip().upper()
        
        # Handle empty or default cases
        if not normalized or normalized in ["NO DECLARADO", "SIN DEPARTAMENTO", "N/A"]:
            return "DECANATURA DE INGENIERIA"
        
        # Fix common spacing issues
        # Add space after periods if missing
        normalized = re.sub(r'\.([A-Z])', r'. \1', normalized)
        
        # Fix multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Common department name corrections
        department_corrections = {
            'INGEN. QUIMICA Y DE ALIMENTOS': 'INGEN. QUIMICA Y DE ALIMENTOS',
            'INGEN.QUIMICA Y DE ALIMENTOS': 'INGEN. QUIMICA Y DE ALIMENTOS',
            'INGENIERIA QUIMICA Y DE ALIMENTOS': 'INGEN. QUIMICA Y DE ALIMENTOS',
            'INGEN. ELECTRICA Y ELECTRONICA': 'INGEN. ELECTRICA Y ELECTRONICA',
            'INGEN.ELECTRICA Y ELECTRONICA': 'INGEN. ELECTRICA Y ELECTRONICA',
            'INGENIERIA ELECTRICA Y ELECTRONICA': 'INGEN. ELECTRICA Y ELECTRONICA',
            'INGEN. MECANICA': 'INGENIERIA MECANICA',
            'INGEN.MECANICA': 'INGENIERIA MECANICA',
            'INGEN. INDUSTRIAL': 'INGENIERIA INDUSTRIAL',
            'INGEN.INDUSTRIAL': 'INGENIERIA INDUSTRIAL',
            'INGEN. CIVIL Y AMBIENTAL': 'INGENIERIA CIVIL Y AMBIENTAL',
            'INGEN.CIVIL Y AMBIENTAL': 'INGENIERIA CIVIL Y AMBIENTAL',
            'INGEN. DE SISTEMAS Y COMPU': 'INGENIERIA DE SISTEMAS Y COMPU',
            'INGEN.DE SISTEMAS Y COMPU': 'INGENIERIA DE SISTEMAS Y COMPU',
            'INGEN. BIOMEDICA': 'INGENIERIA BIOMEDICA',
            'INGEN.BIOMEDICA': 'INGENIERIA BIOMEDICA'
        }
        
        # Apply corrections
        return department_corrections.get(normalized, normalized)

class UIHelpers:
    """Helper functions for UI operations"""
    
    @staticmethod
    def center_window(window: tk.Toplevel, parent: tk.Tk = None) -> None:
        """
        Center a window on screen or parent window
        
        Args:
            window: Window to center
            parent: Parent window (optional)
        """
        window.update_idletasks()
        
        if parent:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (window.winfo_width() // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (window.winfo_height() // 2)
        else:
            x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
            y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
        
        window.geometry(f"+{x}+{y}")
    
    @staticmethod
    def show_error(parent: tk.Widget, title: str, message: str) -> None:
        """
        Show error message dialog
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message, parent=parent)
    
    @staticmethod
    def show_warning(parent: tk.Widget, title: str, message: str) -> None:
        """
        Show warning message dialog
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Warning message
        """
        messagebox.showwarning(title, message, parent=parent)
    
    @staticmethod
    def show_info(parent: tk.Widget, title: str, message: str) -> None:
        """
        Show information message dialog
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Information message
        """
        messagebox.showinfo(title, message, parent=parent)
    
    @staticmethod
    def confirm_action(parent: tk.Widget, title: str, message: str) -> bool:
        """
        Show confirmation dialog
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Confirmation message
            
        Returns:
            bool: True if user confirmed, False otherwise
        """
        return messagebox.askyesno(title, message, parent=parent)
    
    @staticmethod
    def bind_entry_validation(entry: tk.Entry, validation_func: callable, 
                             error_callback: callable = None) -> None:
        """
        Bind validation to entry widget
        
        Args:
            entry: Entry widget to validate
            validation_func: Function to call for validation
            error_callback: Function to call on validation error
        """
        def validate(event=None):
            try:
                value = entry.get()
                validation_func(value)
                entry.config(bg='white')  # Reset background
            except ValidationError as e:
                entry.config(bg='#ffcccc')  # Light red background
                if error_callback:
                    error_callback(str(e))
        
        entry.bind('<FocusOut>', validate)
        entry.bind('<KeyRelease>', validate)
    
    @staticmethod
    def create_tooltip(widget: tk.Widget, text: str) -> None:
        """
        Add tooltip to widget
        
        Args:
            widget: Widget to add tooltip to
            text: Tooltip text
        """
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="lightyellow", 
                           relief="solid", borderwidth=1, font=("Arial", 8))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

class FileHelpers:
    """Helper functions for file operations"""
    
    @staticmethod
    def validate_csv_file(file_path: str) -> bool:
        """
        Check if file is a valid CSV
        
        Args:
            file_path: Path to file
            
        Returns:
            bool: True if valid CSV file
        """
        try:
            df = pd.read_csv(file_path, nrows=1)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """
        Get file size in MB
        
        Args:
            file_path: Path to file
            
        Returns:
            float: File size in MB
        """
        try:
            import os
            size_bytes = os.path.getsize(file_path)
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0
    
    @staticmethod
    def backup_database(db_path: str) -> str:
        """
        Create database backup
        
        Args:
            db_path: Path to database file
            
        Returns:
            str: Path to backup file
        """
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
        shutil.copy2(db_path, backup_path)
        return backup_path

class ScheduleHelpers:
    """Helper functions for schedule-related operations"""
    
    @staticmethod
    def calculate_duration_minutes(start_time: str, end_time: str) -> int:
        """
        Calculate duration in minutes between two times
        
        Args:
            start_time: Start time (HH:MM)
            end_time: End time (HH:MM)
            
        Returns:
            int: Duration in minutes
        """
        try:
            start_h, start_m = map(int, start_time.split(':'))
            end_h, end_m = map(int, end_time.split(':'))
            
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            
            return max(0, end_minutes - start_minutes)
        except (ValueError, AttributeError):
            return 0
    
    @staticmethod
    def time_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
        """
        Check if two time ranges overlap
        
        Args:
            start1, end1: First time range
            start2, end2: Second time range
            
        Returns:
            bool: True if ranges overlap
        """
        try:
            def time_to_minutes(time_str):
                h, m = map(int, time_str.split(':'))
                return h * 60 + m
            
            start1_min = time_to_minutes(start1)
            end1_min = time_to_minutes(end1)
            start2_min = time_to_minutes(start2)
            end2_min = time_to_minutes(end2)
            
            return not (end1_min <= start2_min or end2_min <= start1_min)
        except (ValueError, AttributeError):
            return False
    
    @staticmethod
    def days_overlap(days1: str, days2: str) -> bool:
        """
        Check if two day strings have overlapping days
        
        Args:
            days1: First days string (e.g., "L,M,I")
            days2: Second days string (e.g., "M,J,V")
            
        Returns:
            bool: True if there are common days
        """
        if not days1 or not days2:
            return False
            
        set1 = set(d.strip() for d in days1.split(','))
        set2 = set(d.strip() for d in days2.split(','))
        
        return bool(set1.intersection(set2))
    
    @staticmethod
    def schedule_conflict(session1: Dict, session2: Dict) -> bool:
        """
        Check if two sessions have scheduling conflicts
        
        Args:
            session1: First session dict with 'dias', 'horaInicio', 'horaFin'
            session2: Second session dict with same fields
            
        Returns:
            bool: True if sessions conflict
        """
        # Check if days overlap
        if not ScheduleHelpers.days_overlap(session1.get('dias', ''), session2.get('dias', '')):
            return False
        
        # Check if times overlap
        return ScheduleHelpers.time_overlap(
            session1.get('horaInicio', ''), session1.get('horaFin', ''),
            session2.get('horaInicio', ''), session2.get('horaFin', '')
        )

class JSONHelpers:
    """Helper functions for JSON operations"""
    
    @staticmethod
    def safe_json_loads(json_str: str, default: Any = None) -> Any:
        """
        Safely parse JSON string
        
        Args:
            json_str: JSON string to parse
            default: Default value if parsing fails
            
        Returns:
            Any: Parsed JSON or default value
        """
        if not json_str:
            return default
            
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(obj: Any, default: str = "[]") -> str:
        """
        Safely convert object to JSON string
        
        Args:
            obj: Object to convert
            default: Default string if conversion fails
            
        Returns:
            str: JSON string
        """
        try:
            return json.dumps(obj)
        except (TypeError, ValueError):
            return default

class Constants:
    """Application constants"""
    
    # Database constants
    DEFAULT_DB_NAME = 'university_schedule.db'
    
    # UI constants
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 900
    DEFAULT_DIALOG_WIDTH = 400
    DEFAULT_DIALOG_HEIGHT = 300
    
    # Data constants
    MAX_NRC = 99999
    MAX_CREDITS = 12
    MAX_CAPACITY = 500
    MAX_NAME_LENGTH = 50
    MAX_DEPARTMENT_NAME_LENGTH = 100
    
    # Time constants
    MIN_SESSION_DURATION = 30  # minutes
    MAX_SESSION_DURATION = 240  # minutes
    
    # Days of week
    DAYS_ABBREV = ['L', 'M', 'I', 'J', 'V', 'S', 'D']
    DAYS_FULL = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    # Professor types
    PROFESSOR_TYPES = ['PRINCIPAL', 'AUXILIAR', 'INVITADO']
    
    # Academic levels
    ACADEMIC_LEVELS = ['PREGRADO', 'POSTGRADO', 'ESPECIALIZACION']
    
    # Grading modes
    GRADING_MODES = ['NUMERICO', 'CONCEPTUAL', 'PASS/FAIL']
    
    # Campus options
    CAMPUS_OPTIONS = ['BOGOTA', 'MEDELLIN', 'BARRANQUILLA']

# Convenience functions for common operations
def validate_and_format_nrc(nrc: Any) -> int:
    """Convenience function to validate and format NRC"""
    return DataValidator.validate_nrc(nrc)

def validate_and_format_materia_code(codigo: str) -> str:
    """Convenience function to validate and format materia code"""
    return DataValidator.validate_codigo_materia(codigo)

def format_professor_display_name(nombres: str, apellidos: str) -> str:
    """Convenience function to format professor name"""
    return DataFormatter.format_professor_name(nombres, apellidos)

def safe_convert_to_int(value: Any, default: int = 0) -> int:
    """Convenience function for safe integer conversion"""
    return DataFormatter.safe_int_conversion(value, default)

def safe_convert_to_string(value: Any, default: str = "") -> str:
    """Convenience function for safe string conversion"""
    return DataFormatter.safe_string_conversion(value, default)

def show_validation_error(parent: tk.Widget, error: ValidationError) -> None:
    """Convenience function to show validation error"""
    UIHelpers.show_error(parent, "Error de Validación", str(error))

def confirm_delete_action(parent: tk.Widget, item_name: str) -> bool:
    """Convenience function for delete confirmation"""
    return UIHelpers.confirm_action(
        parent, 
        "Confirmar Eliminación", 
        f"¿Está seguro de que desea eliminar '{item_name}'?\n\nEsta acción no se puede deshacer."
    )