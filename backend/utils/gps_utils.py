"""
Utility functions for working with GPS data in images.
Includes functions for converting between formats and parsing EXIF GPS data.
"""

from typing import Dict, Any, Tuple, Optional, Union
import re

def dms_to_decimal(
    degrees: Union[int, float], 
    minutes: Union[int, float], 
    seconds: Union[int, float], 
    direction: str
) -> float:
    """
    Convert degrees, minutes, seconds (DMS) to decimal degrees.
    
    Args:
        degrees: Degrees component (0-180 for latitude, 0-360 for longitude)
        minutes: Minutes component (0-60)
        seconds: Seconds component (0-60)
        direction: Direction indicator ('N', 'S', 'E', 'W')
        
    Returns:
        Decimal degrees as a float
    
    Example:
        >>> dms_to_decimal(40, 26, 46.302, 'N')
        40.44619500000001
    """
    decimal = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
    
    # If the direction is South or West, negate the value
    if direction in ['S', 'W']:
        decimal = -decimal
        
    return decimal

def parse_dms_string(dms_str: str) -> Optional[float]:
    """
    Parse a DMS (Degrees, Minutes, Seconds) string into decimal degrees.
    
    Supports formats like:
    - "40° 26' 46.302\" N"
    - "40 deg 26' 46.302\" N"
    - "40d 26m 46.302s N"
    - "40.123456° N"
    
    Args:
        dms_str: String containing DMS coordinates
        
    Returns:
        Decimal degrees as a float, or None if parsing failed
    
    Example:
        >>> parse_dms_string("40° 26' 46.302\" N")
        40.44619500000001
    """
    try:
        # Check if it's already in decimal format with direction
        decimal_pattern = r'(-?\d+\.?\d*)°?\s*([NSEW])'
        match = re.search(decimal_pattern, dms_str)
        if match:
            decimal = float(match.group(1))
            direction = match.group(2)
            
            if direction in ['S', 'W']:
                decimal = -decimal
                
            return decimal
        
        # DMS with symbols
        dms_pattern = r'(\d+)°\s*(\d+)[\'′]\s*(\d+\.?\d*)["″]?\s*([NSEW])'
        match = re.search(dms_pattern, dms_str)
        if match:
            d, m, s, direction = match.groups()
            return dms_to_decimal(float(d), float(m), float(s), direction)
            
        # DMS with 'deg', 'min', 'sec' words
        dms_word_pattern = r'(\d+)\s*deg\s*(\d+)\s*min\s*(\d+\.?\d*)\s*sec\s*([NSEW])'
        match = re.search(dms_word_pattern, dms_str)
        if match:
            d, m, s, direction = match.groups()
            return dms_to_decimal(float(d), float(m), float(s), direction)
            
        # DMS with d, m, s letters
        dms_letter_pattern = r'(\d+)d\s*(\d+)m\s*(\d+\.?\d*)s\s*([NSEW])'
        match = re.search(dms_letter_pattern, dms_str)
        if match:
            d, m, s, direction = match.groups()
            return dms_to_decimal(float(d), float(m), float(s), direction)
            
        return None
    except Exception as e:
        print(f"Error parsing DMS string: {e}")
        return None

