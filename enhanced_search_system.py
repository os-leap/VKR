"""Enhanced search system with content search, FGOs integration, and similarity recommendations"""

import re
import os
import json
from datetime import datetime
from collections import defaultdict
from difflib import SequenceMatcher


class EnhancedMaterial:
    """Enhanced class for representing educational material with content and file data"""
    def __init__(self, title, description, grade, subject, content="", file_path=None, tags=None, fgo_list=None, original_id=None):
        self.original_id = original_id  # Store the original database ID
        self.id = hash(title + str(grade) + subject) % 10000  # Simple ID generation
        self.title = title
        self.description = description
        self.grade = grade  # class (e.g., 5)
        self.subject = subject  # subject (e.g., "mathematics")
        self.content = content or ""  # Additional content field for searching
        self.file_path = file_path  # Path to associated file
        self.tags = tags or []  # Additional tags
        self.fgo_list = fgo_list or []  # FGOs list for this material
        self.extracted_content = self._extract_content_from_file()
    
    def _extract_content_from_file(self):
        """Extract content from file if available"""
        if self.file_path and os.path.exists(self.file_path):
            try:
                if self.file_path.lower().endswith('.pdf'):
                    import PyPDF2
                    with open(self.file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        content = ""
                        for page in pdf_reader.pages:
                            content += page.extract_text()
                        return content
                elif self.file_path.lower().endswith(('.txt', '.docx')):
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        return f.read()
            except Exception as e:
                print(f"Error extracting content from {self.file_path}: {e}")
        return ""

    def get_searchable_text(self):
        """Get all searchable text including title, description, content and FGOs"""
        searchable_parts = [
            self.title or "",
            self.description or "",
            self.content or "",
            self.extracted_content or "",
            " ".join(self.tags),
            " ".join(self.fgo_list)
        ]
        return " ".join(searchable_parts).lower()


class EnhancedSearchSystem:
    """Enhanced search system with improved capabilities"""
    
    def __init__(self):
        self.materials = []
        self.materials_by_id = {}
    
    def add_material(self, material):
        """Add material to system and index by ID"""
        self.materials.append(material)
        self.materials_by_id[material.id] = material
    
    def search_by_content(self, query, grade=None, subject=None, tags=None):
        """
        Enhanced search that looks in title, description, content, file content and FGOs
        """
        results = []
        query_lower = query.lower()
        
        for material in self.materials:
            # Check basic filters first
            grade_match = (grade is None) or (material.grade == grade)
            subject_match = (subject is None) or (material.subject.lower() == subject.lower())
            tag_match = (tags is None) or any(tag in material.tags for tag in tags)
            
            if not (grade_match and subject_match and tag_match):
                continue
            
            # Search in all content areas
            searchable_text = material.get_searchable_text()
            
            # Calculate similarity score based on query matching
            similarity_score = self._calculate_similarity(query_lower, searchable_text)
            
            if similarity_score > 0.1:  # Threshold for relevance
                results.append({
                    'material': material,
                    'similarity_score': similarity_score,
                    'matches': self._find_matches(query_lower, searchable_text)
                })
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return [r['material'] for r in results]
    
    def _calculate_similarity(self, query, text):
        """Calculate similarity between query and text"""
        if not query or not text:
            return 0
        
        # Use SequenceMatcher to calculate similarity ratio
        matcher = SequenceMatcher(None, query, text)
        return matcher.ratio()
    
    def _find_matches(self, query, text):
        """Find specific matches of query in text"""
        matches = []
        query_words = query.split()
        
        for word in query_words:
            if word in text:
                # Find context around the match
                start_idx = max(0, text.find(word) - 50)
                end_idx = min(len(text), text.find(word) + len(word) + 50)
                context = text[start_idx:end_idx]
                matches.append({
                    'word': word,
                    'context': context
                })
        
        return matches
    
    def search_in_fgos_lists(self, query):
        """Search specifically in FGOs lists across all materials"""
        results = []
        query_lower = query.lower()
        
        for material in self.materials:
            # Check FGOs list
            for fgo_item in material.fgo_list:
                if query_lower in fgo_item.lower():
                    similarity = self._calculate_similarity(query_lower, fgo_item.lower())
                    results.append({
                        'material': material,
                        'fgo_item': fgo_item,
                        'similarity_score': similarity
                    })
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return [(r['material'], r['fgo_item']) for r in results]
    
    def find_similar_materials(self, material_id, limit=5):
        """Find materials similar to the given material based on tags and content"""
        if material_id not in self.materials_by_id:
            return []
        
        target_material = self.materials_by_id[material_id]
        target_text = target_material.get_searchable_text()
        
        similarities = []
        for material in self.materials:
            if material.id == material_id:
                continue  # Skip the same material
            
            material_text = material.get_searchable_text()
            similarity = self._calculate_similarity(target_text, material_text)
            
            if similarity > 0.2:  # Only include if somewhat similar
                similarities.append({
                    'material': material,
                    'similarity_score': similarity
                })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return [s['material'] for s in similarities[:limit]]
    
    def get_material_by_id(self, material_id):
        """Get material by ID"""
        return self.materials_by_id.get(material_id)


class FGOHeadersProcessor:
    """Processor for FGOs headers from filenames or website sources"""
    
    def __init__(self):
        pass
    
    def generate_headers_from_filename(self, filename):
        """Generate FGOs header from filename following specific rules"""
        # Remove file extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Replace underscores/hyphens with spaces and clean up
        header = name_without_ext.replace('_', ' ').replace('-', ' ')
        
        # Apply formatting rules
        header = self._apply_formatting_rules(header)
        
        return header
    
    def _apply_formatting_rules(self, header):
        """Apply formatting rules to make headers more readable"""
        # Capitalize first letter of each word
        header = header.title()
        
        # Handle special cases for FGOs terms
        special_cases = {
            'Фгос': 'ФГОС',
            'Фгт': 'ФГТ',
            'Федеральные Государственные Образовательные Стандарты': 'Федеральные Государственные Образовательные Стандарты'
        }
        
        for old, new in special_cases.items():
            header = header.replace(old, new)
        
        return header.strip()
    
    def extract_headers_from_website_source(self, source_url):
        """Extract headers from website source (placeholder implementation)"""
        # This would normally involve scraping the website
        # For now, we'll return a placeholder implementation
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(source_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract possible headers from the page
            headers = []
            for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                text = tag.get_text().strip()
                if text and ('фгос' in text.lower() or 'стандарт' in text.lower()):
                    headers.append(text)
            
            return headers
        except Exception as e:
            print(f"Error extracting headers from website: {e}")
            return []


# Example usage
if __name__ == "__main__":
    # Create enhanced search system
    search_system = EnhancedSearchSystem()
    
    # Add example materials
    material1 = EnhancedMaterial(
        title="Algebra Problems", 
        description="Collection of algebra problems for 8th grade", 
        grade=8, 
        subject="algebra",
        content="This contains various algebraic equations and solutions",
        tags=["8th grade", "algebra", "problems", "lessons"],
        fgo_list=["ФГОС 8th grade mathematics", "Algebraic standards"]
    )
    
    material2 = EnhancedMaterial(
        title="Geometry 8th grade", 
        description="Theory and practice for geometry", 
        grade=8, 
        subject="geometry",
        content="Geometric theorems and proofs",
        tags=["8th grade", "geometry", "theorems"],
        fgo_list=["ФГОС 8th grade geometry", "Geometric standards"]
    )
    
    material3 = EnhancedMaterial(
        title="Physics 7th grade", 
        description="Experiments and theories", 
        grade=7, 
        subject="physics",
        content="Physics experiments and theoretical concepts",
        tags=["7th grade", "physics", "experiments"],
        fgo_list=["ФГОС 7th grade physics", "Physical standards"]
    )
    
    search_system.add_material(material1)
    search_system.add_material(material2)
    search_system.add_material(material3)
    
    # Test enhanced search
    print("Searching for 'algebra' in content:")
    results = search_system.search_by_content("algebra", grade=8)
    for result in results:
        print(f"  - {result.title}")
    
    # Test finding similar materials
    print(f"\nFinding materials similar to '{material1.title}':")
    similar = search_system.find_similar_materials(material1.id, limit=3)
    for sim in similar:
        print(f"  - {sim.title}")
    
    # Test FGOs search
    print("\nSearching in FGOs lists for 'ФГОС':")
    fgos_results = search_system.search_in_fgos_lists("ФГОС")
    for material, fgo_item in fgos_results:
        print(f"  - {material.title}: {fgo_item}")
    
    # Test FGOs header processor
    print("\nTesting FGOs header processing:")
    processor = FGOHeadersProcessor()
    print(processor.generate_headers_from_filename("fgos_osnovnoy_obshch_obrazovanie.pdf"))
    print(processor.generate_headers_from_filename("standart_obrazovania_vpo.docx"))