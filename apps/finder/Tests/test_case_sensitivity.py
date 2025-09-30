# File: test_case_sensitivity.py
# Path: /home/herb/Desktop/Finder/Test/test_case_sensitivity.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Test script to verify case sensitivity functionality in Finder
"""

# Create test files with different case variations
test_content = """
This is a Test file with Python code.
def test_function():
    print("Hello World")
    
class TestClass:
    def __init__(self):
        self.python_version = "3.9"
"""

with open('test_file.py', 'w') as f:
    f.write(test_content)

print("Test file created: test_file.py")
print("Content preview:")
print(test_content[:200] + "...")
print("\nYou can now test the Finder application with:")
print("- Phrase A: 'Python' (case-sensitive)")
print("- Phrase B: 'python' (case-insensitive)")
print("- Phrase C: 'Test' (case-sensitive)")
print("- Formula: 'A OR B OR C'")
print("\nExpected results:")
print("- A should find 'Python' (line 2)")
print("- B should find 'python' (line 7)")
print("- C should find 'Test' (line 2 and 5)")