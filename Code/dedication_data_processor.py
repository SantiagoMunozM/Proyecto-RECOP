import pandas as pd
import json
from typing import List, Dict, Optional
from difflib import SequenceMatcher

class DedicationDataProcessor:
    """Processor for dedication data CSV files"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.match_threshold = 0.7  # Name similarity threshold
        
    def load_dedication_csv(self, file_path: str) -> pd.DataFrame:
        """Load and validate dedication CSV file"""
        try:
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['seccion', 'profesor', 'dedicacion', 'periodo']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Basic data validation
            if df.empty:
                raise ValueError("CSV file is empty")
            
            # Check for valid NRCs (should be numeric)
            invalid_nrcs = df[~df['seccion'].astype(str).str.isdigit()]
            if not invalid_nrcs.empty:
                print(f"Warning: Found {len(invalid_nrcs)} rows with non-numeric NRCs")
            
            # Check for valid dedication percentages
            try:
                df['dedicacion'] = pd.to_numeric(df['dedicacion'], errors='coerce')
                invalid_dedicacion = df[df['dedicacion'].isna()]
                if not invalid_dedicacion.empty:
                    print(f"Warning: Found {len(invalid_dedicacion)} rows with invalid dedication values")
            except:
                print("Warning: Could not validate dedication column")
            
            return df
            
        except Exception as e:
            raise Exception(f"Error loading dedication CSV: {str(e)}")
    
    def find_professor_by_name(self, professor_name: str, nrc: int = None) -> Optional[Dict]:
        """Find professor in database by name using similarity matching - OPTIMIZED for section-specific search"""
        if not professor_name or pd.isna(professor_name):
            return None
        
        # Clean the name
        clean_name = str(professor_name).strip().upper()
        if not clean_name:
            return None
        
        # OPTIMIZED: If NRC is provided, search only among professors assigned to that section
        if nrc:
            section_professors = self.db_manager.get_section_professors(nrc)
            if section_professors:
                print(f"Searching among {len(section_professors)} professors assigned to section {nrc}")
                search_pool = section_professors
            else:
                print(f"No professors found for section {nrc}, searching all professors")
                search_pool = self.db_manager.get_all_profesores()
        else:
            # Fallback to searching all professors
            search_pool = self.db_manager.get_all_profesores()
        
        best_match = None
        best_score = 0
        
        for prof in search_pool:
            # Create full name for comparison
            prof_full_name = f"{prof['apellidos']} {prof['nombres']}".upper()
            
            # Calculate similarity
            similarity = self._calculate_name_similarity(clean_name, prof_full_name)
            
            if similarity > best_score and similarity >= self.match_threshold:
                best_score = similarity
                best_match = {
                    'professor': prof,
                    'similarity': similarity,
                    'matched_name': prof_full_name,
                    'search_scope': 'section_specific' if nrc and section_professors else 'global'
                }
        
        return best_match
    
    def process_dedication_csv(self, file_path: str) -> Dict:
        """Process dedication CSV and return matching results - UPDATED for efficient search"""
        result = {
            'success': False,
            'matches': [],
            'errors': [],
            'statistics': {
                'total_rows': 0,
                'valid_rows': 0,
                'professor_matches': 0,
                'nrc_matches': 0,
                'duplicate_entries': 0,
                'ready_to_apply': 0
            }
        }
        
        try:
            # Load CSV
            df = self.load_dedication_csv(file_path)
            result['statistics']['total_rows'] = len(df)
            
            # Track duplicates to enforce first-come-first-served
            seen_combinations = set()
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Extract data
                    nrc = int(row['seccion'])
                    professor_name = str(row['profesor']).strip()
                    dedicacion = float(row['dedicacion'])
                    periodo = str(row['periodo']).strip()
                    
                    # Skip if invalid data
                    if pd.isna(nrc) or pd.isna(professor_name) or pd.isna(dedicacion):
                        continue
                    
                    # Check for duplicate professor-section combination
                    combination_key = (nrc, professor_name.upper())
                    if combination_key in seen_combinations:
                        result['statistics']['duplicate_entries'] += 1
                        continue  # Skip duplicates (first-come-first-served)
                    
                    seen_combinations.add(combination_key)
                    result['statistics']['valid_rows'] += 1
                    
                    # Check if NRC exists first
                    nrc_exists = self.validate_nrc_exists(nrc)
                    if nrc_exists:
                        result['statistics']['nrc_matches'] += 1
                    
                    # OPTIMIZED: Find professor match using section-specific search
                    prof_match = self.find_professor_by_name(professor_name, nrc if nrc_exists else None)
                    professor_found = prof_match is not None
                    if professor_found:
                        result['statistics']['professor_matches'] += 1
                    
                    # Create match record
                    match_record = {
                        'row_index': index,
                        'nrc': nrc,
                        'professor_name': professor_name,
                        'dedicacion': dedicacion,
                        'periodo': periodo,
                        'professor_match': prof_match,
                        'professor_found': professor_found,
                        'nrc_exists': nrc_exists,
                        'can_apply': professor_found and nrc_exists,
                        'issues': []
                    }
                    
                    # Add issues
                    if not professor_found:
                        match_record['issues'].append(f"Professor '{professor_name}' not found in database")
                    if not nrc_exists:
                        match_record['issues'].append(f"NRC {nrc} not found in database")
                    if dedicacion < 0 or dedicacion > 200:  # Allow up to 200% dedication
                        match_record['issues'].append(f"Unusual dedication value: {dedicacion}%")
                    
                    if match_record['can_apply']:
                        result['statistics']['ready_to_apply'] += 1
                    
                    result['matches'].append(match_record)
                    
                except Exception as e:
                    result['errors'].append(f"Row {index + 1}: {str(e)}")
            
            result['success'] = True
            return result
            
        except Exception as e:
            result['errors'].append(f"Processing error: {str(e)}")
            return result
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        norm1 = ' '.join(name1.upper().split())
        norm2 = ' '.join(name2.upper().split())
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def validate_nrc_exists(self, nrc: int) -> bool:
        """Check if NRC exists in database"""
        try:
            return self.db_manager.nrc_exists(nrc)
        except:
            return False
    
    def apply_dedication_matches(self, approved_matches: List[Dict]) -> Dict:
        """Apply approved dedication matches to update section records"""
        results = {
            'updated': 0,
            'errors': [],
            'updated_sections': []
        }
        
        # Group matches by NRC to update all professor dedicaciones for each section
        nrc_groups = {}
        for match in approved_matches:
            if not match.get('can_apply', False):
                continue
                
            nrc = match['nrc']
            if nrc not in nrc_groups:
                nrc_groups[nrc] = []
            nrc_groups[nrc].append(match)
        
        # Update each section
        for nrc, matches in nrc_groups.items():
            try:
                # Get current dedicaciones for this section
                current_dedicaciones = self.db_manager.get_seccion_profesor_dedicaciones(nrc)
                
                # Update with new dedicaciones (only for matched professors)
                updated_dedicaciones = current_dedicaciones.copy()
                professor_updates = []
                
                for match in matches:
                    prof_info = match['professor_match']['professor']
                    profesor_id = prof_info['id']
                    dedicacion = int(match['dedicacion'])
                    
                    # Only update if this professor is assigned to this section
                    if self._is_professor_assigned_to_section(profesor_id, nrc):
                        updated_dedicaciones[profesor_id] = dedicacion
                        professor_updates.append({
                            'profesor_id': profesor_id,
                            'profesor_name': f"{prof_info['nombres']} {prof_info['apellidos']}",
                            'dedicacion': dedicacion
                        })
                    else:
                        results['errors'].append(
                            f"Professor {prof_info['nombres']} {prof_info['apellidos']} "
                            f"is not assigned to section {nrc} - skipping dedication update"
                        )
                
                # Apply updates if any professors were updated
                if professor_updates:
                    if self.db_manager.update_seccion_profesor_dedicaciones(nrc, updated_dedicaciones):
                        results['updated'] += 1
                        results['updated_sections'].append({
                            'nrc': nrc,
                            'professor_updates': professor_updates,
                            'total_dedicacion': sum(d['dedicacion'] for d in professor_updates)
                        })
                    else:
                        results['errors'].append(f"Failed to update section {nrc}")
                
            except Exception as e:
                results['errors'].append(f"Error updating section {nrc}: {str(e)}")
        
        return results
    
    def _is_professor_assigned_to_section(self, profesor_id: int, nrc: int) -> bool:
        """Check if professor is assigned to section"""
        try:
            result = self.db_manager.execute_query(
                "SELECT COUNT(*) FROM SeccionProfesor WHERE profesor_id = ? AND seccion_NRC = ?",
                (profesor_id, nrc),
                fetch_one=True
            )
            return result[0] > 0
        except Exception:
            return False
    
    def get_processing_statistics(self, matches: List[Dict]) -> Dict:
        """Generate statistics about the processing results"""
        stats = {
            'total_matches': len(matches),
            'ready_to_apply': sum(1 for m in matches if m.get('can_apply', False)),
            'professor_not_found': sum(1 for m in matches if not m.get('professor_found', False)),
            'nrc_not_found': sum(1 for m in matches if not m.get('nrc_exists', False)),
            'dedication_ranges': {
                '0-25%': sum(1 for m in matches if 0 <= m.get('dedicacion', 0) <= 25),
                '26-50%': sum(1 for m in matches if 26 <= m.get('dedicacion', 0) <= 50),
                '51-75%': sum(1 for m in matches if 51 <= m.get('dedicacion', 0) <= 75),
                '76-100%': sum(1 for m in matches if 76 <= m.get('dedicacion', 0) <= 100),
                '100%+': sum(1 for m in matches if m.get('dedicacion', 0) > 100)
            },
            'unique_professors': len(set(m['professor_name'] for m in matches)),
            'unique_sections': len(set(m['nrc'] for m in matches))
        }
        
        return stats


def validate_dedication_csv_file(file_path: str) -> Dict:
    """Standalone function to validate dedication CSV file format"""
    result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'file_info': {}
    }
    
    try:
        import os
        
        # Basic file checks
        if not os.path.exists(file_path):
            result['errors'].append("File does not exist")
            return result
        
        if not file_path.lower().endswith('.csv'):
            result['warnings'].append("File does not have .csv extension")
        
        # Try to read the file
        df = pd.read_csv(file_path)
        
        # Check required columns
        required_columns = ['seccion', 'profesor', 'dedicacion', 'periodo']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            result['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Check for data
        if df.empty:
            result['errors'].append("CSV file is empty")
        
        # Basic data validation
        if 'dedicacion' in df.columns:
            try:
                numeric_dedicacion = pd.to_numeric(df['dedicacion'], errors='coerce')
                invalid_count = numeric_dedicacion.isna().sum()
                if invalid_count > 0:
                    result['warnings'].append(f"{invalid_count} rows have invalid dedication values")
                
                # Check for reasonable dedication ranges
                valid_dedicacion = numeric_dedicacion.dropna()
                if len(valid_dedicacion) > 0:
                    max_dedicacion = valid_dedicacion.max()
                    min_dedicacion = valid_dedicacion.min()
                    if max_dedicacion > 200:
                        result['warnings'].append(f"Very high dedication values found (max: {max_dedicacion}%)")
                    if min_dedicacion < 0:
                        result['warnings'].append(f"Negative dedication values found (min: {min_dedicacion}%)")
                        
            except:
                result['warnings'].append("Could not validate dedication column")
        
        # File statistics
        result['file_info'] = {
            'total_rows': len(df),
            'columns': list(df.columns),
            'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2)
        }
        
        if not result['errors']:
            result['valid'] = True
        
    except Exception as e:
        result['errors'].append(f"Error reading file: {str(e)}")
    
    return result