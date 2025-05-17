"""
Service for detecting objects in images using YOLO (You Only Look Once).
"""
import os
import asyncio
from pathlib import Path
import json
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image
import tempfile
from app.core.config import get_settings

settings = get_settings()

# Check if ultralytics is installed
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Object detection will use fallback mechanism.")

# YOLO model cache
_yolo_model = None

async def detect_objects(image_path: str) -> Dict[str, Any]:
    """
    Detect objects in an image using YOLO.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Dict: Dictionary containing detected objects with bounding boxes and confidence scores
    """
    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": f"Image file not found: {image_path}",
            "predictions": []
        }
        
    try:
        # Try to use YOLO if available
        if YOLO_AVAILABLE:
            result = await detect_with_yolo(image_path)
            return {
                "success": True,
                "predictions": result
            }
        else:
            # Fallback to a simpler detection method or mock data for development
            return await detect_with_fallback(image_path)
    except Exception as e:
        print(f"Error in object detection: {e}")
        return {
            "success": False,
            "error": f"Object detection failed: {str(e)}",
            "predictions": []
        }

async def detect_with_yolo(image_path: str) -> List[Dict[str, Any]]:
    """
    Detect objects in an image using YOLOv8.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List[Dict]: List of detected objects with class, confidence and bounding box
    """
    global _yolo_model
    
    # Create results directory if it doesn't exist
    results_dir = Path(settings.TEMP_UPLOAD_DIR) / "yolo_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Load the YOLO model if not already loaded
    if _yolo_model is None:
        # Check if custom model path exists, otherwise use default
        if hasattr(settings, 'YOLO_MODEL_PATH') and os.path.exists(settings.YOLO_MODEL_PATH):
            model_path = settings.YOLO_MODEL_PATH
        else:
            # Use the default "yolov8n.pt" model from ultralytics
            model_path = "yolov8n.pt"  # This will download the model if not present
        
        # Load the model
        try:
            _yolo_model = YOLO(model_path)
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            raise RuntimeError(f"Failed to load YOLO model: {str(e)}")
    
    # Run detection in a separate process to avoid blocking
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        None,
        lambda: _yolo_model.predict(
            source=image_path,
            conf=0.25,  # Confidence threshold
            save=False,  # Don't save annotated images
            project=str(results_dir),
            name="detect",
            verbose=False
        )
    )
    
    # Process the results
    detections = []
    
    # Check if we got any results
    if results and len(results) > 0:
        result = results[0]  # First result
        
        # Convert tensors to Python objects for JSON serialization
        boxes = result.boxes
        for i in range(len(boxes)):
            box = boxes[i]
            x1, y1, x2, y2 = box.xyxy[0].tolist()  # Get the bounding box coordinates
            
            detection = {
                "class": result.names[int(box.cls[0])],  # Class name
                "confidence": float(box.conf[0]),  # Confidence score
                "bbox": {
                    "x1": float(x1),
                    "y1": float(y1),
                    "x2": float(x2),
                    "y2": float(y2),
                    "width": float(x2 - x1),
                    "height": float(y2 - y1),
                    "x": float((x1 + x2) / 2),  # Center X
                    "y": float((y1 + y2) / 2)   # Center Y
                }
            }
            detections.append(detection)
    
    return detections

async def detect_with_fallback(image_path: str) -> List[Dict[str, Any]]:
    """
    Fallback detection method when YOLO is not available.
    In a production environment, you would implement alternate detection methods.
    For development/testing, this returns mock data.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        List[Dict]: List of mock detected objects
    """
    # In a real implementation, you could use a simpler or different detection method
    # For development, we'll return mock data based on image dimensions
    try:
        # Get image dimensions
        with Image.open(image_path) as img:
            width, height = img.size
        
        # Create some mock objects based on image size
        # This is just for development/testing when YOLO isn't available
        mock_objects = [
            {
                "class": "person",
                "confidence": 0.92,
                "bbox": {
                    "x1": width * 0.2,
                    "y1": height * 0.3,
                    "x2": width * 0.5,
                    "y2": height * 0.8,
                    "width": width * 0.3,
                    "height": height * 0.5,
                    "x": width * 0.35,
                    "y": height * 0.55
                }
            },
            {
                "class": "dog",
                "confidence": 0.85,
                "bbox": {
                    "x1": width * 0.6,
                    "y1": height * 0.5,
                    "x2": width * 0.8,
                    "y2": height * 0.7,
                    "width": width * 0.2,
                    "height": height * 0.2,
                    "x": width * 0.7,
                    "y": height * 0.6
                }
            }
        ]
        
        return mock_objects
    except Exception as e:
        print(f"Error in fallback detection: {e}")
        return []

def format_detection_results(results: Dict[str, Any]) -> str:
    """
    Format object detection results into a human-readable string.
    
    Args:
        results: Object detection results
        
    Returns:
        str: Formatted string with detection results
    """
    # if not results.get("success", False):
    #     return "Object detection was not performed or encountered an error."
    
    # predictions = results.get("predictions", [])
    # if not predictions:
    #     return "No objects were detected in the image."
    
    # formatted = ["🔍 Detected Objects:"]
    
    # # Group objects by class
    # class_counts = {}
    # for obj in predictions:
    #     class_name = obj.get("class", "unknown")
    #     if class_name in class_counts:
    #         class_counts[class_name] += 1
    #     else:
    #         class_counts[class_name] = 1
    
    # # Format the counts
    # for class_name, count in class_counts.items():
    #     formatted.append(f"  • {class_name}: {count}")
    
    # return "\n".join(formatted)
        
    #     # Format the response
    # objects = []
    # for pred in predictions.get("predictions", []):
    #         objects.append({
    #             "class": pred.get("class"),
    #             "confidence": pred.get("confidence"),
    #             "bbox": {
    #                 "x": pred.get("x"),
    #                 "y": pred.get("y"),
    #                 "width": pred.get("width"),
    #                 "height": pred.get("height")
    #             }
    #         })
        
    # return {
    #         "success": True,
    #         "objects": objects,
    #         "count": len(objects)
    #     }
        
    # except Exception as e:
    #     print(f"Error detecting objects: {e}")
    #     return {
    #         "success": False,
    #         "error": str(e),
    #         "objects": []
    # }
    pass