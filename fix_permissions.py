#!/usr/bin/env python3
# fix_permissions.py
# A helper script to fix permissions issues with Character Hunter

import os
import sys
import subprocess
import time
import mss
import numpy as np

def test_screen_capture():
    """Test if screen capture permission is granted"""
    print("Testing screen capture permission...")
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Get the primary monitor
            screenshot = np.array(sct.grab(monitor))
            
            # Check if the screenshot is all black (indicates no permission)
            if np.max(screenshot) < 5:  # Almost completely black
                print("❌ Test FAILED: Screenshots appear black, which means permission is NOT granted")
                return False
            else:
                print("✅ Test PASSED: Screen capture permission is granted")
                return True
    except Exception as e:
        print(f"❌ Test ERROR: {e}")
        return False

def open_system_preferences():
    """Open System Preferences/Settings to the Screen Recording permission page"""
    print("Opening System Preferences/Settings to Screen Recording permissions...")
    
    try:
        # macOS Ventura and newer
        subprocess.run([
            "open", 
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
        ])
    except:
        # Fallback for older macOS versions
        subprocess.run(["open", "/System/Library/PreferencePanes/Security.prefPane"])
        
    print("Please enable screen recording permission for Terminal and/or Python")

def main():
    """Main function to check and fix permissions"""
    print("\n=== Character Hunter - Permission Fixer ===\n")
    
    # Test screen capture permission
    has_permission = test_screen_capture()
    
    if not has_permission:
        print("\nTo fix permission issues:")
        print("1. Allow Terminal/Python to record your screen in System Settings")
        print("2. Restart Terminal/Python after granting permission")
        
        # Ask if they want to open System Preferences
        choice = input("\nWould you like to open System Settings now? (y/n): ").strip().lower()
        if choice == 'y':
            open_system_preferences()
            print("\nAfter enabling permission:")
            print("1. Close and reopen Terminal/your IDE")
            print("2. Run this script again to verify permissions are working")
    else:
        print("\nYour screen capture permissions are correctly configured!")
        print("Character Hunter should now be able to capture images properly.")
    
    print("\nIf you're running from VSCode or another IDE, make sure to grant")
    print("permission to that application as well, not just Terminal.")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
