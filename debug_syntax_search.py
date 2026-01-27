#!/usr/bin/env python3
# Debug version of syntax-aware search functionality

import re

def syntax_aware_search_debug(text, query):
    """
    Performs syntax-aware search supporting:
    - AND operator: "word1 AND word2"
    - OR operator: "word1 OR word2" 
    - NOT operator: "word1 NOT word2"
    - Phrase search: "word1 word2" (both words present)
    - Quoted phrases: "\"exact phrase\""
    """
    print(f"DEBUG: Original query: '{query}'")
    
    # Normalize text and query to lowercase
    text_lower = text.lower()
    query = query.strip()
    
    # Handle quoted phrases first
    quoted_phrases = re.findall(r'"([^"]*)"', query)
    print(f"DEBUG: Found quoted phrases: {quoted_phrases}")
    
    query_without_quotes = re.sub(r'"[^"]*"', ' QUOTED_PHRASE_PLACEHOLDER ', query)
    print(f"DEBUG: Query after removing quotes: '{query_without_quotes}'")
    
    # Check if all quoted phrases are present in the text
    for phrase in quoted_phrases:
        phrase = phrase.strip().lower()
        print(f"DEBUG: Checking quoted phrase: '{phrase}'")
        if phrase and phrase not in text_lower:
            print(f"DEBUG: Phrase '{phrase}' not found in text")
            return False
        else:
            print(f"DEBUG: Phrase '{phrase}' found in text: {phrase in text_lower}")
    
    # Split by AND, OR, NOT operators while preserving them
    parts = re.split(r'\s+(AND|OR|NOT)\s+', query_without_quotes, flags=re.IGNORECASE)
    print(f"DEBUG: Parts after splitting: {parts}")
    
    # Process parts with operators
    i = 0
    result = None  # We'll initialize this based on the first term
    operator = 'AND'  # Default operator
    
    while i < len(parts):
        part = parts[i].strip()
        print(f"DEBUG: Processing part: '{part}'")
        
        if part.upper() in ['AND', 'OR', 'NOT']:
            operator = part.upper()
            print(f"DEBUG: Set operator to: {operator}")
        else:
            term = part.strip().lower()
            print(f"DEBUG: Term: '{term}'")
            term_exists = False
            
            # Handle quoted phrases (they were already verified)
            if 'QUOTED_PHRASE_PLACEHOLDER' in term:
                # If this part contains the placeholder (even if mixed with other text), the quoted phrase validation was already done
                # If the term is just the placeholder, then it's True
                # If it has other content, we need to check the other content too
                term_exists = True  # Start with True since quoted phrases were validated
                print(f"DEBUG: Contains QUOTED_PHRASE_PLACEHOLDER, initial term_exists: {term_exists}")
                
                # Check for other non-placeholder content in the same part
                other_content = re.sub(r'QUOTED_PHRASE_PLACEHOLDER', '', term).strip()
                print(f"DEBUG: Other content after removing placeholder: '{other_content}'")
                
                if other_content:
                    # There's other content in this part, check it
                    other_subterms = [t.strip() for t in other_content.split() if t.strip() and t.strip() != 'QUOTED_PHRASE_PLACEHOLDER']
                    print(f"DEBUG: Other subterms: {other_subterms}")
                    
                    for subterm in other_subterms:
                        if subterm:
                            term_exists = term_exists and (subterm in text_lower)
                            print(f"DEBUG: Subterm '{subterm}' in text: {subterm in text_lower}, term_exists now: {term_exists}")
            else:
                # Handle regular terms - for space-separated terms without operators, all should be present (AND logic)
                subterms = [t.strip() for t in term.split() if t.strip()]
                print(f"DEBUG: Regular subterms: {subterms}")
                
                if len(subterms) == 0:
                    term_exists = True  # Empty term matches everything
                    print(f"DEBUG: Empty subterms, term_exists: {term_exists}")
                elif len(subterms) == 1:
                    # Single term - just check if it exists
                    term_exists = (subterms[0] in text_lower)
                    print(f"DEBUG: Single subterm '{subterms[0]}', in text: {subterms[0] in text_lower}, term_exists: {term_exists}")
                else:
                    # Multiple terms - all must exist (AND logic)
                    term_exists = True
                    for subterm in subterms:
                        if subterm != 'QUOTED_PHRASE_PLACEHOLDER':  # Skip placeholder if it's mixed with other terms
                            term_exists = term_exists and (subterm in text_lower)
                    print(f"DEBUG: Multiple subterms, final term_exists: {term_exists}")
            
            print(f"DEBUG: About to apply operator '{operator}' with term_exists: {term_exists}")
            
            # Initialize result with the first term's value
            if result is None:
                result = term_exists
                print(f"DEBUG: Initialized result to: {result}")
            else:
                if operator == 'AND':
                    result = result and term_exists
                    print(f"DEBUG: Applied AND operation, result now: {result}")
                elif operator == 'OR':
                    result = result or term_exists
                    print(f"DEBUG: Applied OR operation, result now: {result}")
                elif operator == 'NOT':
                    result = result and not term_exists
                    print(f"DEBUG: Applied NOT operation, result now: {result}")
        
        i += 1
    
    # If no terms were processed, return True (for edge cases)
    if result is None:
        print(f"DEBUG: Result is None, returning True")
        return True
    
    print(f"DEBUG: Final result: {result}")
    return result

def debug_single_case():
    test_text = "The quick brown fox jumps over the lazy dog. This is a sample text for testing."
    query = "\"quick brown\""
    print(f"Testing query: '{query}'")
    result = syntax_aware_search_debug(test_text, query)
    print(f"Result: {result}")

if __name__ == "__main__":
    debug_single_case()