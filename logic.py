import pandas as pd
import sqlite3
from datetime import datetime
import re
import json

def create_database_schema(conn):
    """Create the database tables based on the model"""
    
    cursor = conn.cursor()
    
    # Create Departamento table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Departamento (
            nombre TEXT PRIMARY KEY
        )
    ''')
    
    # Create Profesor table - NOW with departamento relationship
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Profesor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT,
            apellidos TEXT,
            tipo TEXT,
            departamento_nombre TEXT,
            FOREIGN KEY (departamento_nombre) REFERENCES Departamento(nombre)
        )
    ''')
    
    # Create Materia table - NOW belongs to departamento directly
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Materia (
            codigo TEXT PRIMARY KEY,
            nombre TEXT,
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
            inscritos INTEGER,
            cupoDisponible INTEGER,
            materia_codigo TEXT,
            profesor_ids TEXT,  -- Store as JSON array of professor IDs (aggregated from all sessions)
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
            profesor_ids TEXT,  -- Store as JSON array of professor IDs
            FOREIGN KEY (seccion_NRC) REFERENCES Seccion(NRC)
        )
    ''')
    
    # Create junction table for Sesion-Profesor many-to-many relationship
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SesionProfesor (
            sesion_id INTEGER,
            profesor_id INTEGER,
            PRIMARY KEY (sesion_id, profesor_id),
            FOREIGN KEY (sesion_id) REFERENCES Sesion(id),
            FOREIGN KEY (profesor_id) REFERENCES Profesor(id)
        )
    ''')
    
    # Create junction table for Seccion-Profesor many-to-many relationship (NEW)
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

def is_row_empty(row):
    """Check if a row is essentially empty (all NaN or empty values)"""
    critical_fields = ['NRC', 'Materia', 'Departamento', 'Facultad ']
    
    for field in critical_fields:
        if field in row and not pd.isna(row[field]) and str(row[field]).strip() != '':
            return False
    return True

def safe_strip(value):
    """Safely strip a value, handling null/float cases"""
    if pd.isna(value):
        return ''
    return str(value).strip()

def parse_professors(prof_string):
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
            if len(name_parts) >= 2:
                # Assume last two parts are surnames, rest are names
                nombres = ' '.join(name_parts[:-2]) if len(name_parts) > 2 else name_parts[0]
                apellidos = ' '.join(name_parts[-2:]) if len(name_parts) > 1 else ''
                parsed_profs.append({
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'tipo': 'PRINCIPAL' 
                })
    
    return parsed_profs

def format_time(time_value):
    """Convert time from HHMM format to HH:MM"""
    if pd.isna(time_value):
        return None
    try:
        time_str = str(int(float(time_value))).zfill(4)
        return f"{time_str[:2]}:{time_str[2:]}"
    except (ValueError, TypeError):
        return None

def get_days_string(row):
    """Get the days of the week when the session occurs"""
    days = []
    day_columns = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    day_abbrev = ['L', 'M', 'I', 'J', 'V', 'S', 'D']
    
    for i, day_col in enumerate(day_columns):
        if day_col in row and not pd.isna(row[day_col]) and str(row[day_col]).strip() != '':
            days.append(day_abbrev[i])
    
    return ','.join(days)

def safe_int_convert(value, default=0):
    """Safely convert a value to integer"""
    if pd.isna(value):
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def get_seccion_professors(seccion_nrc, db_file_path='university_schedule.db'):
    """Get current professors for a section from the database"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT profesor_id
            FROM SeccionProfesor
            WHERE seccion_NRC = ?
        ''', (seccion_nrc,))
        
        results = cursor.fetchall()
        return [row[0] for row in results]
        
    except Exception as e:
        print(f"Error getting section professors: {e}")
        return []
    finally:
        conn.close()

def update_seccion_professors(seccion_nrc, new_profesor_ids, db_file_path='university_schedule.db'):
    """Update the professors for a section by adding new ones if they don't exist"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        # Get current professors for this section
        current_profesor_ids = set(get_seccion_professors(seccion_nrc, db_file_path))
        
        # Add new professors that aren't already associated with this section
        for profesor_id in new_profesor_ids:
            if profesor_id not in current_profesor_ids:
                cursor.execute('''
                    INSERT INTO SeccionProfesor (seccion_NRC, profesor_id)
                    VALUES (?, ?)
                ''', (seccion_nrc, profesor_id))
                current_profesor_ids.add(profesor_id)
        
        # Update the JSON field in Seccion table
        profesor_ids_json = json.dumps(list(current_profesor_ids))
        cursor.execute('''
            UPDATE Seccion 
            SET profesor_ids = ?
            WHERE NRC = ?
        ''', (profesor_ids_json, seccion_nrc))
        
        conn.commit()
        return list(current_profesor_ids)
        
    except Exception as e:
        print(f"Error updating section professors: {e}")
        conn.rollback()
        return []
    finally:
        conn.close()

