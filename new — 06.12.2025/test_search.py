#!/usr/bin/env python3
# Test script for syntax-aware search functionality

import sys
import os
sys.path.append('/workspace/new — 06.12.2025')

# Import the syntax_aware_search function from the app
from app import syntax_aware_search

def test_syntax_aware_search():
    test_text = "The quick brown fox jumps over the lazy dog. This is a sample text for testing."
    
    print("Testing syntax-aware search function...")
    
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
    
    # Test complex query
    assert syntax_aware_search(test_text, "\"quick brown\" AND dog") == True
    print("✓ Complex query works")
    
    # Test complex query with OR
    assert syntax_aware_search(test_text, "\"quick brown\" OR cat") == True
    print("✓ Complex query with OR works")
    
    print("\nAll tests passed! The syntax-aware search function is working correctly.")

if __name__ == "__main__":
    test_syntax_aware_search()