"""
Service for extracting metadata from images using various libraries.
"""
import os
import json
import exifread
import piexif
from PIL import Image
from typing import Dict, Any, Optional

def extract_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extract metadata from an image using exifread and piexif.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dict: Dictionary containing the extracted metadata
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    metadata = {
        "file_info": {},
        "exif": {},
        "geo": {}
    }
    
    # Extract basic file information
    file_stats = os.stat(image_path)
    metadata["file_info"] = {
        "filename": os.path.basename(image_path),
        "size_bytes": file_stats.st_size,
        "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
        "created": file_stats.st_ctime,
        "modified": file_stats.st_mtime,
    }
    
    try:
        # Extract image dimensions and format using PIL
        with Image.open(image_path) as img:
            metadata["file_info"]["width"] = img.width
            metadata["file_info"]["height"] = img.height
            metadata["file_info"]["format"] = img.format
            metadata["file_info"]["mode"] = img.mode
    except Exception as e:
        print(f"Error extracting basic image information: {e}")
    
    # Extract EXIF data using exifread
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            
            # Process EXIF tags
            for tag, value in tags.items():
                # Skip thumbnail data
                if tag.startswith('JPEGThumbnail'):
                    continue
                
                # Format tag name and value for storage
                tag_name = tag.split('EXIF ')[1] if 'EXIF ' in tag else tag
                tag_value = str(value)
                
                # Organize by category
                if 'DateTimeOriginal' in tag:
                    metadata["exif"]["date_taken"] = tag_value
                elif 'Make' in tag:
                    metadata["exif"]["camera_make"] = tag_value
                elif 'Model' in tag:
                    metadata["exif"]["camera_model"] = tag_value
                elif 'ISOSpeedRatings' in tag:
                    metadata["exif"]["iso"] = tag_value
                elif 'ExposureTime' in tag:
                    metadata["exif"]["exposure_time"] = tag_value
                elif 'FNumber' in tag:
                    metadata["exif"]["f_number"] = tag_value
                elif 'FocalLength' in tag:
                    metadata["exif"]["focal_length"] = tag_value
                elif 'Flash' in tag:
                    metadata["exif"]["flash"] = tag_value
                elif 'GPSLatitude' in tag:
                    metadata["geo"]["latitude"] = _convert_gps_to_decimal(
                        tags.get('GPS GPSLatitude', None),
                        tags.get('GPS GPSLatitudeRef', None)
                    )
                elif 'GPSLongitude' in tag:
                    metadata["geo"]["longitude"] = _convert_gps_to_decimal(
                        tags.get('GPS GPSLongitude', None),
                        tags.get('GPS GPSLongitudeRef', None)
                    )
                # Store all other values in a general section
                else:
                    if 'general' not in metadata["exif"]:
                        metadata["exif"]["general"] = {}
                    metadata["exif"]["general"][tag_name] = tag_value
    except Exception as e:
        print(f"Error extracting EXIF data with exifread: {e}")
    
    # Try to extract additional metadata with piexif
    try:
        piexif_data = piexif.load(image_path)
        
        # Process GPS info if available
        if "GPS" in piexif_data and piexif_data["GPS"]:
            gps_data = piexif_data["GPS"]
            
            # Check if we already have GPS data from exifread
            if "latitude" not in metadata["geo"] and 2 in gps_data and 1 in gps_data:
                latitude = _convert_piexif_gps(gps_data[2], gps_data[1])
                metadata["geo"]["latitude"] = latitude
                
            if "longitude" not in metadata["geo"] and 4 in gps_data and 3 in gps_data:
                longitude = _convert_piexif_gps(gps_data[4], gps_data[3])
                metadata["geo"]["longitude"] = longitude
                
            # GPS altitude
            if 6 in gps_data:
                try:
                    alt_value = gps_data[6]
                    # Handle different formats (rational or tuple)
                    if isinstance(alt_value, tuple):
                        altitude = alt_value[0] / alt_value[1]
                    else:
                        altitude = alt_value
                    metadata["geo"]["altitude"] = altitude
                except (TypeError, ZeroDivisionError):
                    pass
                
    except Exception as e:
        print(f"Error extracting additional metadata with piexif: {e}")
    
    return metadata

