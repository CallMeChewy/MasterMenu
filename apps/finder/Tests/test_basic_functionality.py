# File: test_basic_functionality.py
# Path: /home/herb/Desktop/Finder/Tests/test_basic_functionality.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-28
# Last Modified: 2025-07-28  03:35PM

"""
Basic functionality tests for Finder application
Tests core functionality without GUI dependencies
"""

import sys
import os
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBasicFunctionality:
    """Test basic functionality that doesn't require GUI"""
    
    def test_project_structure_exists(self):
        """Test that required project files exist"""
        project_root = Path(__file__).parent.parent
        
        # Check main files exist
        assert (project_root / "Finder.py").exists()
        assert (project_root / "CLAUDE.md").exists()
        assert (project_root / "requirements.txt").exists()
        
        # Check Tests directory exists
        assert (project_root / "Tests").exists()
        assert (project_root / "Tests").is_dir()
        
    def test_test_suite_generator_exists(self):
        """Test that test suite generator exists and is importable"""
        try:
            from test_suite_generator import TestSuiteRunner, FormulaGenerator
            assert TestSuiteRunner is not None
            assert FormulaGenerator is not None
        except ImportError as e:
            pytest.fail(f"Could not import test suite components: {e}")
            
    def test_test_suite_runner_instantiation(self):
        """Test that TestSuiteRunner can be instantiated"""
        from test_suite_generator import TestSuiteRunner
        runner = TestSuiteRunner()
        assert runner is not None
        assert hasattr(runner, 'generator')
        
    def test_formula_generator_instantiation(self):
        """Test that FormulaGenerator can be instantiated"""
        from test_suite_generator import FormulaGenerator
        generator = FormulaGenerator()
        assert generator is not None
        
    def test_generate_test_suite(self):
        """Test that test suite can be generated"""
        from test_suite_generator import FormulaGenerator
        generator = FormulaGenerator()
        scenarios = generator.generate_test_suite()
        
        assert isinstance(scenarios, list)
        assert len(scenarios) == 5  # Should generate 5 scenarios
        
        # Check each scenario has required fields
        for scenario in scenarios:
            assert 'name' in scenario
            assert 'formula' in scenario
            assert 'complexity' in scenario
            assert 'phrases' in scenario
            assert 'educational_note' in scenario
            
    def test_scenario_complexity_levels(self):
        """Test that scenarios have correct complexity levels"""
        from test_suite_generator import FormulaGenerator
        generator = FormulaGenerator()
        scenarios = generator.generate_test_suite()
        
        complexities = [scenario['complexity'] for scenario in scenarios]
        expected_complexities = [1, 2, 3, 4, 5]
        
        assert sorted(complexities) == expected_complexities
        
    def test_scenario_formulas_are_different(self):
        """Test that generated scenarios have different formulas"""
        from test_suite_generator import FormulaGenerator
        generator = FormulaGenerator()
        scenarios = generator.generate_test_suite()
        
        formulas = [scenario['formula'] for scenario in scenarios]
        # All formulas should be different
        assert len(set(formulas)) == len(formulas)


class TestFileOperations:
    """Test file operations and path handling"""
    
    def test_current_directory_access(self):
        """Test that current directory can be accessed"""
        current_dir = os.getcwd()
        assert os.path.exists(current_dir)
        assert os.path.isdir(current_dir)
        
    def test_project_directory_structure(self):
        """Test project directory structure"""
        project_root = Path(__file__).parent.parent
        
        # Test that key directories exist or are expected to be missing
        tests_dir = project_root / "Tests"
        assert tests_dir.exists()
        
        # Check if Updates directory exists (might not always be present)
        updates_dir = project_root / "Updates"
        if updates_dir.exists():
            assert updates_dir.is_dir()
            
    def test_python_path_setup(self):
        """Test that Python path includes project directory"""
        project_root = str(Path(__file__).parent.parent)
        assert project_root in sys.path or any(project_root in p for p in sys.path)


class TestImportCapabilities:
    """Test import capabilities for core modules"""
    
    def test_import_standard_libraries(self):
        """Test that standard libraries can be imported"""
        import os
        import sys
        import pathlib
        import datetime
        import re
        
        # Basic assertions to ensure imports worked
        assert hasattr(os, 'path')
        assert hasattr(sys, 'path')
        assert hasattr(pathlib, 'Path')
        assert hasattr(datetime, 'datetime')
        assert hasattr(re, 'compile')
        
    def test_import_testing_libraries(self):
        """Test that testing libraries can be imported"""
        import pytest
        from unittest.mock import Mock, patch
        
        assert pytest is not None
        assert Mock is not None
        assert patch is not None


class TestConfiguration:
    """Test configuration and setup"""
    
    def test_pytest_configuration_exists(self):
        """Test that pytest configuration exists"""
        project_root = Path(__file__).parent.parent
        pytest_config = project_root / "pytest.ini"
        assert pytest_config.exists()
        
    def test_requirements_file_readable(self):
        """Test that requirements.txt is readable"""
        project_root = Path(__file__).parent.parent
        requirements_file = project_root / "requirements.txt"
        
        assert requirements_file.exists()
        
        # Try to read the file
        with open(requirements_file, 'r') as f:
            content = f.read()
            assert len(content) > 0
            
    def test_claude_md_readable(self):
        """Test that CLAUDE.md is readable"""
        project_root = Path(__file__).parent.parent
        claude_md = project_root / "CLAUDE.md"
        
        assert claude_md.exists()
        
        # Try to read the file
        with open(claude_md, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert "CLAUDE.md" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])