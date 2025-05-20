#!/usr/bin/env python3
# screen_watcher.py
# Screen monitoring component for Character Hunter

import threading
import time
import re
import subprocess
import shutil
import os
from datetime import datetime
import cv2
import numpy as np
import pytesseract
from PIL import Image
import AppKit
import logging
from apple_screen_capture import AppleScreenCapture

logger = logging.getLogger("CharacterHunter.ScreenWatcher")

class ScreenWatcher:
    """Monitor screen for Google searches and extract search queries"""
    
    def __init__(self, status_window):
        self.status_window = status_window
        self.running = False
        self.current_search = None
        self.thread = None
        
        # Initialize the Apple screen capture
        self.screen_capturer = AppleScreenCapture()
        
        # Region to monitor for the search bar (top portion of screen)
        screen_width = 1440  # Default width, will be updated on first capture
        self.search_region = {
            'top': 0, 
            'left': 0, 
            'width': screen_width,  # Use full width of screen
            'height': 300  # Capture top portion of screen
        }
        
        # Configure pytesseract path - use the one we found with "which tesseract"
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        
        # Set sampling interval - how often to check for searches
        self.sampling_interval = 0.5  # Check every half second
        
        logger.info(f"ScreenWatcher initialized with search region: {self.search_region}")
        logger.info(f"Using Tesseract OCR at: {pytesseract.pytesseract.tesseract_cmd}")
    
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
            # Clean up screen capturer
            self.screen_capturer.cleanup()
            logger.info("ScreenWatcher stopped")
    
    def _is_chrome_with_google(self):
        """Check if Chrome with Google is the active window"""
        try:
            # Get active window using AppKit (macOS specific)
            active_app = AppKit.NSWorkspace.sharedWorkspace().activeApplication()
            app_name = active_app['NSApplicationName']
            
            if app_name == 'Google Chrome':
                logger.debug("Detected active application: Google Chrome")
                return True
            else:
                logger.debug(f"Active application is not Chrome: {app_name}")
                return False
        except Exception as e:
            logger.error(f"Error detecting active window: {e}")
            return False
    
    def _extract_search_query(self, screenshot):
        """Extract the Google search query from a screenshot using OCR"""
        try:
            # Check if screenshot is valid
            if screenshot is None or screenshot.size == 0:
                logger.error("Screenshot is empty or None")
                return None
                
            # Convert to PIL Image and enhance for OCR
            img = Image.fromarray(screenshot)
            # Enhance image for better OCR
            img = img.convert('L')  # Convert to grayscale
            img = img.point(lambda x: 0 if x < 128 else 255)  # Threshold
            
            # Run OCR
            text = pytesseract.image_to_string(img)
            logger.debug(f"OCR text: {text[:100]}...")  # Log first 100 chars
            
            # Clean up browser UI text that we don't want
            text = self._clean_browser_text(text)
            
            # Method 1: Look for Google search patterns in OCR text
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
                    search_query = self._clean_search_query(search_query)
                    logger.debug(f"Found search query via pattern: {search_query}")
                    return search_query
            
            # Method 2: Try to extract directly from address bar or search box
            # This is a fallback if pattern matching fails
            # Look for "google.com/search" or similar in the text
            if "google.com/search" in text:
                # Try to extract the query parameter
                search_lines = [line for line in text.splitlines() if "google.com/search" in line]
                if search_lines:
                    logger.debug(f"Found Google search URL: {search_lines[0]}")
                    # Try to extract q= parameter
                    q_match = re.search(r'[?&]q=([^&]+)', search_lines[0])
                    if q_match:
                        query = q_match.group(1).replace('+', ' ')
                        query = self._clean_search_query(query)
                        logger.debug(f"Extracted query from URL: {query}")
                        return query
            
            # Method 3: If we're on a Google search results page, look for the search box
            # Extract the search box content directly
            # This is more reliable than looking for patterns in the OCR text
            if "All" in text and "Images" in text and "Maps" in text:
                for line in text.splitlines():
                    line = line.strip()
                    # Look for the search box content - it's usually near Google logo or search tabs
                    if (len(line) > 3 and len(line) < 50 and 
                        "All" not in line and "Images" not in line and 
                        "Maps" not in line and "Videos" not in line and
                        "News" not in line and "Google" not in line and
                        not line.startswith("http") and not line.endswith(".com") and
                        "Chrome" not in line and "New" not in line):
                        
                        logger.debug(f"Possible search query from search box: {line}")
                        return self._clean_search_query(line)
            
            # Method 4: Look for search text in the search input field
            # The search input is usually in the top portion of the page
            # Try a more aggressive approach to find any plausible search term
            search_terms = []
            for line in text.splitlines():
                line = line.strip()
                # Filter out common browser UI elements and tabs
                if (len(line) > 3 and len(line) < 40 and
                    "http" not in line and ".com" not in line and
                    "Google" not in line and "Chrome" not in line and
                    "New" not in line and "tab" not in line.lower() and
                    "available" not in line and "All" not in line and
                    "Images" not in line and "Maps" not in line and
                    "Videos" not in line and "News" not in line):
                    
                    # Clean up the line and add to potential search terms
                    cleaned = self._clean_search_query(line)
                    if cleaned and len(cleaned) > 3:
                        search_terms.append(cleaned)
            
            if search_terms:
                # Choose the most likely search term (middle of the list often works well)
                most_likely = search_terms[len(search_terms) // 2]
                logger.debug(f"Most likely search term from content: {most_likely}")
                return most_likely
            
            logger.debug("No search query found in OCR text")
            return None
        except Exception as e:
            logger.error(f"Error extracting search query: {e}")
            return None
    
    def _clean_browser_text(self, text):
        """Remove common browser UI elements from extracted text"""
        # List of common Chrome UI elements to filter out
        ui_elements = [
            "New Chrome available",
            "New Tab",
            "Google Chrome",
            "Bookmarks",
            "Mon May",
            "File Edit View History",
            "https://",
            "http://",
            "www.",
            ".com",
            "Home",
        ]
        
        # Remove UI elements
        cleaned_text = text
        for element in ui_elements:
            cleaned_text = cleaned_text.replace(element, "")
        
        return cleaned_text
    
    def _clean_search_query(self, query):
        """Clean up extracted search query"""
        if not query:
            return query
        
        # Remove URL encoding
        query = query.replace('+', ' ').replace('%20', ' ')
        
        # Remove common browser UI indicators
        ui_elements = [
            "New Chrome available",
            "Chrome available",
            "New Tab",
            "Tab",
            "Google Chrome",
            "Bookmarks",
            "File Edit",
            "Edit View",
            "History",
            "..."
        ]
        
        # Remove UI elements
        cleaned_query = query
        for element in ui_elements:
            cleaned_query = cleaned_query.replace(element, "")
        
        # Clean up special characters and extra spaces
        cleaned_query = re.sub(r'[^\w\s\-:]', ' ', cleaned_query)  # Replace special chars with space
        cleaned_query = re.sub(r'\s+', ' ', cleaned_query)  # Replace multiple spaces with single space
        
        # Check if query has numbers like timestamps or percentages at the beginning
        # e.g., "19:20:45 actual search term" -> "actual search term"
        cleaned_query = re.sub(r'^[\d:%\s]+\s', '', cleaned_query)
        
        return cleaned_query.strip()
    
    def _parse_character_and_source(self, search_query):
        """Parse a search query into character name and source/game"""
        if not search_query:
            return None, None
            
        try:
            # Clean up search query first
            search_query = self._clean_search_query(search_query)
            
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
                    logger.debug(f"Parsed character: '{character}', source: '{source}'")
                    return character, source
            
            # FNAF-specific parsing: Many FNAF characters are "[Name] [Game]"
            # For example: "Roxy FNAF Security Breach"
            fnaf_pattern = r'(.*?)\s+fnaf\s+(.*)'
            matches = re.search(fnaf_pattern, search_query, re.IGNORECASE)
            if matches:
                character = matches.group(1).strip()
                source = "FNAF " + matches.group(2).strip()
                logger.debug(f"Parsed FNAF character: '{character}', source: '{source}'")
                return character, source
            
            # If no pattern matches, assume the whole query is the character name
            logger.debug(f"Using entire query as character name: '{search_query}'")
            return search_query, None
        except Exception as e:
            logger.error(f"Error parsing search query: {e}")
            return search_query, None
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        last_search = None
        chrome_active_count = 0  # Counter for consecutive Chrome detections
        last_capture_time = 0
        capture_interval = 2.0  # Only capture every 2 seconds to avoid excessive CPU usage
        
        while self.running:
            try:
                # Check if Chrome with Google is active
                is_chrome_active = self._is_chrome_with_google()
                
                current_time = time.time()
                
                if is_chrome_active:
                    chrome_active_count += 1
                    
                    # Only process after Chrome has been active for a few cycles
                    # And only capture at the specified interval
                    if (chrome_active_count > 2 and 
                        current_time - last_capture_time >= capture_interval):
                        
                        last_capture_time = current_time
                        
                        # Capture screen region using AppleScript method
                        logger.debug(f"Capturing search region: {self.search_region}")
                        screenshot = self.screen_capturer.capture_region(self.search_region)
                        
                        # Check if screenshot was successfully captured
                        if screenshot is not None:
                            # Save debug screenshot periodically
                            if int(current_time) % 10 == 0:  # Every 10 seconds approx
                                debug_path = f"debug_search_{int(current_time)}.png"
                                cv2.imwrite(debug_path, cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR))
                                logger.debug(f"Saved debug search image to {debug_path}")
                            
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
                        else:
                            logger.warning("Failed to capture search region screenshot")
                else:
                    chrome_active_count = 0  # Reset counter if Chrome not active
                
                # Sleep to avoid high CPU usage, but be responsive
                time.sleep(self.sampling_interval)
                
            except Exception as e:
                logger.error(f"Error in screen watcher: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(2.0)  # Longer sleep on error
    
    def get_current_search(self):
        """Return the current search information"""
        return self.current_search