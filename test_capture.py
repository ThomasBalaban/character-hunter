#!/usr/bin/env python3
# test_capture.py
# Test script for AppleScreenCapture

import os
import cv2
import numpy as np
from apple_screen_capture import AppleScreenCapture

def test_apple_screen_capture():
    """Test the AppleScreenCapture class"""
    print("Testing AppleScreenCapture...")
    
    # Create an instance of AppleScreenCapture
    capturer = AppleScreenCapture()
    
    # Test full screen capture
    print("\nCapturing full screen...")
    full_screen = capturer.capture_region()
    
    if full_screen is not None:
        print(f"✅ Success! Captured full screen image of shape {full_screen.shape}")
        # Save the image for inspection
        cv2.imwrite("test_full_screen.png", cv2.cvtColor(full_screen, cv2.COLOR_RGB2BGR))
        print(f"Saved to test_full_screen.png")
    else:
        print("❌ Failed to capture full screen")
    
    # Test region capture
    print("\nCapturing top-left region of screen...")
    region = {'top': 0, 'left': 0, 'width': 400, 'height': 300}
    region_capture = capturer.capture_region(region)
    
    if region_capture is not None:
        print(f"✅ Success! Captured region with shape {region_capture.shape}")
        # Save the image for inspection
        cv2.imwrite("test_region.png", cv2.cvtColor(region_capture, cv2.COLOR_RGB2BGR))
        print(f"Saved to test_region.png")
    else:
        print("❌ Failed to capture region")
    
    # Clean up
    capturer.cleanup()
    print("\nTest complete. Check the saved images to verify screen capture is working.")
    print("If the images look black or empty, there might still be permission issues.")

if __name__ == "__main__":
    test_apple_screen_capture()
