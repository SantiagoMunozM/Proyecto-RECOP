# Create a new file: personal_data_processor.py

import pandas as pd
import os
import re
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
from database import DatabaseManager

class PersonalDataProcessor:
    """Processor for integrating personal data with existing professor records"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.match_threshold = 0.3  # Similarity threshold for name matching
    
    def standardize_name_from_personal_data(self, apellidos_nombres: str) -> Tuple[str, str]:
        """
        Convert name format to separate nombres and apellidos
        
        Handles two formats:
        1. "APELLIDOS, NOMBRES" format (comma-separated)
        2. "APELLIDOS NOMBRES" format (space-separated, no comma)
        
        For space-separated format without comma:
        - 2 elements: first = apellido, second = nombre
        - 3 elements: first = apellido, second+third = nombres
        - 4 elements: first+second = apellidos, third+fourth = nombres
        
        Args:
            apellidos_nombres: Name in various formats
            
        Returns:
            Tuple of (nombres, apellidos)
        """
        if not apellidos_nombres or pd.isna(apellidos_nombres):
            return "", ""
        
        # Clean the input
        name_str = str(apellidos_nombres).strip()
        
        # Check if comma-separated format
        if ',' in name_str:
            # Original comma-separated logic
            parts = name_str.split(',', 1)
            apellidos_part = parts[0].strip()
            nombres_part = parts[1].strip() if len(parts) > 1 else ""
            
            # Clean up extra spaces
            nombres = ' '.join(nombres_part.split())
            apellidos = ' '.join(apellidos_part.split())
            
            return nombres, apellidos
        
        else:
            # Space-separated format (no comma)
            # Split by spaces and filter out empty strings
            parts = [part.strip() for part in name_str.split() if part.strip()]
            
            if len(parts) == 1:
                # Only one part - treat as apellido
                return "", parts[0]
            elif len(parts) == 2:
                # Two parts: first = apellido, second = nombre
                apellidos = parts[0]
                nombres = parts[1]
                return nombres, apellidos
            elif len(parts) == 3:
                # Three parts: first = apellido, second+third = nombres
                apellidos = parts[0]
                nombres = f"{parts[1]} {parts[2]}"
                return nombres, apellidos
            elif len(parts) == 4:
                # Four parts: first+second = apellidos, third+fourth = nombres
                apellidos = f"{parts[0]} {parts[1]}"
                nombres = f"{parts[2]} {parts[3]}"
                return nombres, apellidos
            else:
                # More than 4 parts - use similar logic as CSV processor
                # Assume first half are apellidos, second half are nombres
                mid_point = len(parts) // 2
                apellidos = ' '.join(parts[:mid_point])
                nombres = ' '.join(parts[mid_point:])
                return nombres, apellidos
    
    def create_full_name_standardized(self, nombres: str, apellidos: str) -> str:
        """
        Create standardized full name in "NOMBRES APELLIDOS" format
        
        Args:
            nombres: First names
            apellidos: Last names
            
        Returns:
            Full name in standardized format
        """
        nombres_clean = nombres.strip() if nombres else ""
        apellidos_clean = apellidos.strip() if apellidos else ""
        
        if nombres_clean and apellidos_clean:
            return f"{nombres_clean} {apellidos_clean}"
        elif apellidos_clean:
            return apellidos_clean
        elif nombres_clean:
            return nombres_clean
        else:
            return ""
    
    
    def extract_position_info(self, cargo: str, categoria_ordenamiento: str = "", 
                             subcategoria_ordenamiento: str = "", categoria_especial: str = "",
                             dependencia: str = "", tipo_contrato: str = "") -> Dict[str, any]:
        """
        Extract position information from the "Cargo" field and academic ranking columns
        UPDATED: Apply gender normalization consistently to all tipo extractions
        """
        # Always store the original cargo
        cargo_clean = str(cargo).strip() if cargo and not pd.isna(cargo) else ""
        if not cargo_clean:
            cargo_clean = "N/A"
        
        result = {
            'tipo': None,
            'subcategoria': None,
            'cargo_original': cargo_clean,
            'dependencia': dependencia.strip() if dependencia and not pd.isna(dependencia) else None,
            'contrato': tipo_contrato.strip() if tipo_contrato and not pd.isna(tipo_contrato) else None
        }
        
        #print(f"DEBUG: Processing - Cargo: '{cargo_clean}', Categoria: '{categoria_ordenamiento}', Subcategoria: '{subcategoria_ordenamiento}', Especial: '{categoria_especial}'")
        
        # Clean academic ranking fields
        categoria_clean = str(categoria_ordenamiento).strip() if categoria_ordenamiento and not pd.isna(categoria_ordenamiento) else ""
        subcategoria_clean = str(subcategoria_ordenamiento).strip() if subcategoria_ordenamiento and not pd.isna(subcategoria_ordenamiento) else ""
        especial_clean = str(categoria_especial).strip() if categoria_especial and not pd.isna(categoria_especial) else ""
        
        # Priority 1: Check for "Categoría Especial" first (highest priority)
        if especial_clean and especial_clean.upper() != "N/A":
            #print(f"DEBUG: Found special category: '{especial_clean}'")
            
            # Handle special categories like "Profesor Emerito"
            if "PROFESOR" in especial_clean.upper() and "EMERITO" in especial_clean.upper():
                result['tipo'] = "EMERITO"
                result['subcategoria'] = None
            elif "EMERITO" in especial_clean.upper():
                result['tipo'] = "EMERITO"
                result['subcategoria'] = None
            else:
                # For other special categories, normalize gender and use as is
                result['tipo'] = self.normalize_gender_in_tipo(especial_clean.upper())
                result['subcategoria'] = None
            
            #print(f"DEBUG: Special category result: tipo='{result['tipo']}', subcategoria={result['subcategoria']}")
            return result
        
        # Priority 2: Check if cargo indicates professor position
        cargo_is_professor = False
        if cargo_clean and cargo_clean.upper() != "N/A":
            profesor_pattern = r'^Profesor[/a]*\s+(.+)$'
            match = re.match(profesor_pattern, cargo_clean, re.IGNORECASE)
            
            if match:
                cargo_is_professor = True
                position_part = match.group(1).strip()
                #print(f"DEBUG: Cargo indicates professor: '{position_part}'")
                
                # Try to extract tipo and subcategoria from cargo
                ranking_pattern = r'^(\w+)\s+(\d+)$'
                ranking_match = re.match(ranking_pattern, position_part)
                
                if ranking_match:
                    # FIXED: Apply gender normalization to cargo-extracted tipo
                    result['tipo'] = self.normalize_gender_in_tipo(ranking_match.group(1).upper())
                    result['subcategoria'] = int(ranking_match.group(2))
                    #print(f"DEBUG: Extracted from cargo - tipo='{result['tipo']}', subcategoria={result['subcategoria']}")
                else:
                    # FIXED: Apply gender normalization to cargo-extracted tipo
                    result['tipo'] = self.normalize_gender_in_tipo(position_part.upper())
                    result['subcategoria'] = None
                    #print(f"DEBUG: Extracted from cargo - tipo='{result['tipo']}', no subcategoria")
        
        # Priority 3: Check "Categoría de ordenamiento" and "Subcategoría de ordenamiento"
        # This applies whether cargo is professor or not (administrative staff who also teach)
        if categoria_clean and categoria_clean.upper() != "N/A":
            #print(f"DEBUG: Found categoria de ordenamiento: '{categoria_clean}'")
            
            # If we already have tipo from cargo but categoria provides more specific info, use categoria
            # OR if cargo is not professor but categoria exists (administrative staff who teach)
            if not cargo_is_professor or not result['tipo']:
                # FIXED: Apply gender normalization to categoria-extracted tipo
                result['tipo'] = self.normalize_gender_in_tipo(categoria_clean.upper())
                #print(f"DEBUG: Using categoria de ordenamiento as tipo: '{result['tipo']}'")
            
            # Handle subcategoria from subcategoria_ordenamiento
            if subcategoria_clean and subcategoria_clean.upper() != "N/A":
                try:
                    # Try to extract number from subcategoria column
                    # Handle cases like "2", "Titular 2", or just "Titular"
                    if subcategoria_clean.isdigit():
                        result['subcategoria'] = int(subcategoria_clean)
                        #print(f"DEBUG: Direct subcategoria number: {result['subcategoria']}")
                    else:
                        # Try to extract number from text like "Titular 2"
                        number_match = re.search(r'(\d+)', subcategoria_clean)
                        if number_match:
                            result['subcategoria'] = int(number_match.group(1))
                            #print(f"DEBUG: Extracted subcategoria number: {result['subcategoria']}")
                        else:
                            # If no number, use the categoria from subcategoria if different
                            '''
                            if subcategoria_clean.upper() != categoria_clean.upper():
                                # This might be a different academic level
                                print(f"DEBUG: Subcategoria text differs from categoria: '{subcategoria_clean}'")
                            '''
                            result['subcategoria'] = None
                except (ValueError, TypeError):
                    #print(f"DEBUG: Could not parse subcategoria: '{subcategoria_clean}'")
                    result['subcategoria'] = None
        
        # Priority 4: If no academic ranking found anywhere, set tipo based on cargo or default
        if not result['tipo']:
            if cargo_clean and cargo_clean.upper() != "N/A":
                # FIXED: Apply gender normalization to fallback tipo
                result['tipo'] = self.normalize_gender_in_tipo(cargo_clean.upper())
                #print(f"DEBUG: Using full cargo as tipo: '{result['tipo']}'")
            else:
                result['tipo'] = "N/A"
                #print(f"DEBUG: No information found, setting tipo to N/A")
        
        #print(f"DEBUG: Final result: {result}")
        return result
    
    def normalize_gender_in_tipo(self, tipo_text: str) -> str:
        """
        Normalize gendered professor titles to standard gender-neutral forms
        
        Args:
            tipo_text: The tipo text to normalize
            
        Returns:
            str: Normalized tipo without gender variations
        """
        if not tipo_text:
            return tipo_text
        
        tipo_upper = tipo_text.upper().strip()
        
        # Direct mappings for full phrases first
        direct_mappings = {
            'PROFESOR ASOCIADO': 'ASOCIADO',
            'PROFESORA ASOCIADA': 'ASOCIADO',
            'PROFESOR ASISTENTE': 'ASISTENTE',
            'PROFESORA ASISTENTE': 'ASISTENTE',
            'PROFESOR TITULAR': 'TITULAR',
            'PROFESORA TITULAR': 'TITULAR',
            'PROFESOR VISITANTE': 'VISITANTE',
            'PROFESOR DE CÁTEDRA': 'CÁTEDRA',
            'PROFESORA DE CÁTEDRA': 'CÁTEDRA',
            'PROFESOR CÁTEDRA': 'CÁTEDRA',
            'PROFESORA CÁTEDRA': 'CÁTEDRA',
            'INSTRUCTOR': 'INSTRUCTOR',
            'INSTRUCTORA': 'INSTRUCTOR'
        }
        
        # Check for exact matches first
        if tipo_upper in direct_mappings:
            return direct_mappings[tipo_upper]
        
        # Fallback: partial matching for word-based normalization
        if 'ASOCIADO' in tipo_upper or 'ASOCIADA' in tipo_upper:
            return 'ASOCIADO'
        elif 'TITULAR' in tipo_upper:
            return 'TITULAR'
        elif 'ADJUNTO' in tipo_upper or 'ADJUNTA' in tipo_upper:
            return 'ADJUNTO'
        elif 'CÁTEDRA' in tipo_upper:
            return 'CÁTEDRA'
        elif 'INSTRUCTOR' in tipo_upper:
            return 'INSTRUCTOR'
        elif 'EMERITO' in tipo_upper:
            return 'EMERITO'
        elif 'ASISTENTE GRADUADO DOCTORAL' in tipo_upper:
            return 'AGD'
        elif 'ASISTENTE GRADUADO MAESTRÍA' in tipo_upper:
            return 'AGM'
        elif 'COORDINADOR ACADÉMICO' in tipo_upper or 'COORDINADORA ACADÉMICA' in tipo_upper:
            return 'COORDINADOR'
        # Return original if no match found
        return tipo_upper
    
    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names
        
        Args:
            name1: First name string
            name2: Second name string
            
        Returns:
            Similarity score between 0 and 1
        """
        if not name1 or not name2:
            return 0.0
        
        # Normalize names (uppercase, remove extra spaces)
        norm1 = ' '.join(name1.upper().split())
        norm2 = ' '.join(name2.upper().split())
        
        # Calculate similarity using SequenceMatcher
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    # Update this part in the find_matching_professors method in personal_data_processor.py:
    
    def find_matching_professors(self, personal_data_df: pd.DataFrame) -> List[Dict]:
        """
        Find matching professors between personal data and existing database
        MODIFIED: Find best personal data match for each existing professor
        """
        matches = []
        
        # Get all existing professors (these are the ones we want to enhance)
        existing_professors = self.db_manager.get_all_profesores()
        
        # Create a lookup dictionary for personal data records
        personal_data_records = []
        for index, row in personal_data_df.iterrows():
            # Skip if not from engineering faculty
            if 'FACULTAD DE INGENIERÍA' not in str(row.get('Facultad_Unidad', '')):
                continue
                
            # Parse name from personal data
            apellidos_nombres = row.get('Apellido_y_Nombre', '')
            nombres, apellidos = self.standardize_name_from_personal_data(apellidos_nombres)
            
            if not nombres and not apellidos:
                continue
                
            full_name_personal = self.create_full_name_standardized(nombres, apellidos)
            
            # Extract position info
            cargo = row.get('Cargo', '')
            categoria_ordenamiento = row.get('Categoría_de_ordenamiento', '')
            subcategoria_ordenamiento = row.get('Subcategoría_de_ordenamiento', '')
            categoria_especial = row.get('Categoría_Especial', '')
            dependencia = row.get('Dependencia', '')
            tipo_contrato = row.get('Tipo_de_contrato', '')
            
            position_info = self.extract_position_info(
                cargo, categoria_ordenamiento, subcategoria_ordenamiento, 
                categoria_especial, dependencia, tipo_contrato
            )
            
            personal_data_records.append({
                'personal_data': {
                    'person_id': row.get('Número_de_persona', ''),
                    'apellidos_nombres': apellidos_nombres,
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'full_name_standardized': full_name_personal,
                    'cargo': cargo,
                    'departamento': row.get('Dependencia', ''),
                    'facultad': row.get('Facultad_Unidad', ''),
                    'categoria_ordenamiento': categoria_ordenamiento,
                    'subcategoria_ordenamiento': subcategoria_ordenamiento,
                    'categoria_especial': categoria_especial,
                    'dependencia': dependencia,
                    'tipo_contrato': tipo_contrato
                },
                'position_info': position_info
            })
        
        # Now, for each existing professor, find the best match in personal data
        for existing_prof in existing_professors:
            existing_full_name = existing_prof['full_name']
            
            best_match_record = None
            best_score = 0
            
            # Search through all personal data records for the best match
            for record in personal_data_records:
                personal_full_name = record['personal_data']['full_name_standardized']
                similarity = self.calculate_name_similarity(existing_full_name, personal_full_name)
                
                if similarity > best_score and similarity >= self.match_threshold:
                    best_score = similarity
                    best_match_record = record
            
            # If we found a good match, add it to results
            if best_match_record:
                '''
                print(f"DEBUG: Match found for existing professor {existing_full_name} -> "
                      f"personal data: {best_match_record['personal_data']['full_name_standardized']}, "
                      f"confidence: {best_score:.3f}")
                '''
                match_record = {
                    'personal_data': best_match_record['personal_data'],
                    'existing_professor': existing_prof,
                    'position_info': best_match_record['position_info'],
                    'match_confidence': best_score,
                    'match_type': 'automatic' if best_score >= 0.95 else 'review_needed'
                }
                matches.append(match_record)
            '''
            else:
                print(f"DEBUG: No match found for existing professor {existing_full_name}")
            '''
        
        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x['match_confidence'], reverse=True)
        
        #print(f"DEBUG: Found {len(matches)} matches for {len(existing_professors)} existing professors")
        return matches
    
    def load_personal_data_csv(self, file_path: str) -> pd.DataFrame:
        """
        Load and validate personal data CSV file
        
        Args:
            file_path: Path to the personal data CSV file
            
        Returns:
            DataFrame with personal data
        """
        try:
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = [
                'Facultad_Unidad',
                'Dependencia', 
                'Cargo',
                'Número_de_persona',
                'Apellido_y_Nombre'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            return df
            
        except Exception as e:
            raise Exception(f"Error loading personal data CSV: {str(e)}")
    
    def get_match_statistics(self, matches: List[Dict]) -> Dict:
        """
        Get statistics about the matching process
        UPDATED: Statistics now reflect existing professors being matched
        """
        if not matches:
            return {
                'total_matches': 0,
                'automatic_matches': 0,
                'review_needed': 0,
                'avg_confidence': 0,
                'position_types': {},
                'departments': {},
                'existing_professors_matched': 0,
                'existing_professors_unmatched': 0
            }
        
        automatic = sum(1 for m in matches if m['match_type'] == 'automatic')
        review_needed = sum(1 for m in matches if m['match_type'] == 'review_needed')
        avg_confidence = sum(m['match_confidence'] for m in matches) / len(matches)
        
        # Count position types from personal data
        position_types = {}
        departments = {}
        
        for match in matches:
            tipo = match['position_info']['tipo']
            dept = match['personal_data']['departamento']
            
            position_types[tipo] = position_types.get(tipo, 0) + 1
            departments[dept] = departments.get(dept, 0) + 1
        
        # Get total existing professors for comparison
        total_existing = len(self.db_manager.get_all_profesores())
        
        return {
            'total_matches': len(matches),
            'automatic_matches': automatic,
            'review_needed': review_needed,
            'avg_confidence': avg_confidence,
            'position_types': position_types,
            'departments': departments,
            'existing_professors_matched': len(matches),
            'existing_professors_unmatched': total_existing - len(matches)
        }
    
    def apply_approved_matches(self, approved_matches: List[Dict]) -> Dict:
        """
        Apply approved matches to update professor records
        
        Args:
            approved_matches: List of approved match records
            
        Returns:
            Dictionary with results
        """
        results = {
            'updated': 0,
            'errors': [],
            'updated_professors': []
        }
        
        for match in approved_matches:
            try:
                prof_id = match['existing_professor']['id']
                personal_data = match['personal_data']
                position_info = match['position_info']
                
                # Update professor with personal data
                success = self.db_manager.update_professor_personal_data(
                    profesor_id=prof_id,
                    person_id=int(personal_data['person_id']) if personal_data['person_id'] else None,
                    cargo_original=position_info['cargo_original'],
                    tipo_enhanced=position_info['tipo'],
                    subcategoria=position_info['subcategoria'],
                    dependencia = position_info['dependencia'],
                    contrato = position_info['contrato'],
                )
                
                if success:
                    results['updated'] += 1
                    results['updated_professors'].append({
                        'id': prof_id,
                        'name': match['existing_professor']['full_name'],
                        'new_tipo': position_info['tipo'],
                        'subcategoria': position_info['subcategoria'],
                        'dependencia': position_info['dependencia'],
                        'contrato': position_info['contrato']
                    })
                else:
                    results['errors'].append(f"Failed to update professor ID {prof_id}")
                    
            except Exception as e:
                results['errors'].append(f"Error updating professor: {str(e)}")
        
        return results

# Test functions
def test_name_parsing():
    """Test function for name parsing"""
    processor = PersonalDataProcessor(None)
    
    test_cases = [
        "RODRIGUEZ GARCIA, JUAN PABLO",
        "SMITH, MARY ANN",
        "GONZALEZ PEREZ, CARLOS",
        "MARTINEZ, ANA MARIA",
        "BROWN JOHNSON, ROBERT"
    ]
    
    #print("Testing name parsing:")
    for name in test_cases:
        nombres, apellidos = processor.standardize_name_from_personal_data(name)
        full_name = processor.create_full_name_standardized(nombres, apellidos)
        '''
        print(f"Input: {name}")
        print(f"Output: nombres='{nombres}', apellidos='{apellidos}'")
        print(f"Full name: {full_name}")
        print("-" * 50)
        '''

def test_position_extraction():
    """Test function for position extraction"""
    processor = PersonalDataProcessor(None)
    
    test_cases = [
        "Profesor Titular",
        "Profesora Titular 3",
        "Profesor Asociado 2", 
        "Profesora Asistente 1",
        "Director Departamento",
        "Coordinador Académico",
        "Asistente Graduado Doctoral Investigación"
    ]
    
    #print("\nTesting position extraction:")
    for cargo in test_cases:
        result = processor.extract_position_info(cargo)
        '''
        print(f"Input: {cargo}")
        print(f"Output: {result}")
        print("-" * 50)
        '''

# Add this new class to personal_data_processor.py:

class PersonalDataLinkingEngine:
    """Engine for linking personal data with existing professor records"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.processor = PersonalDataProcessor(db_manager)
        self.current_matches = []
        self.approved_matches = []
        self.rejected_matches = []
    
    def load_and_process_personal_data(self, file_path: str) -> Dict:
        """
        Load personal data file and find matches with existing professors
        
        Args:
            file_path: Path to personal data CSV file
            
        Returns:
            Dictionary with processing results
        """
        result = {
            'success': False,
            'matches': [],
            'statistics': {},
            'errors': [],
            'file_info': {}
        }
        
        try:
            # Load CSV file
            df = self.processor.load_personal_data_csv(file_path)
            
            # Get file information
            result['file_info'] = {
                'total_rows': len(df),
                'engineering_faculty_rows': len(df[df['Facultad_Unidad'].str.contains('FACULTAD DE INGENIERÍA', na=False)]),
                'file_name': os.path.basename(file_path),
                'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2)
            }
            
            # Find matches
            matches = self.processor.find_matching_professors(df)
            self.current_matches = matches
            
            # Generate statistics
            statistics = self.processor.get_match_statistics(matches)
            
            # Additional statistics
            statistics['file_info'] = result['file_info']
            statistics['existing_professors_count'] = len(self.db_manager.get_all_profesores())
            statistics['professors_without_personal_data'] = len(self.db_manager.get_professors_without_personal_data())
            
            result.update({
                'success': True,
                'matches': matches,
                'statistics': statistics
            })
            
        except Exception as e:
            result['errors'].append(f"Error processing file: {str(e)}")
            
        return result
    
    def categorize_matches_by_confidence(self, matches: List[Dict]) -> Dict:
        """Categorize matches by confidence levels"""
        categories = {
            'high_confidence': [],      # >= 0.95
            'medium_confidence': [],    # 0.90 - 0.94
            'low_confidence': [],       # 0.85 - 0.89
            'review_required': []       # All matches need some review
        }
        
        for match in matches:
            confidence = match['match_confidence']
            
            if confidence >= 0.95:
                categories['high_confidence'].append(match)
            elif confidence >= 0.90:
                categories['medium_confidence'].append(match)
            else:
                categories['low_confidence'].append(match)
            
            # All matches go to review_required for manual verification
            categories['review_required'].append(match)
        
        return categories
    
    def get_match_preview(self, match: Dict) -> Dict:
        """Get a detailed preview of a match for review"""
        existing_prof = match['existing_professor']
        personal_data = match['personal_data']
        position_info = match['position_info']
        
        return {
            'match_id': id(match),  # Use object id as temporary identifier
            'confidence': match['match_confidence'],
            'match_type': match['match_type'],
            
            # Existing professor data
            'existing': {
                'id': existing_prof['id'],
                'full_name': existing_prof['full_name'],
                'nombres': existing_prof['nombres'],
                'apellidos': existing_prof['apellidos'],
                'tipo_actual': existing_prof['tipo'],
                'departamentos': existing_prof.get('departamentos', 'No especificado')
            },
            
            # Personal data
            'personal': {
                'person_id': personal_data['person_id'],
                'full_name_standardized': personal_data['full_name_standardized'],
                'nombres': personal_data['nombres'],
                'apellidos': personal_data['apellidos'],
                'cargo_original': personal_data['cargo'],
                'departamento_oficial': personal_data['departamento'],
                'facultad': personal_data['facultad'],
                'dependencia': personal_data.get('dependencia', ''),
                'tipo_contrato': personal_data.get('tipo_contrato', ''),
            },
            
            # Proposed changes
            'changes': {
                'new_tipo': position_info['tipo'],
                'subcategoria': position_info['subcategoria'],
                'cargo_original': position_info['cargo_original'],
                'person_id': personal_data['person_id'],
                'dependencia': personal_data.get('dependencia'),
                'tipo_contrato': personal_data.get('tipo_contrato'),
            },
            
            # Comparison flags
            'flags': {
                'name_exact_match': personal_data['full_name_standardized'].upper() == existing_prof['full_name'].upper(),
                'tipo_will_change': existing_prof['tipo'] != position_info['tipo'],
                'has_person_id': bool(personal_data['person_id']),
                'has_subcategoria': position_info['subcategoria'] is not None
            }
        }
    
    def approve_match(self, match_id: int) -> bool:
        """Approve a specific match for processing"""
        match = self._find_match_by_id(match_id)
        if match and match not in self.approved_matches:
            self.approved_matches.append(match)
            if match in self.rejected_matches:
                self.rejected_matches.remove(match)
            return True
        return False
    
    def reject_match(self, match_id: int) -> bool:
        """Reject a specific match"""
        match = self._find_match_by_id(match_id)
        if match and match not in self.rejected_matches:
            self.rejected_matches.append(match)
            if match in self.approved_matches:
                self.approved_matches.remove(match)
            return True
        return False
    
    def approve_all_high_confidence(self) -> int:
        """Approve all high confidence matches (>= 0.95)"""
        count = 0
        for match in self.current_matches:
            if match['match_confidence'] >= 0.95:
                match_id = id(match)
                if self.approve_match(match_id):
                    count += 1
        return count
    
    def get_approval_summary(self) -> Dict:
        """Get summary of approved/rejected matches"""
        return {
            'total_matches': len(self.current_matches),
            'approved': len(self.approved_matches),
            'rejected': len(self.rejected_matches),
            'pending': len(self.current_matches) - len(self.approved_matches) - len(self.rejected_matches),
            'ready_to_apply': len(self.approved_matches) > 0
        }
    
    def apply_approved_matches(self) -> Dict:
        """Apply all approved matches to the database"""
        if not self.approved_matches:
            return {
                'success': False,
                'error': 'No approved matches to apply',
                'results': {}
            }
        
        try:
            results = self.processor.apply_approved_matches(self.approved_matches)
            
            if results['updated'] > 0:
                # Clear approved matches after successful application
                self.approved_matches.clear()
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': {}
            }
    
    def export_match_report(self, file_path: str = None) -> str:
        """Export detailed match report"""
        if not file_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"personal_data_matches_{timestamp}.txt"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("PERSONAL DATA MATCHING REPORT\n")
                f.write("=" * 50 + "\n\n")
                
                # Summary statistics
                stats = self.processor.get_match_statistics(self.current_matches)
                f.write(f"Total matches found: {stats['total_matches']}\n")
                f.write(f"Automatic matches: {stats['automatic_matches']}\n")
                f.write(f"Review needed: {stats['review_needed']}\n")
                f.write(f"Average confidence: {stats['avg_confidence']:.3f}\n\n")
                
                # Position types breakdown
                f.write("POSITION TYPES:\n")
                for tipo, count in stats['position_types'].items():
                    f.write(f"  {tipo}: {count}\n")
                f.write("\n")
                
                # Detailed matches
                f.write("DETAILED MATCHES:\n")
                f.write("-" * 100 + "\n")
                
                for i, match in enumerate(self.current_matches, 1):
                    preview = self.get_match_preview(match)
                    
                    f.write(f"\nMatch {i} (Confidence: {preview['confidence']:.3f}):\n")
                    f.write(f"  Existing: {preview['existing']['full_name']} (ID: {preview['existing']['id']})\n")
                    f.write(f"  Personal: {preview['personal']['full_name_standardized']} (Person ID: {preview['personal']['person_id']})\n")
                    f.write(f"  Cargo: {preview['personal']['cargo_original']}\n")
                    f.write(f"  Proposed tipo: {preview['changes']['new_tipo']}\n")
                    f.write(f"  Subcategoria: {preview['changes']['subcategoria']}\n")
                    f.write(f"  Status: {'APPROVED' if match in self.approved_matches else 'REJECTED' if match in self.rejected_matches else 'PENDING'}\n")
                
                f.write("\n" + "=" * 50 + "\n")
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Error exporting report: {str(e)}")
    
    def _find_match_by_id(self, match_id: int):
        """Find match by ID (using object id)"""
        for match in self.current_matches:
            if id(match) == match_id:
                return match
        return None
    
    def reset_session(self):
        """Reset the current linking session"""
        self.current_matches.clear()
        self.approved_matches.clear()
        self.rejected_matches.clear()

# Add convenience functions
def create_linking_engine(db_manager: DatabaseManager) -> PersonalDataLinkingEngine:
    """Create a new linking engine instance"""
    return PersonalDataLinkingEngine(db_manager)

def validate_personal_data_file(file_path: str) -> Dict:
    """Validate personal data file format"""
    result = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'file_info': {}
    }
    
    try:
        import pandas as pd
        
        # Basic file checks
        if not os.path.exists(file_path):
            result['errors'].append("File does not exist")
            return result
        
        if not file_path.lower().endswith('.csv'):
            result['warnings'].append("File does not have .csv extension")
        
        # Try to read the file
        df = pd.read_csv(file_path)
        
        # Check required columns
        required_columns = [
            'Facultad_Unidad',
            'Dependencia', 
            'Cargo',
            'Número_de_persona',
            'Apellido_y_Nombre'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            result['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Check for engineering faculty data
        if 'Facultad_Unidad' in df.columns:
            engineering_count = len(df[df['Facultad_Unidad'].str.contains('FACULTAD DE INGENIERÍA', na=False)])
            if engineering_count == 0:
                result['warnings'].append("No engineering faculty records found")
            else:
                result['file_info']['engineering_records'] = engineering_count
        
        # Basic statistics
        result['file_info'].update({
            'total_rows': len(df),
            'columns': list(df.columns),
            'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2)
        })
        
        if not result['errors']:
            result['valid'] = True
        
    except Exception as e:
        result['errors'].append(f"Error reading file: {str(e)}")
    
    return result


def test_subcategory_extraction():
    """Test subcategory extraction with sample data"""
    test_cases = [
        "Profesor Titular 3",
        "Profesora Titular 2", 
        "Profesor Asociado 1",
        "Profesora Asistente",
        "Profesor Cátedra",
        "Director Departamento"
    ]
    
    processor = PersonalDataProcessor(None)
    
    #print("\n=== TESTING SUBCATEGORY EXTRACTION ===")
    for cargo in test_cases:
        result = processor.extract_position_info(cargo)
        
        
        #print(f"Input: '{cargo}' -> Output: {result}")
        
    #print("=== END TEST ===\n")
    

test_subcategory_extraction()