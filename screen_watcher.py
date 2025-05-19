#!/usr/bin/env python3
# screen_watcher.py
# Screen monitoring component for Character Hunter

import threading
import time
import re
from datetime import datetime
import numpy as np
import pytesseract
from PIL import Image
import mss
import AppKit
import logging

logger = logging.getLogger("CharacterHunter.ScreenWatcher")

class ScreenWatcher:
    """Monitor screen for Google searches and extract search queries"""
    
    def __init__(self, status_window):
        self.status_window = status_window
        self.running = False
        self.current_search = None
        self.thread = None
        self.sct = mss.mss()
        # Region to monitor for the search bar (top portion of screen)
        self.search_region = {
            'top': 0, 
            'left': 0, 
            'width': 1200, 
            'height': 200
        }
        # Configure pytesseract path if needed
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    
    def start(self):
        """Start monitoring the screen in a separate thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop)
            self.thread.daemon = True
            self.thread.start()
            logger.info("ScreenWatcher started")
    
    def stop(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            logger.info("ScreenWatcher stopped")
    
    def _is_chrome_with_google(self):
        """Check if Chrome with Google is the active window"""
        # Get active window using AppKit (macOS specific)
        active_app = AppKit.NSWorkspace.sharedWorkspace().activeApplication()
        if active_app['NSApplicationName'] == 'Google Chrome':
            # For now, assume if Chrome is active, Google might be open
            # A better implementation would check the URL but that's more complex
            return True
        return False
    
    def _extract_search_query(self, screenshot):
        """Extract the Google search query from a screenshot using OCR"""
        # Convert to PIL Image and enhance for OCR
        img = Image.fromarray(screenshot)
        # Enhance image for better OCR
        img = img.convert('L')  # Convert to grayscale
        img = img.point(lambda x: 0 if x < 128 else 255)  # Threshold
        
        # Run OCR
        text = pytesseract.image_to_string(img)
        
        # Look for Google search patterns
        search_patterns = [
            r'q=(.*?)&',  # URL parameter
            r'Search: (.*)',  # Search box
            r'Google Search for "(.*)"',  # Title
            r'(.*) - Google Search',  # Title pattern
        ]
        
        for pattern in search_patterns:
            matches = re.search(pattern, text)
            if matches:
                search_query = matches.group(1).strip()
                return search_query
        
        return None
    
    def _parse_character_and_source(self, search_query):
        """Parse a search query into character name and source/game"""
        if not search_query:
            return None, None
            
        # Common patterns like "character from game" or "character - game"
        patterns = [
            r'(.*?)\s+from\s+(.*)',
            r'(.*?)\s+-\s+(.*)',
            r'(.*?)\s+in\s+(.*)',
        ]
        
        for pattern in patterns:
            matches = re.search(pattern, search_query, re.IGNORECASE)
            if matches:
                character = matches.group(1).strip()
                source = matches.group(2).strip()
                return character, source
        
        # If no pattern matches, assume the whole query is the character name
        return search_query, None
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        last_search = None
        
        while self.running:
            try:
                # Only check if Chrome with Google is active
                if self._is_chrome_with_google():
                    # Capture screen region
                    screenshot = np.array(self.sct.grab(self.search_region))
                    
                    # Extract search query
                    search_query = self._extract_search_query(screenshot)
                    
                    # If found a new search query
                    if search_query and search_query != last_search:
                        character, source = self._parse_character_and_source(search_query)
                        
                        if character:
                            self.current_search = {
                                'query': search_query,
                                'character': character,
                                'source': source,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            # Update status window
                            if source:
                                status_msg = f"Detected: '{character}' from '{source}'"
                            else:
                                status_msg = f"Detected: '{character}'"
                                
                            self.status_window.update_status(status_msg)
                            logger.info(f"New search detected: {search_query}")
                            last_search = search_query
                
                # Sleep to avoid high CPU usage
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in screen watcher: {e}")
                time.sleep(5.0)  # Longer sleep on error
    
    def get_current_search(self):
        """Return the current search information"""
        return self.current_search