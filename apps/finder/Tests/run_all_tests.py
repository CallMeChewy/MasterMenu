# File: run_all_tests.py
# Path: /home/herb/Desktop/Finder/Test/run_all_tests.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  01:45PM
"""
Comprehensive test runner for the Finder application
Runs both unit tests and functional tests, provides detailed reporting
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_suite(test_module_name, suite_name):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"Running {suite_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Import the test module
    test_module = __import__(test_module_name)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)
    
    # Run tests
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Print results
    output = stream.getvalue()
    print(output)
    
    return result, duration


def print_detailed_summary(unit_result, unit_duration, functional_result, functional_duration):
    """Print detailed test summary"""
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    
    # Unit tests summary
    print(f"\nUNIT TESTS:")
    print(f"  Tests run: {unit_result.testsRun}")
    print(f"  Failures: {len(unit_result.failures)}")
    print(f"  Errors: {len(unit_result.errors)}")
    print(f"  Duration: {unit_duration:.2f} seconds")
    print(f"  Success rate: {((unit_result.testsRun - len(unit_result.failures) - len(unit_result.errors)) / unit_result.testsRun * 100):.1f}%")
    
    # Functional tests summary
    print(f"\nFUNCTIONAL TESTS:")
    print(f"  Tests run: {functional_result.testsRun}")
    print(f"  Failures: {len(functional_result.failures)}")
    print(f"  Errors: {len(functional_result.errors)}")
    print(f"  Duration: {functional_duration:.2f} seconds")
    print(f"  Success rate: {((functional_result.testsRun - len(functional_result.failures) - len(functional_result.errors)) / functional_result.testsRun * 100):.1f}%")
    
    # Overall summary
    total_tests = unit_result.testsRun + functional_result.testsRun
    total_failures = len(unit_result.failures) + len(functional_result.failures)
    total_errors = len(unit_result.errors) + len(functional_result.errors)
    total_duration = unit_duration + functional_duration
    
    print(f"\nOVERALL SUMMARY:")
    print(f"  Total tests run: {total_tests}")
    print(f"  Total failures: {total_failures}")
    print(f"  Total errors: {total_errors}")
    print(f"  Total duration: {total_duration:.2f} seconds")
    print(f"  Overall success rate: {((total_tests - total_failures - total_errors) / total_tests * 100):.1f}%")
    
    # Detailed failure/error reporting
    if unit_result.failures or unit_result.errors:
        print(f"\nUNIT TEST ISSUES:")
        for test, traceback in unit_result.failures:
            print(f"  FAILURE - {test}")
            print(f"    {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
        
        for test, traceback in unit_result.errors:
            print(f"  ERROR - {test}")
            print(f"    {traceback.split(chr(10))[-2]}")
    
    if functional_result.failures or functional_result.errors:
        print(f"\nFUNCTIONAL TEST ISSUES:")
        for test, traceback in functional_result.failures:
            print(f"  FAILURE - {test}")
            print(f"    {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
        
        for test, traceback in functional_result.errors:
            print(f"  ERROR - {test}")
            print(f"    {traceback.split(chr(10))[-2]}")
    
    # Test coverage information
    print(f"\nTEST COVERAGE AREAS:")
    print(f"  ✓ Operator normalization (&, |, !, ^)")
    print(f"  ✓ Auto-formula construction")
    print(f"  ✓ Formula validation and error detection")
    print(f"  ✓ Search functionality with real files")
    print(f"  ✓ Case-sensitive vs case-insensitive search")
    print(f"  ✓ Unique mode functionality")
    print(f"  ✓ Document mode vs line mode")
    print(f"  ✓ Complex formula evaluation")
    print(f"  ✓ Project-specific file patterns")
    
    print(f"{'='*80}")
    
    return total_tests - total_failures - total_errors == total_tests


def main():
    """Main test runner function"""
    print("Finder Application - Comprehensive Test Suite")
    print("Running both unit tests and functional tests...")
    
    overall_start_time = time.time()
    
    try:
        # Run unit tests
        unit_result, unit_duration = run_test_suite('test_finder_unit', 'UNIT TESTS')
        
        # Run functional tests
        functional_result, functional_duration = run_test_suite('test_finder_functional', 'FUNCTIONAL TESTS')
        
        # Print comprehensive summary
        all_passed = print_detailed_summary(unit_result, unit_duration, functional_result, functional_duration)
        
        overall_end_time = time.time()
        overall_duration = overall_end_time - overall_start_time
        
        print(f"\nTotal execution time: {overall_duration:.2f} seconds")
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            print("The Finder application is ready for use.")
        else:
            print("\n❌ SOME TESTS FAILED")
            print("Please review the issues above and fix them before deployment.")
        
        return all_passed
        
    except ImportError as e:
        print(f"\n❌ ERROR: Could not import test modules")
        print(f"Make sure test_finder_unit.py and test_finder_functional.py are in the same directory")
        print(f"Error details: {e}")
        return False
    
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)