#!/usr/bin/env python3
# File: run_tests.py
# Path: /home/herb/Desktop/LLM-Tester/run_tests.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-10-03
# Last Modified: 2025-10-03 11:36PM

"""
Test runner script for LLM-Tester comprehensive test suite.

This script provides various test execution options including:
- Unit tests only
- Integration tests only
- UI tests only
- Performance tests only
- Full test suite
- Coverage reporting
- Parallel execution
- Test result formatting
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime


def check_dependencies():
    """Check if required testing dependencies are installed."""
    required_packages = [
        'pytest',
        'pytest-cov',
        'pytest-mock',
        'pytest-qt',
        'pytest-timeout',
        'pytest-benchmark'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing test dependencies: {', '.join(missing_packages)}")
        print(f"Install with: pip install -r requirements-test.txt")
        return False

    print("✅ All test dependencies are available")
    return True


def run_command(cmd, description="", capture_output=False):
    """Run a command and handle errors."""
    print(f"🚀 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)

    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout, result.stderr
        else:
            subprocess.run(cmd, check=True)
            return None, None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {description}:")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        print(f"Return code: {e.returncode}")
        sys.exit(1)


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests only."""
    cmd = ["python", "-m", "pytest", "-m", "unit"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])

    run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False, coverage=False):
    """Run integration tests only."""
    cmd = ["python", "-m", "pytest", "-m", "integration"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])

    run_command(cmd, "Running integration tests")


def run_ui_tests(verbose=False):
    """Run UI tests only."""
    cmd = ["python", "-m", "pytest", "-m", "ui", "--tb=short"]

    if verbose:
        cmd.append("-v")

    run_command(cmd, "Running UI tests")


def run_api_tests(verbose=False):
    """Run API integration tests only."""
    cmd = ["python", "-m", "pytest", "-m", "api", "--tb=short"]

    if verbose:
        cmd.append("-v")

    run_command(cmd, "Running API integration tests")


def run_performance_tests(verbose=False):
    """Run performance tests only."""
    cmd = ["python", "-m", "pytest", "-m", "performance", "--tb=short"]

    if verbose:
        cmd.append("-v")

    run_command(cmd, "Running performance tests")


def run_database_tests(verbose=False):
    """Run database tests only."""
    cmd = ["python", "-m", "pytest", "-m", "database", "--tb=short"]

    if verbose:
        cmd.append("-v")

    run_command(cmd, "Running database tests")


def run_full_suite(verbose=False, coverage=False, parallel=False, html_report=False):
    """Run the complete test suite."""
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")

    if parallel:
        cmd.extend(["-n", "auto"])  # Requires pytest-xdist

    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=75"  # Lower threshold for full suite
        ])

    if html_report:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])

    run_command(cmd, "Running complete test suite")


def run_quick_tests():
    """Run a quick subset of tests for immediate feedback."""
    cmd = [
        "python", "-m", "pytest",
        "-m", "unit and not slow",
        "-v",
        "--tb=short",
        "--maxfail=5"
    ]

    run_command(cmd, "Running quick tests")


def run_benchmark_tests():
    """Run benchmark tests for performance analysis."""
    cmd = [
        "python", "-m", "pytest",
        "-m", "benchmark",
        "--benchmark-only",
        "--benchmark-json=benchmark_results.json",
        "-v"
    ]

    run_command(cmd, "Running benchmark tests")


def generate_test_report():
    """Generate comprehensive test report."""
    print("📊 Generating comprehensive test report...")

    # Create timestamp for report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)

    report_file = report_dir / f"test_report_{timestamp}.html"

    cmd = [
        "python", "-m", "pytest",
        "--html", str(report_file),
        "--self-contained-html",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--tb=short",
        "-v"
    ]

    stdout, stderr = run_command(cmd, "Generating test report", capture_output=True)

    print(f"✅ Test report generated: {report_file}")
    print(f"📁 Reports directory: {report_dir.absolute()}")


def cleanup_test_artifacts():
    """Clean up test artifacts and temporary files."""
    print("🧹 Cleaning up test artifacts...")

    artifacts_to_remove = [
        ".coverage",
        "htmlcov",
        ".pytest_cache",
        "__pycache__",
        "**/__pycache__",
        "**/.pytest_cache",
        "test_report.html",
        "benchmark_results.json"
    ]

    import shutil
    import glob

    for pattern in artifacts_to_remove:
        for path in glob.glob(pattern, recursive=True):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    print(f"  🗑️  Removed file: {path}")
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"  🗑️  Removed directory: {path}")
            except Exception as e:
                print(f"  ⚠️  Could not remove {path}: {e}")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="LLM-Tester Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --full                    # Run all tests
  python run_tests.py --unit                    # Run unit tests only
  python run_tests.py --integration             # Run integration tests only
  python run_tests.py --ui                      # Run UI tests only
  python run_tests.py --performance             # Run performance tests only
  python run_tests.py --coverage                # Run tests with coverage
  python run_tests.py --quick                   # Run quick tests
  python run_tests.py --benchmark               # Run benchmark tests
  python run_tests.py --report                  # Generate HTML report
  python run_tests.py --cleanup                 # Clean up artifacts
        """
    )

    # Test type options
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--ui", action="store_true", help="Run UI tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--database", action="store_true", help="Run database tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--full", action="store_true", help="Run complete test suite")
    parser.add_argument("--quick", action="store_true", help="Run quick tests (unit tests, no slow tests)")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark tests")

    # Configuration options
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel (requires pytest-xdist)")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML test report")

    # Utility options
    parser.add_argument("--report", action="store_true", help="Generate comprehensive test report")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test artifacts")
    parser.add_argument("--check-deps", action="store_true", help="Check test dependencies")

    args = parser.parse_args()

    # Print header
    print("=" * 60)
    print("🧪 LLM-Tester Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check dependencies if requested
    if args.check_deps:
        if not check_dependencies():
            sys.exit(1)
        print()
        return

    # Run cleanup if requested
    if args.cleanup:
        cleanup_test_artifacts()
        return

    # Generate report if requested
    if args.report:
        generate_test_report()
        return

    # Check dependencies automatically
    if not check_dependencies():
        sys.exit(1)
    print()

    # Track execution time
    start_time = time.time()

    # Execute requested test suite
    try:
        if args.unit:
            run_unit_tests(verbose=args.verbose, coverage=args.coverage)
        elif args.integration:
            run_integration_tests(verbose=args.verbose, coverage=args.coverage)
        elif args.ui:
            run_ui_tests(verbose=args.verbose)
        elif args.api:
            run_api_tests(verbose=args.verbose)
        elif args.database:
            run_database_tests(verbose=args.verbose)
        elif args.performance:
            run_performance_tests(verbose=args.verbose)
        elif args.quick:
            run_quick_tests()
        elif args.benchmark:
            run_benchmark_tests()
        elif args.full:
            run_full_suite(
                verbose=args.verbose,
                coverage=args.coverage,
                parallel=args.parallel,
                html_report=args.html_report
            )
        else:
            # Default: run full suite
            run_full_suite(
                verbose=args.verbose,
                coverage=args.coverage,
                parallel=args.parallel,
                html_report=args.html_report
            )

        # Print execution summary
        end_time = time.time()
        duration = end_time - start_time
        print()
        print("=" * 60)
        print("✅ Test execution completed successfully!")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()