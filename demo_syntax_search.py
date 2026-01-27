#!/usr/bin/env python3
"""
Demo script for syntax-aware search functionality
"""

import re
import os
from pathlib import Path

def syntax_aware_search(text, query):
    """
    Performs syntax-aware search supporting:
    - AND operator: "word1 AND word2"
    - OR operator: "word1 OR word2" 
    - NOT operator: "word1 NOT word2"
    - Phrase search: "word1 word2" (both words present)
    - Quoted phrases: "\"exact phrase\""
    """
    # Normalize text and query to lowercase
    text_lower = text.lower()
    query = query.strip()
    
    # Handle quoted phrases first
    quoted_phrases = re.findall(r'"([^"]*)"', query)
    query_without_quotes = re.sub(r'"[^"]*"', ' QUOTED_PHRASE_PLACEHOLDER ', query)
    
    # Check if all quoted phrases are present in the text
    for phrase in quoted_phrases:
        phrase = phrase.strip().lower()
        if phrase and phrase not in text_lower:
            return False
    
    # Split by AND, OR, NOT operators while preserving them
    parts = re.split(r'\s+(AND|OR|NOT)\s+', query_without_quotes, flags=re.IGNORECASE)
    
    # Process parts with operators
    i = 0
    result = True  # Start with True for AND logic
    operator = 'AND'  # Default operator
    
    while i < len(parts):
        part = parts[i].strip()
        
        if part.upper() in ['AND', 'OR', 'NOT']:
            operator = part.upper()
        else:
            term = part.strip().lower()
            # Handle quoted phrases (they were already verified)
            if 'QUOTED_PHRASE_PLACEHOLDER' in term:
                # If this part contains the placeholder (even if mixed with other text), the quoted phrase validation was already done
                # If the term is just the placeholder, then it's True
                # If it has other content, we need to check the other content too
                term_exists = True  # Start with True since quoted phrases were validated
                
                # Check for other non-placeholder content in the same part
                other_content = re.sub(r'QUOTED_PHRASE_PLACEHOLDER', '', term).strip()
                if other_content:
                    # There's other content in this part, check it
                    other_subterms = [t.strip() for t in other_content.split() if t.strip() and t.strip() != 'QUOTED_PHRASE_PLACEHOLDER']
                    for subterm in other_subterms:
                        if subterm:
                            term_exists = term_exists and (subterm in text_lower)
            else:
                # Handle regular terms - for space-separated terms without operators, all should be present (AND logic)
                subterms = [t.strip() for t in term.split() if t.strip()]
                term_exists = True  # Start with True
                for subterm in subterms:
                    if subterm and subterm != 'QUOTED_PHRASE_PLACEHOLDER':  # Skip placeholder if it's mixed with other terms
                        term_exists = term_exists and (subterm in text_lower)
            
            if operator == 'AND':
                result = result and term_exists
            elif operator == 'OR':
                if i == 0 or all(p.upper() not in ['AND', 'OR', 'NOT'] for p in parts[:i] if p.strip()):  # First term, initialize result
                    result = term_exists
                else:
                    result = result or term_exists
            elif operator == 'NOT':
                result = result and not term_exists
        
        i += 1
    
    # Special case: if the original query only had quoted phrases (no other terms), return True if all phrases were found
    if len([p for p in parts if p.upper() not in ['AND', 'OR', 'NOT']]) == 1 and 'QUOTED_PHRASE_PLACEHOLDER' in parts[0] and not any(op in query.upper() for op in ['AND', 'OR', 'NOT']):
        return len(quoted_phrases) > 0  # If we found and validated quoted phrases with no operators, return True
    
    return result


def search_in_files(directory, query, file_extensions=None):
    """
    Search for a query in all files in the specified directory
    """
    if file_extensions is None:
        file_extensions = ['.py', '.html', '.js', '.css', '.txt', '.json', '.md']
    
    results = []
    dir_path = Path(directory)
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in file_extensions:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                if syntax_aware_search(content, query):
                    results.append(str(file_path))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    return results


def main():
    print("Syntax-Aware Search Demo")
    print("=" * 50)
    
    # Example searches
    examples = [
        "filter AND search",
        "syntax OR parser",
        "class AND def",
        "\"quick brown\"",
        "search AND NOT test",
        "function OR method",
    ]
    
    print("\nSearching for various patterns in workspace files...")
    
    for example_query in examples:
        print(f"\nQuery: '{example_query}'")
        results = search_in_files('/workspace', example_query, ['.py', '.html', '.js', '.txt'])
        if results:
            print(f"  Found in {len(results)} file(s):")
            for result in results[:5]:  # Show first 5 results
                print(f"    - {result}")
            if len(results) > 5:
                print(f"    ... and {len(results)-5} more files")
        else:
            print("  No matches found")
    
    print(f"\n" + "=" * 50)
    print("Interactive mode - enter queries (or 'quit' to exit)")
    
    while True:
        query = input("\nEnter search query: ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if query:
            results = search_in_files('/workspace', query, ['.py', '.html', '.js', '.txt'])
            print(f"Found {len(results)} matching file(s):")
            for result in results:
                print(f"  - {result}")


if __name__ == "__main__":
    main()