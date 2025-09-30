# File: test_regression_suite.py
# Path: /home/herb/Desktop/Finder/Tests/test_regression_suite.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-28
# Last Modified: 2025-07-28  04:10PM

"""
Comprehensive regression test suite
Catches runtime bugs, integration issues, and edge cases
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_searchworker_method_regression():
    """Regression test: Ensure SearchWorker has all required methods"""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    from Finder import SearchWorker
    
    test_params = {
        'formula': 'A',
        'phrases': {'A': {'text': 'test', 'case_sensitive': False}},
        'file_extensions': ['.txt'],
        'search_paths': ['.'],
        'unique_results': False,
        'max_results': 100
    }
    
    worker = SearchWorker(test_params)
    
    # These methods MUST exist and be callable
    critical_methods = [
        '_normalize_operators',
        '_get_files_to_search', 
        '_search_file',
        '_evaluate_formula',
        'run_search',
        'cancel'
    ]
    
    for method in critical_methods:
        assert hasattr(worker, method), f"REGRESSION: SearchWorker missing {method}"
        assert callable(getattr(worker, method)), f"REGRESSION: {method} not callable"
        
    return True

def test_operator_normalization_regression():
    """Regression test: Operator normalization must work correctly"""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    from Finder import SearchWorker
    
    test_params = {
        'formula': 'A',
        'phrases': {'A': {'text': 'test', 'case_sensitive': False}},
        'file_extensions': ['.txt'],
        'search_paths': ['.'],
        'unique_results': False,
        'max_results': 100
    }
    
    worker = SearchWorker(test_params)
    
    # Test cases that were failing before
    test_cases = [
        ('A & B', 'A AND B'),           # Basic AND
        ('A | B', 'A OR B'),            # Basic OR
        ('A && B', 'A AND B'),          # Double AND
        ('A || B', 'A OR B'),           # Double OR
        ('A && B || C', 'A AND B OR C'), # Mixed operators - this was failing
        ('!A', 'NOT A'),                # NOT operator
        ('~A', 'NOT A'),                # Tilde NOT
        ('A ^ B', 'A XOR B'),           # XOR operator
    ]
    
    for input_formula, expected in test_cases:
        result = worker._normalize_operators(input_formula)
        assert result == expected, f"REGRESSION: '{input_formula}' -> '{result}' (expected '{expected}')"
        
    return True

def test_formula_evaluation_regression():
    """Regression test: Formula evaluation must work correctly"""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    from Finder import SearchWorker
    
    test_params = {
        'formula': 'A & B',
        'phrases': {
            'A': {'text': 'test', 'case_sensitive': False},
            'B': {'text': 'word', 'case_sensitive': False}
        },
        'file_extensions': ['.txt'],
        'search_paths': ['.'],
        'unique_results': False,
        'max_results': 100
    }
    
    worker = SearchWorker(test_params)
    
    # Test evaluation cases that should work
    test_cases = [
        ('This is a test with a word', 'A & B', True),   # Both present -> True
        ('This is a test only', 'A & B', False),         # Only A -> False  
        ('This has a word only', 'A & B', False),        # Only B -> False
        ('No matches here', 'A & B', False),             # Neither -> False
        ('This is a test with a word', 'A | B', True),   # Both present with OR -> True
        ('This is a test only', 'A | B', True),          # A present with OR -> True
        ('This has a word only', 'A | B', True),         # B present with OR -> True
        ('No matches here', 'A | B', False),             # Neither with OR -> False
    ]
    
    for content, formula, expected in test_cases:
        result = worker._evaluate_formula(content, test_params['phrases'], formula)
        assert result == expected, f"REGRESSION: Formula '{formula}' on '{content}' -> {result} (expected {expected})"
        
    return True

def test_full_search_execution_regression():
    """Regression test: Full search must execute without crashing"""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    from Finder import SearchWorker
    
    # Create temporary test environment
    test_dir = tempfile.mkdtemp()
    
    try:
        # Create test files
        test_files = {
            'test1.txt': 'This file contains the word test for searching',
            'test2.md': 'Another test file with test content',
            'ignore.log': 'This should be ignored'
        }
        
        for filename, content in test_files.items():
            with open(Path(test_dir) / filename, 'w') as f:
                f.write(content)
                
        test_params = {
            'formula': 'A',
            'phrases': {'A': {'text': 'test', 'case_sensitive': False}},
            'file_extensions': ['.txt', '.md'],  # Exclude .log files
            'search_paths': [test_dir],
            'unique_results': False,
            'max_results': 100
        }
        
        worker = SearchWorker(test_params)
        
        # This must not crash (it was crashing before due to missing _normalize_operators)
        worker.run_search()
        
        return True
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

def test_ui_button_functionality_regression():
    """Regression test: UI buttons must exist and be functional"""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    from PySide6.QtWidgets import QApplication
    from Finder import Finder
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        
    finder = Finder()
    
    # Critical UI elements that must exist
    critical_ui_elements = [
        ('btn_search', '🔍 Start Search'),
        ('btn_validate', '✓ Validate Formula'), 
        ('btn_reset', '🔄 Reset/Clear'),
        ('btn_test_suite', '🎓 Run Examples'),
        ('formula_input', None),
        ('results_display', None),
        ('phrase_inputs', None),
        ('path_display', None)
    ]
    
    for element_name, expected_text in critical_ui_elements:
        assert hasattr(finder, element_name), f"REGRESSION: UI element {element_name} missing"
        
        element = getattr(finder, element_name)
        assert element is not None, f"REGRESSION: UI element {element_name} is None"
        
        if expected_text and hasattr(element, 'text'):
            actual_text = element.text()
            assert actual_text == expected_text, f"REGRESSION: {element_name} text '{actual_text}' != '{expected_text}'"
            
    return True

def test_case_sensitivity_regression():
    """Regression test: Case sensitivity must work correctly"""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    from Finder import SearchWorker
    
    # Test case-insensitive search (should match all variations)
    test_params_insensitive = {
        'formula': 'A',
        'phrases': {'A': {'text': 'claude', 'case_sensitive': False}},
        'file_extensions': ['.txt'],
        'search_paths': ['.'],
        'unique_results': False,
        'max_results': 100
    }
    
    worker = SearchWorker(test_params_insensitive)
    
    # Case-insensitive should match all variations
    insensitive_tests = [
        ('contains claude lowercase', True),
        ('contains Claude capitalized', True),
        ('contains CLAUDE uppercase', True),
    ]
    
    for content, expected in insensitive_tests:
        result = worker._evaluate_formula(content, test_params_insensitive['phrases'], 'A')
        assert result == expected, f"REGRESSION: Case-insensitive '{content}' -> {result} (expected {expected})"
    
    # Test case-sensitive search (should only match exact case)
    test_params_sensitive = {
        'formula': 'A',
        'phrases': {'A': {'text': 'claude', 'case_sensitive': True}},
        'file_extensions': ['.txt'],
        'search_paths': ['.'],
        'unique_results': False,
        'max_results': 100
    }
    
    worker_sensitive = SearchWorker(test_params_sensitive)
    
    # Case-sensitive should only match exact case
    sensitive_tests = [
        ('contains claude lowercase', True),   # Exact match
        ('contains Claude capitalized', False), # Wrong case
        ('contains CLAUDE uppercase', False),   # Wrong case
    ]
    
    for content, expected in sensitive_tests:
        result = worker_sensitive._evaluate_formula(content, test_params_sensitive['phrases'], 'A')
        assert result == expected, f"REGRESSION: Case-sensitive '{content}' -> {result} (expected {expected})"
    
    return True

def test_end_to_end_workflow_regression():
    """Regression test: Complete user workflow must work"""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    from PySide6.QtWidgets import QApplication
    from Finder import Finder
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        
    finder = Finder()
    
    # Create test environment
    test_dir = tempfile.mkdtemp()
    
    try:
        # Create a test file
        test_file = Path(test_dir) / 'test.txt'
        test_file.write_text('This is a test file with test content')
        
        # Simulate user actions
        finder.phrase_inputs['A'].setText('test')
        finder.formula_input.setText('A')
        finder.selected_paths = [test_dir]
        finder.path_display.setText(test_dir)
        
        # This was crashing before due to the SearchWorker bug
        # Now it should work without throwing exceptions
        finder._validate_search_parameters()  # Should return True
        
        # Test that starting search doesn't crash
        # (We won't wait for completion, just ensure it starts)
        finder._start_search()
        
        # Process any immediate events
        app.processEvents()
        
        return True
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

def main():
    """Run all regression tests"""
    print("🚨 REGRESSION TEST SUITE")
    print("=" * 50)
    print("These tests catch bugs that caused user issues!")
    print("=" * 50)
    
    regression_tests = [
        ("SearchWorker Methods", test_searchworker_method_regression),
        ("Operator Normalization", test_operator_normalization_regression), 
        ("Formula Evaluation", test_formula_evaluation_regression),
        ("Case Sensitivity", test_case_sensitivity_regression),
        ("Full Search Execution", test_full_search_execution_regression),
        ("UI Button Functionality", test_ui_button_functionality_regression),
        ("End-to-End Workflow", test_end_to_end_workflow_regression),
    ]
    
    results = {}
    
    for test_name, test_func in regression_tests:
        print(f"\n🔍 {test_name}...")
        try:
            results[test_name] = test_func()
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            results[test_name] = False
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*20} REGRESSION SUMMARY {'='*20}")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} regression tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL REGRESSION TESTS PASSED!")
        print("✅ No regressions detected - application is stable!")
        return 0
    else:
        print(f"\n🚨 {total-passed} regressions detected!")
        print("❌ These represent bugs that would impact users!")
        return 1

if __name__ == "__main__":
    sys.exit(main())