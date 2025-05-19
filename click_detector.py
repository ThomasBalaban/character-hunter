#!/usr/bin/env python3
# click_detector.py
# Click detection and image capture for Character Hunter

import threading
import time
import numpy as np
import cv2
import pyautogui
import mss
import logging

logger = logging.getLogger("CharacterHunter.ClickDetector")

class ClickDetector:
    """Detect user clicks and capture images around the click location"""
    
    def __init__(self, status_window, screen_watcher):
        self.status_window = status_window
        self.screen_watcher = screen_watcher
        self.running = False
        self.thread = None
        self.sct = mss.mss()
        # Size of region to capture around click (half-width and half-height)
        self.capture_radius = 150  # Will create a 300x300 image
        # Minimum time between captures to avoid duplicates (seconds)
        self.min_capture_interval = 0.5
        self.last_capture_time = 0
    
    def start(self):
        """Start monitoring clicks in a separate thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._click_monitor_loop)
            self.thread.daemon = True
            self.thread.start()
            logger.info("ClickDetector started")
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            logger.info("ClickDetector stopped")
    
    def _capture_image_at_click(self, x, y):
        """Capture a region around the click location"""
        # Calculate region to capture
        region = {
            'top': max(0, y - self.capture_radius),
            'left': max(0, x - self.capture_radius),
            'width': 2 * self.capture_radius,
            'height': 2 * self.capture_radius
        }
        
        # Capture screenshot
        screenshot = np.array(self.sct.grab(region))
        
        # Convert to RGB (from BGR)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
        
        return screenshot
    
    def _click_monitor_loop(self):
        """Main loop to monitor for clicks"""
        # Store the last position to avoid duplicate captures
        last_x, last_y = 0, 0
        
        while self.running:
            try:
                # Check for mouse clicks (using pyautogui or pynput could work too)
                if pyautogui.mouseDown():
                    # Get current position
                    x, y = pyautogui.position()
                    
                    # Check if this is a new position since last capture
                    distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
                    current_time = time.time()
                    
                    # Only capture if we have a significant distance change and enough time passed
                    if (distance > 20 and 
                        current_time - self.last_capture_time > self.min_capture_interval):
                        
                        # Check if we have a valid search
                        current_search = self.screen_watcher.get_current_search()
                        if current_search:
                            # Update status
                            self.status_window.update_status(f"Clicked! Capturing image...")
                            
                            # Capture image
                            img = self._capture_image_at_click(x, y)
                            
                            # Process and save the image
                            if img is not None:
                                # Import here to avoid circular imports
                                from data_tagger import DataTagger
                                
                                # Process and save image
                                threading.Thread(
                                    target=self._process_and_save_image,
                                    args=(img, current_search)
                                ).start()
                            
                            # Update state
                            last_x, last_y = x, y
                            self.last_capture_time = current_time
                
                # Sleep to avoid high CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in click detector: {e}")
                time.sleep(1.0)
    
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