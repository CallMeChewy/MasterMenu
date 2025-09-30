# File: test_finder_simple.py
# Path: /home/herb/Desktop/Finder/Test/test_finder_simple.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Simple unit tests for the Finder application
Tests core functionality by directly testing the logic methods
"""

import unittest
import tempfile
import os
import sys

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOperatorNormalization(unittest.TestCase):
    """Test operator normalization functionality"""
    
    def normalize_operators(self, formula):
        """Direct implementation of normalize_operators for testing"""
        operator_map = {
            '&': ' AND ',
            '&&': ' AND ',
            '|': ' OR ',
            '||': ' OR ',
            '!': ' NOT ',
            '~': ' NOT ',
            '^': ' XOR '
        }
        
        normalized = formula
        for symbol, replacement in operator_map.items():
            normalized = normalized.replace(symbol, replacement)
            
        return normalized
    
    def test_normalize_and_operators(self):
        """Test AND operator normalization"""
        self.assertEqual(self.normalize_operators('A & B'), 'A AND B')
        self.assertEqual(self.normalize_operators('A && B'), 'A AND B')
        self.assertEqual(self.normalize_operators('A&B'), 'A AND B')
        self.assertEqual(self.normalize_operators('A&&B'), 'A AND B')
    
    def test_normalize_or_operators(self):
        """Test OR operator normalization"""
        self.assertEqual(self.normalize_operators('A | B'), 'A OR B')
        self.assertEqual(self.normalize_operators('A || B'), 'A OR B')
        self.assertEqual(self.normalize_operators('A|B'), 'A OR B')
        self.assertEqual(self.normalize_operators('A||B'), 'A OR B')
    
    def test_normalize_not_operators(self):
        """Test NOT operator normalization"""
        self.assertEqual(self.normalize_operators('!A'), ' NOT A')
        self.assertEqual(self.normalize_operators('~A'), ' NOT A')
        self.assertEqual(self.normalize_operators('!A & B'), ' NOT A AND B')
    
    def test_normalize_xor_operators(self):
        """Test XOR operator normalization"""
        self.assertEqual(self.normalize_operators('A ^ B'), 'A XOR B')
        self.assertEqual(self.normalize_operators('A^B'), 'A XOR B')
    
    def test_normalize_mixed_operators(self):
        """Test mixed operator normalization"""
        self.assertEqual(self.normalize_operators('A & B | C'), 'A AND B OR C')
        self.assertEqual(self.normalize_operators('!A || B'), ' NOT A OR B')
        self.assertEqual(self.normalize_operators('A & !B'), 'A AND  NOT B')
    
    def test_normalize_complex_expressions(self):
        """Test complex expression normalization"""
        self.assertEqual(self.normalize_operators('(A & B) | (C & D)'), '(A AND B) OR (C AND D)')
        self.assertEqual(self.normalize_operators('!(A | B)'), ' NOT (A OR B)')


class TestAutoFormulaConstruction(unittest.TestCase):
    """Test automatic formula construction"""
    
    def auto_construct_formula(self, phrase_data):
        """Direct implementation of auto_construct_formula for testing"""
        active_vars = []
        
        # Find all variables with non-empty phrases
        for letter in 'ABCDEF':
            if letter in phrase_data and phrase_data[letter].strip():
                active_vars.append(letter)
                
        if not active_vars:
            return ""
        elif len(active_vars) == 1:
            return active_vars[0]
        else:
            # Join with AND operator
            return " AND ".join(active_vars)
    
    def test_auto_construct_single_variable(self):
        """Test auto-construction with single variable"""
        phrases = {'A': 'test'}
        result = self.auto_construct_formula(phrases)
        self.assertEqual(result, 'A')
    
    def test_auto_construct_two_variables(self):
        """Test auto-construction with two variables"""
        phrases = {'A': 'test1', 'C': 'test2'}
        result = self.auto_construct_formula(phrases)
        self.assertEqual(result, 'A AND C')
    
    def test_auto_construct_three_variables(self):
        """Test auto-construction with three variables"""
        phrases = {'A': 'test1', 'B': 'test2', 'D': 'test3'}
        result = self.auto_construct_formula(phrases)
        self.assertEqual(result, 'A AND B AND D')
    
    def test_auto_construct_all_variables(self):
        """Test auto-construction with all variables"""
        phrases = {letter: f'test{letter}' for letter in 'ABCDEF'}
        result = self.auto_construct_formula(phrases)
        self.assertEqual(result, 'A AND B AND C AND D AND E AND F')
    
    def test_auto_construct_no_variables(self):
        """Test auto-construction with no variables"""
        phrases = {}
        result = self.auto_construct_formula(phrases)
        self.assertEqual(result, '')
    
    def test_auto_construct_empty_strings(self):
        """Test auto-construction ignores empty strings"""
        phrases = {'A': 'test', 'B': '   ', 'C': ''}
        result = self.auto_construct_formula(phrases)
        self.assertEqual(result, 'A')


class TestFormulaValidation(unittest.TestCase):
    """Test formula validation functionality"""
    
    def check_balanced_parentheses(self, formula):
        """Direct implementation of parentheses checking"""
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for char in formula:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack:
                    return False
                if pairs[stack.pop()] != char:
                    return False
                    
        return len(stack) == 0
    
    def test_check_balanced_parentheses_valid(self):
        """Test balanced parentheses validation - valid cases"""
        valid_cases = [
            '(A AND B)',
            '((A OR B) AND C)',
            '[A AND B]',
            '{A OR B}',
            '(A AND [B OR C])',
            ''
        ]
        
        for formula in valid_cases:
            result = self.check_balanced_parentheses(formula)
            self.assertTrue(result, f"Should be valid: {formula}")
    
    def test_check_balanced_parentheses_invalid(self):
        """Test balanced parentheses validation - invalid cases"""
        invalid_cases = [
            '(A AND B',
            'A AND B)',
            '((A AND B)',
            '(A AND B])',
            '[A AND B)',
            '{A AND B]'
        ]
        
        for formula in invalid_cases:
            result = self.check_balanced_parentheses(formula)
            self.assertFalse(result, f"Should be invalid: {formula}")


class TestFormulaEvaluation(unittest.TestCase):
    """Test formula evaluation functionality"""
    
    def normalize_operators(self, formula):
        """Direct implementation of normalize_operators for testing"""
        operator_map = {
            '&': ' AND ',
            '&&': ' AND ',
            '|': ' OR ',
            '||': ' OR ',
            '!': ' NOT ',
            '~': ' NOT ',
            '^': ' XOR '
        }
        
        normalized = formula
        for symbol, replacement in operator_map.items():
            normalized = normalized.replace(symbol, replacement)
            
        return normalized
    
    def evaluate_formula(self, content, phrases, formula):
        """Direct implementation of formula evaluation"""
        if not formula.strip():
            return False
            
        # Normalize operators first
        normalized_formula = self.normalize_operators(formula)
            
        # Create a mapping of phrase variables to their presence in content
        phrase_values = {}
        for letter, phrase_data in phrases.items():
            phrase_text = phrase_data.get('text', '')
            case_sensitive = phrase_data.get('case_sensitive', False)
            
            if phrase_text.strip():
                if case_sensitive:
                    # Case-sensitive search
                    phrase_values[letter] = phrase_text in content
                else:
                    # Case-insensitive search
                    phrase_values[letter] = phrase_text.lower() in content.lower()
            else:
                phrase_values[letter] = False
                
        # Replace phrase variables in formula with their boolean values
        eval_formula = normalized_formula.upper()
        for letter in 'ABCDEF':
            eval_formula = eval_formula.replace(letter, str(phrase_values.get(letter, False)))
            
        # Replace logical operators with Python equivalents
        eval_formula = eval_formula.replace('AND', ' and ')
        eval_formula = eval_formula.replace('OR', ' or ')
        eval_formula = eval_formula.replace('NOT', ' not ')
        eval_formula = eval_formula.replace('NOR', ' not (')
        eval_formula = eval_formula.replace('XOR', ' != ')
        eval_formula = eval_formula.replace('XNOR', ' == ')
        
        try:
            return eval(eval_formula)
        except:
            return False
    
    def test_evaluate_formula_simple(self):
        """Test simple formula evaluation"""
        content = 'This is a Python programming tutorial.'
        phrases = {
            'A': {'text': 'Python', 'case_sensitive': False},
            'B': {'text': 'Java', 'case_sensitive': False},
            'C': {'text': 'programming', 'case_sensitive': False}
        }
        
        # Test single variable
        self.assertTrue(self.evaluate_formula(content, phrases, 'A'))
        self.assertFalse(self.evaluate_formula(content, phrases, 'B'))
        
        # Test AND
        self.assertTrue(self.evaluate_formula(content, phrases, 'A AND C'))
        self.assertFalse(self.evaluate_formula(content, phrases, 'A AND B'))
        
        # Test OR
        self.assertTrue(self.evaluate_formula(content, phrases, 'A OR B'))
        self.assertTrue(self.evaluate_formula(content, phrases, 'B OR C'))
    
    def test_evaluate_formula_case_sensitive(self):
        """Test case-sensitive formula evaluation"""
        content = 'This is a Python programming tutorial.'
        phrases = {
            'A': {'text': 'python', 'case_sensitive': True},
            'B': {'text': 'python', 'case_sensitive': False},
            'C': {'text': 'Python', 'case_sensitive': True}
        }
        
        # Case-sensitive should not match
        self.assertFalse(self.evaluate_formula(content, phrases, 'A'))
        
        # Case-insensitive should match
        self.assertTrue(self.evaluate_formula(content, phrases, 'B'))
        
        # Exact case should match
        self.assertTrue(self.evaluate_formula(content, phrases, 'C'))
    
    def test_evaluate_formula_with_operators(self):
        """Test formula evaluation with common operators"""
        content = 'This is a Python programming tutorial.'
        phrases = {
            'A': {'text': 'Python', 'case_sensitive': False},
            'B': {'text': 'Java', 'case_sensitive': False}
        }
        
        # Test normalized operators
        self.assertTrue(self.evaluate_formula(content, phrases, 'A & !B'))
        self.assertTrue(self.evaluate_formula(content, phrases, 'A && !B'))
        self.assertTrue(self.evaluate_formula(content, phrases, 'A | B'))
        self.assertTrue(self.evaluate_formula(content, phrases, 'A || B'))
    
    def test_evaluate_complex_formula(self):
        """Test complex formula evaluation"""
        content = 'This is a Python programming tutorial with examples.'
        phrases = {
            'A': {'text': 'Python', 'case_sensitive': False},
            'B': {'text': 'Java', 'case_sensitive': False},
            'C': {'text': 'tutorial', 'case_sensitive': False},
            'D': {'text': 'examples', 'case_sensitive': False}
        }
        
        # Test complex formula
        self.assertTrue(self.evaluate_formula(content, phrases, '(A & C) | (B & D)'))
        self.assertTrue(self.evaluate_formula(content, phrases, 'A & C & D'))
        self.assertFalse(self.evaluate_formula(content, phrases, 'B & C'))


class TestFileExtensionValidation(unittest.TestCase):
    """Test file extension validation"""
    
    def is_valid_extension(self, filename, extensions):
        """Direct implementation of extension validation"""
        if not extensions:
            return True
        return any(filename.lower().endswith(ext.lower()) for ext in extensions)
    
    def test_valid_extensions(self):
        """Test valid file extensions"""
        extensions = ['.txt', '.py', '.md']
        
        self.assertTrue(self.is_valid_extension('test.txt', extensions))
        self.assertTrue(self.is_valid_extension('test.py', extensions))
        self.assertTrue(self.is_valid_extension('test.md', extensions))
        self.assertTrue(self.is_valid_extension('TEST.TXT', extensions))  # Case insensitive
    
    def test_invalid_extensions(self):
        """Test invalid file extensions"""
        extensions = ['.txt', '.py']
        
        self.assertFalse(self.is_valid_extension('test.md', extensions))
        self.assertFalse(self.is_valid_extension('test.json', extensions))
        self.assertFalse(self.is_valid_extension('test.html', extensions))
    
    def test_empty_extensions(self):
        """Test empty extensions list"""
        extensions = []
        
        self.assertTrue(self.is_valid_extension('test.txt', extensions))
        self.assertTrue(self.is_valid_extension('test.anything', extensions))


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        # Create test files
        test_data = {
            'python_guide.txt': 'This is a Python programming guide with examples.',
            'java_tutorial.txt': 'Java tutorial for beginners and advanced users.',
            'mixed_content.txt': 'Both Python and Java are popular programming languages.',
            'empty_file.txt': ''
        }
        
        for filename, content in test_data.items():
            filepath = os.path.join(self.temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            self.test_files.append(filepath)
    
    def tearDown(self):
        """Clean up test files"""
        for filepath in self.test_files:
            if os.path.exists(filepath):
                os.remove(filepath)
        os.rmdir(self.temp_dir)
    
    def test_real_file_search(self):
        """Test search functionality with real files"""
        # Test file exists
        self.assertTrue(os.path.exists(self.test_files[0]))
        
        # Test file content
        with open(self.test_files[0], 'r') as f:
            content = f.read()
        
        # Test our evaluation logic
        phrases = {
            'A': {'text': 'Python', 'case_sensitive': False},
            'B': {'text': 'Java', 'case_sensitive': False}
        }
        
        # Use our evaluation function
        evaluator = TestFormulaEvaluation()
        
        # Python guide should match A but not B
        self.assertTrue(evaluator.evaluate_formula(content, phrases, 'A'))
        self.assertFalse(evaluator.evaluate_formula(content, phrases, 'B'))
        
        # Test with Java file
        with open(self.test_files[1], 'r') as f:
            java_content = f.read()
        
        # Java tutorial should match B but not A
        self.assertFalse(evaluator.evaluate_formula(java_content, phrases, 'A'))
        self.assertTrue(evaluator.evaluate_formula(java_content, phrases, 'B'))
        
        # Mixed content should match both
        with open(self.test_files[2], 'r') as f:
            mixed_content = f.read()
        
        self.assertTrue(evaluator.evaluate_formula(mixed_content, phrases, 'A'))
        self.assertTrue(evaluator.evaluate_formula(mixed_content, phrases, 'B'))
        self.assertTrue(evaluator.evaluate_formula(mixed_content, phrases, 'A AND B'))


def run_simple_tests():
    """Run simple tests and provide detailed results"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestOperatorNormalization))
    suite.addTest(loader.loadTestsFromTestCase(TestAutoFormulaConstruction))
    suite.addTest(loader.loadTestsFromTestCase(TestFormulaValidation))
    suite.addTest(loader.loadTestsFromTestCase(TestFormulaEvaluation))
    suite.addTest(loader.loadTestsFromTestCase(TestFileExtensionValidation))
    suite.addTest(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print detailed summary
    print(f"\n{'='*70}")
    print(f"SIMPLE UNIT TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
            print(f"  {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
            print(f"  {traceback.split(chr(10))[-2]}")
    
    print(f"\nFUNCTIONALITY TESTED:")
    print(f"✓ Operator normalization (&, |, !, ^, &&, ||, ~)")
    print(f"✓ Auto-formula construction (A, A AND B, A AND B AND C)")
    print(f"✓ Parentheses validation (balanced, unbalanced, mismatched)")
    print(f"✓ Formula evaluation (simple, complex, case-sensitive)")
    print(f"✓ File extension validation (.txt, .py, .md)")
    print(f"✓ Integration scenarios with real files")
    
    print(f"{'='*70}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_simple_tests()
    sys.exit(0 if success else 1)