def upload_csv_to_database(csv_file_path, db_file_path='university_schedule.db'):
    """Main function to upload CSV data to database"""
    
    # Read CSV file and drop completely empty rows
    df = pd.read_csv(csv_file_path)
    df = df.dropna(how='all')  # Remove rows where all values are NaN
    
    # Connect to database
    conn = sqlite3.connect(db_file_path)
    
    try:
        # Create database schema
        create_database_schema(conn)
        
        # Keep track of inserted records to avoid duplicates
        inserted_departamentos = set()
        inserted_profesores = {}  # Key: (nombres, apellidos, departamento), Value: id
        inserted_materias = set()
        inserted_secciones = set()
        seccion_professors = {}  # Key: NRC, Value: set of professor_ids
        
        cursor = conn.cursor()
        processed_rows = 0
        skipped_rows = 0
        
        for index, row in df.iterrows():
            # Check if row is empty
            if is_row_empty(row):
                print(f"Skipping empty row {index + 1}")
                skipped_rows += 1
                continue
                
            print(f"Processing row {index + 1}/{len(df)}")
            processed_rows += 1
            
            # Get departamento for this row
            departamento = safe_strip(row['Departamento'])
            if not departamento:
                print(f"Warning: Row {index + 1} has no departamento, skipping")
                skipped_rows += 1
                continue
            
            # Insert Departamento
            if departamento not in inserted_departamentos:
                cursor.execute('INSERT OR IGNORE INTO Departamento (nombre) VALUES (?)', 
                             (departamento,))
                inserted_departamentos.add(departamento)
            
            # Parse and insert Profesores - ALL belong to the same departamento from this row
            profesores = parse_professors(row['Profesor(es)'])
            profesor_ids = []
        
            for prof in profesores:
                # Key now includes departamento to handle professors in multiple departments
                prof_key = (prof['nombres'], prof['apellidos'], departamento)
                
                if prof_key not in inserted_profesores:
                    cursor.execute('''INSERT INTO Profesor (nombres, apellidos, tipo, departamento_nombre) 
                                 VALUES (?, ?, ?, ?)''', 
                             (prof['nombres'], prof['apellidos'], prof['tipo'], departamento))
                    profesor_id = cursor.lastrowid
                    inserted_profesores[prof_key] = profesor_id
                else:
                    profesor_id = inserted_profesores[prof_key]
                
                profesor_ids.append(profesor_id)
            
            # Insert Materia - belongs to departamento
            materia_codigo = safe_strip(row['Materia'])
            if materia_codigo and materia_codigo not in inserted_materias:
                cursor.execute('''INSERT OR IGNORE INTO Materia 
                                 (codigo, nombre, creditos, nivel, calificacion, campus, periodo, departamento_nombre) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                             (materia_codigo, safe_strip(row['Nombre largo curso']), 
                              safe_int_convert(row['Créditos']),
                              safe_strip(row['Nivel materia']), safe_strip(row['Modo calificación']), 
                              safe_strip(row['Campus']), safe_strip(row['Periodo']), departamento))
                inserted_materias.add(materia_codigo)
            
            # Get NRC
            nrc = safe_int_convert(row['NRC'])
            if nrc <= 0:
                print(f"Warning: Row {index + 1} has invalid NRC, skipping")
                skipped_rows += 1
                continue
            
            # Insert or update Seccion
            if nrc not in inserted_secciones:
                # First time seeing this section - insert it
                cursor.execute('''INSERT OR IGNORE INTO Seccion 
                                 (NRC, indicador, cupo, inscritos, cupoDisponible, materia_codigo, profesor_ids) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                             (nrc, safe_strip(row['Secc']), 
                              safe_int_convert(row['Cupo']),
                              safe_int_convert(row['Inscritos']),
                              safe_int_convert(row['Cupo disponible']),
                              materia_codigo, json.dumps(profesor_ids)))
                
                # Initialize the professors for this section
                seccion_professors[nrc] = set(profesor_ids)
                inserted_secciones.add(nrc)
                
                # Insert into SeccionProfesor junction table
                for profesor_id in profesor_ids:
                    cursor.execute('''INSERT INTO SeccionProfesor (seccion_NRC, profesor_id) 
                                     VALUES (?, ?)''', (nrc, profesor_id))
            else:
                # Section already exists - add new professors if they're not already there
                if nrc not in seccion_professors:
                    seccion_professors[nrc] = set()
                
                # Add new professors to the set
                new_professors = set(profesor_ids) - seccion_professors[nrc]
                if new_professors:
                    print(f"  Adding {len(new_professors)} new professors to section {nrc}")
                    
                    # Add to our tracking set
                    seccion_professors[nrc].update(profesor_ids)
                    
                    # Update the JSON field in database
                    profesor_ids_json = json.dumps(list(seccion_professors[nrc]))
                    cursor.execute('''UPDATE Seccion 
                                     SET profesor_ids = ?
                                     WHERE NRC = ?''', (profesor_ids_json, nrc))
                    
                    # Insert new professors into SeccionProfesor junction table
                    for profesor_id in new_professors:
                        cursor.execute('''INSERT INTO SeccionProfesor (seccion_NRC, profesor_id) 
                                         VALUES (?, ?)''', (nrc, profesor_id))
            
            # Insert Sesion - ONE session with ALL professors
            hora_inicio = format_time(row['Hora inicio'])
            hora_fin = format_time(row['Hora fin'])
            duracion = None
            
            if hora_inicio and hora_fin:
                try:
                    # Calculate duration in hours
                    start_hour, start_min = map(int, hora_inicio.split(':'))
                    end_hour, end_min = map(int, hora_fin.split(':'))
                    duracion = ((end_hour * 60 + end_min) - (start_hour * 60 + start_min) + 10 )/60
                except ValueError:
                    duracion = None
            
            dias = get_days_string(row)
            
            # Store professor IDs as JSON array
            profesor_ids_json = json.dumps(profesor_ids)
            
            cursor.execute('''INSERT INTO Sesion 
                             (tipoHorario, horaInicio, horaFin, duracion, edificio, salon, 
                              atributoSalon, dias, seccion_NRC, profesor_ids) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                         (safe_strip(row['Tipo horario (franja)']), hora_inicio, hora_fin, duracion,
                          safe_strip(row['Edificio']), safe_strip(row['Salón']), 
                          safe_strip(row['Descripción atributo salón']),
                          dias, nrc, profesor_ids_json))
            
            # Insert into SesionProfesor junction table
            sesion_id = cursor.lastrowid
            for profesor_id in profesor_ids:
                cursor.execute('''INSERT INTO SesionProfesor (sesion_id, profesor_id) 
                                 VALUES (?, ?)''', (sesion_id, profesor_id))
        
        conn.commit()
        print(f"Successfully processed {processed_rows} records!")
        print(f"Skipped {skipped_rows} empty/invalid rows")
        
        # Print summary statistics
        cursor.execute("SELECT COUNT(*) FROM Departamento")
        print(f"Departamentos: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM Profesor")
        print(f"Profesores: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM Materia")
        print(f"Materias: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM Seccion")
        print(f"Secciones: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM Sesion")
        print(f"Sesiones: {cursor.fetchone()[0]}")
        
        # Show sections with multiple professors
        cursor.execute('''
            SELECT s.NRC, COUNT(sp.profesor_id) as num_professors
            FROM Seccion s
            JOIN SeccionProfesor sp ON s.NRC = sp.seccion_NRC
            GROUP BY s.NRC
            HAVING num_professors > 1
            ORDER BY num_professors DESC
            LIMIT 5
        ''')
        multi_prof_sections = cursor.fetchall()
        if multi_prof_sections:
            print(f"\nSections with multiple professors:")
            for nrc, count in multi_prof_sections:
                print(f"  Section {nrc}: {count} professors")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_seccion_all_professors(seccion_nrc, db_file_path='university_schedule.db'):
    """Get all professors for a specific seccion (aggregated from all sessions)"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT p.id, p.nombres, p.apellidos, p.tipo, p.departamento_nombre
            FROM SeccionProfesor sp
            JOIN Profesor p ON sp.profesor_id = p.id
            WHERE sp.seccion_NRC = ?
            ORDER BY p.apellidos, p.nombres
        ''', (seccion_nrc,))
        
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Error getting seccion professors: {e}")
        return []
    finally:
        conn.close()

