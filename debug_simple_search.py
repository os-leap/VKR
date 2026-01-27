#!/usr/bin/env python3
# Debug version of the simple syntax-aware search

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
    
    # Normalize text to lowercase
    text_lower = text.lower()
    query = query.strip()
    
    if not query:
        return True
    
    # First, validate all quoted phrases exist in the text
    quoted_phrases = re.findall(r'"([^"]*)"', query)
    print(f"DEBUG: Found quoted phrases: {quoted_phrases}")
    
    for phrase in quoted_phrases:
        exists = phrase.strip() and phrase.lower() in text_lower
        print(f"DEBUG: Phrase '{phrase}' exists in text: {exists}")
        if phrase.strip() and phrase.lower() not in text_lower:
            print(f"DEBUG: Returning False because phrase '{phrase}' not in text")
            return False
    
    # Replace quoted phrases with placeholders to simplify operator parsing
    query_for_operators = re.sub(r'"[^"]*"', 'QUOTED_PHRASE', query)
    print(f"DEBUG: Query after replacing quotes: '{query_for_operators}'")
    
    # Split by logical operators
    parts_with_operators = re.split(r'\s+(AND|OR|NOT)\s+', query_for_operators, flags=re.IGNORECASE)
    print(f"DEBUG: Parts after splitting: {parts_with_operators}")
    
    # Process each term (non-operator) separately
    results = []
    operators = []
    
    for item in parts_with_operators:
        item = item.strip()
        print(f"DEBUG: Processing item: '{item}'")
        
        if item.upper() in ['AND', 'OR', 'NOT']:
            operators.append(item.upper())
            print(f"DEBUG: Added operator: {item.upper()}")
        else:
            # Process the term
            term_result = process_term_debug(item, text_lower)
            results.append(term_result)
            print(f"DEBUG: Term result for '{item}': {term_result}")
    
    print(f"DEBUG: Results: {results}")
    print(f"DEBUG: Operators: {operators}")
    
    # Apply operators to combine results
    if not results:
        print("DEBUG: No results, returning True")
        return True  # No terms to evaluate
    
    final_result = results[0]
    print(f"DEBUG: Starting with first result: {final_result}")
    
    for i, op in enumerate(operators):
        if i < len(results) - 1:
            next_result = results[i + 1]
            old_final = final_result
            if op == 'AND':
                final_result = final_result and next_result
            elif op == 'OR':
                final_result = final_result or next_result
            elif op == 'NOT':
                final_result = final_result and not next_result
            
            print(f"DEBUG: Applying {op} to {old_final} and {next_result} = {final_result}")
    
    print(f"DEBUG: Final result: {final_result}")
    return final_result

def process_term_debug(term, text_lower):
    """
    Process a single term which might contain quoted phrases and regular words
    """
    print(f"  DEBUG process_term: processing term '{term}'")
    
    # If this term contains QUOTED_PHRASE placeholder, it means we had quoted content
    # which was already validated, so we just need to check any other words in the same term
    if 'QUOTED_PHRASE' in term:
        print(f"    DEBUG: Term contains QUOTED_PHRASE")
        # Extract any other words in this term besides the quoted phrase placeholder
        words = re.findall(r'\b\w+\b', term.replace('QUOTED_PHRASE', ''))
        print(f"    DEBUG: Words in term besides QUOTED_PHRASE: {words}")
        term_result = True  # Quoted phrase is already validated
        print(f"    DEBUG: Initial term_result (quoted phrase validated): {term_result}")
        for word in words:
            word_in_text = word.lower() in text_lower
            print(f"      DEBUG: Word '{word}' in text: {word_in_text}")
            if word.lower() not in text_lower:
                term_result = False
                print(f"      DEBUG: Setting term_result to False")
                break
    else:
        # Regular term with space-separated words (implicit AND)
        words = re.findall(r'\b\w+\b', term)
        print(f"    DEBUG: Regular term, words: {words}")
        term_result = True
        for word in words:
            word_in_text = word.lower() in text_lower
            print(f"      DEBUG: Word '{word}' in text: {word_in_text}")
            if word.lower() not in text_lower:
                term_result = False
                print(f"      DEBUG: Setting term_result to False")
                break
    
    print(f"  DEBUG process_term: returning {term_result} for term '{term}'")
    return term_result

def debug_problematic_case():
    test_text = "The quick brown fox jumps over the lazy dog. This is a sample text for testing."
    query = "\"quick brown\" OR \"lazy cat\""
    
    print(f"Debugging query: '{query}'")
    print(f"Test text: '{test_text}'")
    print()
    
    result = syntax_aware_search_debug(test_text, query)
    print(f"\nFinal result: {result}")
    
    # Expected: True (because "quick brown" exists, and with OR, at least one needs to exist)

if __name__ == "__main__":
    debug_problematic_case()