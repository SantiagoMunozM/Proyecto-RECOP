import sqlite3
import json
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
                    calificacion TEXT,
                    campus TEXT,
                    periodo TEXT,
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
                    profesor_ids TEXT,
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
            print(f"DEBUG: Updating professor {profesor_id} with subcategoria: {subcategoria}")  # DEBUG
            
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
            
            print(f"DEBUG: After update, subcategoria = {result[0] if result else 'No result'}")  # DEBUG
            return True
        except Exception as e:
            print(f"Error updating professor personal data: {e}")
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
                'nrc': row[9],
                'indicador': row[10] if row[10] else '',
                'cupo': row[11] if row[11] else 0,
                'inscritos': row[12] if row[12] else 0,
                'materia_codigo': row[13],
                'materia_nombre': row[14],
                'creditos': row[15] if row[15] else 0,
                'departamento': row[16],
                'profesor_nombres': row[17],
                'profesor_apellidos': row[18]
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
                      calificacion: str, campus: str, periodo: str, departamento_nombre: str) -> bool:
        """Create new materia"""
        try:
            self.execute_query(
                """INSERT INTO Materia (codigo, nombre, creditos, nivel, calificacion, campus, periodo, departamento_nombre) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (codigo.strip(), nombre.strip(), creditos, nivel.strip(), 
                 calificacion.strip(), campus.strip(), periodo.strip(), departamento_nombre)
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
            """SELECT m.codigo, m.nombre, m.creditos, m.nivel, m.calificacion, m.campus, m.periodo,
                      COUNT(s.NRC) as num_sections
               FROM Materia m
               LEFT JOIN Seccion s ON m.codigo = s.materia_codigo
               WHERE m.departamento_nombre = ?
               GROUP BY m.codigo, m.nombre, m.creditos, m.nivel, m.calificacion, m.campus, m.periodo
               ORDER BY m.codigo""",
            (departamento,)
        )
        return [
            {
                'codigo': row[0],
                'nombre': row[1],
                'creditos': row[2],
                'nivel': row[3],
                'calificacion': row[4],
                'campus': row[5],
                'periodo': row[6],
                'num_sections': row[7]
            }
            for row in results
        ]
    
    def get_all_materias(self) -> List[Dict]:
        """Get all materias"""
        results = self.execute_query(
            """SELECT m.codigo, m.nombre, m.creditos, m.nivel, m.calificacion, 
                      m.campus, m.periodo, m.departamento_nombre,
                      COUNT(s.NRC) as num_sections
               FROM Materia m
               LEFT JOIN Seccion s ON m.codigo = s.materia_codigo
               GROUP BY m.codigo, m.nombre, m.creditos, m.nivel, m.calificacion, 
                        m.campus, m.periodo, m.departamento_nombre
               ORDER BY m.departamento_nombre, m.codigo"""
        )
        return [
            {
                'codigo': row[0],
                'nombre': row[1],
                'creditos': row[2],
                'nivel': row[3],
                'calificacion': row[4],
                'campus': row[5],
                'periodo': row[6],
                'departamento': row[7],
                'num_sections': row[8]
            }
            for row in results
        ]
    
    def get_materia_by_codigo(self, codigo: str) -> Optional[Dict]:
        """Get materia by codigo"""
        result = self.execute_query(
            """SELECT codigo, nombre, creditos, nivel, calificacion, campus, periodo, departamento_nombre
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
                'calificacion': result[4],
                'campus': result[5],
                'periodo': result[6],
                'departamento': result[7]
            }
        return None
    
    def update_materia(self, codigo: str, nombre: str, creditos: int, nivel: str, 
                      calificacion: str, campus: str, periodo: str) -> bool:
        """Update materia information"""
        try:
            count = self.execute_query(
                """UPDATE Materia SET nombre = ?, creditos = ?, nivel = ?, 
                   calificacion = ?, campus = ?, periodo = ? WHERE codigo = ?""",
                (nombre.strip(), creditos, nivel.strip(), calificacion.strip(), 
                 campus.strip(), periodo.strip(), codigo)
            )
            return count > 0
        except Exception as e:
            print(f"Error updating materia: {e}")
            return False
    
    def delete_materia(self, codigo: str) -> bool:
        """Delete materia and all related data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if materia has sections
            cursor.execute("SELECT COUNT(*) FROM Seccion WHERE materia_codigo = ?", (codigo,))
            section_count = cursor.fetchone()[0]
            
            if section_count > 0:
                conn.close()
                return False  # Cannot delete, has sections
            
            cursor.execute("DELETE FROM Materia WHERE codigo = ?", (codigo,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting materia: {e}")
            return False
    
    
        # Add these methods to the DatabaseManager class:
    
    def get_materia_sections(self, materia_codigo: str) -> List[Dict]:
        """Get all sections for a specific materia with detailed information"""
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
                     m.campus, m.periodo, m.departamento_nombre
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
                'departamento': row[12],
                'num_sessions': row[13] if row[13] else 0,
                'profesores': row[14] if row[14] else 'Sin asignar'
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
            profesor_ids_json = json.dumps(profesor_ids)
            
            cursor.execute(
                """INSERT INTO Seccion (NRC, indicador, cupo, inscritos, cupoDisponible,
                                        lista_cruzada, materia_codigo, profesor_ids)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (nrc, indicador.strip(), cupo, 0, cupo_disponible,
                 lista_cruzada.strip() if lista_cruzada else None, materia_codigo, profesor_ids_json)
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
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if search_term:
            # Table-specific search conditions
            if table_name == "Profesor":
                query += " WHERE (nombres LIKE ? OR apellidos LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            elif table_name == "Materia":
                query += " WHERE (codigo LIKE ? OR nombre LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            elif table_name == "Departamento":
                query += " WHERE nombre LIKE ?"
                params.append(f"%{search_term}%")
            elif table_name == "Seccion":
                query += " WHERE CAST(NRC AS TEXT) LIKE ?"
                params.append(f"%{search_term}%")
            elif table_name == "Sesion":
                query += " WHERE (edificio LIKE ? OR salon LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            elif table_name == "ProfesorDepartamento":
                query += " WHERE (departamento_nombre LIKE ?)"
                params.append(f"%{search_term}%")
            elif table_name == "SeccionProfesor":
                query += " WHERE CAST(seccion_NRC AS TEXT) LIKE ?"
                params.append(f"%{search_term}%")
            elif table_name == "SesionProfesor":
                query += " WHERE CAST(sesion_id AS TEXT) LIKE ?"
                params.append(f"%{search_term}%")
        
        # Add ordering for consistent results - FIXED ordering for Profesor table
        if table_name == "Profesor":
            query += " ORDER BY apellidos, nombres"  # Removed departamento_nombre reference
        elif table_name == "Materia":
            query += " ORDER BY departamento_nombre, codigo"
        elif table_name == "Seccion":
            query += " ORDER BY NRC"
        elif table_name == "Sesion":
            query += " ORDER BY id"
        elif table_name == "Departamento":
            query += " ORDER BY nombre"
        elif table_name == "ProfesorDepartamento":
            query += " ORDER BY departamento_nombre, profesor_id"
        elif table_name == "SeccionProfesor":
            query += " ORDER BY seccion_NRC, profesor_id"
        elif table_name == "SesionProfesor":
            query += " ORDER BY sesion_id, profesor_id"
        else:
            # Default ordering for other tables
            query += " ORDER BY rowid"
        
        if limit:
            query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
        
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