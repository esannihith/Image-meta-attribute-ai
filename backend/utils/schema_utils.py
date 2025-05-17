"""
Utility functions for working with metadata schemas and formats.
Includes functions for normalizing, cleaning and structuring metadata.
"""

from typing import Dict, Any, List, Optional, Union
import re
import json
import datetime

def normalize_key(key: str) -> str:
    """
    Normalize metadata keys by removing prefixes and standardizing format.
    
    Args:
        key: Original metadata key with potential prefixes
        
    Returns:
        Normalized key string
        
    Example:
        >>> normalize_key("EXIF:DateTimeOriginal")
        'datetime_original'
    """
    # Remove common prefixes
    prefixes_to_remove = [
        "EXIF:", "XMP:", "IPTC:", "GPS:", "GPS ", "File:", "JFIF:", "ICC_Profile:"
    ]
    
    cleaned_key = key
    for prefix in prefixes_to_remove:
        if key.startswith(prefix):
            cleaned_key = key[len(prefix):]
            break
    
    # Convert to snake_case
    # Replace spaces, dashes, and other non-alphanumeric chars with underscores
    cleaned_key = re.sub(r'[^a-zA-Z0-9]', '_', cleaned_key)
    
    # Convert to lowercase
    cleaned_key = cleaned_key.lower()
    
    # Replace multiple underscores with a single one
    cleaned_key = re.sub(r'_+', '_', cleaned_key)
    
    # Remove leading and trailing underscores
    cleaned_key = cleaned_key.strip('_')
    
    return cleaned_key

def normalize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize all keys in a metadata dictionary recursively.
    
    Args:
        metadata: Dictionary containing metadata with keys to normalize
        
    Returns:
        Dictionary with normalized keys
        
    Example:
        >>> normalize_metadata({"EXIF:Make": "Canon", "EXIF:Model": "EOS 5D"})
        {'make': 'Canon', 'model': 'EOS 5D'}
    """
    if not isinstance(metadata, dict):
        return metadata
    
    normalized = {}
    
    for key, value in metadata.items():
        # Normalize the key
        norm_key = normalize_key(key)
        
        # Recursively normalize nested dictionaries
        if isinstance(value, dict):
            normalized[norm_key] = normalize_metadata(value)
        # Normalize lists that might contain dictionaries
        elif isinstance(value, list):
            normalized[norm_key] = [
                normalize_metadata(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            normalized[norm_key] = value
    
    return normalized

def clean_metadata_values(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean metadata values to ensure they're serializable and consistent.
    
    Args:
        metadata: Dictionary containing metadata with values to clean
        
    Returns:
        Dictionary with cleaned values
        
    Example:
        >>> clean_metadata_values({"binary_data": b"\\x00\\x01\\x02"})
        {'binary_data': '<binary data: 3 bytes>'}
    """
    if not isinstance(metadata, dict):
        return metadata
    
    cleaned = {}
    
    for key, value in metadata.items():
        # Handle different types of values
        if isinstance(value, dict):
            # Recursively clean nested dictionaries
            cleaned[key] = clean_metadata_values(value)
        elif isinstance(value, list):
            # Clean lists that might contain dictionaries or other complex types
            cleaned[key] = [
                clean_metadata_values(item) if isinstance(item, dict)
                else clean_value(item)
                for item in value
            ]
        else:
            # Clean individual values
            cleaned[key] = clean_value(value)
    
    return cleaned

def clean_value(value: Any) -> Any:
    """
    Clean an individual metadata value to ensure it's serializable.
    
    Args:
        value: The value to clean
        
    Returns:
        Cleaned value that's JSON serializable
    """
    # Handle bytes (binary data)
    if isinstance(value, bytes):
        return f"<binary data: {len(value)} bytes>"
    
    # Handle datetime objects
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    
    # Handle other non-serializable types
    try:
        # Check if it's JSON serializable
        json.dumps(value)
        return value
    except (TypeError, OverflowError):
        # Convert to string if not serializable
        return str(value)

def extract_common_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract commonly used metadata fields into a standardized structure.
    
    Args:
        metadata: Full metadata dictionary
        
    Returns:
        Dictionary with common metadata in a standardized format
    """
    common = {}
    
    # Try to extract image format/type
    format_keys = ['format', 'file_format', 'mime_type', 'file_type']
    for key in format_keys:
        if key in metadata:
            common['format'] = metadata[key]
            break
    
    # Try to extract dimensions
    if 'dimensions' in metadata and isinstance(metadata['dimensions'], dict):
        common['dimensions'] = metadata['dimensions']
    elif all(k in metadata for k in ['width', 'height']):
        common['dimensions'] = {
            'width': metadata['width'],
            'height': metadata['height']
        }
    
    # Try to extract camera make/model
    make_keys = ['make', 'camera_make', 'manufacturer']
    model_keys = ['model', 'camera_model']
    
    for key in make_keys:
        if key in metadata:
            common['camera_make'] = metadata[key]
            break
    
    for key in model_keys:
        if key in metadata:
            common['camera_model'] = metadata[key]
            break
    
    # If we have both make and model, combine them
    if 'camera_make' in common and 'camera_model' in common:
        # Avoid duplication if model already includes make
        if common['camera_model'].startswith(common['camera_make']):
            common['camera'] = common['camera_model']
        else:
            common['camera'] = f"{common['camera_make']} {common['camera_model']}"
    
    # Try to extract date/time
    datetime_keys = [
        'datetime', 'datetime_original', 'create_date',
        'date_time_original', 'creation_time'
    ]
    
    for key in datetime_keys:
        if key in metadata:
            common['datetime'] = metadata[key]
            break
    
    # Try to extract GPS coordinates
    if 'gps' in metadata and isinstance(metadata['gps'], dict):
        gps = metadata['gps']
        if 'latitude' in gps and 'longitude' in gps:
            common['coordinates'] = {
                'latitude': gps['latitude'],
                'longitude': gps['longitude']
            }
    
    return common

def create_clean_metadata(raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process raw metadata from various tools into a clean, normalized structure.
    
    This is the main function to use for processing metadata from different 
    extraction tools into a consistent format.
    
    Args:
        raw_metadata: Raw metadata from extraction tools
        
    Returns:
        Clean, normalized metadata structure
    """
    # Start with a copy to avoid modifying the original
    metadata = raw_metadata.copy()
    
    # Normalize keys
    normalized = normalize_metadata(metadata)
    
    # Clean values
    cleaned = clean_metadata_values(normalized)
    
    # Extract common metadata into a standardized format
    common = extract_common_metadata(cleaned)
    
    # Build the final metadata structure
    result = {
        'common': common,
        'metadata': cleaned
    }
    
    return result

def metadata_to_json(metadata: Dict[str, Any], pretty: bool = False) -> str:
    """
    Convert metadata dictionary to a JSON string.
    
    Args:
        metadata: Metadata dictionary
        pretty: Whether to format with pretty-printing (default: False)
        
    Returns:
        JSON string representation
    """
    try:
        # Clean the metadata to ensure it's serializable
        cleaned = clean_metadata_values(metadata)
        
        # Convert to JSON
        if pretty:
            return json.dumps(cleaned, indent=2, sort_keys=True)
        else:
            return json.dumps(cleaned)
    except Exception as e:
        return json.dumps({
            "error": f"Failed to serialize metadata: {str(e)}"
        })