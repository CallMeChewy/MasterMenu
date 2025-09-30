# File: run_validation_suite.py
# Path: /home/herb/Desktop/Finder/Tests/run_validation_suite.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-28
# Last Modified: 2025-07-28  03:50PM

"""
Comprehensive validation suite using MCP tools
Tests all functionality and reports status
"""

import sys
import os
import subprocess
from pathlib import Path

def run_basic_tests():
    """Run basic functionality tests"""
    print("🔍 Running basic functionality tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", "Tests/test_basic_functionality.py", "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Basic functionality tests: PASSED")
        return True
    else:
        print("❌ Basic functionality tests: FAILED")
        print(result.stdout)
        print(result.stderr)
        return False

def run_search_button_tests():
    """Run search button functionality tests"""
    print("🔍 Running search button tests...")
    result = subprocess.run([
        sys.executable, "Tests/test_search_button_direct.py"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Search button tests: PASSED")
        return True
    else:
        print("❌ Search button tests: FAILED")
        print(result.stdout)
        print(result.stderr)
        return False

def run_test_suite_generator():
    """Run test suite generator"""
    print("🔍 Running test suite generator...")
    result = subprocess.run([
        sys.executable, "Tests/test_suite_generator.py"
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        print("✅ Test suite generator: PASSED")
        return True
    else:
        print("❌ Test suite generator: FAILED")
        print(result.stdout)
        print(result.stderr)
        return False

def run_regression_tests():
    """Run regression test suite"""
    print("🔍 Running regression tests...")
    result = subprocess.run([
        sys.executable, "Tests/test_regression_suite.py"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Regression tests: PASSED")
        return True
    else:
        print("❌ Regression tests: FAILED")
        print(result.stdout)
        print(result.stderr)
        return False

def run_compliance_validation():
    """Run compliance validation if available"""
    print("🔍 Running compliance validation...")
    compliance_file = Path("Tests/validate_compliance.py")
    
    if compliance_file.exists():
        result = subprocess.run([
            sys.executable, str(compliance_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Compliance validation: PASSED")
            return True
        else:
            print("❌ Compliance validation: FAILED")
            print(result.stdout)
            print(result.stderr)
            return False
    else:
        print("⚠️  Compliance validation: SKIPPED (file not found)")
        return True

def check_file_structure():
    """Check that required files exist"""
    print("🔍 Checking file structure...")
    
    required_files = [
        "Finder.py",
        "CLAUDE.md",
        "requirements.txt",
        "pytest.ini",
        "Tests/test_basic_functionality.py",
        "Tests/test_search_button_direct.py",
        "Tests/test_suite_generator.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Run comprehensive validation suite"""
    print("🚀 FINDER APPLICATION - COMPREHENSIVE VALIDATION SUITE")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(Path(__file__).parent.parent)
    
    tests = [
        ("File Structure", check_file_structure),
        ("Basic Functionality", run_basic_tests),
        ("Search Button", run_search_button_tests),
        ("Test Suite Generator", run_test_suite_generator),
        ("Regression Tests", run_regression_tests),
        ("Compliance", run_compliance_validation)
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
    print(f"\n{'='*20} VALIDATION SUMMARY {'='*20}")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ The Finder application is ready for user testing.")
        return 0
    else:
        print(f"\n⚠️  {total-passed} tests failed.")
        print("❌ Please address failing tests before user testing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())