def get_profesor_secciones(db_file_path='university_schedule.db', nombres=None, apellidos=None, profesor_id=None):
    """Get all secciones for a specific professor"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        if profesor_id:
            query = '''
                SELECT 
                    sec.NRC,
                    sec.indicador,
                    m.codigo as materia_codigo,
                    m.nombre as materia_nombre,
                    m.departamento_nombre,
                    sec.cupo,
                    sec.inscritos,
                    sec.cupoDisponible,
                    COUNT(s.id) as num_sessions
                FROM Seccion sec
                JOIN SeccionProfesor sp ON sec.NRC = sp.seccion_NRC
                JOIN Materia m ON sec.materia_codigo = m.codigo
                LEFT JOIN Sesion s ON sec.NRC = s.seccion_NRC
                WHERE sp.profesor_id = ?
                GROUP BY sec.NRC, sec.indicador, m.codigo, m.nombre, m.departamento_nombre, sec.cupo, sec.inscritos, sec.cupoDisponible
                ORDER BY m.codigo, sec.NRC
            '''
            cursor.execute(query, (profesor_id,))
            
        else:
            query = '''
                SELECT 
                    sec.NRC,
                    sec.indicador,
                    m.codigo as materia_codigo,
                    m.nombre as materia_nombre,
                    m.departamento_nombre,
                    sec.cupo,
                    sec.inscritos,
                    sec.cupoDisponible,
                    COUNT(s.id) as num_sessions
                FROM Seccion sec
                JOIN SeccionProfesor sp ON sec.NRC = sp.seccion_NRC
                JOIN Profesor p ON sp.profesor_id = p.id
                JOIN Materia m ON sec.materia_codigo = m.codigo
                LEFT JOIN Sesion s ON sec.NRC = s.seccion_NRC
                WHERE 1=1
            '''
            params = []
            
            if nombres:
                query += ' AND p.nombres LIKE ?'
                params.append(f'%{nombres}%')
            
            if apellidos:
                query += ' AND p.apellidos LIKE ?'
                params.append(f'%{apellidos}%')
            
            query += ' GROUP BY sec.NRC, sec.indicador, m.codigo, m.nombre, m.departamento_nombre, sec.cupo, sec.inscritos, sec.cupoDisponible ORDER BY m.codigo, sec.NRC'
            cursor.execute(query, params)
        
        results = cursor.fetchall()
        
        if not results:
            print("No sections found for the specified professor.")
            return []
        
        print(f"\nFound {len(results)} section(s):")
        print("-" * 130)
        print(f"{'NRC':<8} {'Sec':<4} {'Course':<12} {'Name':<25} {'Dept':<15} {'Cap':<4} {'Enr':<4} {'Avl':<4} {'Sess':<4}")
        print("-" * 130)
        
        for row in results:
            nrc, indicador, codigo, nombre, departamento, cupo, inscritos, disponible, sessions = row
            
            print(f"{nrc:<8} {indicador:<4} {codigo:<12} {nombre[:24]:<25} {departamento[:14]:<15} {cupo:<4} {inscritos:<4} {disponible:<4} {sessions:<4}")
        
        return results
        
    except Exception as e:
        print(f"Error querying database: {e}")
        return []
    finally:
        conn.close()

# Update existing functions to include the new relationships...

def get_departamento_professors(departamento_nombre, db_file_path='university_schedule.db'):
    """Get all professors in a specific departamento"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT p.id, p.nombres, p.apellidos, p.tipo, 
                   COUNT(DISTINCT sp.sesion_id) as num_sessions,
                   COUNT(DISTINCT scp.seccion_NRC) as num_sections
            FROM Profesor p
            LEFT JOIN SesionProfesor sp ON p.id = sp.profesor_id
            LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
            WHERE p.departamento_nombre = ?
            GROUP BY p.id, p.nombres, p.apellidos, p.tipo
            ORDER BY p.apellidos, p.nombres
        ''', (departamento_nombre,))
        
        results = cursor.fetchall()
        
        print(f"\nProfessors in {departamento_nombre}:")
        print("-" * 100)
        print(f"{'ID':<4} {'Name':<35} {'Type':<12} {'Sessions':<8} {'Sections':<8}")
        print("-" * 100)
        
        for prof_id, nombres, apellidos, tipo, num_sessions, num_sections in results:
            full_name = f"{nombres} {apellidos}"
            print(f"{prof_id:<4} {full_name:<35} {tipo:<12} {num_sessions:<8} {num_sections:<8}")
        
        return results
        
    except Exception as e:
        print(f"Error getting departamento professors: {e}")
        return []
    finally:
        conn.close()

def get_departamento_materias(departamento_nombre, db_file_path='university_schedule.db'):
    """Get all materias in a specific departamento"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT m.codigo, m.nombre, m.creditos, COUNT(sec.NRC) as num_sections
            FROM Materia m
            LEFT JOIN Seccion sec ON m.codigo = sec.materia_codigo
            WHERE m.departamento_nombre = ?
            GROUP BY m.codigo, m.nombre, m.creditos
            ORDER BY m.codigo
        ''', (departamento_nombre,))
        
        results = cursor.fetchall()
        
        print(f"\nMaterias in {departamento_nombre}:")
        print("-" * 80)
        print(f"{'Code':<12} {'Name':<40} {'Credits':<8} {'Sections':<10}")
        print("-" * 80)
        
        for codigo, nombre, creditos, num_sections in results:
            print(f"{codigo:<12} {nombre[:39]:<40} {creditos:<8} {num_sections:<10}")
        
        return results
        
    except Exception as e:
        print(f"Error getting departamento materias: {e}")
        return []
    finally:
        conn.close()

