"""
Object Detection Agent for identifying objects in images.
"""
from typing import Dict, Any, List
import json
from pathlib import Path

from app.services.object_detection_service import detect_objects
from app.core.config import get_settings
from app.core.llm import get_llm_response

# Get application settings
settings = get_settings()

class ObjectDetectionAgent:
    """
    Agent for analyzing images and identifying objects using computer vision.
    """
    def __init__(self):
        """Initialize the object detection agent."""
        self.settings = settings
    
    async def analyze_objects(
        self, 
        image_path: str,
        object_data: Dict[str, Any] = None,
        message: str = "",
        requires_detection: bool = True
    ) -> str:
        """
        Analyze objects in an image and provide relevant information.
        
        Args:
            image_path: Path to the image
            object_data: Pre-detected object data (if available)
            message: User message for context
            requires_detection: Whether object detection is needed
            
        Returns:
            str: Analysis of detected objects
        """
        # If we already have object data, use it
        if not object_data:
            if requires_detection:
                # Run object detection
                try:
                    object_data = await detect_objects(image_path)
                except Exception as e:
                    print(f"Error during object detection: {e}")
                    return "Object detection failed. I couldn't analyze objects in this image."
            else:
                return "No object detection was performed as it didn't seem relevant to your query."
        
        # If no objects detected or detection not required
        if not object_data or not requires_detection:
            return "No relevant objects were detected in this image."
        
        # Format object data for LLM analysis
        formatted_objects = self._format_objects(object_data)
        
        # Get LLM to analyze the object data
        system_message = """
You are an expert computer vision analyst that can interpret object detection results.
Provide a concise but informative analysis of the detected objects in relation to the user's query.
Focus on what's visible in the image based on the detection results.
"""
        
        prompt = f"""
The user asked: "{message}"

The following objects were detected in the image:

{formatted_objects}

Please analyze these detected objects and provide relevant insights based on the user's query.
If the user is asking something specific about objects in the image, focus on addressing that.
Otherwise, provide a general overview of what's in the image based on the detection results.
"""
        
        try:
            response = await get_llm_response(
                prompt=prompt,
                system_message=system_message
            )
            return response
        except Exception as e:
            print(f"Error getting LLM response for object analysis: {e}")
            return f"I detected the following objects: {', '.join(self._extract_object_names(object_data))}"
    
    def _format_objects(self, object_data: Dict[str, Any]) -> str:
        """Format object detection data for LLM consumption"""
        if not object_data or not isinstance(object_data, dict):
            return "No objects detected."
            
        try:
            result = "Detected objects:\n"
            
            # Handle different object detection result formats
            if "predictions" in object_data:
                # Roboflow format
                objects = object_data["predictions"]
                for i, obj in enumerate(objects):
                    confidence = obj.get("confidence", 0) * 100
                    result += f"- {obj.get('class', 'Unknown object')} (Confidence: {confidence:.1f}%)\n"
                    if "bbox" in obj:
                        x, y, w, h = obj["bbox"]["x"], obj["bbox"]["y"], obj["bbox"]["width"], obj["bbox"]["height"]
                        result += f"  Position: center({x:.1f}, {y:.1f}), width: {w:.1f}, height: {h:.1f}\n"
                        
            elif "detections" in object_data:
                # YOLO format
                objects = object_data["detections"]
                for i, obj in enumerate(objects):
                    result += f"- {obj.get('class', 'Unknown object')} (Confidence: {obj.get('confidence', 0)*100:.1f}%)\n"
                    
            elif isinstance(object_data, list):
                # Simple list format
                for i, obj in enumerate(object_data):
                    if isinstance(obj, dict):
                        name = obj.get("name", obj.get("class", "Unknown object"))
                        conf = obj.get("confidence", obj.get("score", 0)) * 100
                        result += f"- {name} (Confidence: {conf:.1f}%)\n"
            
            # If no objects were properly formatted, return a simple list
            if result == "Detected objects:\n":
                return "Objects detected, but in an unrecognized format."
                
            return result
        
        except Exception as e:
            print(f"Error formatting object data: {e}")
            return "Objects detected, but couldn't format the data."
    
    def _extract_object_names(self, object_data: Dict[str, Any]) -> List[str]:
        """Extract just the names of detected objects"""
        names = []
        
        try:
            if "predictions" in object_data:
                names = [obj.get("class", "unknown object") for obj in object_data["predictions"]]
            elif "detections" in object_data:
                names = [obj.get("class", "unknown object") for obj in object_data["detections"]]
            elif isinstance(object_data, list):
                names = [obj.get("name", obj.get("class", "unknown object")) 
                        for obj in object_data if isinstance(obj, dict)]
        except Exception:
            pass
            
        return names if names else ["unidentified object"]