def parse_exif_gps(exif_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Extract and parse GPS coordinates from EXIF data.
    
    Args:
        exif_data: Dictionary containing EXIF data with GPS tags
        
    Returns:
        Dictionary with 'latitude' and 'longitude' keys, or None if GPS data not found
    
    Example:
        >>> exif_data = {
        ...     'GPS GPSLatitude': [(40, 1), (26, 1), (46, 100)],
        ...     'GPS GPSLatitudeRef': 'N',
        ...     'GPS GPSLongitude': [(74, 1), (0, 1), (21, 100)],
        ...     'GPS GPSLongitudeRef': 'W'
        ... }
        >>> parse_exif_gps(exif_data)
        {'latitude': 40.44619500000001, 'longitude': -74.00583333333333}
    """
    try:
        # Check if required GPS tags exist
        required_tags = [
            'GPS GPSLatitude', 'GPS GPSLatitudeRef', 
            'GPS GPSLongitude', 'GPS GPSLongitudeRef'
        ]
        
        # Check if all required tags are present
        if not all(tag in exif_data for tag in required_tags):
            # Try alternative tag formats (some libraries use different formats)
            alt_tags = [
                'GPSLatitude', 'GPSLatitudeRef', 
                'GPSLongitude', 'GPSLongitudeRef'
            ]
            if not all(tag in exif_data for tag in alt_tags):
                return None
            
            # Use alternative tags if they exist
            lat_tag, lat_ref_tag = 'GPSLatitude', 'GPSLatitudeRef'
            lon_tag, lon_ref_tag = 'GPSLongitude', 'GPSLongitudeRef'
        else:
            # Use standard tags
            lat_tag, lat_ref_tag = 'GPS GPSLatitude', 'GPS GPSLatitudeRef'
            lon_tag, lon_ref_tag = 'GPS GPSLongitude', 'GPS GPSLongitudeRef'
        
        # Get latitude components
        lat_value = exif_data[lat_tag]
        lat_ref = exif_data[lat_ref_tag]
        
        # Get longitude components
        lon_value = exif_data[lon_tag]
        lon_ref = exif_data[lon_ref_tag]
        
        # Parse latitude and longitude based on their type
        if isinstance(lat_value, str):
            # String DMS format
            latitude = parse_dms_string(f"{lat_value} {lat_ref}")
            longitude = parse_dms_string(f"{lon_value} {lon_ref}")
        elif isinstance(lat_value, list) or isinstance(lat_value, tuple):
            # Rational format (list of fractions)
            # Extract degree, minute, second components
            lat_degrees = lat_value[0][0] / lat_value[0][1] if isinstance(lat_value[0], tuple) else lat_value[0]
            lat_minutes = lat_value[1][0] / lat_value[1][1] if isinstance(lat_value[1], tuple) else lat_value[1]
            lat_seconds = lat_value[2][0] / lat_value[2][1] if isinstance(lat_value[2], tuple) else lat_value[2]
            
            lon_degrees = lon_value[0][0] / lon_value[0][1] if isinstance(lon_value[0], tuple) else lon_value[0]
            lon_minutes = lon_value[1][0] / lon_value[1][1] if isinstance(lon_value[1], tuple) else lon_value[1]
            lon_seconds = lon_value[2][0] / lon_value[2][1] if isinstance(lon_value[2], tuple) else lon_value[2]
            
            # Convert to decimal format
            latitude = dms_to_decimal(lat_degrees, lat_minutes, lat_seconds, lat_ref)
            longitude = dms_to_decimal(lon_degrees, lon_minutes, lon_seconds, lon_ref)
        else:
            # Already in decimal format
            latitude = float(lat_value) * (-1 if lat_ref == 'S' else 1)
            longitude = float(lon_value) * (-1 if lon_ref == 'W' else 1)
        
        return {
            'latitude': latitude,
            'longitude': longitude
        }
        
    except Exception as e:
        print(f"Error parsing GPS EXIF data: {e}")
        return None

def get_location_url(latitude: float, longitude: float, label: str = None) -> str:
    """
    Create a Google Maps URL for a given latitude and longitude.
    
    Args:
        latitude: Decimal latitude
        longitude: Decimal longitude
        label: Optional label for the pin (default: "Location")
        
    Returns:
        Google Maps URL string
        
    Example:
        >>> get_location_url(40.7128, -74.0060)
        'https://www.google.com/maps/search/?api=1&query=40.7128,-74.0060'
    """
    if label is None:
        label = "Location"
    
    # URL-encode the label
    import urllib.parse
    encoded_label = urllib.parse.quote(label)
    
    # Format the URL
    return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"