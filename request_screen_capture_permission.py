#!/usr/bin/env python3
# request_screen_capture_permission.py
# A helper script to request screen capture permission on macOS

import AppKit
import subprocess
import sys
import time

def request_screen_capture_permission():
    """Request screen capture permission by attempting to capture the screen"""
    try:
        print("Requesting screen capture permission...")
        print("If prompted, please allow Terminal/Python to record your screen.")
        print("This is required for the Character Hunter app to detect Google searches.")
        print("\nWaiting for permission dialog...")
        
        # Try to capture the screen using AppleScript, which will trigger the permission dialog
        script = '''
        tell application "System Events"
            keystroke (key code 21 using {command down, shift down, control down})  # Command+Shift+Control+3
        end tell
        '''
        
        # Execute the AppleScript
        subprocess.run(["osascript", "-e", script], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        print("\n✓ Permission requested.")
        print("If you didn't see a permission dialog, please grant screen recording permission manually:")
        print("  1. Go to System Settings > Privacy & Security > Screen Recording")
        print("  2. Find Terminal (or your Python IDE) and enable the permission")
        
    except Exception as e:
        print(f"Error requesting permission: {e}")
        print("Please grant screen recording permission manually:")
        print("  1. Go to System Settings > Privacy & Security > Screen Recording")
        print("  2. Find Terminal (or your Python IDE) and enable the permission")
    
    # Wait a moment before exiting
    time.sleep(1)
    print("\nTry running Character Hunter again after granting permission.")

if __name__ == "__main__":
    request_screen_capture_permission()
