#!/usr/bin/env python3
# apple_screen_capture.py
# Alternative screen capture implementation using AppleScript

import os
import subprocess
import tempfile
import time
import logging
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("CharacterHunter.AppleScreenCapture")

class AppleScreenCapture:
    """Screen capture using AppleScript and screencapture utility"""
    
    def __init__(self):
        # Create a temporary directory for screen captures
        self.temp_dir = tempfile.mkdtemp(prefix="character_hunter_")
        logger.info(f"Created temporary directory for screen captures: {self.temp_dir}")
        
        # Check if screencapture command is available
        try:
            subprocess.run(["which", "screencapture"], 
                         check=True, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
            logger.info("screencapture utility is available")
            self.screencapture_available = True
        except subprocess.SubprocessError:
            logger.warning("screencapture utility not found, falling back to alternative methods")
            self.screencapture_available = False
    
    def capture_region(self, region=None):
        """Capture a region of the screen
        
        Args:
            region (dict, optional): Region to capture {'top': int, 'left': int, 'width': int, 'height': int}
                                    If None, captures the entire screen
        
        Returns:
            numpy.ndarray: The captured screenshot as a numpy array, or None if failed
        """
        temp_file = os.path.join(self.temp_dir, f"capture_{int(time.time())}.png")
        
        try:
            if self.screencapture_available:
                # Use macOS screencapture utility
                if region:
                    # Calculate region parameters for screencapture
                    x = region['left']
                    y = region['top']
                    w = region['width']
                    h = region['height']
                    cmd = ["screencapture", "-R", f"{x},{y},{w},{h}", "-t", "png", temp_file]
                else:
                    # Capture entire screen
                    cmd = ["screencapture", "-t", "png", temp_file]
                
                result = subprocess.run(cmd, check=True, capture_output=True)
                logger.debug(f"screencapture completed: {result.returncode}")
            else:
                # Fallback: use AppleScript
                script = f'''
                do shell script "screencapture -t png {temp_file}"
                '''
                subprocess.run(["osascript", "-e", script], check=True)
                logger.debug("AppleScript screencapture completed")
            
            # Check if the file was created and has content
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 100:
                # Read the captured image
                img = cv2.imread(temp_file)
                
                # Convert to RGB (from BGR)
                if img is not None:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    
                    # Crop to region if needed and only if we captured the whole screen
                    if region and not self.screencapture_available:
                        h, w = img.shape[:2]
                        x1 = min(region['left'], w-1)
                        y1 = min(region['top'], h-1)
                        x2 = min(x1 + region['width'], w)
                        y2 = min(y1 + region['height'], h)
                        img = img[y1:y2, x1:x2]
                    
                    # Clean up
                    os.remove(temp_file)
                    return img
                else:
                    logger.error(f"Failed to read screenshot from {temp_file}")
            else:
                logger.error(f"Screenshot file not created or empty: {temp_file}")
                
            return None
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            # Clean up if file exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            # Remove the temporary directory and its contents
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    try:
                        os.remove(os.path.join(self.temp_dir, file))
                    except Exception as e:
                        logger.warning(f"Failed to remove temp file: {e}")
                
                os.rmdir(self.temp_dir)
                logger.info(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()