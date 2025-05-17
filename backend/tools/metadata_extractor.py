import os
import json
import subprocess
from typing import Dict, Any, Optional, Type
from datetime import datetime

from PIL import Image
import exifread
import piexif
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class ImagePathModel(BaseModel):
    """Input schema for the metadata extractor tool."""
    image_path: str = Field(description="Path to the image file to extract metadata from")

class MetadataExtractorTool(BaseTool):
    """
    A CrewAI-compatible Tool for extracting metadata from images
    using multiple libraries (PIL, ExifRead, piexif, ExifTool).
    """
    
    name: str = "image_metadata_extractor"  # Add type annotation
    description: str = "Extracts comprehensive metadata from images including EXIF data, GPS coordinates, and technical information."  # Add type annotation
    args_schema: Type[BaseModel] = ImagePathModel
    def _run(self, image_path: str = None, **kwargs) -> Dict[str, Any]:
        if image_path is None and kwargs:
        # Handle case where input is a dictionary
            input_data = self.args_schema(**kwargs)
            image_path = input_data.image_path
        return self.extract_metadata(image_path)
    
    def extract_metadata(self, image_path: str) -> Dict[str, Any]:
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        metadata = {}
        
        # Get basic metadata from PIL
        pil_metadata = self._extract_pil_metadata(image_path)
        metadata.update(pil_metadata)
        
        # Get EXIF data using ExifRead
        exifread_metadata = self._extract_exifread_metadata(image_path)
        metadata["exif"] = exifread_metadata.get("exif", {})
        
        # If GPS info found, include it at the top level
        if "gps" in exifread_metadata:
            metadata["gps"] = exifread_metadata["gps"]
        
        # Get structured EXIF data using piexif
        piexif_metadata = self._extract_piexif_metadata(image_path)
        # Merge with existing EXIF data
        if piexif_metadata.get("exif"):
            metadata["exif_piexif"] = piexif_metadata["exif"]

        
        # Get full metadata using ExifTool (if available)
        exiftool_metadata = self._extract_exiftool_metadata(image_path)
        if exiftool_metadata:
            metadata["exiftool"] = exiftool_metadata
        
        # Extract common metadata for easy access at top level
        self._extract_common_metadata(metadata)
        
        return metadata
    
    def _extract_pil_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract basic metadata using PIL."""
        try:
            with Image.open(image_path) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "dimensions": {
                        "width": img.width,
                        "height": img.height,
                    },
                    "source": "PIL"
                }
        except Exception as e:
            return {"error_pil": str(e)}
    
    def _extract_exifread_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract EXIF metadata using ExifRead."""
        try:
            result = {"exif": {}, "source": "ExifRead"}
            
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=True)
                
                if not tags:
                    return result
                
                # Process standard EXIF tags
                for tag, value in tags.items():
                    # Skip thumbnail data
                    if tag.startswith('JPEGThumbnail'):
                        continue
                    
                    # Convert value to string to ensure it's serializable
                    result["exif"][tag] = str(value)
                
                # Extract GPS data if available
                gps_data = {}
                gps_tags = [t for t in tags.keys() if t.startswith('GPS')]
                
                if gps_tags:
                    for tag in gps_tags:
                        gps_data[tag] = str(tags[tag])
                    
                    # Try to extract latitude and longitude
                    try:
                        if 'GPS GPSLatitude' in tags and 'GPS GPSLatitudeRef' in tags:
                            lat = self._convert_to_degrees(tags['GPS GPSLatitude'])
                            lat_ref = str(tags['GPS GPSLatitudeRef'])
                            if lat_ref == 'S':
                                lat = -lat
                            gps_data['latitude'] = lat
                        
                        if 'GPS GPSLongitude' in tags and 'GPS GPSLongitudeRef' in tags:
                            lon = self._convert_to_degrees(tags['GPS GPSLongitude'])
                            lon_ref = str(tags['GPS GPSLongitudeRef'])
                            if lon_ref == 'W':
                                lon = -lon
                            gps_data['longitude'] = lon
                    except Exception as e:
                        gps_data['conversion_error'] = str(e)
                    
                    result['gps'] = gps_data
                
                return result
        except Exception as e:
            return {"error_exifread": str(e)}
    
    def _convert_to_degrees(self, value) -> float:
        """
        Helper method to convert the GPS coordinates from ExifRead format to decimal degrees.
        """
        try:
            d = float(value.values[0].num) / float(value.values[0].den)
            m = float(value.values[1].num) / float(value.values[1].den)
            s = float(value.values[2].num) / float(value.values[2].den)
            return d + (m / 60.0) + (s / 3600.0)
        except Exception as e:
            raise ValueError(f"Could not convert GPS value: {e}")
    
    def _extract_piexif_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract structured EXIF data using piexif."""
        try:
            result = {"exif": {}, "source": "piexif"}
            
            # Check if format supported by piexif (JPEG, TIFF)
            with Image.open(image_path) as img:
                if img.format not in ['JPEG', 'TIFF']:
                    return {"error_piexif": "Format not supported by piexif"}
            
            exif_dict = piexif.load(image_path)
            
            # Map IFD (Image File Directory) names for better readability
            ifd_map = {
                "0th": "Image",
                "1st": "Thumbnail",
                "Exif": "Exif",
                "GPS": "GPS",
                "Interop": "Interoperability"
            }
            
            for ifd, tag_dict in exif_dict.items():
                if ifd == "thumbnail":
                    continue  # Skip thumbnail binary data
                
                section_name = ifd_map.get(ifd, ifd)
                section_data = {}
                
                for tag_id, value in tag_dict.items():
                    # Convert byte strings to regular strings if possible
                    if isinstance(value, bytes):
                        try:
                            decoded = value.decode('utf-8').strip('\x00')
                            section_data[f"{tag_id}"] = decoded
                        except UnicodeDecodeError:
                            section_data[f"{tag_id}"] = f"<binary data: {len(value)} bytes>"
                    else:
                        section_data[f"{tag_id}"] = value
                
                result["exif"][section_name] = section_data
            
            return result
        except Exception as e:
            return {"error_piexif": str(e)}
    
    def _extract_exiftool_metadata(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Extract full metadata using ExifTool (if available on system)."""
        try:
            # Check if ExifTool is available
            try:
                subprocess.run(["exiftool", "-ver"], 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                return None  # ExifTool not available
            
            # Run ExifTool with JSON output
            result = subprocess.run(
                ["exiftool", "-json", "-a", "-u", "-g", image_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Parse JSON output
            try:
                json_data = json.loads(result.stdout)
                if json_data and isinstance(json_data, list):
                    flat_metadata = {}
                    for key, value in json_data[0].items():
                        if isinstance(value, dict):
                            for subkey, subval in value.items():
                                flat_metadata[f"{key}:{subkey}"] = subval
                        else:
                            flat_metadata[key] = value
                    return flat_metadata
                return {}
            except json.JSONDecodeError:
                return {"error": "Could not parse ExifTool JSON output"}
        except Exception as e:
            return {"error_exiftool": str(e)}
    
    def _extract_common_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Extract commonly used metadata fields to the top level for easier access.
        Modifies the metadata dictionary in place.
        """
        common = {}
        
        # Basic image information (already at top level from PIL)
        common["format"] = metadata.get("format")
        common["dimensions"] = metadata.get("dimensions")
       
        
        # Extract camera information
        exif_data = metadata.get("exif", {})
        exiftool_data = metadata.get("exiftool", {})

        common["lens"] = exiftool_data.get("EXIF:LensModel") or exiftool_data.get("LensModel")
        common["iso"] = exiftool_data.get("EXIF:ISO") or exiftool_data.get("ISO")
        common["exposure_time"] = exiftool_data.get("EXIF:ExposureTime")
        common["f_number"] = exiftool_data.get("EXIF:FNumber")
        common["aperture"] = exiftool_data.get("EXIF:ApertureValue")
        common["white_balance"] = exiftool_data.get("EXIF:WhiteBalance")
        common["flash"] = exiftool_data.get("EXIF:Flash")
        common["artist"] = exiftool_data.get("IFD0:Artist") or exiftool_data.get("Artist")

        
        # Try to extract camera model
        camera_model = None
        if "EXIF:Model" in exiftool_data:
            camera_model = exiftool_data["EXIF:Model"]
        elif "Image" in exif_data and "271" in exif_data["Image"]:  # Standard EXIF tag for Maker
            camera_model = exif_data["Image"]["271"]
        elif "Make" in exif_data:
            camera_model = exif_data["Make"]
        
        if camera_model:
            common["camera_model"] = camera_model
            
        # Try to extract datetime
        datetime_original = None
        if "EXIF:DateTimeOriginal" in exiftool_data:
            datetime_original = exiftool_data["EXIF:DateTimeOriginal"]
        elif "DateTime" in exif_data:
            datetime_original = exif_data["DateTime"]
        
        if datetime_original:
            common["datetime"] = datetime_original
            
            # Try to parse datetime to standard format
            try:
                # Common EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
                parsed_dt = datetime.strptime(datetime_original, "%Y:%m:%d %H:%M:%S")
                common["datetime_iso"] = parsed_dt.isoformat()
            except (ValueError, TypeError):
                pass
        
        # Add GPS coordinates if available
        if "gps" in metadata and "latitude" in metadata["gps"] and "longitude" in metadata["gps"]:
            common["coordinates"] = {
                "latitude": metadata["gps"]["latitude"],
                "longitude": metadata["gps"]["longitude"]
            }
        
        # Add the common metadata to the top level
        metadata["common"] = common