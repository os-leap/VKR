#!/usr/bin/env python3
# Debug test for syntax-aware search functionality

import re

def syntax_aware_search(text, query):
    """
    Performs syntax-aware search supporting:
    - AND operator: "word1 AND word2"
    - OR operator: "word1 OR word2" 
    - NOT operator: "word1 NOT word2"
    - Phrase search: "word1 word2" (both words present)
    - Quoted phrases: "\"exact phrase\""
    """
    print(f"Input text: {text}")
    print(f"Input query: {query}")
    
    # Normalize text and query to lowercase
    text_lower = text.lower()
    query = query.strip()
    
    # Handle quoted phrases first
    quoted_phrases = re.findall(r'"([^"]*)"', query)
    print(f"Quoted phrases found: {quoted_phrases}")
    
    query_without_quotes = re.sub(r'"[^"]*"', ' QUOTED_PHRASE_PLACEHOLDER ', query)
    print(f"Query after removing quotes: {query_without_quotes}")
    
    # Check if all quoted phrases are present in the text
    for phrase in quoted_phrases:
        phrase = phrase.strip().lower()
        print(f"Checking quoted phrase: '{phrase}' in text")
        if phrase and phrase not in text_lower:
            print(f"Phrase '{phrase}' not found in text")
            return False
        else:
            print(f"Phrase '{phrase}' found in text")
    
    # Split by AND, OR, NOT operators while preserving them
    parts = re.split(r'\s+(AND|OR|NOT)\s+', query_without_quotes, flags=re.IGNORECASE)
    print(f"Parts after splitting: {parts}")
    
    # Process parts with operators
    i = 0
    result = True  # Start with True for AND logic
    operator = 'AND'  # Default operator
    
    while i < len(parts):
        part = parts[i].strip()
        print(f"Processing part {i}: '{part}' with operator '{operator}'")
        
        if part.upper() in ['AND', 'OR', 'NOT']:
            operator = part.upper()
            print(f"Setting operator to: {operator}")
        else:
            term = part.strip().lower()
            # Replace placeholder with actual phrase for search
            if 'QUOTED_PHRASE_PLACEHOLDER' in term:
                # If there were quoted phrases, we already verified them, so this part is true
                term_exists = True
                print(f"Found quoted phrase placeholder, setting term_exists to: {term_exists}")
            else:
                # Handle regular terms
                term_exists = True  # Start with True
                # For space-separated terms without operators, all should be present (AND logic)
                subterms = [t.strip() for t in term.split() if t.strip()]
                print(f"Subterms: {subterms}")
                for subterm in subterms:
                    if subterm:  # Skip empty strings
                        subterm_exists = subterm in text_lower
                        print(f"Checking subterm '{subterm}': {subterm_exists}")
                        term_exists = term_exists and subterm_exists
            
            print(f"Term '{term}' exists: {term_exists}")
            
            if operator == 'AND':
                result = result and term_exists
            elif operator == 'OR':
                if i == 0 or all(p.upper() not in ['AND', 'OR', 'NOT'] for p in parts[:i] if p.strip()):  # First term, initialize result
                    result = term_exists
                else:
                    result = result or term_exists
            elif operator == 'NOT':
                result = result and not term_exists
        
        print(f"Current result: {result}")
        i += 1
    
    print(f"Final result: {result}")
    return result

def debug_test():
    test_text = "The quick brown fox jumps over the lazy dog. This is a sample text for testing."
    
    print("Testing: \"quick brown\"")
    result = syntax_aware_search(test_text, "\"quick brown\"")
    print(f"Result: {result}\n")
    
    print("Testing: quick AND fox")
    result = syntax_aware_search(test_text, "quick AND fox")
    print(f"Result: {result}\n")

if __name__ == "__main__":
    debug_test()