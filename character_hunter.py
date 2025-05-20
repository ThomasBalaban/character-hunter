#!/usr/bin/env python3
# character_hunter.py
# Main application file for Character Hunter

import sys
import logging
import signal
import mss
import numpy as np
import cv2
import os
from status_window import StatusWindow
from screen_watcher import ScreenWatcher
from click_detector import ClickDetector
from quality_controller import QualityController

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level for detailed logging
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
        print("\nTesting screen capture permission...")
        
        # Create debugging directory
        debug_dir = os.path.join(os.getcwd(), "debug_captures")
        os.makedirs(debug_dir, exist_ok=True)
        print(f"Debug images will be saved to: {debug_dir}")
        
        # Try to capture a small region of the screen
        with mss.mss() as sct:
            test_region = {'top': 0, 'left': 0, 'width': 100, 'height': 100}
            test_screenshot = np.array(sct.grab(test_region))
            
            # Save the test capture
            test_path = os.path.join(debug_dir, "test_capture_mss.png")
            cv2.imwrite(test_path, cv2.cvtColor(test_screenshot, cv2.COLOR_BGRA2BGR))
            
            # Check if the screenshot is all black (indicates no permission)
            if np.max(test_screenshot) < 5:  # Almost completely black
                logger.warning("Screen capture permission not granted - screenshots appear black.")
                print("\n\033[1;31mWARNING: MSS capture failed - screenshots appear black\033[0m")
                
                # Try using AppleScreenCapture as a fallback
                from apple_screen_capture import AppleScreenCapture
                apple_capturer = AppleScreenCapture()
                apple_test = apple_capturer.capture_region(test_region)
                
                if apple_test is not None:
                    # Save the AppleScript test capture
                    apple_path = os.path.join(debug_dir, "test_capture_applescript.png")
                    cv2.imwrite(apple_path, cv2.cvtColor(apple_test, cv2.COLOR_RGB2BGR))
                    
                    if np.mean(apple_test) > 5:  # Not all black
                        print("\033[1;32mGood news! AppleScript capture works correctly\033[0m")
                        print("The app will use this method instead.")
                        logger.info("AppleScript capture method works")
                        return True
                
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
                # MSS capture works
                logger.info("Screen capture permission test passed with MSS")
                print("\033[1;32mScreen capture permission test passed!\033[0m")
        
        return True
    except Exception as e:
        logger.error(f"Error checking screen capture permission: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n\033[1;31mError testing screen capture: {e}\033[0m")
        
        # Ask if they want to continue anyway
        response = input("Continue anyway despite test error? (y/n): ").strip().lower()
        return response == 'y'

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
    
    print("\n=== Character Hunter - AI Training Data Collector ===\n")
    print("This app detects Google searches and captures images when you click,")
    print("automatically labeling them for AI training purposes.\n")
    
    # Check for screen capture permission
    if not check_screen_capture_permission():
        print("Exiting due to permission issues. Please fix and try again.")
        sys.exit(1)
    
    # Create and start the application
    app = CharacterHunter()
    try:
        print("\nStarting Character Hunter...")
        print("Workflow:")
        print("1. Use Chrome to search for a character (e.g., \"Roxy FNAF Security Breach\")")
        print("2. Click on relevant images while in Chrome")
        print("3. Images will be automatically captured and labeled")
        print("\nPress Ctrl+C in terminal or click × on status window to exit")
        app.start()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        print("\nCharacter Hunter terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\nApplication error: {e}")
    finally:
        app.stop()
        print("\nThank you for using Character Hunter!")
        print(f"Captured images have been saved to the 'dataset' directory.")


if __name__ == "__main__":
    main()