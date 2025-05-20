#!/usr/bin/env python3
# simple_hunter.py
# Simplified version of Character Hunter with direct debugging

import os
import sys
import time
import logging
import tkinter as tk
from pynput import mouse
import cv2
import numpy as np
from PIL import Image
import pytesseract
from apple_screen_capture import AppleScreenCapture

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level for more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_hunter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SimpleHunter")

class SimpleHunter:
    """Simplified Character Hunter with direct debugging"""
    
    def __init__(self):
        # Create a simple UI
        self.root = tk.Tk()
        self.root.title("Simple Hunter")
        self.root.geometry("250x130+10+10")
        self.root.attributes("-topmost", True)
        
        # Current state label
        self.state_var = tk.StringVar()
        self.state_var.set("Waiting for clicks...")
        self.state_label = tk.Label(
            self.root,
            textvariable=self.state_var,
            font=('Helvetica', 10),
            wraplength=230,
            justify='left'
        )
        self.state_label.pack(pady=10, padx=5, fill=tk.BOTH)
        
        # Last detection label
        self.detection_var = tk.StringVar()
        self.detection_var.set("No search detected yet")
        self.detection_label = tk.Label(
            self.root,
            textvariable=self.detection_var,
            font=('Helvetica', 10, 'bold'),
            fg='blue',
            wraplength=230,
            justify='left'
        )
        self.detection_label.pack(pady=5, padx=5, fill=tk.BOTH)
        
        # Initialize screen capturer
        self.screen_capturer = AppleScreenCapture()
        
        # Set tesseract path - use the one we found with "which tesseract"
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        
        # Mouse listener
        self.listener = None
        
        # Create output directory
        self.output_dir = os.path.join(os.getcwd(), "captured_images")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize state
        self.last_click_time = 0
        self.click_cooldown = 1.0  # seconds
        self.running = False
    
    def start(self):
        """Start the application"""
        self.running = True
        
        # Start mouse listener
        self.listener = mouse.Listener(on_click=self._on_click)
        self.listener.start()
        
        logger.info("Simple Hunter started")
        self.state_var.set("Click on browser to capture\nimages for dataset")
        
        # Start UI loop
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.mainloop()
    
    def stop(self):
        """Stop the application"""
        self.running = False
        
        # Stop listener
        if self.listener:
            self.listener.stop()
        
        # Clean up screen capturer
        self.screen_capturer.cleanup()
        
        # Close UI
        self.root.destroy()
        logger.info("Simple Hunter stopped")
    
    def _on_click(self, x, y, button, pressed):
        """Handle mouse clicks"""
        # Only process left button press events
        if not pressed or button != mouse.Button.left:
            return
            
        # Check if click is on our UI window
        if (self.root.winfo_x() <= x <= self.root.winfo_x() + self.root.winfo_width() and
            self.root.winfo_y() <= y <= self.root.winfo_y() + self.root.winfo_height()):
            return
        
        # Check if enough time has passed since last click
        current_time = time.time()
        if current_time - self.last_click_time <= self.click_cooldown:
            return
            
        self.last_click_time = current_time
        
        # Update UI
        self.state_var.set(f"Clicked at ({x}, {y})\nCapturing image...")
        self.root.update_idletasks()
        
        try:
            # First, capture search area (top of screen)
            search_region = {'top': 0, 'left': 0, 'width': 1440, 'height': 200}
            search_img = self.screen_capturer.capture_region(search_region)
            
            if search_img is None:
                logger.error("Failed to capture search area")
                self.state_var.set("Failed to capture search area")
                return
            
            # Save search area for debugging
            search_path = os.path.join(self.output_dir, f"search_{int(current_time)}.png")
            cv2.imwrite(search_path, cv2.cvtColor(search_img, cv2.COLOR_RGB2BGR))
            logger.info(f"Saved search area to {search_path}")
            
            # Try to extract search query
            search_query = self._extract_search_text(search_img)
            logger.info(f"Extracted search query: {search_query}")
            
            # Then capture click area
            click_region = {
                'top': max(0, y - 150),
                'left': max(0, x - 150),
                'width': 300,
                'height': 300
            }
            click_img = self.screen_capturer.capture_region(click_region)
            
            if click_img is None:
                logger.error("Failed to capture click area")
                self.state_var.set("Failed to capture click area")
                return
            
            # Save click image for debugging
            click_path = os.path.join(self.output_dir, f"click_{int(current_time)}.png")
            cv2.imwrite(click_path, cv2.cvtColor(click_img, cv2.COLOR_RGB2BGR))
            logger.info(f"Saved click image to {click_path}")
            
            # Update UI with results
            if search_query:
                self.detection_var.set(f"Detected: {search_query}")
                # Save with search query name for dataset
                dataset_path = os.path.join(self.output_dir, 
                                         f"{search_query.replace(' ', '_')}_{int(current_time)}.png")
                cv2.imwrite(dataset_path, cv2.cvtColor(click_img, cv2.COLOR_RGB2BGR))
                logger.info(f"Saved to dataset: {dataset_path}")
                self.state_var.set(f"Saved image for '{search_query}'")
            else:
                self.detection_var.set("No search query detected")
                self.state_var.set("Saved debug images only")
            
        except Exception as e:
            logger.error(f"Error processing click: {e}")
            self.state_var.set(f"Error: {str(e)[:50]}")
    
    def _extract_search_text(self, img):
        """Extract search text from image using OCR"""
        try:
            # Convert to PIL Image
            pil_img = Image.fromarray(img)
            
            # Preprocess for OCR
            pil_img = pil_img.convert('L')  # Grayscale
            pil_img = pil_img.point(lambda x: 0 if x < 128 else 255)  # Threshold
            
            # Run OCR
            text = pytesseract.image_to_string(pil_img)
            logger.debug(f"OCR raw text: {text}")
            
            # Look for Google search patterns
            if "google" in text.lower():
                # Extract potential search terms
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                
                # Filter out common Chrome UI elements
                search_terms = []
                for line in lines:
                    # Skip common UI elements
                    if (len(line) > 3 and len(line) < 50 and
                        not line.startswith("http") and
                        "chrome" not in line.lower() and
                        "google" not in line.lower() and
                        "all" not in line.lower() and
                        "images" not in line.lower() and
                        "maps" not in line.lower() and
                        "news" not in line.lower()):
                        search_terms.append(line)
                
                if search_terms:
                    # Take the most promising search term
                    # Middle of the list often works well
                    return search_terms[len(search_terms) // 2]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting search text: {e}")
            return None

if __name__ == "__main__":
    app = SimpleHunter()
    try:
        print("Starting Simple Hunter...")
        print("Click anywhere to capture images")
        print("Images will be saved to the 'captured_images' folder")
        app.start()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    finally:
        app.stop()