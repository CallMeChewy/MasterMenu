#!/usr/bin/env python3
"""
Simple test to verify the LLM Tester application launches successfully
"""

import sys
import subprocess
import time

def test_app_launch():
    """Test that the app launches without crashing"""
    print("🧪 Testing LLM Tester Application Launch...")

    try:
        # Start the application process
        process = subprocess.Popen(
            [sys.executable, "LLM-Tester-Enhanced.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/home/herb/Desktop/LLM-Tester"
        )

        # Let it run for a few seconds to initialize
        time.sleep(3)

        # Check if process is still running (no crash)
        if process.poll() is None:
            print("✅ Application launched successfully!")
            print("✅ No crash detected in first 3 seconds")

            # Terminate the process
            process.terminate()
            process.wait(timeout=5)

            return True
        else:
            # Process terminated (crashed)
            stdout, stderr = process.communicate()
            print("❌ Application crashed during launch")
            if stderr:
                print(f"Error: {stderr}")
            if stdout:
                print(f"Output: {stdout}")
            return False

    except Exception as e:
        print(f"❌ Failed to test application launch: {e}")
        return False

if __name__ == "__main__":
    success = test_app_launch()
    if success:
        print("\n🎉 LLM Tester is ready to use!")
        print("🚀 You can now run: python3 LLM-Tester-Enhanced.py")
    else:
        print("\n❌ There are still issues to resolve")

    sys.exit(0 if success else 1)