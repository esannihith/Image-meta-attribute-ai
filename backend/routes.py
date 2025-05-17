from flask import Blueprint, request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

from crews.metadata_crew import MetadataCrew

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for routes
routes_bp = Blueprint('routes', __name__)

# Configure upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'tiff'}

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@routes_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle image upload and extract metadata.
    
    Accepts multipart form data with an image file,
    saves it to the uploads directory, and extracts metadata.
    
    Returns:
        JSON response with metadata or error message
    """
    try:        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file part in the request'
            }), 400
            
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
            
        # Check if the file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Get the socket_id if provided in the form data
        socket_id = request.form.get('socket_id')
            
        # Generate a secure filename with UUID to avoid collisions
        original_filename = secure_filename(file.filename)
        extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{extension}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
          # Save the file
        file.save(filepath)
        logger.info(f"Saved uploaded file to {filepath}")
        
        # Extract metadata using MetadataCrew
        metadata_crew = MetadataCrew(verbose=True)
        metadata = metadata_crew.run_extraction(filepath)
          # Add file information to the response
        metadata['file_info'] = {
            'original_filename': original_filename,
            'saved_filename': unique_filename,
            'upload_time': datetime.now().isoformat(),
            'file_size': os.path.getsize(filepath),
            'file_path': filepath
        }
        
        # If socket_id is provided, we can emit an event to the client via Socket.IO
        if socket_id:
            from socketio_server import socketio
            socketio.emit('image_uploaded', {
                'success': True,
                'message': 'Image uploaded successfully! You can now ask questions about it.'
            }, room=socket_id)
        
        return jsonify({
            'success': True,
            'metadata': metadata
        })
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500
        
@routes_bp.route('/uploads/<filename>', methods=['GET'])
def get_upload_info(filename):
    """
    Get information about a previously uploaded file.
    
    Args:
        filename: The unique filename of the uploaded file
        
    Returns:
        JSON response with file information or error message
    """
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
            
        # Get basic file information
        file_info = {
            'filename': filename,
            'file_size': os.path.getsize(filepath),
            'last_modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
            'file_path': filepath
        }
        
        return jsonify({
            'success': True,
            'file_info': file_info
        })
        
    except Exception as e:
        logger.error(f"Error getting upload info: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500
