# File: test_search_button_direct.py
# Path: /home/herb/Desktop/Finder/Tests/test_search_button_direct.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-28
# Last Modified: 2025-07-28  03:45PM

"""
Direct test for search button functionality without pytest-qt
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_search_button_exists():
    """Test that the search button exists in the Finder application"""
    
    # Set up offscreen display
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from PySide6.QtWidgets import QApplication
        from Finder import Finder
        
        # Create application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            
        # Create Finder instance
        finder = Finder()
        
        # Test search button exists
        assert hasattr(finder, 'btn_search'), "Search button should exist"
        assert finder.btn_search is not None, "Search button should not be None"
        assert finder.btn_search.text() == "🔍 Start Search", f"Expected '🔍 Start Search', got '{finder.btn_search.text()}'"
        assert finder.btn_search.isEnabled(), "Search button should be enabled"
        
        print("✅ Search button exists and is properly configured")
        print(f"✅ Button text: {finder.btn_search.text()}")
        print(f"✅ Button enabled: {finder.btn_search.isEnabled()}")
        
        # Test other buttons exist
        buttons_to_test = [
            ('btn_validate', '✓ Validate Formula'),
            ('btn_reset', '🔄 Reset/Clear'),  # Fixed text
            ('btn_test_suite', '🎓 Run Examples')
        ]
        
        for button_attr, expected_text in buttons_to_test:
            assert hasattr(finder, button_attr), f"{button_attr} should exist"
            button = getattr(finder, button_attr)
            assert button is not None, f"{button_attr} should not be None"
            assert button.text() == expected_text, f"Expected '{expected_text}', got '{button.text()}'"
            print(f"✅ {button_attr}: {button.text()}")
        
        # Test phrase inputs exist
        assert hasattr(finder, 'phrase_inputs'), "phrase_inputs dictionary should exist"
        assert finder.phrase_inputs is not None, "phrase_inputs should not be None"
        
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            assert letter in finder.phrase_inputs, f"Phrase input {letter} should exist in phrase_inputs"
            input_field = finder.phrase_inputs[letter]
            assert input_field is not None, f"Phrase input {letter} should not be None"
            print(f"✅ phrase_inputs['{letter}'] exists")
        
        # Test formula input exists
        assert hasattr(finder, 'formula_input'), "Formula input should exist"
        assert finder.formula_input is not None, "Formula input should not be None"
        print("✅ formula_input exists")
        
        # Test results display exists
        assert hasattr(finder, 'results_display'), "Results display should exist"
        assert finder.results_display is not None, "Results display should not be None"
        print("✅ results_display exists")
        
        # Test path input exists
        assert hasattr(finder, 'path_display'), "Path display should exist"
        assert finder.path_display is not None, "Path display should not be None"
        print("✅ path_display exists")
        
        # Test that search functionality methods exist
        search_methods = ['_start_search', '_validate_search_parameters', '_validate_formula_on_demand']
        for method in search_methods:
            assert hasattr(finder, method), f"Method {method} should exist"
            print(f"✅ {method} method exists")
        
        print("\n🎉 ALL TESTS PASSED - Search button and UI components are properly configured!")
        print("SUCCESS: All search button tests completed successfully.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        if 'app' in locals() and app:
            try:
                app.quit()
            except:
                pass


def test_search_button_can_be_clicked():
    """Test that the search button can be clicked (without actually running search)"""
    
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from unittest.mock import patch
        from Finder import Finder
        
        # Create application
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
            
        # Create Finder instance
        finder = Finder()
        
        # Mock the _start_search method to avoid actually running search
        with patch.object(finder, '_start_search') as mock_search:
            # Simulate button click
            finder.btn_search.click()
            
            # Verify the method was called
            mock_search.assert_called_once()
            print("✅ Search button click triggers _start_search method")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in click test: {e}")
        return False
    
    finally:
        # Clean up
        if 'app' in locals() and app:
            try:
                app.quit()
            except:
                pass


if __name__ == "__main__":
    print("Testing Finder application search button functionality...\n")
    
    test1_passed = test_search_button_exists()
    print("\n" + "="*60 + "\n")
    test2_passed = test_search_button_can_be_clicked()
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! The search button is working correctly.")
        print("SUCCESS: Search button validation completed successfully.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)