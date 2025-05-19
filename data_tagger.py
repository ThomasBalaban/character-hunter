#!/usr/bin/env python3
# data_tagger.py
# Image processing and labeling for Character Hunter

import json
import re
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
import threading
import logging

logger = logging.getLogger("CharacterHunter.DataTagger")

class DataTagger:
    """Process captured images and save them with appropriate labels"""
    
    def __init__(self, status_window):
        self.status_window = status_window
        self.data_dir = Path("./dataset")
        self.data_dir.mkdir(exist_ok=True)
        self.target_size = (512, 512)  # Target size for processed images
        logger.info("DataTagger initialized")
    
    def _sanitize_filename(self, name):
        """Create a valid filename from a string"""
        # Replace invalid characters with underscore
        return re.sub(r'[\\/*?:"<>|]', "_", name)
    
    def _preprocess_image(self, img):
        """Preprocess image to prepare for saving"""
        try:
            logger.debug(f"Preprocessing image of shape {img.shape}")
            
            # Convert to RGB if needed
            if len(img.shape) == 2:  # Grayscale
                logger.debug("Converting grayscale image to RGB")
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:  # RGBA
                logger.debug("Converting RGBA image to RGB")
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            
            # Maintain aspect ratio when resizing
            h, w = img.shape[:2]
            aspect = w / h
            logger.debug(f"Original dimensions: {w}x{h}, aspect ratio: {aspect:.2f}")
            
            if aspect > 1:  # Width > Height
                new_w = self.target_size[0]
                new_h = int(new_w / aspect)
            else:  # Height >= Width
                new_h = self.target_size[1]
                new_w = int(new_h * aspect)
            
            logger.debug(f"Resizing to: {new_w}x{new_h}")
            
            # Resize the image
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # Create a square canvas with padding
            canvas = np.zeros((self.target_size[1], self.target_size[0], 3), dtype=np.uint8)
            # Center the image on the canvas
            y_offset = (self.target_size[1] - new_h) // 2
            x_offset = (self.target_size[0] - new_w) // 2
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            
            logger.debug(f"Created padded canvas of size {self.target_size}")
            
            # Optional: Basic enhancement
            # Simple auto contrast
            for i in range(3):  # For each channel
                channel = canvas[:,:,i]
                if channel.std() > 0:  # Avoid division by zero
                    # Stretch histogram
                    min_val = channel.min()
                    max_val = channel.max()
                    if min_val < max_val:  # Avoid division by zero
                        canvas[:,:,i] = np.clip(255 * (channel - min_val) / (max_val - min_val), 0, 255).astype(np.uint8)
            
            logger.debug("Image preprocessing complete")
            return canvas
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            # Return the original image if there's an error
            return img
    
    def _create_metadata(self, search_info):
        """Create metadata for the captured image"""
        return {
            "timestamp": datetime.now().isoformat(),
            "search_query": search_info['query'],
            "character": search_info['character'],
            "source": search_info['source'],
            "image_size": self.target_size,
            "preprocessed": True
        }
    
    def process_and_save(self, img, search_info):
        """Process and save an image with metadata"""
        try:
            # Update status
            self.status_window.update_status("Processing image...")
            
            # Preprocess image
            processed_img = self._preprocess_image(img)
            
            # Create directory structure
            character = search_info['character']
            source = search_info['source'] if search_info['source'] else "unknown"
            
            # Sanitize names for file system
            character_safe = self._sanitize_filename(character)
            source_safe = self._sanitize_filename(source)
            
            # Create character directory
            char_dir = self.data_dir / character_safe
            char_dir.mkdir(exist_ok=True)
            
            # Create timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            # Create filenames
            img_filename = f"{character_safe}_{timestamp}.png"
            meta_filename = f"{character_safe}_{timestamp}.json"
            
            # Save image
            img_path = str(char_dir / img_filename)
            cv2.imwrite(img_path, cv2.cvtColor(processed_img, cv2.COLOR_RGB2BGR))
            logger.info(f"Saved image to {img_path}")
            
            # Create and save metadata
            metadata = self._create_metadata(search_info)
            meta_path = str(char_dir / meta_filename)
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {meta_path}")
            
            # Update status
            self.status_window.update_status(f"Saved image for '{character}'")
            logger.info(f"Successfully saved image for '{character}' in '{char_dir}'")
            
            # Schedule status reset
            threading.Timer(2.0, lambda: self.status_window.update_status("Ready for next image")).start()
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            self.status_window.update_status(f"Error saving image: {str(e)[:50]}")