def _convert_gps_to_decimal(gps_coords, gps_ref) -> Optional[float]:
    """
    Convert GPS coordinates from the EXIF format to decimal format.
    
    Args:
        gps_coords: GPS coordinates in the format [degrees, minutes, seconds]
        gps_ref: Direction reference (N, S, E, W)
        
    Returns:
        float or None: Decimal GPS coordinates or None if conversion fails
    """
    if not gps_coords or not gps_ref:
        return None
    
    try:
        d = float(gps_coords.values[0].num) / float(gps_coords.values[0].den)
        m = float(gps_coords.values[1].num) / float(gps_coords.values[1].den)
        s = float(gps_coords.values[2].num) / float(gps_coords.values[2].den)
        
        coord = d + (m / 60.0) + (s / 3600.0)
        
        # If reference is South or West, make the coordinate negative
        if gps_ref.values[0] in ['S', 'W']:
            coord = -coord
            
        return coord
    except (AttributeError, IndexError, TypeError, ZeroDivisionError):
        return None

def _convert_piexif_gps(gps_coords, gps_ref) -> Optional[float]:
    """
    Convert GPS coordinates from piexif format to decimal format.
    
    Args:
        gps_coords: GPS coordinates as a tuple of tuples ((d_num, d_den), (m_num, m_den), (s_num, s_den))
        gps_ref: Direction reference as bytes (N, S, E, W)
        
    Returns:
        float or None: Decimal GPS coordinates or None if conversion fails
    """
    try:
        d = gps_coords[0][0] / gps_coords[0][1]
        m = gps_coords[1][0] / gps_coords[1][1]
        s = gps_coords[2][0] / gps_coords[2][1]
        
        coord = d + (m / 60.0) + (s / 3600.0)
        
        # Check reference direction
        if isinstance(gps_ref, bytes):
            gps_ref = gps_ref.decode('utf-8', errors='replace')
            
        # If reference is South or West, make the coordinate negative
        if gps_ref in ['S', 'W']:
            coord = -coord
            
        return coord
    except (IndexError, TypeError, ZeroDivisionError):
        return None

def get_formatted_metadata(metadata: Dict[str, Any]) -> str:
    """
    Format metadata into a human-readable string.
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        str: Formatted metadata string
    """
    result = []
    
    # File Information
    if metadata.get("file_info"):
        result.append("📄 File Information:")
        fi = metadata["file_info"]
        if fi.get("filename"):
            result.append(f"  • Filename: {fi['filename']}")
        if fi.get("format"):
            result.append(f"  • Format: {fi['format']}")
        if fi.get("width") and fi.get("height"):
            result.append(f"  • Dimensions: {fi['width']}x{fi['height']} pixels")
        if fi.get("size_mb"):
            result.append(f"  • Size: {fi['size_mb']} MB")
        result.append("")
    
    # Camera Information
    exif = metadata.get("exif", {})
    if exif.get("camera_make") or exif.get("camera_model"):
        result.append("📷 Camera Information:")
        if exif.get("camera_make"):
            result.append(f"  • Make: {exif['camera_make']}")
        if exif.get("camera_model"):
            result.append(f"  • Model: {exif['camera_model']}")
        if exif.get("date_taken"):
            result.append(f"  • Date Taken: {exif['date_taken']}")
        result.append("")
    
    # Settings Information
    if exif.get("iso") or exif.get("exposure_time") or exif.get("f_number"):
        result.append("⚙️ Camera Settings:")
        if exif.get("iso"):
            result.append(f"  • ISO: {exif['iso']}")
        if exif.get("exposure_time"):
            result.append(f"  • Exposure Time: {exif['exposure_time']}")
        if exif.get("f_number"):
            result.append(f"  • Aperture: {exif['f_number']}")
        if exif.get("focal_length"):
            result.append(f"  • Focal Length: {exif['focal_length']}")
        if exif.get("flash"):
            result.append(f"  • Flash: {exif['flash']}")
        result.append("")
    
    # Location Information
    geo = metadata.get("geo", {})
    if geo.get("latitude") and geo.get("longitude"):
        result.append("Location Information:")
        result.append(f"  • Latitude: {geo['latitude']}")
        result.append(f"  • Longitude: {geo['longitude']}")
        if geo.get("altitude"):
            result.append(f"  • Altitude: {geo['altitude']} meters")
        result.append("")
    
    return "\n".join(result).strip()