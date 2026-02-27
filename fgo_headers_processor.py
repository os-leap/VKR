"""Module for processing FGO headers from filenames or website sources"""

import re
import requests
from urllib.parse import urlparse
import os


class FGOHeadersProcessor:
    """Class for extracting FGO headers from filenames or website sources"""
    
    def __init__(self):
        self.fgo_patterns = [
            r'фгос',
            r'федеральный.*государственный.*образовательный.*стандарт',
            r'государственный.*образовательный.*стандарт',
            r'стандарт.*образования',
            r'фederal.*educational.*standard',
            r'educational.*standard'
        ]
        
        # Patterns to extract class numbers from filenames
        self.class_patterns = [
            r'(\d+)(?:-(?:го|й|ый|ий|ой|ая|яя))?[-_\s]*класс',
            r'(\d+)[-_]*[кk][лl][аa][сc][сc]?[-_\s]*',
            r'[кk][лl][аa][сc][сc]?[-_\s]*(\d+)',
            r'(\d+)[-_\s]*(?:год|year)'
        ]
        
        # Subject patterns
        self.subject_patterns = [
            r'(?:по)?[-_\s]*([а-яёa-z]+)[-_]*[-_\s]*(?:класс|year|год)',
            r'(?:по)?[-_\s]*([а-яёa-z]+)[-_]*[-_\s]*материал',
            r'(?:по)?[-_\s]*([а-яёa-z]+)[-_]*[-_\s]*учебник',
            r'(?:по)?[-_\s]*([а-яёa-z]+)[-_]*[-_\s]*задачник',
            r'(?:по)?[-_\s]*([а-яёa-z]+)[-_]*[-_\s]*план',
            r'(?:по)?[-_\s]*([а-яёa-z]+)[-_]*[-_\s]*программа'
        ]

    def extract_fgo_info_from_filename(self, filename):
        """
        Extract FGO information from filename
        Returns dict with class, subject, and FGO type
        """
        # Normalize filename
        normalized = filename.lower()
        name_without_ext = os.path.splitext(normalized)[0]
        
        # Check if filename contains FGO indicators
        has_fgo = any(re.search(pattern, normalized, re.IGNORECASE) for pattern in self.fgo_patterns)
        
        if not has_fgo:
            return None
            
        # Extract class
        class_number = None
        for pattern in self.class_patterns:
            match = re.search(pattern, name_without_ext, re.IGNORECASE)
            if match:
                class_number = match.group(1)
                break
                
        # Extract subject
        subject = None
        for pattern in self.subject_patterns:
            match = re.search(pattern, name_without_ext, re.IGNORECASE)
            if match:
                subject = match.group(1)
                break
        
        # Determine FGO type
        fgo_type = self._determine_fgo_type(normalized)
        
        return {
            'class': class_number,
            'subject': subject,
            'fgos_type': fgo_type,
            'has_fgo': True
        }

    def _determine_fgo_type(self, text):
        """Determine type of FGO based on keywords in text"""
        if 'дошкольное' in text:
            return 'ФГОС ДО'
        elif 'начальное' in text or '1-' in text or '4-' in text:
            return 'ФГОС НОО'
        elif 'основное' in text or '5-' in text or '9-' in text:
            return 'ФГОС ООО'
        elif 'среднее' in text or '10-' in text or '11-' in text:
            return 'ФГОС СОО'
        elif 'профессиональное' in text or 'спо' in text or 'нпо' in text:
            return 'ФГОС СПО'
        else:
            return 'ФГОС'

    def generate_headers_from_filename(self, filename):
        """Generate FGO header based on filename analysis"""
        fgo_info = self.extract_fgo_info_from_filename(filename)
        
        if not fgo_info:
            return filename  # Return original filename if no FGO info found
            
        # Generate header based on available information
        parts = []
        
        # Add FGO type
        if fgo_info['fgos_type']:
            parts.append(fgo_info['fgos_type'])
            
        # Add class if available
        if fgo_info['class']:
            parts.append(f"{fgo_info['class']} класс")
            
        # Add subject if available
        if fgo_info['subject']:
            # Convert subject to readable form
            subject_readable = self._convert_subject_name(fgo_info['subject'])
            parts.append(f"по {subject_readable}")
        
        if parts:
            return " ".join(parts)
        else:
            return filename

    def _convert_subject_name(self, subject_code):
        """Convert abbreviated subject names to full names"""
        subject_map = {
            'математика': 'Математике',
            'русский': 'Русскому языку',
            'литература': 'Литературе',
            'история': 'Истории',
            'география': 'Географии',
            'биология': 'Биологии',
            'химия': 'Химии',
            'физика': 'Физике',
            'английский': 'Английскому языку',
            'немецкий': 'Немецкому языку',
            'французский': 'Французскому языку',
            'информатика': 'Информатике',
            'технология': 'Технологии',
            'музыка': 'Музыке',
            'изо': 'Изобразительному искусству',
            'окр_мир': 'Окружающему миру',
            'обществознание': 'Обществознанию',
            'право': 'Праву',
            'экономика': 'Экономике'
        }
        
        # Normalize subject name
        normalized = subject_code.lower().replace('_', ' ').replace('-', ' ')
        for abbrev, full_name in subject_map.items():
            if abbrev in normalized:
                return full_name
                
        # If no mapping found, return capitalized version
        return subject_code.capitalize()

    def fetch_fgo_headers_from_website(self, url):
        """
        Fetch FGO headers from website
        This method would fetch FGO headers from edsoo.ru or other educational websites
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # This is a simplified implementation
            # In a real application, you would parse the website content
            # and extract relevant FGO information
            
            # Look for FGO-related keywords in page content
            content = response.text.lower()
            
            fgo_indicators = [
                'фгос',
                'федеральный государственный образовательный стандарт',
                'образовательный стандарт',
                'стандарт образования'
            ]
            
            has_fgo = any(indicator in content for indicator in fgo_indicators)
            
            if has_fgo:
                # Extract title from HTML
                title_match = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
                if title_match:
                    return title_match.group(1)
                    
                # Or look for h1 tags
                h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', response.text, re.IGNORECASE)
                if h1_match:
                    return h1_match.group(1)
                    
            return None
            
        except Exception as e:
            print(f"Error fetching FGO headers from {url}: {e}")
            return None

    def process_file_and_extract_fgo(self, filepath_or_url):
        """
        Process file or URL and extract FGO information
        """
        if filepath_or_url.startswith(('http://', 'https://')):
            # It's a URL
            return self.fetch_fgo_headers_from_website(filepath_or_url)
        else:
            # It's a local file
            filename = os.path.basename(filepath_or_url)
            return self.generate_headers_from_filename(filename)


# Example usage
if __name__ == "__main__":
    processor = FGOHeadersProcessor()
    
    # Test with various filenames
    test_files = [
        "fgos_matematika_5_klass.pdf",
        "ФГОС_Русский_язык_3_класс.docx",
        "programma_po_fgos_istoria_7_klass.pdf",
        "normal_file.txt"
    ]
    
    for test_file in test_files:
        header = processor.generate_headers_from_filename(test_file)
        print(f"File: {test_file} -> Header: {header}")