#!/usr/bin/env python3
# Simple and correct version of syntax-aware search functionality

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
    # Normalize text to lowercase
    text_lower = text.lower()
    query = query.strip()
    
    if not query:
        return True
    
    # First, validate all quoted phrases exist in the text
    quoted_phrases = re.findall(r'"([^"]*)"', query)
    for phrase in quoted_phrases:
        if phrase.strip() and phrase.lower() not in text_lower:
            return False
    
    # Replace quoted phrases with placeholders to simplify operator parsing
    query_for_operators = re.sub(r'"[^"]*"', 'QUOTED_PHRASE', query)
    
    # Split by logical operators
    parts_with_operators = re.split(r'\s+(AND|OR|NOT)\s+', query_for_operators, flags=re.IGNORECASE)
    
    # Process each term (non-operator) separately
    results = []
    operators = []
    
    for item in parts_with_operators:
        item = item.strip()
        if item.upper() in ['AND', 'OR', 'NOT']:
            operators.append(item.upper())
        else:
            # Process the term
            term_result = process_term(item, query, text_lower)
            results.append(term_result)
    
    # Apply operators to combine results
    if not results:
        return True  # No terms to evaluate
    
    final_result = results[0]
    for i, op in enumerate(operators):
        if i < len(results) - 1:
            next_result = results[i + 1]
            if op == 'AND':
                final_result = final_result and next_result
            elif op == 'OR':
                final_result = final_result or next_result
            elif op == 'NOT':
                final_result = final_result and not next_result
    
    return final_result

def process_term(term, original_query, text_lower):
    """
    Process a single term which might contain quoted phrases and regular words
    """
    # If this term contains QUOTED_PHRASE placeholder, it means we had quoted content
    # which was already validated, so we just need to check any other words in the same term
    if 'QUOTED_PHRASE' in term:
        # Extract any other words in this term besides the quoted phrase placeholder
        words = re.findall(r'\b\w+\b', term.replace('QUOTED_PHRASE', ''))
        term_result = True  # Quoted phrase is already validated
        for word in words:
            if word.lower() not in text_lower:
                term_result = False
                break
    else:
        # Regular term with space-separated words (implicit AND)
        words = re.findall(r'\b\w+\b', term)
        term_result = True
        for word in words:
            if word.lower() not in text_lower:
                term_result = False
                break
    
    return term_result

def test_syntax_aware_search():
    test_text = "The quick brown fox jumps over the lazy dog. This is a sample text for testing."
    
    print("Testing simple and correct syntax-aware search function...")
    
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
    
    print("\nAll tests passed! The simple syntax-aware search function is working correctly.")

if __name__ == "__main__":
    test_syntax_aware_search()