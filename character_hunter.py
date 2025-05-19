#!/usr/bin/env python3
# character_hunter.py
# Main application file for Character Hunter

import sys
import logging
import signal
import mss
import numpy as np
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
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {sig}, shutting down...")
        self.stop()
        sys.exit(0)
    
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
            self.stop()
    
    def stop(self):
        """Stop all application components"""
        if self.running:
            logger.info("Stopping Character Hunter application")
            
            # Stop components
            self.click_detector.stop()
            self.screen_watcher.stop()
            
            # Mark as not running
            self.running = False


def check_screen_capture_permission():
    """Check if the app has screen recording permission"""
    try:
        # Try to capture a small region of the screen
        with mss.mss() as sct:
            test_region = {'top': 0, 'left': 0, 'width': 10, 'height': 10}
            test_screenshot = np.array(sct.grab(test_region))
            
            # Check if the screenshot is all black (indicates no permission)
            if np.max(test_screenshot) < 5:  # Almost completely black
                logger.warning("Screen capture permission not granted - screenshots appear black.")
                print("\n\033[1;31mWARNING: Screen capture permission may not be granted\033[0m")
                print("Images appear black, which typically means macOS is blocking screen recording.")
                print("\nTo fix this:")
                print("1. Go to System Settings > Privacy & Security > Screen Recording")
                print("2. Enable the permission for Terminal (or your Python IDE)")
                print("3. Restart Terminal/IDE after granting permission\n")
                
                # Ask if they want to continue anyway
                response = input("Continue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    logger.info("User chose to exit due to permission issues")
                    return False
            else:
                logger.info("Screen capture permission test passed")
    except Exception as e:
        logger.error(f"Error checking screen capture permission: {e}")
        
    return True

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
    
    # Check for screen capture permission
    if not check_screen_capture_permission():
        print("Exiting due to permission issues. Please fix and try again.")
        sys.exit(1)
    
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