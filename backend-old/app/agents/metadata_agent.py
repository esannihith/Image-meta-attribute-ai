"""
Metadata Agent for analyzing image metadata.
"""
from typing import Dict, Any, List
import json
from pathlib import Path

from app.core.config import get_settings
from app.core.llm import get_llm_response
from app.services.metadata_service import get_formatted_metadata

# Get application settings
settings = get_settings()

class MetadataAgent:
    """
    Agent for analyzing metadata from images (EXIF, IPTC, XMP).
    """
    def __init__(self):
        """Initialize the metadata agent."""
        self.settings = settings
    
    async def analyze_metadata(
        self, 
        metadata: Dict[str, Any],
        message: str = "",
        specific_field: str = "general"
    ) -> str:
        """
        Analyze image metadata and provide insights.
        
        Args:
            metadata: Extracted metadata from the image
            message: User message for context
            specific_field: Specific field of interest from the query interpretation
            
        Returns:
            str: Analysis of the metadata
        """
        if not metadata:
            return "No metadata was found in this image."
        
        # Format metadata for LLM consumption
        formatted_metadata = get_formatted_metadata(metadata)
        
        # Generate metadata analysis using LLM
        system_message = f"""
You are an expert at analyzing image metadata (EXIF, IPTC, XMP).
You can extract useful insights from this data to help users understand their images.
The user is specifically interested in {specific_field} information.
"""
        
        prompt = f"""
The user asked: "{message}"

Here is the metadata from their image:

{formatted_metadata}

Analyze this metadata and provide useful insights. Focus on:
1. Camera/device information if available
2. When and where the image was taken (if location data exists)
3. Technical details like exposure, ISO, etc. that might be relevant
4. Any other interesting information in the metadata

Be especially attentive to {specific_field} information since that's what the user seems interested in.
If certain information is missing, don't mention it or specifically state it's not available.
"""
        
        try:
            response = await get_llm_response(
                prompt=prompt,
                system_message=system_message
            )
            return response
        except Exception as e:
            print(f"Error getting LLM response for metadata analysis: {e}")
            return self._create_fallback_analysis(metadata)
    
    def _create_fallback_analysis(self, metadata: Dict[str, Any]) -> str:
        """Create a simple fallback analysis if LLM fails"""
        analysis = "I found the following information in your image metadata:\n\n"
        
        # Add camera info if available
        if "Make" in metadata or "Model" in metadata:
            camera = f"{metadata.get('Make', '')} {metadata.get('Model', '')}".strip()
            analysis += f"Camera: {camera}\n"
            
        # Add date if available
        if "DateTime" in metadata:
            analysis += f"Date taken: {metadata['DateTime']}\n"
            
        # Add location if available
        if "GPSLatitude" in metadata and "GPSLongitude" in metadata:
            lat = metadata["GPSLatitude"]
            lng = metadata["GPSLongitude"]
            analysis += f"Location: {lat}, {lng}\n"
            
        # Add basic technical info if available
        tech_info = []
        if "ExposureTime" in metadata:
            tech_info.append(f"Exposure: {metadata['ExposureTime']}")
        if "FNumber" in metadata:
            tech_info.append(f"F-stop: {metadata['FNumber']}")
        if "ISOSpeedRatings" in metadata:
            tech_info.append(f"ISO: {metadata['ISOSpeedRatings']}")
            
        if tech_info:
            analysis += "Technical info: " + ", ".join(tech_info)
            
        # If no specific info was added
        if analysis == "I found the following information in your image metadata:\n\n":
            analysis += "No detailed metadata was found in this image."
            
        return analysis