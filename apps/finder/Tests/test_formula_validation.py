# File: test_formula_validation.py
# Path: /home/herb/Desktop/Finder/Test/test_formula_validation.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Test script to verify formula validation functionality
"""

print("Formula Validation Test Cases")
print("="*50)

test_cases = [
    # Valid formulas
    ("A AND B", "Valid: Basic AND operation"),
    ("(A OR B) AND C", "Valid: Parentheses with operators"),
    ("NOT A", "Valid: NOT operation"),
    ("A XOR B", "Valid: XOR operation"),
    
    # Syntax errors
    ("A AND", "Error: Missing right operand"),
    ("AND B", "Error: Missing left operand"),
    ("A B", "Error: Missing operator between variables"),
    ("A AND AND B", "Error: Consecutive operators"),
    ("(A AND B", "Error: Unmatched opening parenthesis"),
    ("A AND B)", "Error: Unmatched closing parenthesis"),
    ("A AND B]", "Error: Mismatched parenthesis types"),
    ("()", "Error: Empty parentheses"),
    
    # Invalid characters
    ("A & B", "Error: Invalid character '&'"),
    ("A + B", "Error: Invalid character '+'"),
    ("A123", "Error: Invalid character '123'"),
    
    # Logical paradoxes/warnings
    ("A AND NOT A", "Warning: Logical paradox (always false)"),
    ("A OR NOT A", "Warning: Tautology (always true)"),
    ("(A AND B) OR (A AND NOT A)", "Warning: Contains paradox"),
    
    # Variables without phrases
    ("G AND H", "Warning: Variables G,H not defined (A-F only)"),
]

print("\nTest Cases to Try in the Finder Application:")
print("-" * 50)

for i, (formula, description) in enumerate(test_cases, 1):
    print(f"{i:2d}. Formula: '{formula}'")
    print(f"    Expected: {description}")
    print()

print("Instructions:")
print("1. Run the Finder application: python Finder.py")
print("2. Enter each formula in the 'Search Formula' field")
print("3. Observe the syntax highlighting and error messages")
print("4. Try clicking 'Search' with invalid formulas to see error dialogs")
print("5. Add some phrases (A, B, C) to test variable validation")