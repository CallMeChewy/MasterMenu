# File: test_finder_unit.py
# Path: /home/herb/Desktop/Finder/Test/test_finder_unit.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Unit tests for the Finder application
Tests core functionality without requiring GUI interaction
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import sys

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our classes (we'll need to mock Qt components)
with patch('PySide6.QtWidgets.QApplication'), \
     patch('PySide6.QtWidgets.QMainWindow'), \
     patch('PySide6.QtWidgets.QWidget'), \
     patch('PySide6.QtCore.QObject'), \
     patch('PySide6.QtCore.QThread'), \
     patch('PySide6.QtGui.QSyntaxHighlighter'):
    
    from Finder import SearchWorker, Finder


class TestOperatorNormalization(unittest.TestCase):
    """Test operator normalization functionality"""
    
    def setUp(self):
        """Set up test environment"""
        with patch('PySide6.QtWidgets.QApplication'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__'), \
             patch('PySide6.QtWidgets.QWidget'), \
             patch('PySide6.QtCore.QObject.__init__'):
            self.finder = Finder()
    
    def test_normalize_and_operators(self):
        """Test AND operator normalization"""
        self.assertEqual(self.finder._normalize_operators('A & B'), 'A AND B')
        self.assertEqual(self.finder._normalize_operators('A && B'), 'A AND B')
        self.assertEqual(self.finder._normalize_operators('A&B'), 'A AND B')
        self.assertEqual(self.finder._normalize_operators('A&&B'), 'A AND B')
    
    def test_normalize_or_operators(self):
        """Test OR operator normalization"""
        self.assertEqual(self.finder._normalize_operators('A | B'), 'A OR B')
        self.assertEqual(self.finder._normalize_operators('A || B'), 'A OR B')
        self.assertEqual(self.finder._normalize_operators('A|B'), 'A OR B')
        self.assertEqual(self.finder._normalize_operators('A||B'), 'A OR B')
    
    def test_normalize_not_operators(self):
        """Test NOT operator normalization"""
        self.assertEqual(self.finder._normalize_operators('!A'), ' NOT A')
        self.assertEqual(self.finder._normalize_operators('~A'), ' NOT A')
        self.assertEqual(self.finder._normalize_operators('!A & B'), ' NOT A AND B')
    
    def test_normalize_xor_operators(self):
        """Test XOR operator normalization"""
        self.assertEqual(self.finder._normalize_operators('A ^ B'), 'A XOR B')
        self.assertEqual(self.finder._normalize_operators('A^B'), 'A XOR B')
    
    def test_normalize_mixed_operators(self):
        """Test mixed operator normalization"""
        self.assertEqual(self.finder._normalize_operators('A & B | C'), 'A AND B OR C')
        self.assertEqual(self.finder._normalize_operators('!A || B'), ' NOT A OR B')
        self.assertEqual(self.finder._normalize_operators('A & !B'), 'A AND  NOT B')
    
    def test_normalize_complex_expressions(self):
        """Test complex expression normalization"""
        self.assertEqual(self.finder._normalize_operators('(A & B) | (C & D)'), '(A AND B) OR (C AND D)')
        self.assertEqual(self.finder._normalize_operators('!(A | B)'), ' NOT (A OR B)')


class TestAutoFormulaConstruction(unittest.TestCase):
    """Test automatic formula construction"""
    
    def setUp(self):
        """Set up test environment"""
        with patch('PySide6.QtWidgets.QApplication'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__'), \
             patch('PySide6.QtWidgets.QWidget'), \
             patch('PySide6.QtCore.QObject.__init__'):
            self.finder = Finder()
            
            # Mock phrase inputs
            self.finder.phrase_inputs = {}
            for letter in 'ABCDEF':
                mock_input = Mock()
                mock_input.text.return_value = ''
                self.finder.phrase_inputs[letter] = mock_input
    
    def test_auto_construct_single_variable(self):
        """Test auto-construction with single variable"""
        self.finder.phrase_inputs['A'].text.return_value = 'test'
        result = self.finder._auto_construct_formula()
        self.assertEqual(result, 'A')
    
    def test_auto_construct_two_variables(self):
        """Test auto-construction with two variables"""
        self.finder.phrase_inputs['A'].text.return_value = 'test1'
        self.finder.phrase_inputs['C'].text.return_value = 'test2'
        result = self.finder._auto_construct_formula()
        self.assertEqual(result, 'A AND C')
    
    def test_auto_construct_three_variables(self):
        """Test auto-construction with three variables"""
        self.finder.phrase_inputs['A'].text.return_value = 'test1'
        self.finder.phrase_inputs['B'].text.return_value = 'test2'
        self.finder.phrase_inputs['D'].text.return_value = 'test3'
        result = self.finder._auto_construct_formula()
        self.assertEqual(result, 'A AND B AND D')
    
    def test_auto_construct_all_variables(self):
        """Test auto-construction with all variables"""
        for letter in 'ABCDEF':
            self.finder.phrase_inputs[letter].text.return_value = f'test{letter}'
        result = self.finder._auto_construct_formula()
        self.assertEqual(result, 'A AND B AND C AND D AND E AND F')
    
    def test_auto_construct_no_variables(self):
        """Test auto-construction with no variables"""
        result = self.finder._auto_construct_formula()
        self.assertEqual(result, '')
    
    def test_auto_construct_empty_strings(self):
        """Test auto-construction ignores empty strings"""
        self.finder.phrase_inputs['A'].text.return_value = 'test'
        self.finder.phrase_inputs['B'].text.return_value = '   '  # Just spaces
        self.finder.phrase_inputs['C'].text.return_value = ''     # Empty
        result = self.finder._auto_construct_formula()
        self.assertEqual(result, 'A')


class TestFormulaValidation(unittest.TestCase):
    """Test formula validation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        with patch('PySide6.QtWidgets.QApplication'), \
             patch('PySide6.QtWidgets.QMainWindow.__init__'), \
             patch('PySide6.QtWidgets.QWidget'), \
             patch('PySide6.QtCore.QObject.__init__'):
            self.finder = Finder()
            
            # Mock phrase inputs for validation
            self.finder.phrase_inputs = {}
            for letter in 'ABCDEF':
                mock_input = Mock()
                mock_input.text.return_value = f'phrase_{letter}'
                self.finder.phrase_inputs[letter] = mock_input
    
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
            result = self.finder._check_balanced_parentheses(formula)
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
            result = self.finder._check_balanced_parentheses(formula)
            self.assertFalse(result, f"Should be invalid: {formula}")
    
    def test_check_valid_tokens_detailed(self):
        """Test detailed token validation"""
        # Valid tokens
        valid_result = self.finder._check_valid_tokens_detailed('A AND B')
        self.assertEqual(len(valid_result['errors']), 0)
        
        # Invalid characters
        invalid_result = self.finder._check_valid_tokens_detailed('A $ B')
        self.assertGreater(len(invalid_result['errors']), 0)
        
        # Invalid sequences
        sequence_result = self.finder._check_valid_tokens_detailed('A B')
        self.assertGreater(len(sequence_result['errors']), 0)
    
    def test_check_logical_structure(self):
        """Test logical structure validation"""
        # Valid structures
        valid_result = self.finder._check_logical_structure('A AND B')
        self.assertEqual(len(valid_result['errors']), 0)
        
        # Invalid structures
        invalid_result = self.finder._check_logical_structure('AND B')
        self.assertGreater(len(invalid_result['errors']), 0)
        
        # Missing operands
        missing_result = self.finder._check_logical_structure('A AND')
        self.assertGreater(len(missing_result['errors']), 0)
    
    def test_check_paradoxes_detailed(self):
        """Test paradox detection"""
        # Paradox
        paradox_result = self.finder._check_paradoxes_detailed('A AND NOT A')
        self.assertGreater(len(paradox_result['warnings']), 0)
        
        # Tautology
        tautology_result = self.finder._check_paradoxes_detailed('A OR NOT A')
        self.assertGreater(len(tautology_result['warnings']), 0)
        
        # Normal formula
        normal_result = self.finder._check_paradoxes_detailed('A AND B')
        self.assertEqual(len(normal_result['warnings']), 0)


class TestSearchWorker(unittest.TestCase):
    """Test SearchWorker functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        # Create test files
        test_data = {
            'test1.txt': 'This is a Python programming tutorial.\nIt covers basic concepts.',
            'test2.txt': 'Java programming guide.\nAdvanced topics included.',
            'test3.py': 'def hello():\n    print("Hello World")\n    return True',
            'test4.md': '# Documentation\nThis is **important** information.\nPython and Java comparison.'
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
    
    def test_get_files_to_search(self):
        """Test file collection functionality"""
        search_params = {
            'search_paths': [self.temp_dir],
            'file_extensions': ['.txt', '.py']
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            files = worker._get_files_to_search()
            
            # Should find txt and py files
            txt_files = [f for f in files if f.endswith('.txt')]
            py_files = [f for f in files if f.endswith('.py')]
            
            self.assertEqual(len(txt_files), 2)
            self.assertEqual(len(py_files), 1)
    
    def test_is_valid_extension(self):
        """Test file extension validation"""
        extensions = ['.txt', '.py']
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker({})
            
            self.assertTrue(worker._is_valid_extension('test.txt', extensions))
            self.assertTrue(worker._is_valid_extension('test.py', extensions))
            self.assertFalse(worker._is_valid_extension('test.md', extensions))
    
    def test_evaluate_formula_simple(self):
        """Test simple formula evaluation"""
        content = 'This is a Python programming tutorial.'
        phrases = {
            'A': {'text': 'Python', 'case_sensitive': False},
            'B': {'text': 'Java', 'case_sensitive': False},
            'C': {'text': 'programming', 'case_sensitive': False}
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker({})
            
            # Test single variable
            self.assertTrue(worker._evaluate_formula(content, phrases, 'A'))
            self.assertFalse(worker._evaluate_formula(content, phrases, 'B'))
            
            # Test AND
            self.assertTrue(worker._evaluate_formula(content, phrases, 'A AND C'))
            self.assertFalse(worker._evaluate_formula(content, phrases, 'A AND B'))
            
            # Test OR
            self.assertTrue(worker._evaluate_formula(content, phrases, 'A OR B'))
            self.assertTrue(worker._evaluate_formula(content, phrases, 'B OR C'))
    
    def test_evaluate_formula_case_sensitive(self):
        """Test case-sensitive formula evaluation"""
        content = 'This is a Python programming tutorial.'
        phrases = {
            'A': {'text': 'python', 'case_sensitive': True},
            'B': {'text': 'python', 'case_sensitive': False},
            'C': {'text': 'Python', 'case_sensitive': True}
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker({})
            
            # Case-sensitive should not match
            self.assertFalse(worker._evaluate_formula(content, phrases, 'A'))
            
            # Case-insensitive should match
            self.assertTrue(worker._evaluate_formula(content, phrases, 'B'))
            
            # Exact case should match
            self.assertTrue(worker._evaluate_formula(content, phrases, 'C'))
    
    def test_evaluate_formula_with_operators(self):
        """Test formula evaluation with common operators"""
        content = 'This is a Python programming tutorial.'
        phrases = {
            'A': {'text': 'Python', 'case_sensitive': False},
            'B': {'text': 'Java', 'case_sensitive': False}
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker({})
            
            # Test normalized operators
            self.assertTrue(worker._evaluate_formula(content, phrases, 'A & !B'))
            self.assertTrue(worker._evaluate_formula(content, phrases, 'A && !B'))
            self.assertTrue(worker._evaluate_formula(content, phrases, 'A | B'))
            self.assertTrue(worker._evaluate_formula(content, phrases, 'A || B'))


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        # Create realistic test files
        test_data = {
            'python_guide.txt': '''
# Python Programming Guide
This document covers Python basics.
Functions and classes are important concepts.
def hello_world():
    print("Hello, World!")
''',
            'java_tutorial.md': '''
# Java Tutorial
Object-oriented programming with Java.
Classes and inheritance are key features.
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
''',
            'mixed_content.txt': '''
Comparison between Python and Java:
- Python is interpreted
- Java is compiled
Both support object-oriented programming.
''',
            'config.json': '''
{
    "language": "python",
    "version": "3.9",
    "features": ["async", "type_hints"]
}
'''
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
    
    def test_complete_search_workflow(self):
        """Test complete search workflow"""
        search_params = {
            'search_paths': [self.temp_dir],
            'file_extensions': ['.txt', '.md'],
            'search_mode': 'line',
            'unique_mode': False,
            'phrases': {
                'A': {'text': 'Python', 'case_sensitive': False},
                'B': {'text': 'Java', 'case_sensitive': False},
                'C': {'text': 'programming', 'case_sensitive': False}
            },
            'formula': 'A & C'
        }
        
        with patch('PySide6.QtCore.QObject.__init__'):
            worker = SearchWorker(search_params)
            
            # Test file collection
            files = worker._get_files_to_search()
            self.assertGreater(len(files), 0)
            
            # Test search execution (simplified)
            matches = []
            for filepath in files:
                file_matches = worker._search_file(filepath)
                matches.extend(file_matches)
            
            # Should find matches in files containing both Python and programming
            self.assertGreater(len(matches), 0)


if __name__ == '__main__':
    # Set up test environment
    unittest.TestCase.maxDiff = None
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestOperatorNormalization))
    suite.addTest(unittest.makeSuite(TestAutoFormulaConstruction))
    suite.addTest(unittest.makeSuite(TestFormulaValidation))
    suite.addTest(unittest.makeSuite(TestSearchWorker))
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)