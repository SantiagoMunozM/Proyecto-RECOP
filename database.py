import sqlite3
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='university_schedule.db'):
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
                tipo TEXT
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
                      profesor_ids: List[int] = None) -> bool:
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
                """INSERT INTO Seccion (NRC, indicador, cupo, inscritos, cupoDisponible, materia_codigo, profesor_ids)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (nrc, indicador.strip(), cupo, 0, cupo_disponible, materia_codigo, profesor_ids_json)
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
                      s.materia_codigo, m.nombre as materia_nombre, m.departamento_nombre,
                      COUNT(ses.id) as num_sessions
               FROM Seccion s
               JOIN Materia m ON s.materia_codigo = m.codigo
               LEFT JOIN Sesion ses ON s.NRC = ses.seccion_NRC
               GROUP BY s.NRC, s.indicador, s.cupo, s.inscritos, s.cupoDisponible, 
                        s.materia_codigo, m.nombre, m.departamento_nombre
               ORDER BY m.departamento_nombre, s.materia_codigo, s.NRC"""
        )
        return [
            {
                'nrc': row[0],
                'indicador': row[1],
                'cupo': row[2],
                'inscritos': row[3],
                'cupo_disponible': row[4],
                'materia_codigo': row[5],
                'materia_nombre': row[6],
                'departamento': row[7],
                'num_sessions': row[8]
            }
            for row in results
        ]
    
    def get_seccion_by_nrc(self, nrc: int) -> Optional[Dict]:
        """Get section by NRC"""
        result = self.execute_query(
            """SELECT s.NRC, s.indicador, s.cupo, s.inscritos, s.cupoDisponible, 
                      s.materia_codigo, m.nombre as materia_nombre, m.departamento_nombre
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
                'materia_codigo': result[5],
                'materia_nombre': result[6],
                'departamento': result[7]
            }
        return None
    
    def update_seccion(self, nrc: int, indicador: str, cupo: int, inscritos: int) -> bool:
        """Update section information"""
        try:
            cupo_disponible = cupo - inscritos
            count = self.execute_query(
                """UPDATE Seccion SET indicador = ?, cupo = ?, inscritos = ?, cupoDisponible = ?
                   WHERE NRC = ?""",
                (indicador.strip(), cupo, inscritos, cupo_disponible, nrc)
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