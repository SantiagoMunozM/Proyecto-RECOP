import sqlite3
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path='Bases de Datos/university_schedule.db'):
        self.db_path = db_path
        self.create_schema()
    
    def create_schema(self):
        """Create database tables"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Create Departamento table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Departamento (
                    nombre TEXT PRIMARY KEY
                )
            ''')
            
            # Create Profesor table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS Profesor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombres TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                tipo TEXT,
                person_id INTEGER,
                cargo_original TEXT,
                subcategoria INTEGER,
                dependencia TEXT,
                contrato TEXT,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                datos_personales_vinculados BOOLEAN DEFAULT FALSE
            )
            ''')
            
            # New junction table for Professor-Department relationship
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ProfesorDepartamento (
                profesor_id INTEGER,
                departamento_nombre TEXT,
                PRIMARY KEY (profesor_id, departamento_nombre),
                FOREIGN KEY (profesor_id) REFERENCES Profesor(id),
                FOREIGN KEY (departamento_nombre) REFERENCES Departamento(nombre)
                )
            ''')
            
            # Create Materia table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Materia (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    creditos INTEGER,
                    nivel TEXT,
                    nivel_numerico INTEGER,
                    calificacion TEXT,
                    campus TEXT,
                    periodo TEXT,
                    semanas INTEGER DEFAULT 16,
                    departamento_nombre TEXT,
                    FOREIGN KEY (departamento_nombre) REFERENCES Departamento(nombre)
                )
            ''')
            
            # Create Seccion table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Seccion (
                    NRC INTEGER PRIMARY KEY,
                    indicador TEXT,
                    cupo INTEGER,
                    inscritos INTEGER DEFAULT 0,
                    cupoDisponible INTEGER,
                    lista_cruzada TEXT,
                    materia_codigo TEXT,
                    profesor_dedicaciones TEXT,
                    FOREIGN KEY (materia_codigo) REFERENCES Materia(codigo)
                )
            ''')
            
            # Create Sesion table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Sesion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipoHorario TEXT,
                    horaInicio TEXT,
                    horaFin TEXT,
                    duracion INTEGER,
                    edificio TEXT,
                    salon TEXT,
                    atributoSalon TEXT,
                    dias TEXT,
                    PER INTEGER DEFAULT 0,
                    seccion_NRC INTEGER,
                    profesor_ids TEXT,
                    FOREIGN KEY (seccion_NRC) REFERENCES Seccion(NRC)
                )
            ''')
            
            # Create junction tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS SesionProfesor (
                    sesion_id INTEGER,
                    profesor_id INTEGER,
                    PRIMARY KEY (sesion_id, profesor_id),
                    FOREIGN KEY (sesion_id) REFERENCES Sesion(id),
                    FOREIGN KEY (profesor_id) REFERENCES Profesor(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS SeccionProfesor (
                    seccion_NRC INTEGER,
                    profesor_id INTEGER,
                    PRIMARY KEY (seccion_NRC, profesor_id),
                    FOREIGN KEY (seccion_NRC) REFERENCES Seccion(NRC),
                    FOREIGN KEY (profesor_id) REFERENCES Profesor(id)
                )
            ''')
            
            conn.commit()
        except Exception as e:
            print(f"Error creating schema: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = True):
        """Execute a query and return results"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
                return cursor.lastrowid if query.strip().upper().startswith('INSERT') else cursor.rowcount
            elif fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return None
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # Add this method to the DatabaseManager class:
    
    def cleanup_duplicate_professor_departments(self) -> Dict:
        """Remove duplicate professor-department relationships"""
        result = {'removed': 0, 'errors': []}
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Find duplicate relationships
            cursor.execute("""
                SELECT profesor_id, departamento_nombre, COUNT(*) as count, MIN(rowid) as keep_rowid
                FROM ProfesorDepartamento 
                GROUP BY profesor_id, departamento_nombre 
                HAVING COUNT(*) > 1
            """)
            
            duplicates = cursor.fetchall()
            
            if duplicates:
                print(f"Found {len(duplicates)} sets of duplicate professor-department relationships")
                
                for profesor_id, dept_name, count, keep_rowid in duplicates:
                    # Delete all duplicates except the one with the smallest rowid
                    cursor.execute("""
                        DELETE FROM ProfesorDepartamento 
                        WHERE profesor_id = ? AND departamento_nombre = ? AND rowid != ?
                    """, (profesor_id, dept_name, keep_rowid))
                    
                    removed = cursor.rowcount
                    result['removed'] += removed
                    print(f"Removed {removed} duplicate entries for professor {profesor_id} in department {dept_name}")
            
            conn.commit()
            conn.close()
            
            if result['removed'] > 0:
                print(f"Cleanup complete: {result['removed']} duplicate relationships removed")
            else:
                print("No duplicate relationships found")
            return result
            
        except Exception as e:
            result['errors'].append(str(e))
            print(f"Error during cleanup: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return result       
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        try:
            # Special handling for Sesion table with materia information
            if table_name == "Sesion":
                return [
                    'id', 'tipoHorario', 'horaInicio', 'horaFin', 'duracion', 
                    'edificio', 'salon', 'atributoSalon', 'dias', 'PER', 
                    'seccion_NRC', 'materia_codigo', 'materia_nombre', 
                    'departamento_nombre', 'profesor_ids'
                ]
                
            # Special handling for Seccion table with dedication information
            if table_name == "Seccion":
                return [
                    'NRC', 'indicador', 'cupo', 'inscritos', 'cupoDisponible',
                    'lista_cruzada', 'materia_codigo', 'profesor_dedicaciones'
                ]
            
            # For other tables, get columns from database schema
            result = self.execute_query(f"PRAGMA table_info({table_name})")
            if result:
                return [row[1] for row in result]  # Column name is at index 1
            else:
                return []
        except Exception as e:
            print(f"Error getting columns for table {table_name}: {e}")
            return []
    # ==================== DEPARTAMENTO OPERATIONS ====================
    
    def create_departamento(self, nombre: str) -> bool:
        """Create new departamento"""
        try:
            self.execute_query(
                "INSERT INTO Departamento (nombre) VALUES (?)",
                (nombre.strip(),)
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Already exists
    
    def get_departamentos(self) -> List[str]:
        """Get all departamentos"""
        results = self.execute_query("SELECT nombre FROM Departamento ORDER BY nombre")
        return [row[0] for row in results]
    
    def delete_departamento(self, nombre: str) -> bool:
        """Delete departamento and all related data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if departamento has related data
            cursor.execute("SELECT COUNT(*) FROM Profesor WHERE departamento_nombre = ?", (nombre,))
            prof_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM Materia WHERE departamento_nombre = ?", (nombre,))
            mat_count = cursor.fetchone()[0]
            
            if prof_count > 0 or mat_count > 0:
                conn.close()
                return False  # Cannot delete, has related data
            
            cursor.execute("DELETE FROM Departamento WHERE nombre = ?", (nombre,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting departamento: {e}")
            return False
    
    # ==================== PROFESOR OPERATIONS ====================
    
        # Update the professor operations:
    
    def create_profesor(self, nombres: str, apellidos: str, tipo: str, departamento_nombres: List[str]) -> Optional[int]:
        """Create new profesor with multiple departments"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Insert profesor
            cursor.execute(
                "INSERT INTO Profesor (nombres, apellidos, tipo) VALUES (?, ?, ?)",
                (nombres.strip(), apellidos.strip(), tipo.strip())
            )
            
            profesor_id = cursor.lastrowid
            
            unique_depts = list(set(departamento_nombres))  # Remove duplicates
            for dept in unique_depts:
                cursor.execute(
                    "SELECT COUNT(*) FROM ProfesorDepartamento WHERE profesor_id = ? AND departamento_nombre = ?",
                    (profesor_id, dept)
                )
                if cursor.fetchone()[0] == 0:  # Only insert if doesn't exist
                    cursor.execute(
                        "INSERT INTO ProfesorDepartamento (profesor_id, departamento_nombre) VALUES (?, ?)",
                        (profesor_id, dept)
                    )
            conn.commit()
            conn.close()
            return profesor_id
            
        except Exception as e:
            print(f"Error creating profesor: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return None
    
    def get_profesores_by_departamento(self, departamento: str) -> List[Dict]:
        """Get professors by department"""
        results = self.execute_query(
            """SELECT DISTINCT p.id, p.nombres, p.apellidos, p.tipo 
               FROM Profesor p
               JOIN ProfesorDepartamento pd ON p.id = pd.profesor_id
               WHERE pd.departamento_nombre = ? 
               ORDER BY p.apellidos, p.nombres""",
            (departamento,)
        )
        return [
            {
                'id': row[0],
                'nombres': row[1],
                'apellidos': row[2],
                'tipo': row[3],
                'full_name': f"{row[1]} {row[2]}"
            }
            for row in results
        ]
    
        # Replace the get_all_profesores method with this corrected version:
    
    def get_all_profesores(self) -> List[Dict]:
        """Get all professors with their departments (avoiding duplicates)"""
        results = self.execute_query(
            """SELECT p.id, p.nombres, p.apellidos, p.tipo,
                      COUNT(DISTINCT sp.sesion_id) as num_sessions,
                      COUNT(DISTINCT scp.seccion_NRC) as num_sections
               FROM Profesor p
               LEFT JOIN SesionProfesor sp ON p.id = sp.profesor_id
               LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
               GROUP BY p.id, p.nombres, p.apellidos, p.tipo
               ORDER BY p.apellidos, p.nombres"""
        )
        
        profesores = []
        for row in results:
            profesor_id = row[0]
            
            # Get departments separately to avoid duplicates
            dept_results = self.execute_query(
                """SELECT DISTINCT departamento_nombre 
                   FROM ProfesorDepartamento 
                   WHERE profesor_id = ? 
                   ORDER BY departamento_nombre""",
                (profesor_id,)
            )
            
            # Create clean department list
            departamentos = [dept[0] for dept in dept_results]
            departamentos_str = ', '.join(departamentos) if departamentos else 'Sin departamento'
            
            profesores.append({
                'id': row[0],
                'nombres': row[1],
                'apellidos': row[2],
                'tipo': row[3],
                'departamentos': departamentos_str,
                'full_name': f"{row[1]} {row[2]}",
                'num_sessions': row[4],
                'num_sections': row[5]
            })
        
        return profesores
    
    def get_profesor_departamentos(self, profesor_id: int) -> List[str]:
        """Get all departments for a professor"""
        results = self.execute_query(
            "SELECT departamento_nombre FROM ProfesorDepartamento WHERE profesor_id = ?",
            (profesor_id,)
        )
        return [row[0] for row in results]
    
    def update_profesor_departamentos(self, profesor_id: int, departamento_nombres: List[str]) -> bool:
        """Update professor's department assignments"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Remove existing department assignments
            cursor.execute("DELETE FROM ProfesorDepartamento WHERE profesor_id = ?", (profesor_id,))
            
            # Add new department assignments (avoid duplicates)
            unique_depts = list(set(departamento_nombres))  # Remove duplicates
            for dept in unique_depts:
                cursor.execute(
                    "INSERT INTO ProfesorDepartamento (profesor_id, departamento_nombre) VALUES (?, ?)",
                    (profesor_id, dept)
                )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error updating profesor departments: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
        # Add these methods to the DatabaseManager class:
    
    # Update this method in database.py:
    
    def update_professor_personal_data(self, profesor_id: int, person_id: int, 
                                     cargo_original: str, tipo_enhanced: str, 
                                     subcategoria: int = None, dependencia: str = None,
                                     contrato: str = None) :
        """Update professor with personal data information"""
        try:
            #print(f"DEBUG: Updating professor {profesor_id} with subcategoria: {subcategoria}")  # DEBUG
            
            # Handle None subcategoria explicitly
            subcategoria_value = subcategoria if subcategoria is not None else None
            
            self.execute_query("""
                UPDATE Profesor 
                SET person_id = ?, 
                    cargo_original = ?, 
                    tipo = ?, 
                    subcategoria = ?, 
                    dependencia = ?,
                    contrato = ?,
                    fecha_actualizacion = CURRENT_TIMESTAMP,
                    datos_personales_vinculados = TRUE
                WHERE id = ?
            """, (person_id, cargo_original, tipo_enhanced, subcategoria_value, dependencia, contrato, profesor_id))
            
            # Verify the update
            result = self.execute_query("""
                SELECT subcategoria FROM Profesor WHERE id = ?
            """, (profesor_id,), fetch_one=True)
            
            
            #print(f"DEBUG: After update, subcategoria = {result[0] if result else 'No result'}")  # DEBUG
            return True
        except Exception as e:
            #print(f"Error updating professor personal data: {e}")
            return False
    
    def get_professors_without_personal_data(self):
        """Get professors that haven't been linked to personal data yet"""
        return self.execute_query("""
            SELECT id, nombres, apellidos, tipo 
            FROM Profesor 
            WHERE datos_personales_vinculados = FALSE OR datos_personales_vinculados IS NULL
            ORDER BY apellidos, nombres
        """)
    
    def get_enhanced_professor_info(self, profesor_id: int):
        """Get professor with enhanced personal data information"""
        result = self.execute_query("""
            SELECT id, nombres, apellidos, tipo,
                   person_id, cargo_original, subcategoria,
                   dependencia, contrato, 
                   fecha_actualizacion, datos_personales_vinculados
            FROM Profesor 
            WHERE id = ?
        """, (profesor_id,), fetch_one=True)
        
        if result:
            return {
                'id': result[0],
                'nombres': result[1],
                'apellidos': result[2],
                'tipo': result[3],
                'person_id': result[4],
                'cargo_original': result[5],
                'subcategoria': result[6],
                'dependencia': result[7],
                'contrato': result[8],
                'fecha_actualizacion': result[9],
                'datos_personales_vinculados': result[10]
            }
        return None
    
    def get_professors_with_personal_data(self):
        """Get all professors that have been enhanced with personal data"""
        return self.execute_query("""
            SELECT id, nombres, apellidos, tipo, person_id, cargo_original, subcategoria
            FROM Profesor 
            WHERE datos_personales_vinculados = TRUE
            ORDER BY apellidos, nombres
        """)
    def delete_profesor(self, profesor_id: int) -> bool:
        """Delete profesor and all related data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete from junction tables first
            cursor.execute("DELETE FROM SesionProfesor WHERE profesor_id = ?", (profesor_id,))
            cursor.execute("DELETE FROM SeccionProfesor WHERE profesor_id = ?", (profesor_id,))
            cursor.execute("DELETE FROM ProfesorDepartamento WHERE profesor_id = ?", (profesor_id,))
            
            # Delete profesor
            cursor.execute("DELETE FROM Profesor WHERE id = ?", (profesor_id,))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error deleting profesor: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    
    def get_profesor_sessions(self, profesor_id: int) -> List[Dict]:
        """Get all sessions for a specific professor with detailed information"""
        results = self.execute_query(
            """SELECT 
                ses.id as sesion_id,
                ses.tipoHorario,
                ses.horaInicio,
                ses.horaFin,
                ses.duracion,
                ses.edificio,
                ses.salon,
                ses.atributoSalon,
                ses.dias,
                SES.PER,
                sec.NRC,
                sec.indicador,
                sec.cupo,
                sec.inscritos,
                m.codigo as materia_codigo,
                m.nombre as materia_nombre,
                m.creditos,
                m.departamento_nombre,
                p.nombres,
                p.apellidos
            FROM Sesion ses
            JOIN SesionProfesor sp ON ses.id = sp.sesion_id
            JOIN Seccion sec ON ses.seccion_NRC = sec.NRC
            JOIN Materia m ON sec.materia_codigo = m.codigo
            JOIN Profesor p ON sp.profesor_id = p.id
            WHERE sp.profesor_id = ?
            ORDER BY m.departamento_nombre, m.codigo, sec.NRC, ses.horaInicio""",
            (profesor_id,)
        )
        
        sessions = []
        for row in results:
            sessions.append({
                'sesion_id': row[0],
                'tipo_horario': row[1] if row[1] else 'No especificado',
                'hora_inicio': row[2] if row[2] else '',
                'hora_fin': row[3] if row[3] else '',
                'duracion': row[4] if row[4] else 0,
                'edificio': row[5] if row[5] else 'No especificado',
                'salon': row[6] if row[6] else 'No especificado',
                'atributo_salon': row[7] if row[7] else '',
                'dias': row[8] if row[8] else '',
                'per': row[9] if row[9] is not None else 0,
                'nrc': row[10],
                'indicador': row[11] if row[11] else '',
                'cupo': row[12] if row[12] else 0,
                'inscritos': row[13] if row[13] else 0,
                'materia_codigo': row[14],
                'materia_nombre': row[15],
                'creditos': row[16] if row[16] else 0,
                'departamento': row[17],
                'profesor_nombres': row[18],
                'profesor_apellidos': row[19]
            })
        
        return sessions

        # Replace the get_profesor_sessions_summary method with this corrected version:
    
    def get_profesor_sessions_summary(self, profesor_id: int) -> Dict:
        """Get summary statistics for a professor's sessions"""
        sessions = self.get_profesor_sessions(profesor_id)
        
        if not sessions:
            return {
                'total_sessions': 0,
                'total_sections': 0,
                'total_credits': 0,
                'departments': [],
                'materias': [],
                'total_students': 0,
                'schedule_days': []
            }
        
        # Calculate summary using unique sections to avoid double counting
        unique_sections = {}  # Key: NRC, Value: section info
        unique_materias = set()
        departments = set()
        days = set()
        
        for session in sessions:
            nrc = session['nrc']
            
            # Store unique section information
            if nrc not in unique_sections:
                unique_sections[nrc] = {
                    'credits': session['creditos'],
                    'students': session['inscritos']
                }
            
            unique_materias.add(session['materia_codigo'])
            departments.add(session['departamento'])
            
            # Parse days
            if session['dias']:
                for day in session['dias'].split(','):
                    days.add(day.strip())
        
        # Calculate totals from unique sections
        total_credits = sum(section['credits'] for section in unique_sections.values())
        total_students = sum(section['students'] for section in unique_sections.values())
        
        return {
            'total_sessions': len(sessions),
            'total_sections': len(unique_sections),
            'total_credits': total_credits,
            'departments': sorted(list(departments)),
            'materias': sorted(list(unique_materias)),
            'total_students': total_students,
            'schedule_days': sorted(list(days))
        }
    
    
    def get_profesor_sections(self, profesor_id: int) -> List[Dict]:
        """Get all sections for a specific professor with detailed information"""
        results = self.execute_query(
            """SELECT DISTINCT
                sec.NRC,
                sec.indicador,
                sec.cupo,
                sec.inscritos,
                sec.cupoDisponible,
                m.codigo as materia_codigo,
                m.nombre as materia_nombre,
                m.creditos,
                m.nivel,
                m.calificacion,
                m.campus,
                m.periodo,
                m.departamento_nombre,
                COUNT(ses.id) as num_sessions
            FROM Seccion sec
            JOIN SeccionProfesor sp ON sec.NRC = sp.seccion_NRC
            JOIN Materia m ON sec.materia_codigo = m.codigo
            LEFT JOIN Sesion ses ON sec.NRC = ses.seccion_NRC
            WHERE sp.profesor_id = ?
            GROUP BY sec.NRC, sec.indicador, sec.cupo, sec.inscritos, sec.cupoDisponible,
                     m.codigo, m.nombre, m.creditos, m.nivel, m.calificacion, 
                     m.campus, m.periodo, m.departamento_nombre
            ORDER BY m.departamento_nombre, m.codigo, sec.NRC""",
            (profesor_id,)
        )
        
        sections = []
        for row in results:
            sections.append({
                'nrc': row[0],
                'indicador': row[1] if row[1] else '',
                'cupo': row[2] if row[2] else 0,
                'inscritos': row[3] if row[3] else 0,
                'cupo_disponible': row[4] if row[4] else 0,
                'materia_codigo': row[5],
                'materia_nombre': row[6],
                'creditos': row[7] if row[7] else 0,
                'nivel': row[8] if row[8] else '',
                'calificacion': row[9] if row[9] else '',
                'campus': row[10] if row[10] else '',
                'periodo': row[11] if row[11] else '',
                'departamento': row[12],
                'num_sessions': row[13] if row[13] else 0
            })
        
        return sections
    
    def get_profesor_sections_summary(self, profesor_id: int) -> Dict:
        """Get summary statistics for a professor's sections"""
        sections = self.get_profesor_sections(profesor_id)
        
        if not sections:
            return {
                'total_sections': 0,
                'total_credits': 0,
                'departments': [],
                'materias': [],
                'total_students': 0,
                'total_capacity': 0,
                'total_sessions': 0,
                'campus_list': [],
                'academic_levels': []
            }
        
        # Calculate summary
        unique_materias = set()
        departments = set()
        campus_set = set()
        levels_set = set()
        total_credits = 0
        total_students = 0
        total_capacity = 0
        total_sessions = 0
        
        for section in sections:
            unique_materias.add(section['materia_codigo'])
            departments.add(section['departamento'])
            campus_set.add(section['campus'])
            levels_set.add(section['nivel'])
            
            total_credits += section['creditos']
            total_students += section['inscritos']
            total_capacity += section['cupo']
            total_sessions += section['num_sessions']
        
        return {
            'total_sections': len(sections),
            'total_credits': total_credits,
            'departments': sorted(list(departments)),
            'materias': sorted(list(unique_materias)),
            'total_students': total_students,
            'total_capacity': total_capacity,
            'total_sessions': total_sessions,
            'campus_list': sorted(list(campus_set)),
            'academic_levels': sorted(list(levels_set))
        }
    
    
    
    def get_departamentos_with_professor_stats(self) -> List[Dict]:
        """Get all departments with professor and section statistics"""
        results = self.execute_query(
            """SELECT 
                d.nombre as departamento_nombre,
                COUNT(DISTINCT pd.profesor_id) as num_professors,
                COUNT(DISTINCT sec.NRC) as num_sections,
                COUNT(DISTINCT ses.id) as num_sessions,
                SUM(sec.inscritos) as total_students,
                SUM(sec.cupo) as total_capacity
            FROM Departamento d
            LEFT JOIN ProfesorDepartamento pd ON d.nombre = pd.departamento_nombre
            LEFT JOIN Profesor p ON pd.profesor_id = p.id
            LEFT JOIN SeccionProfesor sp ON p.id = sp.profesor_id
            LEFT JOIN Seccion sec ON sp.seccion_NRC = sec.NRC
            LEFT JOIN Sesion ses ON sec.NRC = ses.seccion_NRC
            GROUP BY d.nombre
            ORDER BY d.nombre"""
        )
        
        departamentos = []
        for row in results:
            departamentos.append({
                'nombre': row[0],
                'num_professors': row[1] if row[1] else 0,
                'num_sections': row[2] if row[2] else 0,
                'num_sessions': row[3] if row[3] else 0,
                'total_students': row[4] if row[4] else 0,
                'total_capacity': row[5] if row[5] else 0
            })
        
        return departamentos
    
    def get_departamento_summary(self, departamento_nombre: str) -> Dict:
        """Get comprehensive summary statistics for a department"""
        # Get basic stats
        result = self.execute_query(
            """SELECT 
                COUNT(DISTINCT pd.profesor_id) as num_professors,
                COUNT(DISTINCT m.codigo) as num_materias,
                COUNT(DISTINCT sec.NRC) as num_sections,
                COUNT(DISTINCT ses.id) as num_sessions,
                SUM(sec.inscritos) as total_students,
                SUM(sec.cupo) as total_capacity,
                SUM(m.creditos) as total_credits
            FROM Departamento d
            LEFT JOIN ProfesorDepartamento pd ON d.nombre = pd.departamento_nombre
            LEFT JOIN Materia m ON d.nombre = m.departamento_nombre
            LEFT JOIN Seccion sec ON m.codigo = sec.materia_codigo
            LEFT JOIN Sesion ses ON sec.NRC = ses.seccion_NRC
            WHERE d.nombre = ?
            GROUP BY d.nombre""",
            (departamento_nombre,),
            fetch_one=True
        )
        
        if not result:
            return {
                'num_professors': 0,
                'num_materias': 0,
                'num_sections': 0,
                'num_sessions': 0,
                'total_students': 0,
                'total_capacity': 0,
                'total_credits': 0,
                'academic_levels': [],
                'campus_list': []
            }
        
        # Get academic levels and campus info
        levels_result = self.execute_query(
            """SELECT DISTINCT m.nivel 
            FROM Materia m 
            WHERE m.departamento_nombre = ? AND m.nivel IS NOT NULL""",
            (departamento_nombre,)
        )
        
        campus_result = self.execute_query(
            """SELECT DISTINCT m.campus 
            FROM Materia m 
            WHERE m.departamento_nombre = ? AND m.campus IS NOT NULL""",
            (departamento_nombre,)
        )
        
        return {
            'num_professors': result[0] if result[0] else 0,
            'num_materias': result[1] if result[1] else 0,
            'num_sections': result[2] if result[2] else 0,
            'num_sessions': result[3] if result[3] else 0,
            'total_students': result[4] if result[4] else 0,
            'total_capacity': result[5] if result[5] else 0,
            'total_credits': result[6] if result[6] else 0,
            'academic_levels': [row[0] for row in levels_result] if levels_result else [],
            'campus_list': [row[0] for row in campus_result] if campus_result else []
        }
        
    def get_profesores_by_departamento_with_stats(self, departamento: str) -> List[Dict]:
        """Get professors by department with session and section statistics"""
        results = self.execute_query(
            """SELECT DISTINCT p.id, p.nombres, p.apellidos, p.tipo,
                      COUNT(DISTINCT sp.sesion_id) as num_sessions,
                      COUNT(DISTINCT scp.seccion_NRC) as num_sections
               FROM Profesor p
               JOIN ProfesorDepartamento pd ON p.id = pd.profesor_id
               LEFT JOIN SesionProfesor sp ON p.id = sp.profesor_id
               LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
               WHERE pd.departamento_nombre = ? 
               GROUP BY p.id, p.nombres, p.apellidos, p.tipo
               ORDER BY p.apellidos, p.nombres""",
            (departamento,)
        )
        
        profesores = []
        for row in results:
            profesores.append({
                'id': row[0],
                'nombres': row[1],
                'apellidos': row[2],
                'tipo': row[3],
                'full_name': f"{row[1]} {row[2]}",
                'num_sessions': row[4] if row[4] else 0,
                'num_sections': row[5] if row[5] else 0
            })
        
        return profesores
    
    
    
    
    def get_profesores_by_departamento_with_filters(self, departamento: str, tipo_filter: str = None, 
                                                   nivel_filter: str = None, name_filter: str = "") -> List[Dict]:
        """Get professors by department with type and academic level filters"""
        
        # Base query with joins for statistics
        base_query = """
            SELECT DISTINCT p.id, p.nombres, p.apellidos, p.tipo, p.subcategoria,
                   COUNT(DISTINCT sp.sesion_id) as num_sessions,
                   COUNT(DISTINCT scp.seccion_NRC) as num_sections
            FROM Profesor p
            JOIN ProfesorDepartamento pd ON p.id = pd.profesor_id
            LEFT JOIN SesionProfesor sp ON p.id = sp.profesor_id
            LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
        """
        
        # Add joins for level filtering if needed
        if nivel_filter and nivel_filter != "Todos los niveles":
            base_query += """
                LEFT JOIN Seccion sec ON scp.seccion_NRC = sec.NRC
                LEFT JOIN Materia m ON sec.materia_codigo = m.codigo
            """
        
        # WHERE conditions
        conditions = ["pd.departamento_nombre = ?"]
        params = [departamento]
        
        # Type filter (Planta/Cátedra) - CORRECTED LOGIC
        if tipo_filter and tipo_filter != "Todos los tipos":
            if tipo_filter == "Planta":
                # Planta are those whose tipo is NOT 'CÁTEDRA'
                conditions.append("(p.tipo != 'CÁTEDRA' OR p.tipo IS NULL)")
            elif tipo_filter == "Cátedra":
                # Cátedra are those whose tipo is exactly 'CÁTEDRA'
                conditions.append("p.tipo = 'CÁTEDRA'")
        
        # Level filter (Pregrado/Magister)
        if nivel_filter and nivel_filter != "Todos los niveles":
            conditions.append("m.nivel = ?")
            params.append(nivel_filter.upper())
        
        # Name filter
        if name_filter:
            conditions.append("(LOWER(p.nombres) LIKE ? OR LOWER(p.apellidos) LIKE ?)")
            filter_param = f"%{name_filter.lower()}%"
            params.extend([filter_param, filter_param])
        
        # Combine query
        query = base_query + " WHERE " + " AND ".join(conditions)
        query += " GROUP BY p.id, p.nombres, p.apellidos, p.tipo, p.subcategoria"
        query += " ORDER BY p.apellidos, p.nombres"
        
        try:
            results = self.execute_query(query, tuple(params))
            
            profesores = []
            for row in results:
                # Determine actual type based on tipo field - CORRECTED LOGIC
                actual_tipo = "Cátedra" if row[3] == "CÁTEDRA" else "Planta"
                
                profesores.append({
                    'id': row[0],
                    'nombres': row[1],
                    'apellidos': row[2],
                    'tipo': row[3],  # Original tipo from database
                    'subcategoria': row[4],
                    'actual_tipo': actual_tipo,  # Determined tipo
                    'full_name': f"{row[1]} {row[2]}",
                    'num_sessions': row[5] if row[5] else 0,
                    'num_sections': row[6] if row[6] else 0
                })
            
            return profesores
            
        except Exception as e:
            print(f"Error in filtered query: {e}")
            return []
    
    def get_available_academic_levels_for_department(self, departamento: str) -> List[str]:
        """Get available academic levels for professors in a department"""
        results = self.execute_query(
            """SELECT DISTINCT m.nivel
               FROM Materia m
               JOIN Seccion sec ON m.codigo = sec.materia_codigo
               JOIN SeccionProfesor sp ON sec.NRC = sp.seccion_NRC
               JOIN Profesor p ON sp.profesor_id = p.id
               JOIN ProfesorDepartamento pd ON p.id = pd.profesor_id
               WHERE pd.departamento_nombre = ? AND m.nivel IS NOT NULL
               ORDER BY m.nivel""",
            (departamento,)
        )
        
        return [row[0] for row in results if row[0]]
    
    def get_professor_type_stats_for_department(self, departamento: str) -> Dict:
        """Get professor type statistics for a department - CORRECTED LOGIC"""
        results = self.execute_query(
            """SELECT 
                   SUM(CASE WHEN p.tipo != 'CÁTEDRA' OR p.tipo IS NULL THEN 1 ELSE 0 END) as planta_count,
                   SUM(CASE WHEN p.tipo = 'CÁTEDRA' THEN 1 ELSE 0 END) as catedra_count,
                   COUNT(*) as total_count
               FROM Profesor p
               JOIN ProfesorDepartamento pd ON p.id = pd.profesor_id
               WHERE pd.departamento_nombre = ?""",
            (departamento,),
            fetch_one=True
        )
        
        if results:
            return {
                'planta': results[0] or 0,
                'catedra': results[1] or 0,
                'total': results[2] or 0
            }
        return {'planta': 0, 'catedra': 0, 'total': 0}
        
        # Add these methods to the DatabaseManager class in database.py:
    
    def get_all_profesores_with_materia_stats(self) -> List[Dict]:
        """Get all professors with their materia statistics"""
        results = self.execute_query(
            """SELECT p.id, p.nombres, p.apellidos, p.tipo,
                      COUNT(DISTINCT m.codigo) as num_materias,
                      COUNT(DISTINCT scp.seccion_NRC) as num_sections
               FROM Profesor p
               LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
               LEFT JOIN Seccion sec ON scp.seccion_NRC = sec.NRC
               LEFT JOIN Materia m ON sec.materia_codigo = m.codigo
               GROUP BY p.id, p.nombres, p.apellidos, p.tipo
               ORDER BY p.apellidos, p.nombres"""
        )
        
        profesores = []
        for row in results:
            profesor_id = row[0]
            
            # Get departments separately to avoid duplicates
            dept_results = self.execute_query(
                """SELECT DISTINCT departamento_nombre 
                   FROM ProfesorDepartamento 
                   WHERE profesor_id = ? 
                   ORDER BY departamento_nombre""",
                (profesor_id,)
            )
            
            # Create clean department list
            departamentos = [dept[0] for dept in dept_results]
            departamentos_str = ', '.join(departamentos) if departamentos else 'Sin departamento'
            
            profesores.append({
                'id': row[0],
                'nombres': row[1],
                'apellidos': row[2],
                'tipo': row[3],
                'departamentos': departamentos_str,
                'full_name': f"{row[1]} {row[2]}",
                'num_materias': row[4],
                'num_sections': row[5]
            })
        
        return profesores
    
    def get_profesor_materias(self, profesor_id: int) -> List[Dict]:
        """Get all materias for a specific professor with detailed information"""
        results = self.execute_query(
            """SELECT DISTINCT
                m.codigo,
                m.nombre,
                m.creditos,
                m.nivel,
                m.calificacion,
                m.campus,
                m.periodo,
                m.departamento_nombre,
                COUNT(DISTINCT sec.NRC) as num_sections,
                SUM(sec.inscritos) as total_students,
                SUM(sec.cupo) as total_capacity
            FROM Materia m
            JOIN Seccion sec ON m.codigo = sec.materia_codigo
            JOIN SeccionProfesor sp ON sec.NRC = sp.seccion_NRC
            WHERE sp.profesor_id = ?
            GROUP BY m.codigo, m.nombre, m.creditos, m.nivel, m.calificacion, 
                     m.campus, m.periodo, m.departamento_nombre
            ORDER BY m.departamento_nombre, m.codigo""",
            (profesor_id,)
        )
        
        materias = []
        for row in results:
            materias.append({
                'codigo': row[0],
                'nombre': row[1],
                'creditos': row[2] if row[2] else 0,
                'nivel': row[3],
                'calificacion': row[4],
                'campus': row[5],
                'periodo': row[6],
                'departamento': row[7],
                'num_sections': row[8] if row[8] else 0,
                'total_students': row[9] if row[9] else 0,
                'total_capacity': row[10] if row[10] else 0
            })
        
        return materias
    
    def get_profesor_materias_summary(self, profesor_id: int) -> Dict:
        """Get summary statistics for a professor's materias"""
        materias = self.get_profesor_materias(profesor_id)
        
        if not materias:
            return {
                'total_materias': 0,
                'total_sections': 0,
                'total_credits': 0,
                'total_students': 0,
                'total_capacity': 0,
                'departments': [],
                'academic_levels': [],
                'campus_list': [],
                'grading_modes': []
            }
        
        # Calculate summary
        departments = set()
        levels_set = set()
        campus_set = set()
        grading_set = set()
        total_sections = 0
        total_credits = 0
        total_students = 0
        total_capacity = 0
        
        for materia in materias:
            departments.add(materia['departamento'])
            if materia['nivel']:
                levels_set.add(materia['nivel'])
            if materia['campus']:
                campus_set.add(materia['campus'])
            if materia['calificacion']:
                grading_set.add(materia['calificacion'])
            
            total_sections += materia['num_sections']
            total_credits += materia['creditos']
            total_students += materia['total_students']
            total_capacity += materia['total_capacity']
        
        return {
            'total_materias': len(materias),
            'total_sections': total_sections,
            'total_credits': total_credits,
            'total_students': total_students,
            'total_capacity': total_capacity,
            'departments': sorted(list(departments)),
            'academic_levels': sorted(list(levels_set)),
            'campus_list': sorted(list(campus_set)),
            'grading_modes': sorted(list(grading_set))
        }
    
    # ==================== MATERIA OPERATIONS ====================
    
    def create_materia(self, codigo: str, nombre: str, creditos: int, nivel: str, 
                      calificacion: str, campus: str, periodo: str, departamento_nombre: str,
                      semanas: int = 16) -> bool:
        """Create new materia"""
        try:
            
            nivel_numerico = self.extract_nivel_numerico(codigo)
            self.execute_query(
                """INSERT INTO Materia (codigo, nombre, creditos, nivel, nivel_numerico,
                calificacion, campus, periodo, semanas, departamento_nombre) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (codigo.strip(), nombre.strip(), creditos, nivel.strip(), nivel_numerico,
                 calificacion.strip(), campus.strip(), periodo.strip(), semanas, departamento_nombre)
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Already exists
        except Exception as e:
            print(f"Error creating materia: {e}")
            return False
    
    def get_materias_by_departamento(self, departamento: str) -> List[Dict]:
        """Get materias by department"""
        results = self.execute_query(
            """SELECT m.codigo, m.nombre, m.creditos, m.nivel, m.nivel_numerico, m.calificacion,
                      m.campus, m.periodo, m.semanas,
                      COUNT(s.NRC) as num_sections
               FROM Materia m
               LEFT JOIN Seccion s ON m.codigo = s.materia_codigo
               WHERE m.departamento_nombre = ?
               GROUP BY m.codigo, m.nombre, m.creditos, m.nivel, m.nivel_numerico, m.calificacion,
                        m.campus, m.periodo, m.semanas
               ORDER BY m.nivel_numerico, m.codigo""",
            (departamento,)
        )
        return [
            {
                'codigo': row[0],
                'nombre': row[1],
                'creditos': row[2],
                'nivel': row[3],
                'nivel_numerico': row[4],
                'calificacion': row[5],
                'campus': row[6],
                'periodo': row[7],
                'semanas': row[8],
                'num_sections': row[9]
            }
            for row in results
        ]
    
    def get_all_materias(self) -> List[Dict]:
        """Get all materias"""
        results = self.execute_query(
            """SELECT m.codigo, m.nombre, m.creditos, m.nivel, m.nivel_numerico, m.calificacion, 
                      m.campus, m.periodo, m.semanas, m.departamento_nombre,
                      COUNT(s.NRC) as num_sections
               FROM Materia m
               LEFT JOIN Seccion s ON m.codigo = s.materia_codigo
               GROUP BY m.codigo, m.nombre, m.creditos, m.nivel, m.nivel_numerico, m.calificacion, 
                        m.campus, m.periodo, m.semanas, m.departamento_nombre
               ORDER BY m.departamento_nombre, m.nivel_numerico, m.codigo"""
        )
        return [
            {
                'codigo': row[0],
                'nombre': row[1],
                'creditos': row[2],
                'nivel': row[3],
                'nivel_numerico': row[4],
                'calificacion': row[5],
                'campus': row[6],
                'periodo': row[7],
                'semanas': row[9],
                'departamento_nombre': row[9],
                'num_sections':row[10]
            }
            for row in results
        ]
    
    def get_materia_by_codigo(self, codigo: str) -> Optional[Dict]:
        """Get materia by codigo"""
        result = self.execute_query(
            """SELECT codigo, nombre, creditos, nivel, nivel_numerico, calificacion, 
                      campus, periodo, semanas, departamento_nombre
               FROM Materia WHERE codigo = ?""",
            (codigo,),
            fetch_one=True
        )
        if result:
            return {
                'codigo': result[0],
                'nombre': result[1],
                'creditos': result[2],
                'nivel': result[3],
                'nivel_numerico': result[4],
                'calificacion': result[5],
                'campus': result[6],
                'periodo': result[7],
                'semanas': result[8],
                'num_sections': result[9]
            }
        return None
    
    def update_materia(self, codigo: str, nombre: str, creditos: int, nivel: str, 
                      calificacion: str, campus: str, periodo: str, semanas:int = 16) -> bool:
        """Update materia information"""
        try:
            nivel_numerico = self.extract_nivel_numerico(codigo)
            count = self.execute_query(
                """UPDATE Materia SET nombre = ?, creditos = ?, nivel = ?, nivel_numerico = ?, 
                   calificacion = ?, campus = ?, periodo = ?, semanas = ?, WHERE codigo = ?""",
                (nombre.strip(), creditos, nivel.strip(), nivel_numerico, calificacion.strip(), 
                 campus.strip(), periodo.strip(), semanas, codigo)
            )
            return count > 0
        except Exception as e:
            print(f"Error updating materia: {e}")
            return False
    
    def get_materia_sections(self, materia_codigo: str) -> List[Dict]:
        """Get all sections for a specific materia with detailed information - UPDATED to include semanas"""
        results = self.execute_query(
            """SELECT 
                sec.NRC,
                sec.indicador,
                sec.cupo,
                sec.inscritos,
                sec.cupoDisponible,
                m.codigo as materia_codigo,
                m.nombre as materia_nombre,
                m.creditos,
                m.nivel,
                m.calificacion,
                m.campus,
                m.periodo,
                m.semanas,
                m.departamento_nombre,
                COUNT(ses.id) as num_sessions,
                GROUP_CONCAT(DISTINCT p.nombres || ' ' || p.apellidos) as profesores
            FROM Seccion sec
            JOIN Materia m ON sec.materia_codigo = m.codigo
            LEFT JOIN Sesion ses ON sec.NRC = ses.seccion_NRC
            LEFT JOIN SeccionProfesor sp ON sec.NRC = sp.seccion_NRC
            LEFT JOIN Profesor p ON sp.profesor_id = p.id
            WHERE sec.materia_codigo = ?
            GROUP BY sec.NRC, sec.indicador, sec.cupo, sec.inscritos, sec.cupoDisponible,
                     m.codigo, m.nombre, m.creditos, m.nivel, m.calificacion, 
                     m.campus, m.periodo, m.semanas, m.departamento_nombre
            ORDER BY sec.NRC""",
            (materia_codigo,)
        )
        
        sections = []
        for row in results:
            sections.append({
                'nrc': row[0],
                'indicador': row[1] if row[1] else '',
                'cupo': row[2] if row[2] else 0,
                'inscritos': row[3] if row[3] else 0,
                'cupo_disponible': row[4] if row[4] else 0,
                'materia_codigo': row[5],
                'materia_nombre': row[6],
                'creditos': row[7] if row[7] else 0,
                'nivel': row[8] if row[8] else '',
                'calificacion': row[9] if row[9] else '',
                'campus': row[10] if row[10] else '',
                'periodo': row[11] if row[11] else '',
                'semanas': row[12] if row[12] else 16,  # NEW: Include semanas
                'departamento': row[13],
                'num_sessions': row[14] if row[14] else 0,
                'profesores': row[15] if row[15] else 'Sin asignar'
            })
        
        return sections
    
    def get_materia_sections_summary(self, materia_codigo: str) -> Dict:
        """Get summary statistics for a materia's sections"""
        sections = self.get_materia_sections(materia_codigo)
        
        if not sections:
            return {
                'total_sections': 0,
                'total_students': 0,
                'total_capacity': 0,
                'total_sessions': 0,
                'professors': [],
                'campus_list': [],
                'academic_level': '',
                'credits': 0,
                'grading_mode': '',
                'department': '',
                'period': ''
            }
        
        # Calculate summary
        professors = set()
        campus_set = set()
        total_students = 0
        total_capacity = 0
        total_sessions = 0
        
        # Get materia details from first section
        first_section = sections[0]
        
        for section in sections:
            total_students += section['inscritos']
            total_capacity += section['cupo']
            total_sessions += section['num_sessions']
            campus_set.add(section['campus'])
            
            # Parse professors for this section
            if section['profesores'] and section['profesores'] != 'Sin asignar':
                for prof in section['profesores'].split(','):
                    professors.add(prof.strip())
        
        return {
            'total_sections': len(sections),
            'total_students': total_students,
            'total_capacity': total_capacity,
            'total_sessions': total_sessions,
            'professors': sorted(list(professors)),
            'campus_list': sorted(list(campus_set)),
            'academic_level': first_section['nivel'],
            'credits': first_section['creditos'],
            'grading_mode': first_section['calificacion'],
            'department': first_section['departamento'],
            'period': first_section['periodo']
        }
    
    def get_all_materias_with_stats(self) -> List[Dict]:
        """Get all materias with section and session statistics"""
        results = self.execute_query(
            """SELECT 
                m.codigo,
                m.nombre,
                m.creditos,
                m.nivel,
                m.departamento_nombre,
                m.campus,
                m.periodo,
                COUNT(DISTINCT sec.NRC) as num_sections,
                COUNT(DISTINCT ses.id) as num_sessions,
                SUM(sec.inscritos) as total_students,
                SUM(sec.cupo) as total_capacity
            FROM Materia m
            LEFT JOIN Seccion sec ON m.codigo = sec.materia_codigo
            LEFT JOIN Sesion ses ON sec.NRC = ses.seccion_NRC
            GROUP BY m.codigo, m.nombre, m.creditos, m.nivel, m.departamento_nombre, m.campus, m.periodo
            ORDER BY m.departamento_nombre, m.codigo"""
        )
        
        materias = []
        for row in results:
            materias.append({
                'codigo': row[0],
                'nombre': row[1],
                'creditos': row[2] if row[2] else 0,
                'nivel': row[3] if row[3] else '',
                'departamento': row[4],
                'campus': row[5] if row[5] else '',
                'periodo': row[6] if row[6] else '',
                'num_sections': row[7] if row[7] else 0,
                'num_sessions': row[8] if row[8] else 0,
                'total_students': row[9] if row[9] else 0,
                'total_capacity': row[10] if row[10] else 0,
                'display_name': f"{row[0]} - {row[1]}"
            })
        
        return materias
    
    def extract_nivel_numerico(self, codigo: str) -> Optional[int]:
        """
        Extract numeric level from materia code
        Examples: ISIS-1221 -> 1, ISIS-3001 -> 3, MBIO-2010 -> 2
        """
        import re
        
        if not codigo:
            return None
        
        # Look for pattern: letters-numbers or letters numbers
        # Extract the first digit from the numeric part
        patterns = [
            r'[A-Z]+-(\d)',  # ISIS-1221 -> 1
            r'[A-Z]+\s+(\d)',  # ISIS 1221 -> 1
            r'[A-Z]+(\d)',     # ISIS1221 -> 1
            r'(\d)',           # Any first digit
        ]
        
        for pattern in patterns:
            match = re.search(pattern, codigo.upper())
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None
    # ==================== SECCION OPERATIONS ====================
    
    def create_seccion(self, nrc: int, indicador: str, cupo: int, materia_codigo: str, 
                      profesor_ids: List[int] = None, lista_cruzada: str = None) -> bool:
        """Create new seccion"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if NRC already exists
            cursor.execute("SELECT COUNT(*) FROM Seccion WHERE NRC = ?", (nrc,))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False  # NRC already exists
            
            if profesor_ids is None:
                profesor_ids = []
            
            cupo_disponible = cupo  # Initially all spots are available
            profesor_dedicaciones = {}
            for profesor_id in profesor_ids:
                profesor_dedicaciones[str(profesor_id)]= 0
            
            profesor_dedicaciones_json = json.dumps(profesor_dedicaciones)
            
            cursor.execute(
                """INSERT INTO Seccion (NRC, indicador, cupo, inscritos, cupoDisponible,
                                        lista_cruzada, materia_codigo, profesor_dedicaciones)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (nrc, indicador.strip(), cupo, 0, cupo_disponible,
                 lista_cruzada.strip() if lista_cruzada else None, materia_codigo, profesor_dedicaciones_json)
            )
            
            # Insert into SeccionProfesor junction table
            for profesor_id in profesor_ids:
                cursor.execute(
                    "INSERT INTO SeccionProfesor (seccion_NRC, profesor_id) VALUES (?, ?)",
                    (nrc, profesor_id)
                )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating seccion: {e}")
            return False
    
    def get_secciones_by_materia(self, materia_codigo: str) -> List[Dict]:
        """Get sections by materia"""
        results = self.execute_query(
            """SELECT s.NRC, s.indicador, s.cupo, s.inscritos, s.cupoDisponible,
                      COUNT(ses.id) as num_sessions
               FROM Seccion s
               LEFT JOIN Sesion ses ON s.NRC = ses.seccion_NRC
               WHERE s.materia_codigo = ?
               GROUP BY s.NRC, s.indicador, s.cupo, s.inscritos, s.cupoDisponible
               ORDER BY s.NRC""",
            (materia_codigo,)
        )
        return [
            {
                'nrc': row[0],
                'indicador': row[1],
                'cupo': row[2],
                'inscritos': row[3],
                'cupo_disponible': row[4],
                'num_sessions': row[5]
            }
            for row in results
        ]
    
    def get_all_secciones(self) -> List[Dict]:
        """Get all sections with materia info"""
        results = self.execute_query(
            """SELECT s.NRC, s.indicador, s.cupo, s.inscritos, s.cupoDisponible, 
                      s.lista_cruzada, s.materia_codigo, m.nombre as materia_nombre, m.departamento_nombre,
                      COUNT(ses.id) as num_sessions
               FROM Seccion s
               JOIN Materia m ON s.materia_codigo = m.codigo
               LEFT JOIN Sesion ses ON s.NRC = ses.seccion_NRC
               GROUP BY s.NRC, s.indicador, s.cupo, s.inscritos, s.cupoDisponible, 
                        s.lista_cruzada, s.materia_codigo, m.nombre, m.departamento_nombre
               ORDER BY m.departamento_nombre, s.materia_codigo, s.NRC"""
        )
        return [
            {
                'nrc': row[0],
                'indicador': row[1],
                'cupo': row[2],
                'inscritos': row[3],
                'cupo_disponible': row[4],
                'lista_cruzada': row[5],
                'materia_codigo': row[6],
                'materia_nombre': row[7],
                'departamento': row[8],
                'num_sessions': row[9]
            }
            for row in results
        ]
    
    def get_seccion_by_nrc(self, nrc: int) -> Optional[Dict]:
        """Get section by NRC"""
        result = self.execute_query(
            """SELECT s.NRC, s.indicador, s.cupo, s.inscritos, s.cupoDisponible, 
                      s.lista_cruzada, s.materia_codigo, m.nombre as materia_nombre, m.departamento_nombre
               FROM Seccion s
               JOIN Materia m ON s.materia_codigo = m.codigo
               WHERE s.NRC = ?""",
            (nrc,),
            fetch_one=True
        )
        if result:
            return {
                'nrc': result[0],
                'indicador': result[1],
                'cupo': result[2],
                'inscritos': result[3],
                'cupo_disponible': result[4],
                'lista_cruzada': result[5],
                'materia_codigo': result[6],
                'materia_nombre': result[7],
                'departamento': result[8]
            }
        return None
    
    def update_seccion(self, nrc: int, indicador: str, cupo: int, inscritos: int,
                       lista_cruzada: str = None) -> bool:
        """Update section information"""
        try:
            cupo_disponible = cupo - inscritos
            count = self.execute_query(
                """UPDATE Seccion SET indicador = ?, cupo = ?, inscritos = ?, cupoDisponible = ?, lista_cruzada = ?
                   WHERE NRC = ?""",
                (indicador.strip(), cupo, inscritos, cupo_disponible, lista_cruzada.strip() if lista_cruzada else None, nrc)
            )
            return count > 0
        except Exception as e:
            print(f"Error updating seccion: {e}")
            return False
        
    def _update_section_professors(self, nrc: int, profesor_ids: List[int]):
        """Update professors for a section"""
        try:
            conn = self.get_connection()
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
            
            # UPDATED: Update profesor_dedicaciones JSON field (keep existing dedicaciones, add new professors with 0%)
            cursor.execute("SELECT profesor_dedicaciones FROM Seccion WHERE NRC = ?", (nrc,))
            current_dedicaciones_json = cursor.fetchone()[0]
            
            if current_dedicaciones_json:
                current_dedicaciones = json.loads(current_dedicaciones_json)
            else:
                current_dedicaciones = {}
            
            # Add new professors with 0% dedication (don't overwrite existing)
            for prof_id in profesor_ids:
                if str(prof_id) not in current_dedicaciones:
                    current_dedicaciones[str(prof_id)] = 0
            
            # Update section with new dedicaciones
            cursor.execute(
                "UPDATE Seccion SET profesor_dedicaciones = ? WHERE NRC = ?",
                (json.dumps(current_dedicaciones), nrc)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error updating section professors: {e}")
            
    def get_seccion_profesor_dedicaciones(self, nrc: int) -> Dict[int, int]:
        """Get professor dedicaciones for a section"""
        try:
            result = self.execute_query(
                "SELECT profesor_dedicaciones FROM Seccion WHERE NRC = ?",
                (nrc,),
                fetch_one=True
            )
            
            if result and result[0]:
                dedicaciones_json = json.loads(result[0])
                # Convert string keys back to integers
                return {int(prof_id): dedicacion for prof_id, dedicacion in dedicaciones_json.items()}
            return {}
        except Exception as e:
            print(f"Error getting section dedicaciones: {e}")
            return {}
    
    
    def get_profesor_dedicaciones_by_seccion(self, profesor_id: int) -> List[Dict]:
        """Get all sections and dedicaciones for a specific professor"""
        try:
            results = self.execute_query(
                """SELECT sec.NRC, sec.profesor_dedicaciones, m.codigo, m.nombre
                   FROM Seccion sec
                   JOIN SeccionProfesor sp ON sec.NRC = sp.seccion_NRC
                   JOIN Materia m ON sec.materia_codigo = m.codigo
                   WHERE sp.profesor_id = ?
                   ORDER BY m.codigo""",
                (profesor_id,)
            )
            
            dedicaciones = []
            for row in results:
                nrc = row[0]
                dedicaciones_json = row[1]
                materia_codigo = row[2]
                materia_nombre = row[3]
                
                # Parse dedicaciones JSON
                if dedicaciones_json:
                    dedicaciones_dict = json.loads(dedicaciones_json)
                    dedicacion = dedicaciones_dict.get(str(profesor_id), 0)
                else:
                    dedicacion = 0
                
                dedicaciones.append({
                    'nrc': nrc,
                    'materia_codigo': materia_codigo,
                    'materia_nombre': materia_nombre,
                    'dedicacion': dedicacion
                })
            
            return dedicaciones
        except Exception as e:
            print(f"Error getting profesor dedicaciones: {e}")
            return []
        
    def get_sections_with_dedication_info(self) -> List[Dict]:
        """Get all sections with current dedication information"""
        results = self.execute_query(
            """SELECT 
                sec.NRC,
                sec.indicador,
                sec.cupo,
                sec.inscritos,
                sec.profesor_dedicaciones,
                m.codigo as materia_codigo,
                m.nombre as materia_nombre,
                m.departamento_nombre
            FROM Seccion sec
            JOIN Materia m ON sec.materia_codigo = m.codigo
            ORDER BY m.departamento_nombre, m.codigo, sec.NRC"""
        )
        
        sections = []
        for row in results:
            # Parse dedication JSON
            dedicaciones_json = row[4]
            dedicaciones = {}
            total_dedicacion = 0
            
            if dedicaciones_json:
                try:
                    dedicaciones_dict = json.loads(dedicaciones_json)
                    # Convert back to int keys and calculate total
                    for prof_id_str, dedicacion in dedicaciones_dict.items():
                        prof_id = int(prof_id_str)
                        dedicaciones[prof_id] = dedicacion
                        total_dedicacion += dedicacion
                except:
                    pass
            
            sections.append({
                'nrc': row[0],
                'indicador': row[1],
                'cupo': row[2],
                'inscritos': row[3],
                'dedicaciones': dedicaciones,
                'total_dedicacion': total_dedicacion,
                'materia_codigo': row[5],
                'materia_nombre': row[6],
                'departamento': row[7]
            })
        
        return sections
    
    def get_professor_dedication_summary(self) -> List[Dict]:
        """Get summary of professor dedication across all sections"""
        results = self.execute_query(
            """SELECT 
                p.id,
                p.nombres,
                p.apellidos,
                COUNT(DISTINCT sp.seccion_NRC) as total_sections
            FROM Profesor p
            LEFT JOIN SeccionProfesor sp ON p.id = sp.profesor_id
            GROUP BY p.id, p.nombres, p.apellidos
            ORDER BY p.apellidos, p.nombres"""
        )
        
        professors = []
        for row in results:
            profesor_id = row[0]
            
            # Get dedication details for this professor
            dedicaciones = self.get_profesor_dedicaciones_by_seccion(profesor_id)
            total_dedicacion = sum(d['dedicacion'] for d in dedicaciones)
            
            professors.append({
                'id': profesor_id,
                'nombres': row[1],
                'apellidos': row[2],
                'full_name': f"{row[1]} {row[2]}",
                'total_sections': row[3],
                'total_dedicacion': total_dedicacion,
                'sections_with_dedicacion': len([d for d in dedicaciones if d['dedicacion'] > 0]),
                'dedicaciones': dedicaciones
            })
        
        return professors
    
    def get_section_professors(self, nrc: int) -> List[Dict]:
        """Get all professors assigned to a specific section"""
        try:
            query = """
                SELECT p.id, p.nombres, p.apellidos, p.tipo
                FROM Profesor p
                JOIN SeccionProfesor sp ON p.id = sp.profesor_id
                WHERE sp.seccion_NRC = ?
                ORDER BY p.apellidos, p.nombres
            """
            results = self.execute_query(query, (nrc,))
            
            professors = []
            for row in results:
                professors.append({
                    'id': row[0],
                    'nombres': row[1],
                    'apellidos': row[2],
                    'tipo': row[3],
                    'full_name': f"{row[1]} {row[2]}"
                })
            
            return professors
            
        except Exception as e:
            print(f"Error getting section professors: {e}")
            return []
    
    def get_seccion_profesor_dedicaciones(self, nrc: int) -> Dict[int, int]:
        """Get current professor dedicaciones for a section - FIXED to handle both list and dict JSON"""
        try:
            result = self.execute_query(
                "SELECT profesor_dedicaciones FROM Seccion WHERE NRC = ?",
                (nrc,),
                fetch_one=True
            )
            
            if not result or not result[0]:
                return {}
            
            dedicaciones_json = result[0]
            
            # Handle different data types
            if isinstance(dedicaciones_json, str):
                try:
                    dedicaciones_data = json.loads(dedicaciones_json)
                except json.JSONDecodeError:
                    print(f"Invalid JSON in profesor_dedicaciones for NRC {nrc}")
                    return {}
            else:
                dedicaciones_data = dedicaciones_json
            
            # FIXED: Handle both list and dict formats
            if isinstance(dedicaciones_data, list):
                # If it's a list, it might be empty or contain professor IDs
                # Convert to dict format with 0% dedication
                if not dedicaciones_data:
                    return {}
                
                # If list contains professor IDs, convert to dict
                result_dict = {}
                for item in dedicaciones_data:
                    if isinstance(item, (int, str)):
                        try:
                            prof_id = int(item)
                            result_dict[prof_id] = 0  # Default to 0% dedication
                        except (ValueError, TypeError):
                            continue
                return result_dict
                
            elif isinstance(dedicaciones_data, dict):
                # Handle normal dict format
                result_dict = {}
                for key, value in dedicaciones_data.items():
                    try:
                        prof_id = int(key)
                        dedicacion = int(value) if value is not None else 0
                        result_dict[prof_id] = dedicacion
                    except (ValueError, TypeError):
                        print(f"Invalid profesor_dedicaciones data: {key}={value}")
                        continue
                return result_dict
            
            else:
                print(f"Unexpected data type for profesor_dedicaciones: {type(dedicaciones_data)}")
                return {}
                
        except Exception as e:
            print(f"Error getting section dedicaciones: {e}")
            return {}
    
    def update_seccion_profesor_dedicaciones(self, nrc: int, dedicaciones: Dict[int, int]) -> bool:
        """Update professor dedicaciones for a section - ENSURES dict format"""
        try:
            # FIXED: Always ensure we're storing a dict format, not a list
            if not isinstance(dedicaciones, dict):
                print(f"Warning: Expected dict for dedicaciones, got {type(dedicaciones)}")
                return False
            
            # Convert dedicaciones dict to JSON string with string keys
            dedicaciones_json = json.dumps({str(k): v for k, v in dedicaciones.items()})
            
            result = self.execute_query(
                "UPDATE Seccion SET profesor_dedicaciones = ? WHERE NRC = ?",
                (dedicaciones_json, nrc),
                fetch_one=False
            )
            
            return True
            
        except Exception as e:
            print(f"Error updating section dedicaciones: {e}")
            return False
    
    def delete_seccion(self, nrc: int) -> bool:
        """Delete section and all related data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Delete sessions first
            cursor.execute("DELETE FROM SesionProfesor WHERE sesion_id IN (SELECT id FROM Sesion WHERE seccion_NRC = ?)", (nrc,))
            cursor.execute("DELETE FROM Sesion WHERE seccion_NRC = ?", (nrc,))
            
            # Delete from SeccionProfesor
            cursor.execute("DELETE FROM SeccionProfesor WHERE seccion_NRC = ?", (nrc,))
            
            # Delete section
            cursor.execute("DELETE FROM Seccion WHERE NRC = ?", (nrc,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting seccion: {e}")
            return False
        
    
        # Add this method to DatabaseManager class:
    
    def update_session_per(self, sesion_id: int, per_value: int) -> bool:
        """Update PER value for a session"""
        try:
            count = self.execute_query(
                "UPDATE Sesion SET PER = ? WHERE id = ?",
                (per_value, sesion_id)
            )
            return count > 0
        except Exception as e:
            print(f"Error updating session PER: {e}")
            return False
    
    def get_sessions_by_per(self, per_value: int) -> List[Dict]:
        """Get all sessions with a specific PER value"""
        results = self.execute_query(
            """SELECT ses.id, ses.tipoHorario, ses.horaInicio, ses.horaFin, 
                      ses.edificio, ses.salon, ses.dias, ses.PER,
                      sec.NRC, m.codigo as materia_codigo, m.nombre as materia_nombre
               FROM Sesion ses
               JOIN Seccion sec ON ses.seccion_NRC = sec.NRC
               JOIN Materia m ON sec.materia_codigo = m.codigo
               WHERE ses.PER = ?
               ORDER BY ses.horaInicio""",
            (per_value,)
        )
        
        sessions = []
        for row in results:
            sessions.append({
                'sesion_id': row[0],
                'tipo_horario': row[1],
                'hora_inicio': row[2],
                'hora_fin': row[3],
                'edificio': row[4],
                'salon': row[5],
                'dias': row[6],
                'per': row[7],
                'nrc': row[8],
                'materia_codigo': row[9],
                'materia_nombre': row[10]
            })
        
        return sessions
    
    def get_per_statistics(self) -> Dict:
        """Get statistics about PER values"""
        results = self.execute_query(
            """SELECT PER, COUNT(*) as count
               FROM Sesion
               GROUP BY PER
               ORDER BY PER"""
        )
        
        stats = {}
        for row in results:
            stats[row[0]] = row[1]
        
        return stats
    
    def get_sessions_for_per_calculation(self) -> List[Dict]:
        """Get sessions from materias with nivel_numerico 1 or 2 for PER calculation - UPDATED with lista_cruzada grouping"""
        results = self.execute_query(
            """SELECT 
                ses.id as sesion_id,
                ses.tipoHorario,
                ses.PER as current_per,
                m.codigo as materia_codigo,
                m.nombre as materia_nombre,
                m.nivel_numerico,
                sec.inscritos,
                sec.NRC,
                sec.lista_cruzada
            FROM Sesion ses
            JOIN Seccion sec ON ses.seccion_NRC = sec.NRC
            JOIN Materia m ON sec.materia_codigo = m.codigo
            WHERE m.nivel_numerico IN (1, 2)
            ORDER BY m.nivel_numerico, m.codigo, sec.NRC"""
        )
        
        # Group sessions by lista_cruzada for combined enrollment calculation
        grouped_sessions = {}
        individual_sessions = []
        
        for row in results:
            session_data = {
                'sesion_id': row[0],
                'tipo_horario': row[1] if row[1] else 'No especificado',
                'current_per': row[2] if row[2] is not None else 0,
                'materia_codigo': row[3],
                'materia_nombre': row[4],
                'nivel_numerico': row[5],
                'inscritos': row[6] if row[6] else 0,
                'nrc': row[7],
                'lista_cruzada': row[8]
            }
            
            lista_cruzada = row[8]
            
            # SPECIAL CASE: ISIS_001 should be calculated individually
            if lista_cruzada == 'ISIS_001' or not lista_cruzada:
                # No grouping - individual calculation
                individual_sessions.append(session_data)
            else:
                # Group by lista_cruzada
                if lista_cruzada not in grouped_sessions:
                    grouped_sessions[lista_cruzada] = {
                        'sessions': [],
                        'total_inscritos': 0,
                        'nrcs': set()
                    }
                
                grouped_sessions[lista_cruzada]['sessions'].append(session_data)
                
                # Only count enrollment once per NRC to avoid double counting
                if row[7] not in grouped_sessions[lista_cruzada]['nrcs']:
                    grouped_sessions[lista_cruzada]['total_inscritos'] += session_data['inscritos']
                    grouped_sessions[lista_cruzada]['nrcs'].add(row[7])
        
        # Convert grouped sessions back to individual session format with combined enrollment
        final_sessions = []
        
        # Add individual sessions (no grouping)
        final_sessions.extend(individual_sessions)
        
        # Add grouped sessions with combined enrollment
        for lista_cruzada, group_data in grouped_sessions.items():
            combined_inscritos = group_data['total_inscritos']
            
            for session in group_data['sessions']:
                # Update session with combined enrollment for PER calculation
                session_copy = session.copy()
                session_copy['original_inscritos'] = session['inscritos']  # Keep original for reference
                session_copy['inscritos'] = combined_inscritos  # Use combined for PER calculation
                session_copy['grouped_with'] = lista_cruzada
                session_copy['group_size'] = len(group_data['sessions'])
                final_sessions.append(session_copy)
        
        return final_sessions
    
    def bulk_update_per_values(self, updates: List[Dict]) -> int:
        """Bulk update PER values for multiple sessions"""
        updated_count = 0
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for update in updates:
                cursor.execute(
                    "UPDATE Sesion SET PER = ? WHERE id = ?",
                    (update['new_per'], update['sesion_id'])
                )
                updated_count += 1
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error updating PER values: {e}")
            if conn:
                conn.rollback()
                conn.close()
        
        return updated_count
    
    def get_per_statistics(self) -> Dict:
        """Get statistics about PER values"""
        results = self.execute_query(
            """SELECT PER, COUNT(*) as count
               FROM Sesion
               WHERE PER IS NOT NULL
               GROUP BY PER
               ORDER BY PER"""
        )
        
        stats = {}
        for row in results:
            stats[row[0]] = row[1]
        
        return stats
    
    def reset_per_values_for_levels(self, nivel_numerico_list: List[int]) -> int:
        """Reset PER values to 0 for sessions of specific academic levels"""
        try:
            placeholders = ','.join(['?' for _ in nivel_numerico_list])
            query = f"""
                UPDATE Sesion 
                SET PER = 0 
                WHERE seccion_NRC IN (
                    SELECT sec.NRC 
                    FROM Seccion sec 
                    JOIN Materia m ON sec.materia_codigo = m.codigo 
                    WHERE m.nivel_numerico IN ({placeholders})
                )
            """
            
            count = self.execute_query(query, tuple(nivel_numerico_list))
            return count
        except Exception as e:
            print(f"Error resetting PER values: {e}")
            return 0
        
    def get_sessions_for_tamano_estandar_calculation(self) -> List[Dict]:
        """Get sessions from materias with nivel_numerico 3 or 4 for Tamaño Estándar calculation - UPDATED with lista_cruzada grouping"""
        results = self.execute_query(
            """SELECT 
                ses.tipoHorario,
                sec.inscritos,
                sec.NRC,
                m.departamento_nombre,
                m.nivel_numerico,
                sec.lista_cruzada
            FROM Sesion ses
            JOIN Seccion sec ON ses.seccion_NRC = sec.NRC
            JOIN Materia m ON sec.materia_codigo = m.codigo
            WHERE m.nivel_numerico IN (3, 4)
            ORDER BY m.departamento_nombre, ses.tipoHorario"""
        )
        
        # Group by lista_cruzada to avoid double counting enrollment
        processed_grupos = set()
        final_sessions = []
        
        for row in results:
            tipo_horario = row[0] if row[0] else 'No especificado'
            inscritos = row[1] if row[1] else 0
            nrc = row[2]
            departamento = row[3]
            nivel_numerico = row[4]
            lista_cruzada = row[5]
            
            session_data = {
                'tipo_horario': tipo_horario,
                'inscritos': inscritos,
                'nrc': nrc,
                'departamento': departamento,
                'nivel_numerico': nivel_numerico,
                'lista_cruzada': lista_cruzada
            }
            
            # SPECIAL CASE: ISIS_001 should be calculated individually
            if lista_cruzada == 'ISIS_001' or not lista_cruzada:
                # No grouping - individual calculation
                final_sessions.append(session_data)
            else:
                # For grouped sections, only count once per lista_cruzada group
                if lista_cruzada not in processed_grupos:
                    # Get all sections in this lista_cruzada group
                    group_results = self.execute_query(
                        """SELECT sec.inscritos, sec.NRC
                           FROM Seccion sec
                           JOIN Materia m ON sec.materia_codigo = m.codigo
                           WHERE sec.lista_cruzada = ? AND m.nivel_numerico IN (3, 4)""",
                        (lista_cruzada,)
                    )
                    
                    # Calculate combined enrollment for the group
                    total_inscritos = sum(row[0] if row[0] else 0 for row in group_results)
                    
                    # Add one representative session with combined enrollment
                    session_data['inscritos'] = total_inscritos
                    session_data['is_grouped'] = True
                    session_data['group_size'] = len(group_results)
                    final_sessions.append(session_data)
                    
                    processed_grupos.add(lista_cruzada)
        
        return final_sessions
    
    def calculate_tamano_estandar_by_department(self) -> Dict:
        """Calculate Tamaño Estándar for each department and course type"""
        sessions = self.get_sessions_for_tamano_estandar_calculation()
        
        if not sessions:
            return {}
        
        # Group by department and course type
        department_data = {}
        
        for session in sessions:
            dept = session['departamento']
            tipo_horario = session['tipo_horario'].upper()
            inscritos = session['inscritos']
            nrc = session['nrc']
            
            # Classify course type
            course_type = None
            if tipo_horario in ['MAGISTRAL', 'TEORICA']:
                course_type = 'TEORICO'
            elif tipo_horario in ['LABORATORIO', 'TALLER Y PBL']:
                course_type = 'PRACTICO'
            else:
                continue  # Skip unrecognized types
            
            # Initialize department structure
            if dept not in department_data:
                department_data[dept] = {
                    'TEORICO': {'sections': set(), 'total_inscritos': 0},
                    'PRACTICO': {'sections': set(), 'total_inscritos': 0}
                }
            
            # Add section if not already counted
            if nrc not in department_data[dept][course_type]['sections']:
                department_data[dept][course_type]['sections'].add(nrc)
                department_data[dept][course_type]['total_inscritos'] += inscritos
        
        # Calculate averages
        results = {}
        for dept, data in department_data.items():
            results[dept] = {}
            
            for course_type in ['TEORICO', 'PRACTICO']:
                sections = data[course_type]['sections']
                total_inscritos = data[course_type]['total_inscritos']
                
                if len(sections) > 0:
                    tamano_estandar = round( total_inscritos / len(sections),2)
                    
                    if course_type == 'TEORICO':
                        if tamano_estandar < 10:
                            tamano_estandar = 10
                        elif tamano_estandar > 30:
                            tamano_estandar = 30
                    else:
                        if tamano_estandar < 10:
                            tamano_estandar = 10
                        elif tamano_estandar > 20:
                            tamano_estandar = 20
                    results[dept][course_type] = {
                        'tamano_estandar': tamano_estandar,
                        'total_sections': len(sections),
                        'total_inscritos': total_inscritos
                    }
                else:
                    results[dept][course_type] = {
                        'tamano_estandar': 0,
                        'total_sections': 0,
                        'total_inscritos': 0
                    }
        
        return results
    
    def get_tamano_estandar_statistics(self) -> Dict:
        """Get statistics about Tamaño Estándar calculations"""
        data = self.calculate_tamano_estandar_by_department()
        
        stats = {
            'total_departments': len(data),
            'departments_with_teorico': 0,
            'departments_with_practico': 0,
            'average_teorico': 0,
            'average_practico': 0,
            'total_sections_teorico': 0,
            'total_sections_practico': 0,
            'department_details': data
        }
        
        teorico_values = []
        practico_values = []
        
        for dept, dept_data in data.items():
            if dept_data['TEORICO']['total_sections'] > 0:
                stats['departments_with_teorico'] += 1
                stats['total_sections_teorico'] += dept_data['TEORICO']['total_sections']
                teorico_values.append(dept_data['TEORICO']['tamano_estandar'])
            
            if dept_data['PRACTICO']['total_sections'] > 0:
                stats['departments_with_practico'] += 1
                stats['total_sections_practico'] += dept_data['PRACTICO']['total_sections']
                practico_values.append(dept_data['PRACTICO']['tamano_estandar'])
        
        # Calculate overall averages
        if teorico_values:
            stats['average_teorico'] = round(sum(teorico_values) / len(teorico_values), 2)
        
        if practico_values:
            stats['average_practico'] = round(sum(practico_values) / len(practico_values), 2)
        
        return stats
    
    
    def get_sessions_for_per_calculation_levels_3_4(self) -> List[Dict]:
        """Get sessions from materias with nivel_numerico 3 or 4 for PER calculation - UPDATED with lista_cruzada grouping"""
        results = self.execute_query(
            """SELECT 
                ses.id as sesion_id,
                ses.tipoHorario,
                ses.PER as current_per,
                sec.inscritos,
                sec.NRC,
                m.codigo as materia_codigo,
                m.nombre as materia_nombre,
                m.nivel_numerico,
                m.departamento_nombre,
                sec.lista_cruzada
            FROM Sesion ses
            JOIN Seccion sec ON ses.seccion_NRC = sec.NRC
            JOIN Materia m ON sec.materia_codigo = m.codigo
            WHERE m.nivel_numerico IN (3, 4)
            ORDER BY m.departamento_nombre, m.codigo, sec.NRC"""
        )
        
        # Group sessions by lista_cruzada for combined enrollment calculation
        grouped_sessions = {}
        individual_sessions = []
        
        for row in results:
            session_data = {
                'sesion_id': row[0],
                'tipo_horario': row[1] if row[1] else 'No especificado',
                'current_per': row[2] if row[2] is not None else 0,
                'inscritos': row[3] if row[3] else 0,
                'nrc': row[4],
                'materia_codigo': row[5],
                'materia_nombre': row[6],
                'nivel_numerico': row[7],
                'departamento': row[8],
                'lista_cruzada': row[9]
            }
            
            lista_cruzada = row[9]
            
            # SPECIAL CASE: ISIS_001 should be calculated individually
            if lista_cruzada == 'ISIS_001' or not lista_cruzada:
                # No grouping - individual calculation
                individual_sessions.append(session_data)
            else:
                # Group by lista_cruzada
                if lista_cruzada not in grouped_sessions:
                    grouped_sessions[lista_cruzada] = {
                        'sessions': [],
                        'total_inscritos': 0,
                        'nrcs': set()
                    }
                
                grouped_sessions[lista_cruzada]['sessions'].append(session_data)
                
                # Only count enrollment once per NRC to avoid double counting
                if row[4] not in grouped_sessions[lista_cruzada]['nrcs']:
                    grouped_sessions[lista_cruzada]['total_inscritos'] += session_data['inscritos']
                    grouped_sessions[lista_cruzada]['nrcs'].add(row[4])
        
        # Convert grouped sessions back to individual session format with combined enrollment
        final_sessions = []
        
        # Add individual sessions (no grouping)
        final_sessions.extend(individual_sessions)
        
        # Add grouped sessions with combined enrollment
        for lista_cruzada, group_data in grouped_sessions.items():
            combined_inscritos = group_data['total_inscritos']
            
            for session in group_data['sessions']:
                # Update session with combined enrollment for PER calculation
                session_copy = session.copy()
                session_copy['original_inscritos'] = session['inscritos']  # Keep original for reference
                session_copy['inscritos'] = combined_inscritos  # Use combined for PER calculation
                session_copy['grouped_with'] = lista_cruzada
                session_copy['group_size'] = len(group_data['sessions'])
                final_sessions.append(session_copy)
        
        return final_sessions
    
    def calculate_per_for_levels_3_4_with_tamano_estandar(self) -> Dict:
        """Calculate PER for levels 3 and 4 using Tamaño Estándar"""
        # First, get the Tamaño Estándar for each department and course type
        tamano_estandar_data = self.calculate_tamano_estandar_by_department()
        
        # Get sessions that need PER calculation
        sessions = self.get_sessions_for_per_calculation_levels_3_4()
        
        if not sessions:
            return {'updates': [], 'tamano_estandar_used': {}}
        
        updates = []
        tamano_estandar_used = {}
        
        for session in sessions:
            dept = session['departamento']
            tipo_horario = session['tipo_horario'].upper()
            inscritos = session['inscritos']  # PE (Puestos estudiante en el curso)
            
            # Classify course type
            if tipo_horario in ['MAGISTRAL', 'TEORICA']:
                course_type = 'TEORICO'
            elif tipo_horario in ['LABORATORIO', 'TALLER Y PBL']:
                course_type = 'PRACTICO'
            else:
                continue  # Skip unrecognized types
            
            # Get Tamaño Estándar for this department and course type
            if dept in tamano_estandar_data and tamano_estandar_data[dept][course_type]['total_sections'] > 0:
                tamano_estandar = tamano_estandar_data[dept][course_type]['tamano_estandar']
            else:
                continue  # Skip if no Tamaño Estándar available
            
            # Store the Tamaño Estándar used for reporting
            if dept not in tamano_estandar_used:
                tamano_estandar_used[dept] = {}
            tamano_estandar_used[dept][course_type] = tamano_estandar
            
            # Calculate PER based on the table logic
            new_per = self.calculate_per_from_table(course_type, tamano_estandar, inscritos)
            
            # Only update if PER changed
            if new_per != session['current_per']:
                updates.append({
                    'sesion_id': session['sesion_id'],
                    'new_per': new_per,
                    'old_per': session['current_per'],
                    'materia': session['materia_codigo'],
                    'tipo_horario': session['tipo_horario'],
                    'inscritos': inscritos,
                    'departamento': dept,
                    'tamano_estandar': tamano_estandar,
                    'course_type': course_type
                })
        
        return {
            'updates': updates,
            'tamano_estandar_used': tamano_estandar_used
        }
    
    def calculate_per_from_table(self, course_type: str, tamano_estandar: float, pe: int) -> int:
        """
        Calculate PER based on the provided table logic
        
        Args:
            course_type: 'TEORICO' or 'PRACTICO'
            tamano_estandar: The calculated standard size (promedio)
            pe: Puestos estudiante en el curso (enrolled students)
        
        Returns:
            int: Calculated PER value
        """
        if course_type == 'TEORICO':
            # Determine which row of the table to use based on Tamaño Estándar
            if tamano_estandar >= 30:
                # Row 1: Teórico with Tamaño estándar = 30
                if 1 <= pe <= 10:
                    return 10
                elif 11 <= pe <= 60:
                    return pe
                elif 61 <= pe <= 120:
                    return 60 + ((pe - 60) // 2)
                elif pe >= 121:
                    return 90
                    
            elif 21 <= tamano_estandar <= 29:
                # Row 2: Teórico with Tamaño estándar = 21 a 29
                promedio = int(tamano_estandar)  # Use the actual Tamaño Estándar as promedio
                if 1 <= pe <= 10:
                    return pe
                elif 11 <= pe <= 20:
                    return 20
                elif 21 <= pe <= promedio:
                    return promedio
                elif (promedio + 1) <= pe <= 60:
                    return pe
                elif 61 <= pe <= 120:
                    return 60 + ((pe - 60) // 2)
                elif pe >= 121:
                    return 90
                    
            elif 10 <= tamano_estandar <= 20:
                # Row 3: Teórico with Tamaño estándar = 10 a 20
                promedio = int(tamano_estandar)
                if 1 <= pe <= 10:
                    return pe
                elif 11 <= pe <= promedio:
                    return promedio
                elif (promedio + 1) <= pe <= 60:
                    return pe
                elif 61 <= pe <= 120:
                    return 60 + ((pe - 60) // 2)
                elif pe >= 121:
                    return 90
                    
            elif tamano_estandar < 10:
                # Row 4: Teórico with Tamaño estándar = 10
                promedio = 10  # Minimum is 10
                if 1 <= pe <= promedio:
                    return promedio
                elif (promedio + 1) <= pe <= 60:
                    return pe
                elif 61 <= pe <= 120:
                    return 60 + ((pe - 60) // 2)
                elif pe >= 121:
                    return 90
        
        elif course_type == 'PRACTICO':
            if tamano_estandar >= 20:
                # Row 1: Práctico with Tamaño estándar = 20
                if 1 <= pe <= 6:
                    return 6
                elif 7 <= pe <= 25:
                    return pe
                elif pe >= 26:
                    return 25
                    
            elif 10 <= tamano_estandar <= 19:
                # Row 2: Práctico with Tamaño estándar = 10 a 19
                promedio = int(tamano_estandar)
                if 1 <= pe <= 10:
                    return pe
                elif 11 <= pe <= promedio:
                    return promedio
                elif (promedio + 1) <= pe <= 25:
                    return pe
                elif pe >= 26:
                    return 25
        
        # Default fallback
        return 1
    # ==================== VALIDATION METHODS ====================
    
    def nrc_exists(self, nrc: int) -> bool:
        """Check if NRC already exists"""
        result = self.execute_query(
            "SELECT COUNT(*) FROM Seccion WHERE NRC = ?",
            (nrc,),
            fetch_one=True
        )
        return result[0] > 0
    
    def materia_codigo_exists(self, codigo: str) -> bool:
        """Check if materia codigo already exists"""
        result = self.execute_query(
            "SELECT COUNT(*) FROM Materia WHERE codigo = ?",
            (codigo,),
            fetch_one=True
        )
        return result[0] > 0
    
    def departamento_exists(self, nombre: str) -> bool:
        """Check if departamento exists"""
        result = self.execute_query(
            "SELECT COUNT(*) FROM Departamento WHERE nombre = ?",
            (nombre,),
            fetch_one=True
        )
        return result[0] > 0
    
    # ==================== STATISTICS METHODS ====================
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        tables = ['Departamento', 'Profesor', 'Materia', 'Seccion', 'Sesion']
        for table in tables:
            result = self.execute_query(f"SELECT COUNT(*) FROM {table}", fetch_one=True)
            stats[table.lower()] = result[0] if result else 0
        
        return stats
    
    def get_table_data(self, table_name: str, search_term: str = None, 
                      limit: int = None, offset: int = None) -> List[tuple]:
        """Get data from any table with optional search and pagination"""
        
        # Special handling for Sesion table to include materia information
        if table_name == "Sesion":
            query = """
                SELECT 
                    ses.id,
                    ses.tipoHorario,
                    ses.horaInicio,
                    ses.horaFin,
                    ses.duracion,
                    ses.edificio,
                    ses.salon,
                    ses.atributoSalon,
                    ses.dias,
                    ses.PER,
                    ses.seccion_NRC,
                    m.codigo as materia_codigo,
                    m.nombre as materia_nombre,
                    m.departamento_nombre,
                    ses.profesor_ids
                FROM Sesion ses
                JOIN Seccion sec ON ses.seccion_NRC = sec.NRC
                JOIN Materia m ON sec.materia_codigo = m.codigo
            """
            params = []
            
            if search_term:
                query += """ WHERE (
                    ses.tipoHorario LIKE ? OR
                    ses.edificio LIKE ? OR
                    ses.salon LIKE ? OR
                    m.codigo LIKE ? OR
                    m.nombre LIKE ? OR
                    m.departamento_nombre LIKE ? OR
                    CAST(ses.seccion_NRC AS TEXT) LIKE ?
                )"""
                search_param = f"%{search_term}%"
                params.extend([search_param] * 7)
            
            query += " ORDER BY ses.id"
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset or 0])
            
            return self.execute_query(query, tuple(params))
        
        # Original logic for other tables
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if search_term:
            # Get table columns to build search condition
            columns = self.get_table_columns(table_name)
            if columns:
                search_conditions = []
                for col in columns:
                    search_conditions.append(f"CAST({col} AS TEXT) LIKE ?")
                query += f" WHERE ({' OR '.join(search_conditions)})"
                params = [f"%{search_term}%"] * len(columns)
        
        # Add ordering for consistent results
        if table_name == "Profesor":
            query += " ORDER BY apellidos, nombres"
        elif table_name == "Materia":
            query += " ORDER BY departamento_nombre, nivel_numerico, codigo"
        elif table_name == "Seccion":
            query += " ORDER BY NRC"
        elif table_name == "Departamento":
            query += " ORDER BY nombre"
        elif table_name == "ProfesorDepartamento":
            query += " ORDER BY departamento_nombre, profesor_id"
        elif table_name == "SeccionProfesor":
            query += " ORDER BY seccion_NRC, profesor_id"
        elif table_name == "SesionProfesor":
            query += " ORDER BY sesion_id, profesor_id"
        else:
            query += " ORDER BY 1"  # Order by first column
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset or 0])
        
        return self.execute_query(query, tuple(params))
    
    # ==================== PERSONAL MERGE METHODS ====================
    
    
    def find_professors_by_name_similarity(self, target_name: str, threshold: float = 0.8) -> List[Dict]:
        """Find professors by name similarity"""
        from difflib import SequenceMatcher
        
        all_professors = self.get_all_profesores()
        similar_professors = []
        
        target_normalized = ' '.join(target_name.upper().split())
        
        for prof in all_professors:
            existing_normalized = ' '.join(prof['full_name'].upper().split())
            similarity = SequenceMatcher(None, target_normalized, existing_normalized).ratio()
            
            if similarity >= threshold:
                prof_copy = prof.copy()
                prof_copy['similarity_score'] = similarity
                similar_professors.append(prof_copy)
        
        # Sort by similarity score (highest first)
        similar_professors.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_professors
    
    def get_professor_by_exact_name(self, nombres: str, apellidos: str) -> Optional[Dict]:
        """Get professor by exact name match"""
        result = self.execute_query(
            """SELECT id, nombres, apellidos, tipo,
                      person_id, cargo_original, subcategoria,
                      datos_personales_vinculados
               FROM Profesor 
               WHERE UPPER(nombres) = UPPER(?) AND UPPER(apellidos) = UPPER(?)""",
            (nombres.strip(), apellidos.strip()),
            fetch_one=True
        )
        
        if result:
            return {
                'id': result[0],
                'nombres': result[1],
                'apellidos': result[2],
                'tipo': result[3],
                'person_id': result[4],
                'cargo_original': result[5],
                'subcategoria': result[6],
                'datos_personales_vinculados': result[7],
                'full_name': f"{result[1]} {result[2]}"
            }
        return None
    
    def create_dedication_processor(self):
        """Create a new dedication data processor instance"""
        try:
            from dedication_data_processor import DedicationDataProcessor
            return DedicationDataProcessor(self)
        except ImportError as e:
            print(f"Error importing DedicationDataProcessor: {e}")
            return None
        except Exception as e:
            print(f"Error creating DedicationDataProcessor: {e}")
            return None
        
        
        # ==================== HORAS PROMEDIO POR SECCION OPERATIONS ====================
    
    def calculate_horas_promedio_and_tamano_estandar_unified(self) -> Dict:
        """
        UNIFIED calculation for both Horas Promedio and Secciones a Tamaño Estándar
        Enhanced structure: {dependencia: {nivel: {tipo_profesor: {tipo_sesion: {nrc: {profesor_id: {horas: float, per: float}}}}}}}
        """
        try:
            # Get all sessions with required data
            query = """
                SELECT 
                    ses.id as sesion_id,
                    ses.tipoHorario,
                    ses.duracion,
                    ses.dias,
                    ses.PER as session_per,
                    ses.seccion_NRC,
                    sec.profesor_dedicaciones,
                    m.creditos,
                    m.codigo as materia_codigo,
                    m.semanas,
                    m.nivel_numerico,
                    m.departamento_nombre,
                    p.id as profesor_id,
                    p.dependencia,
                    p.tipo as profesor_tipo
                FROM Sesion ses
                JOIN Seccion sec ON ses.seccion_NRC = sec.NRC
                JOIN Materia m ON sec.materia_codigo = m.codigo
                JOIN SesionProfesor sp ON ses.id = sp.sesion_id
                JOIN Profesor p ON sp.profesor_id = p.id
                WHERE m.nivel_numerico IN (1, 2, 3, 4)
                AND UPPER(ses.tipoHorario) IN ('MAGISTRAL', 'TEORICA', 'LABORATORIO', 'TALLER Y PBL')
                ORDER BY ses.seccion_NRC, ses.id
            """
            
            results = self.execute_query(query)
            
            if not results:
                return {}
            
            # Initialize the nested dictionary structure
            unified_estructura = {}
            
            # Track processed professor-section combinations to avoid PER duplication
            
            print(f"Processing {len(results)} session-professor combinations...")
            
            # Process each session record
            for row in results:
                sesion_id = row[0]
                tipo_horario = row[1] if row[1] else 'No especificado'
                duracion = row[2] if row[2] else 0
                dias = row[3] if row[3] else ''
                session_per = row[4] if row[4] else 0
                seccion_nrc = row[5]
                profesor_dedicaciones_json = row[6]
                creditos = row[7] if row[7] else 0
                materia_codigo = row[8]
                semanas = row[9] if row[9] else 16
                nivel_numerico = row[10] if row[10] else 1
                departamento_nombre = row[11]
                profesor_id = row[12]
                profesor_dependencia = row[13]
                profesor_tipo = row[14]
                
                
                if profesor_dependencia: # Step 1: Determine Professor's Dependencia using simple mapping
                    if ('DEPARTAMENTO' in profesor_dependencia.upper()):
                        dependencia_key = self.get_dependency_for_department(departamento_nombre, profesor_dependencia)
                    else:
                        dependencia_key = self.get_dependency_for_department(departamento_nombre, None)
                else: 
                    dependencia_key = self.get_dependency_for_department(departamento_nombre, None)
                
                # Step 2: Determine Academic Level Category
                if nivel_numerico in [1, 2]:
                    nivel_categoria = "Basico e intermedio"
                elif nivel_numerico in [3, 4]:
                    nivel_categoria = "Avanzado"
                else:
                    continue  # Skip higher levels as requested
                
                # Step 3: Classify session type
                session_classification = self.classify_session_type(tipo_horario)
                if session_classification is None:
                    continue  # Skip sessions that are not considered
                
                # Step 4: Get Dedication Percentage
                dedication_percentage = 0
                if profesor_dedicaciones_json:
                    try:
                        if isinstance(profesor_dedicaciones_json, str):
                            dedicaciones = json.loads(profesor_dedicaciones_json)
                        else:
                            dedicaciones = profesor_dedicaciones_json
                        
                        if isinstance(dedicaciones, dict):
                            dedication_percentage = dedicaciones.get(str(profesor_id), 0)
                    except Exception as e:
                        print(f"Error parsing dedicaciones for section {seccion_nrc}: {e}")
                        dedication_percentage = 0
                
                # Skip if no dedication (professor gets 0 hours and PER)
                if dedication_percentage == 0:
                    continue
                
                # Step 5: Normalize Professor Type
                tipo_profesor_normalizado = self.normalize_profesor_tipo_for_calculation(profesor_tipo)
                
                if tipo_profesor_normalizado == 'AGD' or tipo_profesor_normalizado == 'AGM':
                    continue
                
                # Step 6: Calculate Base Hours
                base_hours = self.calculate_horas_reconocidas_formula(
                    duracion=duracion,
                    dias=dias,
                    creditos=creditos,
                    semanas=semanas,
                    tipo_horario=tipo_horario,
                    tipo_profesor=tipo_profesor_normalizado,
                    materia_codigo=materia_codigo
                )
                
                # Step 7: Apply Dedication Percentage to Hours
                final_hours = base_hours * (dedication_percentage / 100.0)
                
                # Step 8: Calculate PER with Dedication (only once per professor-section)
                final_per = session_per * (dedication_percentage / 100.0)

                
                # Step 9: Build/Update the Enhanced Nested Structure
                # Ensure structure exists
                if dependencia_key not in unified_estructura:
                    unified_estructura[dependencia_key] = {}
                
                if nivel_categoria not in unified_estructura[dependencia_key]:
                    unified_estructura[dependencia_key][nivel_categoria] = {}
                
                if tipo_profesor_normalizado not in unified_estructura[dependencia_key][nivel_categoria]:
                    unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado] = {}
                
                if session_classification not in unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado]:
                    unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado][session_classification] = {}
                
                if seccion_nrc not in unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado][session_classification]:
                    unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado][session_classification][seccion_nrc] = {}
                
                # Add/update professor with both hours and PER
                if profesor_id not in unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado][session_classification][seccion_nrc]:
                    unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado][session_classification][seccion_nrc][profesor_id] = {
                        'horas': final_hours,
                        'per': final_per
                    }
                else:
                    
                    if materia_codigo != 'ISIS-1221':
                        horas_actuales = unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado][session_classification][seccion_nrc][profesor_id]['horas']
                        unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado][session_classification][seccion_nrc][profesor_id]['horas'] = min(horas_actuales + final_hours, creditos)
                    else:
                        unified_estructura[dependencia_key][nivel_categoria][tipo_profesor_normalizado][session_classification][seccion_nrc][profesor_id]['horas'] += final_hours
                    
                    

            
            print("Unified structure calculation completed successfully.")
            return unified_estructura
            
        except Exception as e:
            print(f"Error calculating unified structure: {e}")
            return {}
    
    def calculate_both_metrics_from_unified_structure(self, unified_estructura: Dict) -> Dict:
        """
        Calculate both Horas Promedio and Secciones a Tamaño Estándar from unified structure
        """
        try:
            # Get Tamaño Estándar values for Básico e Intermedio (predefined)
            tamano_estandar_basico = {
                'Teorico': 30,
                'Practico': 20
            }
            
            # Get Tamaño Estándar values for Avanzado (from previous calculation)
            tamano_estandar_avanzado = self.calculate_tamano_estandar_by_department()
            
            # Initialize results
            combined_results = {}
            
            for dependencia, niveles in unified_estructura.items():
                combined_results[dependencia] = {}
                
                for nivel, tipos_prof in niveles.items():
                    combined_results[dependencia][nivel] = {}
                    
                    for tipo_prof, tipos_sesion in tipos_prof.items():
                        combined_results[dependencia][nivel][tipo_prof] = {}
                        
                        for tipo_sesion, secciones in tipos_sesion.items():
                            # Calculate metrics for this specific combination
                            
                            # 1. HORAS PROMEDIO calculation
                            total_hours = 0
                            num_sections = len(secciones)
                            
                            for nrc, profesores in secciones.items():
                                section_hours = sum(prof_data['horas'] for prof_data in profesores.values())
                                total_hours += section_hours
                            
                            promedio_horas = total_hours / num_sections if num_sections > 0 else 0
                            
                            # 2. SECCIONES A TAMAÑO ESTÁNDAR calculation
                            total_per = 0
                            for nrc, profesores in secciones.items():
                                section_per = sum(prof_data['per'] for prof_data in profesores.values())
                                total_per += section_per
                            
                            # Get appropriate Tamaño Estándar
                            if nivel == "Basico e intermedio":
                                tamano_estandar = tamano_estandar_basico.get(tipo_sesion, 30)
                            else:  # Avanzado
                                # Try to get from calculated values, fallback to defaults
                                departamento = self.equivalencia_dependencia_depto(dependencia)
                                if departamento in tamano_estandar_avanzado:
                                    dept_data = tamano_estandar_avanzado[departamento]
                                    tipo_key = 'TEORICO' if tipo_sesion == 'Teorico' else 'PRACTICO'
                                    if tipo_key in dept_data and dept_data[tipo_key]['tamano_estandar'] > 0:
                                        tamano_estandar = dept_data[tipo_key]['tamano_estandar']
                                    else:
                                        tamano_estandar = tamano_estandar_basico.get(tipo_sesion, 30)
                                else:
                                    tamano_estandar = tamano_estandar_basico.get(tipo_sesion, 30)
                            
                            secciones_tamano_estandar = total_per / tamano_estandar if tamano_estandar > 0 else 0
                            
                            horas = promedio_horas * secciones_tamano_estandar
                            
                            profesores = 0
                            
                            if tipo_prof != 'CÁTEDRA':
                                profesores = round(horas/9, 2)
                                
                            
                            
                            
                            
                            
                            # Store both metrics
                            combined_results[dependencia][nivel][tipo_prof][tipo_sesion] = {
                                'promedio_horas': round(promedio_horas, 2),
                                'secciones_tamano_estandar': round(secciones_tamano_estandar, 2),
                                'total_horas': round(total_hours, 2),
                                'total_per': round(total_per, 2),
                                'num_secciones': num_sections,
                                'tamano_estandar_usado': tamano_estandar,
                                'num_profesores': len(set(prof_id for nrc_profs in secciones.values() 
                                                         for prof_id in nrc_profs.keys())),
                                'horas': horas,
                                'profesores': profesores
                            }
            
            return combined_results
            
        except Exception as e:
            print(f"Error calculating combined metrics: {e}")
            return {}
        
    def equivalencia_dependencia_depto(self, dependencia: str) -> str:
            
        dependency_to_department = {
            'DEPARTAMENTO ING DE SISTEMAS Y COMPUTACIÓN': 'INGENIERIA DE SISTEMAS Y COMPU',
            'DEPARTAMENTO DE INGENIERÍA INDUSTRIAL': 'INGENIERIA INDUSTRIAL',
            'DEPARTAMENTO DE INGENIERÍA CIVIL Y AMBIENTAL': 'INGENIERIA CIVIL Y AMBIENTAL',
            'DEPARTAMENTO DE INGENIERÍA MECÁNICA': 'INGENIERIA MECANICA',
            'DEPARTAMENTO DE INGENIERÍA ELÉCTRICA Y ELECTRÓNICA': 'INGEN. ELECTRICA Y ELECTRONICA',
            'DEPARTAMENTO DE INGENIERÍA QUÍMICA Y ALIMENTOS': 'INGEN. QUIMICA Y DE ALIMENTOS',
            'DEPARTAMENTO DE INGENIERÍA BIOMÉDICA': 'INGENIERIA BIOMEDICA',
        }
        
        if dependencia in dependency_to_department:
            return dependency_to_department[dependencia]
        else:
            return dependencia
        
    
    def get_unified_recop_statistics(self) -> Dict:
        """Get comprehensive statistics for both metrics from unified calculation"""
        try:
            # Calculate the unified structure
            unified_structure = self.calculate_horas_promedio_and_tamano_estandar_unified()
            
            if not unified_structure:
                return {
                    'total_dependencias': 0,
                    'total_niveles': 0,
                    'total_tipos_profesor': 0,
                    'total_tipos_sesion': 0,
                    'total_secciones': 0,
                    'unified_structure': {},
                    'combined_metrics': {},
                    'summary': {}
                }
            
            # Calculate both metrics
            combined_metrics = self.calculate_both_metrics_from_unified_structure(unified_structure)
            
            # Calculate summary statistics
            total_dependencias = len(unified_structure)
            all_niveles = set()
            all_tipos_profesor = set()
            all_tipos_sesion = set()
            total_secciones = 0
            
            for dependencia, niveles in unified_structure.items():
                for nivel, tipos_prof in niveles.items():
                    all_niveles.add(nivel)
                    for tipo_prof, tipos_sesion in tipos_prof.items():
                        all_tipos_profesor.add(tipo_prof)
                        for tipo_sesion, secciones in tipos_sesion.items():
                            all_tipos_sesion.add(tipo_sesion)
                            total_secciones += len(secciones)
            
            # Create detailed summary by dependencia and level
            dependencia_summary = {}
            for dependencia, nivel_data in combined_metrics.items():
                dependencia_summary[dependencia] = {}
                dependencia_total_horas = 0
                dependencia_total_per = 0
                dependencia_total_secciones = 0
                
                for nivel, level_data in nivel_data.items():
                    nivel_horas = sum(
                        sum(ts_data['total_horas'] for ts_data in tp_data.values())
                        for tp_data in level_data.values()
                    )
                    nivel_per = sum(
                        sum(ts_data['total_per'] for ts_data in tp_data.values())
                        for tp_data in level_data.values()
                    )
                    nivel_secciones = sum(
                        sum(ts_data['num_secciones'] for ts_data in tp_data.values())
                        for tp_data in level_data.values()
                    )
                    
                    dependencia_summary[dependencia][nivel] = {
                        'tipos_profesor': len(level_data),
                        'total_horas': nivel_horas,
                        'total_per': nivel_per,
                        'total_secciones': nivel_secciones
                    }
                    
                    dependencia_total_horas += nivel_horas
                    dependencia_total_per += nivel_per
                    dependencia_total_secciones += nivel_secciones
                
                # Add departamento total
                dependencia_summary[dependencia]['TOTAL'] = {
                    'total_horas': dependencia_total_horas,
                    'total_per': dependencia_total_per,
                    'total_secciones': dependencia_total_secciones,
                    'niveles': len(nivel_data)
                }
            
            return {
                'total_dependencias': total_dependencias,
                'total_niveles': len(all_niveles),
                'total_tipos_profesor': len(all_tipos_profesor),
                'total_tipos_sesion': len(all_tipos_sesion),
                'total_secciones': total_secciones,
                'niveles_found': sorted(list(all_niveles)),
                'tipos_profesor_found': sorted(list(all_tipos_profesor)),
                'tipos_sesion_found': sorted(list(all_tipos_sesion)),
                'unified_structure': unified_structure,
                'combined_metrics': combined_metrics,
                'dependencia_summary': dependencia_summary
            }
            
        except Exception as e:
            print(f"Error getting unified RECOP statistics: {e}")
            return {}
        
    def normalize_profesor_tipo_for_calculation(self, tipo: str) -> str:
        """
        Normalize professor tipo for horas promedio calculation
        
        Args:
            tipo: Professor tipo to normalize
            
        Returns:
            str: Normalized tipo (standalone types or 'CÁTEDRA')
        """
        # Standalone professor types whitelist
        STANDALONE_PROFESOR_TIPOS = [
            'TITULAR', 'ASOCIADO', 'ASISTENTE', 'ASISTENTE POSDOCTORAL', 
            'INSTRUCTOR', 'EMERITO', 'VISITANTE', 'AGM', 'AGD'
        ]
        
        if not tipo:
            return 'CÁTEDRA'
        
        tipo_upper = tipo.upper().strip()
        
        if tipo_upper in STANDALONE_PROFESOR_TIPOS:
            return tipo_upper
        elif tipo_upper == 'PROFESIONAL DISTINGUIDO':
            return  'ASOCIADO'
        else:
            return 'CÁTEDRA'
    
    def parse_weekly_frequency(self, dias_string: str) -> int:
        """
        Parse weekly frequency from dias string
        
        Args:
            dias_string: Days string (e.g., "L,M,V")
            
        Returns:
            int: Number of days per week
        """
        if not dias_string:
            return 1
        days = [d.strip() for d in dias_string.split(',') if d.strip()]
        return len(days)
    
    def calculate_horas_reconocidas_formula(self, duracion: int, dias: str, creditos: int, 
                                          semanas: int, tipo_horario: str, tipo_profesor: str, 
                                          materia_codigo: str) -> float:
        """
        Calculate recognized hours based on complex formula
        
        Args:
            duracion: Session duration in hours
            dias: Days string (e.g., "L,M,V")
            creditos: Subject credits
            semanas: Number of weeks in the period (8 or 16)
            tipo_horario: Session type
            tipo_profesor: Professor type (normalized)
            materia_codigo: Subject code for exceptions
            
        Returns:
            float: Calculated hours
        """
        weekly_frequency = self.parse_weekly_frequency(dias)
        
        horas_banner = weekly_frequency*duracion
        
        horas_reconocidas = min(horas_banner*(semanas/16), creditos)
        
        if creditos == 2 and tipo_profesor != 'CÁTEDRA':
            horas_reconocidas *= 1.17
        if materia_codigo == 'ISIS-1221':
            horas_reconocidas = horas_banner*(semanas/16)
        
        return float(horas_reconocidas)
    
    def classify_session_type(self, tipo_horario: str) -> Optional[str]:
        """
        Classify session type into 'Teorico' or 'Practico'
        
        Args:
            tipo_horario: Session type from database
            
        Returns:
            str: 'Teorico', 'Practico', or None if not considered
        """
        if not tipo_horario:
            return None
        
        tipo_upper = tipo_horario.upper().strip()
        
        # Teorico types
        if tipo_upper in ['MAGISTRAL', 'TEORICA']:
            return 'Teorico'
        
        # Practico types
        elif tipo_upper in ['LABORATORIO', 'TALLER Y PBL']:
            return 'Practico'
        
        # Not considered
        else:
            return None
        
    def get_dependency_for_department(self, department_name: str, professor_dependencia: Optional[str] = None) -> str:
        """
        Simple mapping from department to dependency for horas reconocidas calculation
        
        Args:
            department_name: Department name from materia
            professor_dependencia: Professor's existing dependencia (if any)
            
        Returns:
            str: Resolved dependency name
        """
        # If professor already has a dependencia, use it
        if professor_dependencia and professor_dependencia.strip():
            return professor_dependencia.strip()
        
        # Simple mapping dictionary
        department_to_dependency = {
            # Engineering departments (normalize variations)
            'INGENIERIA DE SISTEMAS Y COMPU': 'DEPARTAMENTO ING DE SISTEMAS Y COMPUTACIÓN',
            'INGENIERIA INDUSTRIAL': 'DEPARTAMENTO DE INGENIERÍA INDUSTRIAL',
            'INGENIERIA CIVIL Y AMBIENTAL': 'DEPARTAMENTO DE INGENIERÍA CIVIL Y AMBIENTAL',
            'INGENIERIA MECANICA': 'DEPARTAMENTO DE INGENIERÍA MECÁNICA',
            'INGEN. ELECTRICA Y ELECTRONICA': 'DEPARTAMENTO DE INGENIERÍA ELÉCTRICA Y ELECTRÓNICA',
            'INGEN. QUIMICA Y DE ALIMENTOS': 'DEPARTAMENTO DE INGENIERÍA QUÍMICA Y ALIMENTOS',
            'INGENIERIA BIOMEDICA': 'DEPARTAMENTO DE INGENIERÍA BIOMÉDICA',
        }
        
        # Try exact match first
        if department_name in department_to_dependency:
            return department_to_dependency[department_name]
        
        # Try case-insensitive partial match
        dept_upper = department_name.upper().strip()
        for dept_key, dependency in department_to_dependency.items():
            if dept_upper in dept_key.upper() or dept_key.upper() in dept_upper:
                return dependency
        
        # Fallback: use department name as-is
        return department_name