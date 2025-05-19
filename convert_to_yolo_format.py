#!/usr/bin/env python3
# convert_to_yolo_format.py
# Script to convert Character Hunter dataset to YOLO format

import os
import json
import argparse
import shutil
from pathlib import Path
import yaml # type: ignore

def create_class_mapping(input_dir):
    """Create a mapping from character names to class IDs"""
    input_path = Path(input_dir)
    
    # Get all character directories
    character_dirs = [d for d in input_path.iterdir() if d.is_dir()]
    
    # Sort alphabetically for consistent class IDs
    character_dirs.sort()
    
    # Create mapping
    class_mapping = {d.name: i for i, d in enumerate(character_dirs)}
    
    return class_mapping

def convert_dataset(input_dir, output_dir, split_ratio=0.8):
    """Convert Character Hunter dataset to YOLO format"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directories
    output_path.mkdir(exist_ok=True)
    
    images_train_dir = output_path / "images" / "train"
    images_val_dir = output_path / "images" / "val"
    labels_train_dir = output_path / "labels" / "train"
    labels_val_dir = output_path / "labels" / "val"
    
    for directory in [images_train_dir, images_val_dir, labels_train_dir, labels_val_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create class mapping
    class_mapping = create_class_mapping(input_dir)
    
    # Write class names file
    with open(output_path / "classes.txt", "w") as f:
        for char_name in class_mapping.keys():
            f.write(f"{char_name}\n")
    
    # Process each character directory
    for class_name, class_id in class_mapping.items():
        char_dir = input_path / class_name
        
        # Get all images (excluding metadata files)
        images = [f for f in char_dir.glob("*.png")]
        
        # Sort by name for reproducibility
        images.sort()
        
        # Split into train and validation sets
        split_idx = int(len(images) * split_ratio)
        train_images = images[:split_idx]
        val_images = images[split_idx:]
        
        # Process training images
        for img_path in train_images:
            # Copy image to training directory
            shutil.copy(img_path, images_train_dir / img_path.name)
            
            # For Character Hunter, we're assuming the whole image contains the character
            # Create a simple YOLO label with the entire image as the bounding box
            label_path = labels_train_dir / (img_path.stem + ".txt")
            with open(label_path, "w") as f:
                # Format: class_id x_center y_center width height
                # For full image: center at (0.5, 0.5), width and height of 1.0
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
        
        # Process validation images
        for img_path in val_images:
            # Copy image to validation directory
            shutil.copy(img_path, images_val_dir / img_path.name)
            
            # Create YOLO label
            label_path = labels_val_dir / (img_path.stem + ".txt")
            with open(label_path, "w") as f:
                f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")
    
    # Create YAML configuration file for YOLO
    yaml_config = {
        "path": str(output_path.absolute()),
        "train": str(images_train_dir.relative_to(output_path)),
        "val": str(images_val_dir.relative_to(output_path)),
        "nc": len(class_mapping),
        "names": list(class_mapping.keys())
    }
    
    with open(output_path / "dataset.yaml", "w") as f:
        yaml.dump(yaml_config, f, default_flow_style=False)
    
    print(f"Conversion complete. Dataset saved to {output_path}")
    print(f"Number of classes: {len(class_mapping)}")
    total_images = len(list(images_train_dir.glob("*.png"))) + len(list(images_val_dir.glob("*.png")))
    print(f"Total images: {total_images}")
    print(f"Training images: {len(list(images_train_dir.glob('*.png')))}")
    print(f"Validation images: {len(list(images_val_dir.glob('*.png')))}")
    print(f"YOLO configuration saved to {output_path / 'dataset.yaml'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Character Hunter dataset to YOLO format")
    parser.add_argument("--input", type=str, required=True, help="Input directory (Character Hunter dataset)")
    parser.add_argument("--output", type=str, required=True, help="Output directory for YOLO dataset")
    parser.add_argument("--split", type=float, default=0.8, help="Train/validation split ratio (default: 0.8)")
    
    args = parser.parse_args()
    
    convert_dataset(args.input, args.output, args.split)