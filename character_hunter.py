#!/usr/bin/env python3
# character_hunter.py
# Main application file for Character Hunter

import sys
import logging
from status_window import StatusWindow
from screen_watcher import ScreenWatcher
from click_detector import ClickDetector
from quality_controller import QualityController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("character_hunter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CharacterHunter.Main")

class CharacterHunter:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        # Create UI
        self.status_window = StatusWindow()
        
        # Initialize components
        self.screen_watcher = ScreenWatcher(self.status_window)
        self.click_detector = ClickDetector(self.status_window, self.screen_watcher)
        
        # Optional: Initialize quality controller
        self.quality_controller = QualityController(self.status_window)
        
        # Initialize flags
        self.running = False
    
    def start(self):
        """Start all application components"""
        try:
            logger.info("Starting Character Hunter application")
            
            # Start screen watcher
            self.screen_watcher.start()
            
            # Start click detector
            self.click_detector.start()
            
            # Mark as running
            self.running = True
            
            # Update status
            self.status_window.update_status("Waiting for user search...")
            
            # Start the UI (this will block until the window is closed)
            self.status_window.start()
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
    
    def stop(self):
        """Stop all application components"""
        if self.running:
            logger.info("Stopping Character Hunter application")
            
            # Stop components
            self.click_detector.stop()
            self.screen_watcher.stop()
            
            # Mark as not running
            self.running = False


def main():
    """Entry point for the application"""
    # Set up exception handler for uncaught exceptions
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't print traceback for Ctrl+C
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    # Create and start the application
    app = CharacterHunter()
    try:
        print("Starting Character Hunter...")
        print("Press Ctrl+C in terminal or click × on status window to exit")
        app.start()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    finally:
        app.stop()


if __name__ == "__main__":
    main()