def list_all_departamentos(db_file_path='university_schedule.db'):
    """List all departamentos with their professors and materias count"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                d.nombre,
                COUNT(DISTINCT p.id) as num_professors,
                COUNT(DISTINCT m.codigo) as num_materias,
                COUNT(DISTINCT sec.NRC) as num_sections
            FROM Departamento d
            LEFT JOIN Profesor p ON d.nombre = p.departamento_nombre
            LEFT JOIN Materia m ON d.nombre = m.departamento_nombre
            LEFT JOIN Seccion sec ON m.codigo = sec.materia_codigo
            GROUP BY d.nombre
            ORDER BY d.nombre
        ''')
        
        results = cursor.fetchall()
        
        print(f"\nAll Departamentos:")
        print("-" * 90)
        print(f"{'Departamento':<30} {'Professors':<12} {'Materias':<10} {'Sections':<10}")
        print("-" * 90)
        
        for nombre, num_profs, num_materias, num_sections in results:
            print(f"{nombre:<30} {num_profs:<12} {num_materias:<10} {num_sections:<10}")
        
        return results
        
    except Exception as e:
        print(f"Error listing departamentos: {e}")
        return []
    finally:
        conn.close()

def get_session_professors(sesion_id, db_file_path='university_schedule.db'):
    """Get all professors for a specific session"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT p.id, p.nombres, p.apellidos, p.tipo, p.departamento_nombre
            FROM SesionProfesor sp
            JOIN Profesor p ON sp.profesor_id = p.id
            WHERE sp.sesion_id = ?
            ORDER BY p.apellidos, p.nombres
        ''', (sesion_id,))
        
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Error getting session professors: {e}")
        return []
    finally:
        conn.close()

def get_profesor_sessions(db_file_path='university_schedule.db', nombres=None, apellidos=None, profesor_id=None):
    """Get all sessions for a specific professor"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        if profesor_id:
            query = '''
                SELECT 
                    s.id as sesion_id,
                    m.codigo as materia_codigo,
                    m.nombre as materia_nombre,
                    m.departamento_nombre,
                    sec.NRC,
                    sec.indicador as seccion,
                    s.tipoHorario,
                    s.horaInicio,
                    s.horaFin,
                    s.duracion,
                    s.dias,
                    s.edificio,
                    s.salon,
                    s.atributoSalon,
                    m.creditos,
                    sec.cupo,
                    sec.inscritos,
                    sec.cupoDisponible,
                    s.profesor_ids
                FROM Sesion s
                JOIN SesionProfesor sp ON s.id = sp.sesion_id
                JOIN Seccion sec ON s.seccion_NRC = sec.NRC
                JOIN Materia m ON sec.materia_codigo = m.codigo
                WHERE sp.profesor_id = ?
                ORDER BY s.dias, s.horaInicio
            '''
            cursor.execute(query, (profesor_id,))
            
        else:
            query = '''
                SELECT 
                    s.id as sesion_id,
                    m.codigo as materia_codigo,
                    m.nombre as materia_nombre,
                    m.departamento_nombre,
                    sec.NRC,
                    sec.indicador as seccion,
                    s.tipoHorario,
                    s.horaInicio,
                    s.horaFin,
                    s.duracion,
                    s.dias,
                    s.edificio,
                    s.salon,
                    s.atributoSalon,
                    m.creditos,
                    sec.cupo,
                    sec.inscritos,
                    sec.cupoDisponible,
                    s.profesor_ids
                FROM Sesion s
                JOIN SesionProfesor sp ON s.id = sp.sesion_id
                JOIN Profesor p ON sp.profesor_id = p.id
                JOIN Seccion sec ON s.seccion_NRC = sec.NRC
                JOIN Materia m ON sec.materia_codigo = m.codigo
                WHERE 1=1
            '''
            params = []
            
            if nombres:
                query += ' AND p.nombres LIKE ?'
                params.append(f'%{nombres}%')
            
            if apellidos:
                query += ' AND p.apellidos LIKE ?'
                params.append(f'%{apellidos}%')
            
            query += ' ORDER BY s.dias, s.horaInicio'
            cursor.execute(query, params)
        
        results = cursor.fetchall()
        
        if not results:
            print("No sessions found for the specified professor.")
            return []
        
        print(f"\nFound {len(results)} session(s):")
        print("-" * 150)
        print(f"{'ID':<4} {'Course':<12} {'Name':<20} {'Dept':<15} {'NRC':<6} {'Days':<6} {'Time':<12} {'Room':<12} {'Professors':<25}")
        print("-" * 150)
        
        for row in results:
            sesion_id, codigo, nombre, departamento, nrc, seccion, tipo, inicio, fin, duracion, dias, edificio, salon, atributo, creditos, cupo, inscritos, disponible, profesor_ids_json = row
            
            time_str = f"{inicio}-{fin}" if inicio and fin else "TBD"
            room_str = f"{edificio}_{salon}" if edificio and salon else "TBD"
            
            # Get all professors for this session
            session_profs = get_session_professors(sesion_id, db_file_path)
            prof_names = [f"{p[1]} {p[2]}" for p in session_profs]
            prof_str = ", ".join(prof_names[:2])
            if len(prof_names) > 2:
                prof_str += f" +{len(prof_names)-2}"
            
            print(f"{sesion_id:<4} {codigo:<12} {nombre[:19]:<20} {departamento[:14]:<15} {nrc:<6} {dias:<6} {time_str:<12} {room_str:<12} {prof_str[:24]:<25}")
        
        return results
        
    except Exception as e:
        print(f"Error querying database: {e}")
        return []
    finally:
        conn.close()

def list_all_professors(db_file_path='university_schedule.db'):
    """List all professors in the database"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT p.id, p.nombres, p.apellidos, p.departamento_nombre, 
                   COUNT(DISTINCT sp.sesion_id) as num_sessions,
                   COUNT(DISTINCT scp.seccion_NRC) as num_sections
            FROM Profesor p
            LEFT JOIN SesionProfesor sp ON p.id = sp.profesor_id
            LEFT JOIN SeccionProfesor scp ON p.id = scp.profesor_id
            GROUP BY p.id, p.nombres, p.apellidos, p.departamento_nombre
            ORDER BY p.departamento_nombre, p.apellidos, p.nombres
        ''')
        
        results = cursor.fetchall()
        
        print(f"\nFound {len(results)} professor(s):")
        print("-" * 110)
        print(f"{'ID':<4} {'Name':<30} {'Departamento':<25} {'Sessions':<8} {'Sections':<8}")
        print("-" * 110)
        
        for professor_id, nombres, apellidos, departamento, num_sessions, num_sections in results:
            full_name = f"{nombres} {apellidos}"
            print(f"{professor_id:<4} {full_name:<30} {departamento:<25} {num_sessions:<8} {num_sections:<8}")
        
        return results
        
    except Exception as e:
        print(f"Error querying database: {e}")
        return []
    finally:
        conn.close()

