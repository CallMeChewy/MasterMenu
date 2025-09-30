# File: test_case_sensitivity_comprehensive.py
# Path: /home/herb/Desktop/Finder/Tests/test_case_sensitivity_comprehensive.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-28
# Last Modified: 2025-07-28  04:30PM

"""
Comprehensive case sensitivity testing
Ensures proper case-sensitive and case-insensitive search behavior
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_case_insensitive_search():
    """Test case-insensitive search behavior - should match all variations"""
    print("🔍 Testing case-INSENSITIVE search...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Create test content with different cases
    test_content = """
    This file contains claude in lowercase.
    This file contains Claude in proper case.
    This file contains CLAUDE in uppercase.
    This file contains cLaUdE in mixed case.
    """
    
    # Create temporary test file
    test_dir = tempfile.mkdtemp()
    test_file = Path(test_dir) / 'case_test.txt'
    test_file.write_text(test_content)
    
    try:
        from Finder import SearchWorker
        
        # Test case-INSENSITIVE search (default behavior)
        test_params = {
            'formula': 'A',
            'phrases': {'A': {'text': 'claude', 'case_sensitive': False}},  # Case INSENSITIVE
            'file_extensions': ['.txt'],
            'search_paths': [test_dir],
            'unique_results': False,
            'max_results': 100
        }
        
        worker = SearchWorker(test_params)
        
        # Test the evaluation for each line
        test_lines = [
            ('contains claude in lowercase', True),   # Should match
            ('contains Claude in proper case', True), # Should match  
            ('contains CLAUDE in uppercase', True),   # Should match
            ('contains cLaUdE in mixed case', True),  # Should match
            ('contains no match here', False),        # Should NOT match
        ]
        
        all_passed = True
        for line_content, expected in test_lines:
            result = worker._evaluate_formula(line_content, test_params['phrases'], 'A')
            if result != expected:
                print(f"❌ FAILED: '{line_content}' -> {result} (expected {expected})")
                all_passed = False
            else:
                print(f"✅ PASSED: '{line_content}' -> {result}")
                
        return all_passed
        
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

def test_case_sensitive_search():
    """Test case-sensitive search behavior - should only match exact case"""
    print("\n🔍 Testing case-SENSITIVE search...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from Finder import SearchWorker
        
        # Test case-SENSITIVE search  
        test_params = {
            'formula': 'A',
            'phrases': {'A': {'text': 'claude', 'case_sensitive': True}},  # Case SENSITIVE
            'file_extensions': ['.txt'],
            'search_paths': ['.'],
            'unique_results': False,
            'max_results': 100
        }
        
        worker = SearchWorker(test_params)
        
        # Test the evaluation for each case variation
        test_lines = [
            ('contains claude in lowercase', True),    # Should match (exact)
            ('contains Claude in proper case', False), # Should NOT match
            ('contains CLAUDE in uppercase', False),   # Should NOT match  
            ('contains cLaUdE in mixed case', False),  # Should NOT match
            ('contains no match here', False),         # Should NOT match
        ]
        
        all_passed = True
        for line_content, expected in test_lines:
            result = worker._evaluate_formula(line_content, test_params['phrases'], 'A')
            if result != expected:
                print(f"❌ FAILED: '{line_content}' -> {result} (expected {expected})")
                all_passed = False
            else:
                print(f"✅ PASSED: '{line_content}' -> {result}")
                
        return all_passed
        
    except Exception as e:
        print(f"❌ Error in case-sensitive test: {e}")
        return False

def test_mixed_case_sensitivity():
    """Test mixed case sensitivity across multiple variables"""
    print("\n🔍 Testing mixed case sensitivity (A=insensitive, B=sensitive)...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from Finder import SearchWorker
        
        # Test mixed case sensitivity
        test_params = {
            'formula': 'A & B',
            'phrases': {
                'A': {'text': 'claude', 'case_sensitive': False},  # Case INSENSITIVE
                'B': {'text': 'code', 'case_sensitive': True}      # Case SENSITIVE
            },
            'file_extensions': ['.txt'],
            'search_paths': ['.'],
            'unique_results': False,
            'max_results': 100
        }
        
        worker = SearchWorker(test_params)
        
        # Test combinations
        test_lines = [
            ('Claude writes code daily', True),     # A matches (insensitive), B matches (exact)
            ('claude writes code daily', True),     # A matches (exact), B matches (exact)
            ('CLAUDE writes code daily', True),     # A matches (insensitive), B matches (exact)
            ('claude writes CODE daily', False),    # A matches, but B doesn't (wrong case)
            ('Claude writes Code daily', False),    # A matches, but B doesn't (wrong case)
            ('no matches here', False),             # Neither matches
        ]
        
        all_passed = True
        for line_content, expected in test_lines:
            result = worker._evaluate_formula(line_content, test_params['phrases'], 'A & B')
            if result != expected:
                print(f"❌ FAILED: '{line_content}' -> {result} (expected {expected})")
                all_passed = False
            else:
                print(f"✅ PASSED: '{line_content}' -> {result}")
                
        return all_passed
        
    except Exception as e:
        print(f"❌ Error in mixed case test: {e}")
        return False

def test_ui_case_sensitivity_controls():
    """Test that UI case sensitivity controls work properly"""
    print("\n🔍 Testing UI case sensitivity controls...")
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from PySide6.QtWidgets import QApplication
        from Finder import Finder
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            
        finder = Finder()
        
        # Test default state (should be case-insensitive)
        for letter in 'ABCDEF':
            checkbox = finder.case_sensitive_checkboxes[letter]
            if checkbox.isChecked():
                print(f"❌ FAILED: {letter} checkbox should default to unchecked (case-insensitive)")
                return False
                
        print("✅ All checkboxes default to case-insensitive")
        
        # Test checking/unchecking
        test_letter = 'A'
        checkbox = finder.case_sensitive_checkboxes[test_letter]
        
        # Check the box
        checkbox.setChecked(True)
        if not checkbox.isChecked():
            print(f"❌ FAILED: Could not check {test_letter} case sensitivity box")
            return False
            
        print(f"✅ Can enable case sensitivity for {test_letter}")
        
        # Uncheck the box
        checkbox.setChecked(False)
        if checkbox.isChecked():
            print(f"❌ FAILED: Could not uncheck {test_letter} case sensitivity box")
            return False
            
        print(f"✅ Can disable case sensitivity for {test_letter}")
        
        # Test that search parameters are built correctly
        finder.phrase_inputs['A'].setText('test')
        finder.case_sensitive_checkboxes['A'].setChecked(True)
        
        # Get search parameters
        phrases = {}
        for letter in 'ABCDEF':
            phrases[letter] = {
                'text': finder.phrase_inputs[letter].text().strip(),
                'case_sensitive': finder.case_sensitive_checkboxes[letter].isChecked()
            }
            
        if not phrases['A']['case_sensitive']:
            print("❌ FAILED: Case sensitivity setting not properly captured")
            return False
            
        print("✅ Case sensitivity settings properly captured in search parameters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in UI test: {e}")
        return False

def main():
    """Run comprehensive case sensitivity tests"""
    print("🔍 COMPREHENSIVE CASE SENSITIVITY TEST SUITE")
    print("=" * 60)
    print("This verifies that case sensitivity works correctly in all scenarios")
    print("=" * 60)
    
    tests = [
        ("Case-Insensitive Search", test_case_insensitive_search),
        ("Case-Sensitive Search", test_case_sensitive_search),
        ("Mixed Case Sensitivity", test_mixed_case_sensitivity),
        ("UI Case Controls", test_ui_case_sensitivity_controls),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*20} CASE SENSITIVITY SUMMARY {'='*20}")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL CASE SENSITIVITY TESTS PASSED!")
        print("✅ Case sensitivity behavior is working correctly!")
        print("\n📋 BEHAVIOR SUMMARY:")
        print("• Case INSENSITIVE (default): 'claude' matches 'claude', 'Claude', 'CLAUDE'")
        print("• Case SENSITIVE (checked): 'claude' only matches 'claude'")
        print("• Each variable (A-F) can have independent case sensitivity settings")
        return 0
    else:
        print(f"\n⚠️  {total-passed} case sensitivity tests failed!")
        print("❌ Case sensitivity behavior needs to be fixed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())