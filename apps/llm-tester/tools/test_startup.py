#!/usr/bin/env python3
"""
Test script to check if LLM Tester Enhanced can initialize without crashing
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    import ollama
    import psutil
    from PySide6.QtWidgets import QApplication
    from database import init_db
    print("✓ All imports successful")

    print("Testing database connection...")
    init_db()
    print("✓ Database initialized")

    print("Testing Ollama connection...")
    models = ollama.list()
    print(f"✓ Ollama connected, found {len(models['models'])} models")

    print("Testing GUI initialization...")
    app = QApplication(sys.argv)
    # Import the class directly from the file
    import importlib.util
    spec = importlib.util.spec_from_file_location("llm_tester", "LLM-Tester-Enhanced.py")
    llm_tester_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(llm_tester_module)
    LLMTesterEnhanced = llm_tester_module.LLMTesterEnhanced
    window = LLMTesterEnhanced()
    print("✓ GUI initialized successfully")

    # Clean up threads properly
    window.test_worker.stop()
    window.system_monitor.stop()
    window.test_worker.wait()
    window.system_monitor.wait()

    print("All tests passed! Application should start correctly.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)