def check_relationships(db_file_path='university_schedule.db'):
    """Check and display database relationships"""
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*80)
        print("CHECKING DATABASE RELATIONSHIPS")
        print("="*80)
        
        # 1. Check departamento-professor relationships
        print("\n1. Departamento-Professor relationships:")
        cursor.execute('''
            SELECT 
                d.nombre,
                COUNT(DISTINCT p.id) as num_professors,
                COUNT(DISTINCT m.codigo) as num_materias
            FROM Departamento d
            LEFT JOIN Profesor p ON d.nombre = p.departamento_nombre
            LEFT JOIN Materia m ON d.nombre = m.departamento_nombre
            GROUP BY d.nombre
            ORDER BY num_professors DESC
        ''')
        
        results = cursor.fetchall()
        print(f"{'Departamento':<30} {'Professors':<12} {'Materias':<10}")
        print("-" * 55)
        for dept, num_profs, num_materias in results:
            print(f"{dept:<30} {num_profs:<12} {num_materias:<10}")
        
        # 2. Check sections with multiple professors
        print("\n2. Sections with multiple professors:")
        cursor.execute('''
            SELECT 
                sec.NRC,
                m.codigo,
                m.departamento_nombre,
                COUNT(scp.profesor_id) as num_professors,
                GROUP_CONCAT(p.nombres || ' ' || p.apellidos, ' | ') as professors
            FROM Seccion sec
            JOIN SeccionProfesor scp ON sec.NRC = scp.seccion_NRC
            JOIN Profesor p ON scp.profesor_id = p.id
            JOIN Materia m ON sec.materia_codigo = m.codigo
            GROUP BY sec.NRC
            HAVING num_professors > 1
            ORDER BY num_professors DESC
            LIMIT 10
        ''')
        
        results = cursor.fetchall()
        if results:
            print(f"{'NRC':<8} {'Course':<12} {'Dept':<15} {'# Profs':<8} {'Professors'}")
            print("-" * 100)
            for nrc, codigo, dept, num_profs, professors in results:
                prof_list = professors[:60] + "..." if professors and len(professors) > 60 else professors
                print(f"{nrc:<8} {codigo:<12} {dept[:14]:<15} {num_profs:<8} {prof_list}")
        else:
            print("No sections with multiple professors found.")
        
        # 3. Check sessions with multiple professors (should be same as sections or subset)
        print("\n3. Sessions with multiple professors:")
        cursor.execute('''
            SELECT 
                s.id,
                m.codigo,
                sec.NRC,
                COUNT(sp.profesor_id) as num_professors
            FROM Sesion s
            JOIN SesionProfesor sp ON s.id = sp.sesion_id
            JOIN Seccion sec ON s.seccion_NRC = sec.NRC
            JOIN Materia m ON sec.materia_codigo = m.codigo
            GROUP BY s.id
            HAVING num_professors > 1
            ORDER BY num_professors DESC
            LIMIT 5
        ''')
        
        results = cursor.fetchall()
        if results:
            print(f"{'Session':<8} {'Course':<12} {'NRC':<8} {'# Profs':<8}")
            print("-" * 40)
            for session_id, codigo, nrc, num_profs in results:
                print(f"{session_id:<8} {codigo:<12} {nrc:<8} {num_profs:<8}")
        else:
            print("No sessions with multiple professors found.")
            
    except Exception as e:
        print(f"Error checking relationships: {e}")
    finally:
        conn.close()

# Example usage functions
def main(csv_file_path = "/Users/santi/Documents/Universidad/Trabajo ISIS/proyectoIngieneria-202519/Cartelera20251.csv"):
    # Upload the CSV first
    upload_csv_to_database(csv_file_path)
    
    # Check relationships
    check_relationships()
    
    # List all departamentos
    print("\n" + "="*50)
    print("LISTING ALL DEPARTAMENTOS")
    print("="*50)
    list_all_departamentos()
    
    # Example: Get professors from a specific departamento
    print("\n" + "="*50)
    print("EXAMPLE: PROFESSORS IN INGENIERIA DE SISTEMAS")
    print("="*50)
    get_departamento_professors("INGENIERIA DE SISTEMAS")
    
    # List all professors
    print("\n" + "="*50)
    print("LISTING ALL PROFESSORS")
    print("="*50)
    list_all_professors()
    
    # Example: Get sections for a specific professor
    print("\n" + "="*50)
    print("EXAMPLE: SECTIONS FOR PROFESOR ID 1")
    print("="*50)
    get_profesor_secciones(profesor_id=1)