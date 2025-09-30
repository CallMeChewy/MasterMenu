# File: run_tests.py
# Path: /home/herb/Desktop/Finder/Test/run_tests.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-18
# Last Modified: 2025-07-18  13:46PM

"""
Comprehensive test runner for Finder application
Runs all tests from the Test directory with proper configuration
"""

import os
import sys
import unittest
import subprocess
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

class TestRunner:
    def __init__(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.results = {}
        
    def run_all_tests(self):
        """Run all available test suites"""
        print("🔬 FINDER APPLICATION TEST SUITE")
        print("=" * 80)
        print(f"📁 Test Directory: {self.test_dir}")
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Test suites to run
        test_suites = [
            ("Unit Tests", "test_finder_working.py"),
            ("Functional Tests", "test_finder_functional.py"),
            ("Enhanced Features", "test_finder_enhanced.py"),
            ("Formula Validation", "test_formula_validation.py"),
            ("Educational Suite", "test_suite_generator.py"),
            ("Operator Tests", "test_enhanced_operators.py"),
            ("Case Sensitivity", "test_case_sensitivity.py")
        ]
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for suite_name, test_file in test_suites:
            print(f"\n📋 Running {suite_name}: {test_file}")
            print("-" * 60)
            
            result = self._run_test_file(test_file)
            self.results[suite_name] = result
            
            if result['success']:
                print(f"✅ {suite_name}: PASSED")
                passed_tests += 1
            else:
                print(f"❌ {suite_name}: FAILED")
                failed_tests += 1
                
            total_tests += 1
            
            if result.get('output'):
                print(f"📝 Output: {result['output'][:200]}...")
                
        # Print summary
        self._print_summary(total_tests, passed_tests, failed_tests)
        
    def _run_test_file(self, test_file):
        """Run individual test file"""
        test_path = os.path.join(self.test_dir, test_file)
        
        if not os.path.exists(test_path):
            return {'success': False, 'error': 'File not found', 'output': ''}
            
        try:
            # Change to test directory
            original_dir = os.getcwd()
            os.chdir(self.test_dir)
            
            # Run the test
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Restore directory
            os.chdir(original_dir)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'returncode': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            os.chdir(original_dir)
            return {'success': False, 'error': 'Test timeout', 'output': ''}
        except Exception as e:
            os.chdir(original_dir)
            return {'success': False, 'error': str(e), 'output': ''}
    
    def _print_summary(self, total, passed, failed):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        print(f"📁 Total Test Suites: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total*100):.1f}%")
        
        print(f"\n🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Detailed results
        if failed > 0:
            print(f"\n🚨 FAILED TESTS:")
            for suite_name, result in self.results.items():
                if not result['success']:
                    print(f"  ❌ {suite_name}: {result.get('error', 'Unknown error')}")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED!")
            print("✅ Finder application is working correctly")
        else:
            print(f"\n⚠️  SOME TESTS FAILED")
            print("🔧 Check individual test outputs for details")

def run_unittest_discovery():
    """Run unittest discovery for all test files"""
    print("\n🔍 RUNNING UNITTEST DISCOVERY")
    print("=" * 50)
    
    # Change to test directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    try:
        # Add parent directory to path
        sys.path.insert(0, '..')
        
        # Discover and run tests
        loader = unittest.TestLoader()
        suite = loader.discover('.', pattern='test_*.py')
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print results
        print(f"\n📊 Tests run: {result.testsRun}")
        print(f"✅ Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"🚨 Errors: {len(result.errors)}")
        
        return result.wasSuccessful()
        
    finally:
        os.chdir(original_dir)

def main():
    """Main test runner function"""
    print("🔬 FINDER APPLICATION - COMPREHENSIVE TEST RUNNER")
    print("=" * 80)
    
    # Check if we're in the right directory
    current_dir = os.path.basename(os.getcwd())
    if current_dir != "Test":
        print("⚠️  Warning: Not running from Test directory")
        print(f"📁 Current directory: {os.getcwd()}")
    
    # Run comprehensive tests
    runner = TestRunner()
    runner.run_all_tests()
    
    # Run unittest discovery
    unittest_success = run_unittest_discovery()
    
    print("\n" + "=" * 80)
    print("🏁 TESTING COMPLETE")
    print("=" * 80)
    
    if unittest_success:
        print("🎉 All unittest discovery tests passed!")
    else:
        print("⚠️  Some unittest discovery tests failed")
        
    print("\n💡 To run individual tests:")
    print("  cd Test")
    print("  python test_finder_working.py")
    print("  python test_suite_generator.py")
    print("\n💡 To run this comprehensive suite:")
    print("  cd Test")
    print("  python run_tests.py")

if __name__ == "__main__":
    main()