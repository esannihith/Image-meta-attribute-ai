"""
Utility functions for handling image operations such as saving, loading, and processing.
"""
import os
import base64
import uuid
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

def ensure_temp_dir(directory: str) -> None:
    """
    Ensure the temporary directory exists.
    
    Args:
        directory: Path to the directory
    """
    os.makedirs(directory, exist_ok=True)

def save_image(image_data: str, filename: str, output_dir: str) -> str:
    """
    Save a base64-encoded image to disk.
    
    Args:
        image_data: Base64-encoded image data
        filename: Desired filename
        output_dir: Directory to save the image in
        
    Returns:
        str: Path to the saved image
    """
    # Ensure output directory exists
    ensure_temp_dir(output_dir)
    
    # Clean up the base64 data if it includes data URI scheme
    if ',' in image_data:
        # Extract the base64 part after the comma
        image_data = image_data.split(',', 1)[1]
    
    # Create a unique filename to avoid collisions
    file_extension = os.path.splitext(filename)[1]
    if not file_extension:
        file_extension = '.jpg'  # Default to .jpg if no extension
    
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(output_dir, unique_filename)
    
    # Decode and save the image
    with open(file_path, 'wb') as f:
        f.write(base64.b64decode(image_data))
    
    return file_path

def cleanup_old_images(directory: str, hours: int = 24) -> None:
    """
    Delete images older than the specified time.
    
    Args:
        directory: Directory containing images
        hours: Number of hours after which images are considered old
    """
    if not os.path.exists(directory):
        return
    
    cutoff_time = time.time() - (hours * 3600)
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        # Check if it's a file (not a directory)
        if os.path.isfile(file_path):
            # Check if file is older than the cutoff time
            if os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                    print(f"Removed old file: {file_path}")
                except Exception as e:
                    print(f"Error removing old file {file_path}: {e}")

def get_image_as_base64(image_path: str) -> Optional[str]:
    """
    Convert an image file to base64 encoding.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str or None: Base64-encoded image data or None if file doesn't exist
    """
    if not os.path.exists(image_path):
        return None
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
        
    return base64.b64encode(image_data).decode('utf-8')

def draw_bounding_boxes(image_path: str, detections: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Draw bounding boxes on an image based on object detection results.
    
    Args:
        image_path: Path to the original image
        detections: Dictionary containing object detection results with bounding boxes
        output_path: Optional path to save the annotated image (if None, will generate one)
        
    Returns:
        str: Path to the annotated image
    """
    # This is a placeholder function that would need to be implemented with a library like PIL or OpenCV
    # For now, we'll just return the original image path
    # In a real implementation, this would draw boxes on the image
    
    # TODO: Implement actual bounding box drawing functionality
    if output_path is None:
        directory = os.path.dirname(image_path)
        filename = os.path.basename(image_path)
        output_path = os.path.join(directory, f"annotated_{filename}")
    
    # Just copy the original file for now
    import shutil
    shutil.copy(image_path, output_path)
    
    return output_path