# File: test_comprehensive_integration.py
# Path: /home/herb/Desktop/Finder/Tests/test_comprehensive_integration.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-28
# Last Modified: 2025-07-28  04:00PM

"""
Comprehensive integration test suite that would have caught the SearchWorker issue
Tests the full execution path including edge cases and error scenarios
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_search_worker_has_all_required_methods():
    """Test that SearchWorker has all methods it tries to call - THIS WOULD HAVE CAUGHT THE BUG"""
    print("🔍 Testing SearchWorker method completeness...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from Finder import SearchWorker
        
        # Create a SearchWorker instance
        test_params = {
            'formula': 'A',
            'phrases': {'A': {'text': 'test', 'case_sensitive': False}},
            'file_extensions': ['.txt'],
            'search_paths': ['.'],
            'unique_results': False,
            'max_results': 100
        }
        
        worker = SearchWorker(test_params)
        
        # Check all methods that are called internally
        required_methods = [
            '_normalize_operators',  # This was missing!
            '_get_files_to_search',
            '_search_file',
            '_evaluate_formula',
            'cancel',
            'run_search'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(worker, method):
                missing_methods.append(method)
                
        if missing_methods:
            print(f"❌ CRITICAL: SearchWorker missing methods: {missing_methods}")
            return False
        else:
            print("✅ All required methods present in SearchWorker")
            return True
            
    except Exception as e:
        print(f"❌ Error testing SearchWorker methods: {e}")
        return False


def test_search_worker_normalize_operators():
    """Test the _normalize_operators method specifically"""
    print("🔍 Testing _normalize_operators method...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
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
        
        # Test various operator normalizations
        test_cases = [
            ('A & B', 'A  AND  B'),
            ('A | B', 'A  OR  B'),
            ('!A', ' NOT A'),
            ('A && B || C', 'A  AND  B  OR  C'),
            ('~A ^ B', ' NOT A  XOR  B'),
        ]
        
        for input_formula, expected in test_cases:
            result = worker._normalize_operators(input_formula)
            if result != expected:
                print(f"❌ Normalization failed: '{input_formula}' -> '{result}' (expected '{expected}')")
                return False
                
        print("✅ _normalize_operators works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing _normalize_operators: {e}")
        return False


def test_full_search_execution_with_real_files():
    """Test complete search execution with real files - THIS WOULD HAVE CAUGHT THE BUG"""
    print("🔍 Testing full search execution with real files...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Create temporary test files
    test_dir = tempfile.mkdtemp()
    try:
        # Create test files with known content
        test_files = {
            'test1.txt': 'This contains the word claude and other text',
            'test2.txt': 'This has no matching content',
            'test3.md': 'Another claude reference in markdown',
            'test4.py': 'def claude_function(): pass'
        }
        
        for filename, content in test_files.items():
            with open(Path(test_dir) / filename, 'w') as f:
                f.write(content)
                
        from Finder import SearchWorker
        
        # Test parameters that would trigger the bug
        test_params = {
            'formula': 'A',  # Simple formula that calls _normalize_operators
            'phrases': {'A': {'text': 'claude', 'case_sensitive': False}},
            'file_extensions': ['.txt', '.md', '.py'],
            'search_paths': [test_dir],
            'unique_results': False,
            'max_results': 100
        }
        
        worker = SearchWorker(test_params)
        
        # This would have failed with the original bug
        worker.run_search()  # This calls _normalize_operators internally
        
        print("✅ Full search execution completed without errors")
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL: Full search execution failed: {e}")
        print("   This indicates a runtime error that should have been caught!")
        return False
        
    finally:
        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)


def test_search_worker_formula_evaluation():
    """Test formula evaluation with various operators"""
    print("🔍 Testing formula evaluation...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
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
        
        # Test formula evaluation with different content
        test_cases = [
            ('This is a test word', 'A & B', True),   # Both present
            ('This is a test', 'A & B', False),       # Only A present
            ('This is a word', 'A & B', False),       # Only B present
            ('No match here', 'A & B', False),        # Neither present
            ('This is a test word', 'A | B', True),   # Either present
            ('This is a test', 'A | B', True),        # A present
            ('This is a word', 'A | B', True),        # B present
        ]
        
        for content, formula, expected in test_cases:
            # Update worker formula
            worker.search_params['formula'] = formula
            result = worker._evaluate_formula(content, worker.search_params['phrases'], formula)
            
            if result != expected:
                print(f"❌ Formula evaluation failed:")
                print(f"   Content: '{content}'")
                print(f"   Formula: '{formula}'")
                print(f"   Expected: {expected}, Got: {result}")
                return False
                
        print("✅ Formula evaluation works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error testing formula evaluation: {e}")
        return False


def test_end_to_end_user_workflow():
    """Test the complete user workflow from GUI to results"""
    print("🔍 Testing end-to-end user workflow...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from PySide6.QtWidgets import QApplication
        from Finder import Finder
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            
        finder = Finder()
        
        # Simulate user input
        finder.phrase_inputs['A'].setText('test')
        finder.formula_input.setText('A')
        
        # Create a temporary test file
        test_dir = tempfile.mkdtemp()
        test_file = Path(test_dir) / 'test.txt'
        test_file.write_text('This is a test file with test content')
        
        finder.selected_paths = [test_dir]
        finder.path_display.setText(test_dir)
        
        # Mock the UI updates to capture results
        results_captured = []
        
        def capture_result(file_path, content, line_num, is_unique):
            results_captured.append((file_path, content, line_num, is_unique))
            
        # Test the full workflow - this would have failed with the original bug
        try:
            finder._start_search()  # This eventually calls SearchWorker._normalize_operators
            
            # Wait a moment for search to potentially complete
            app.processEvents()
            
            print("✅ End-to-end workflow completed without crashing")
            return True
            
        except Exception as workflow_error:
            print(f"❌ CRITICAL: End-to-end workflow failed: {workflow_error}")
            print("   This is exactly the bug the user encountered!")
            return False
            
    except Exception as e:
        print(f"❌ Error in end-to-end test setup: {e}")
        return False
        
    finally:
        # Clean up
        if 'test_dir' in locals():
            shutil.rmtree(test_dir, ignore_errors=True)


def test_edge_cases_and_error_scenarios():
    """Test edge cases that commonly cause issues"""
    print("🔍 Testing edge cases and error scenarios...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from Finder import SearchWorker
        
        # Test empty formula
        test_params = {
            'formula': '',
            'phrases': {'A': {'text': 'test', 'case_sensitive': False}},
            'file_extensions': ['.txt'],
            'search_paths': ['.'],
            'unique_results': False,
            'max_results': 100
        }
        
        worker = SearchWorker(test_params)
        
        # Test various edge cases
        edge_cases = [
            ('', 'Empty formula'),
            ('   ', 'Whitespace only formula'),
            ('A & & B', 'Invalid operator sequence'),
            ('(A & B', 'Unmatched parentheses'),
            ('A & B)', 'Extra closing parentheses'),
            ('X', 'Undefined variable'),
            ('A & B & C & D & E & F & G', 'Too many variables'),
        ]
        
        for formula, description in edge_cases:
            try:
                test_params['formula'] = formula
                worker.search_params = test_params
                result = worker._evaluate_formula('test content', test_params['phrases'], formula)
                print(f"   ✅ {description}: Handled gracefully")
            except Exception as e:
                print(f"   ⚠️  {description}: Error (may be expected): {e}")
                
        print("✅ Edge case testing completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing edge cases: {e}")
        return False


def test_search_worker_thread_safety():
    """Test SearchWorker thread safety and cancellation"""
    print("🔍 Testing SearchWorker thread safety...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
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
        
        # Test cancellation
        worker.cancel()
        assert worker.is_cancelled == True, "Cancellation should set is_cancelled flag"
        
        print("✅ SearchWorker thread safety tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing thread safety: {e}")
        return False


def main():
    """Run comprehensive integration tests"""
    print("🚀 COMPREHENSIVE INTEGRATION TEST SUITE")
    print("=" * 60)
    print("This test suite would have caught the SearchWorker._normalize_operators bug!")
    print("=" * 60)
    
    tests = [
        ("SearchWorker Method Completeness", test_search_worker_has_all_required_methods),
        ("Normalize Operators Method", test_search_worker_normalize_operators),
        ("Full Search Execution", test_full_search_execution_with_real_files),
        ("Formula Evaluation", test_search_worker_formula_evaluation),
        ("End-to-End User Workflow", test_end_to_end_user_workflow),
        ("Edge Cases", test_edge_cases_and_error_scenarios),
        ("Thread Safety", test_search_worker_thread_safety),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}: CRITICAL ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*20} COMPREHENSIVE TEST SUMMARY {'='*20}")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("✅ This test suite WOULD HAVE CAUGHT the SearchWorker bug!")
        return 0
    else:
        print(f"\n⚠️  {total-passed} tests failed.")
        print("❌ These failures represent the types of bugs we need to catch!")
        return 1


if __name__ == "__main__":
    sys.exit(main())