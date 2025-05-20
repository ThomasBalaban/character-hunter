#!/usr/bin/env python3
# click_detector.py
# Click detection and image capture for Character Hunter
# Updated to use AppleScreenCapture for better macOS compatibility

import threading
import time
import numpy as np
import cv2
import pyautogui
import logging
from pynput import mouse
from apple_screen_capture import AppleScreenCapture

logger = logging.getLogger("CharacterHunter.ClickDetector")

class ClickDetector:
    """Detect user clicks and capture images around the click location"""
    
    def __init__(self, status_window, screen_watcher):
        self.status_window = status_window
        self.screen_watcher = screen_watcher
        self.running = False
        self.thread = None
        self.mouse_listener = None
        
        # Use the AppleScreenCapture for more reliable screen capture
        self.screen_capturer = AppleScreenCapture()
        
        # Size of region to capture around click (half-width and half-height)
        self.capture_radius = 150  # Will create a 300x300 image
        # Minimum time between captures to avoid duplicates (seconds)
        self.min_capture_interval = 1.0  # Increased to 1 second for trackpad
        self.last_capture_time = 0
    
    def start(self):
        """Start monitoring clicks using pynput for better trackpad support"""
        if not self.running:
            self.running = True
            # Use pynput for more reliable click detection, especially with trackpads
            self.mouse_listener = mouse.Listener(on_click=self._on_click)
            self.mouse_listener.start()
            logger.info("ClickDetector started with pynput listener")
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.mouse_listener:
            self.mouse_listener.stop()
            
        # Clean up the screen capturer
        if hasattr(self, 'screen_capturer'):
            self.screen_capturer.cleanup()
            
        logger.info("ClickDetector stopped")
    
    def _capture_image_at_click(self, x, y):
        """Capture a region around the click location using AppleScreenCapture"""
        try:
            # Calculate region to capture
            region = {
                'top': max(0, y - self.capture_radius),
                'left': max(0, x - self.capture_radius),
                'width': 2 * self.capture_radius,
                'height': 2 * self.capture_radius
            }
            
            logger.debug(f"Capturing region: {region}")
            
            # Capture screenshot using AppleScreenCapture
            screenshot = self.screen_capturer.capture_region(region)
            
            # Check if screenshot was successfully captured
            if screenshot is not None:
                # Check if image is valid (not all black)
                if np.mean(screenshot) < 5:  # Very dark image
                    logger.warning("Captured image is too dark (might be black)")
                    # Save it anyway for debugging
                    cv2.imwrite("black_capture.png", cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR))
                
                logger.debug(f"Captured image at ({x}, {y}) of size {screenshot.shape}")
                return screenshot
            else:
                logger.error(f"Failed to capture image at ({x}, {y})")
                return None
        except Exception as e:
            logger.error(f"Exception in _capture_image_at_click: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _on_click(self, x, y, button, pressed):
        """Handle mouse click events from pynput"""
        try:
            # Only process on button press (not release), and only left clicks
            if not pressed or button != mouse.Button.left:
                return
            
            # Check if click is on the status window - ignore if it is
            # Get window position and size
            win_x = self.status_window.root.winfo_x()
            win_y = self.status_window.root.winfo_y()
            win_width = self.status_window.root.winfo_width()
            win_height = self.status_window.root.winfo_height()
            
            # If click is within status window bounds, ignore it
            if (win_x <= x <= win_x + win_width and
                win_y <= y <= win_y + win_height):
                logger.debug("Click detected on status window - ignoring")
                return
            
            # Check if enough time has passed since last capture
            current_time = time.time()
            if current_time - self.last_capture_time <= self.min_capture_interval:
                logger.debug("Click ignored due to debounce")
                return
            
            # Check if Chrome is the active window - IMPORTANT
            is_chrome_active = self.screen_watcher._is_chrome_with_google()
            if not is_chrome_active:
                logger.debug("Click ignored - not in Chrome")
                return
                
            # Check if we have a valid search
            current_search = self.screen_watcher.get_current_search()
            if not current_search:
                logger.debug("Click ignored - no active search detected")
                return
                
            # Update status
            self.status_window.update_status(f"Clicked! Capturing image...")
            logger.info(f"Click detected at ({x}, {y}) in Chrome")
            
            # Capture image
            img = self._capture_image_at_click(x, y)
            
            # Process and save the image
            if img is not None:
                # Save debug image
                debug_path = f"debug_click_{int(current_time)}.png"
                cv2.imwrite(debug_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                logger.debug(f"Saved debug image to {debug_path}")
                
                # Import here to avoid circular imports
                from data_tagger import DataTagger
                
                # Process and save image
                threading.Thread(
                    target=self._process_and_save_image,
                    args=(img, current_search)
                ).start()
                
                # Update last capture time
                self.last_capture_time = current_time
            else:
                self.status_window.update_status("Failed to capture image")
                logger.error("Capture returned None")
            
        except Exception as e:
            logger.error(f"Error in click detector: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _process_and_save_image(self, img, search_info):
        """Process the captured image and save it with appropriate metadata"""
        try:
            # Import here to avoid circular imports
            from data_tagger import DataTagger
            
            # Create a DataTagger instance and use it
            tagger = DataTagger(self.status_window)
            tagger.process_and_save(img, search_info)
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            self.status_window.update_status("Error processing image")