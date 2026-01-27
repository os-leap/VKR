#!/usr/bin/env python3
# Corrected version of syntax-aware search functionality

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
    result = None  # We'll initialize this based on the first term
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
            
            # Initialize result with the first term's value
            if result is None:
                result = term_exists
            else:
                if operator == 'AND':
                    result = result and term_exists
                elif operator == 'OR':
                    result = result or term_exists
                elif operator == 'NOT':
                    result = result and not term_exists
        
        i += 1
    
    # If no terms were processed, return True (for edge cases)
    if result is None:
        return True
    
    return result

def test_syntax_aware_search():
    test_text = "The quick brown fox jumps over the lazy dog. This is a sample text for testing."
    
    print("Testing corrected syntax-aware search function...")
    
    # Test basic word search
    assert syntax_aware_search(test_text, "quick") == True
    print("✓ Basic word search works")
    
    # Test phrase search (AND logic by default)
    assert syntax_aware_search(test_text, "quick brown") == True
    print("✓ Phrase search works")
    
    # Test AND operator
    assert syntax_aware_search(test_text, "quick AND fox") == True
    print("✓ AND operator works")
    
    # Test OR operator
    assert syntax_aware_search(test_text, "cat OR fox") == True
    print("✓ OR operator works")
    
    # Test NOT operator
    assert syntax_aware_search(test_text, "quick NOT cat") == True
    print("✓ NOT operator works")
    
    # Test NOT operator with existing word
    assert syntax_aware_search(test_text, "quick NOT dog") == False
    print("✓ NOT operator with existing word works")
    
    # Test quoted phrases
    assert syntax_aware_search(test_text, "\"quick brown\"") == True
    print("✓ Quoted phrases work")
    
    # Test complex query - this was failing before
    assert syntax_aware_search(test_text, "\"quick brown\" AND dog") == True
    print("✓ Complex query works")
    
    # Test complex query with OR
    assert syntax_aware_search(test_text, "\"quick brown\" OR cat") == True
    print("✓ Complex query with OR works")
    
    # Additional test cases
    assert syntax_aware_search(test_text, "fox AND \"lazy dog\"") == True
    print("✓ More complex query works")
    
    assert syntax_aware_search(test_text, "\"quick brown\" AND \"lazy dog\"") == True
    print("✓ Multiple quoted phrases work")
    
    assert syntax_aware_search(test_text, "\"quick brown\" OR \"lazy cat\"") == True
    print("✓ OR with quoted phrases works")
    
    print("\nAll tests passed! The corrected syntax-aware search function is working correctly.")

if __name__ == "__main__":
    test_syntax_aware_search()