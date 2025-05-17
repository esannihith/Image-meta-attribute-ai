"""
Main application module for the image analysis backend.
Sets up FastAPI with Socket.IO integration and defines WebSocket event handlers.
"""
import os
import uuid
import base64
from pathlib import Path
from typing import Dict, Any, Optional
import socketio
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.socket_manager import sio_app, sio_server
from app.services.metadata_service import extract_metadata
from app.services.object_detection_service import detect_objects
from app.agents.coordinator import CrewCoordinator
from app.utils.session_manager import SessionManager
from app.utils.image_utils import save_image, cleanup_old_images, ensure_temp_dir

# Load environment variables
load_dotenv()

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(title="Image Analysis API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.SOCKET_CORS_ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO app
app.mount("/", sio_app)

# Initialize session manager for storing user context
session_manager = SessionManager()

# Ensure temporary image directory exists
ensure_temp_dir(settings.TEMP_IMAGE_DIR)

@app.on_event("startup")
async def startup_event():
    """Run tasks when the application starts up."""
    # Clean up old images from previous sessions
    cleanup_old_images(settings.TEMP_IMAGE_DIR, hours=2)

@sio_server.event
async def connect(sid, environ):
    """Handle new client connections."""
    print(f"Client connected: {sid}")
    session_manager.create_session(sid)
    await sio_server.emit('message', {'role': 'system', 'content': 'Connected to Image Analysis System. Upload an image and ask questions about it.'}, room=sid)

@sio_server.event
async def disconnect(sid):
    """Handle client disconnections."""
    print(f"Client disconnected: {sid}")
    # Clean up session data and temporary images
    session_data = session_manager.get_session(sid)
    if session_data and 'image_path' in session_data:
        try:
            os.remove(session_data['image_path'])
        except (FileNotFoundError, PermissionError) as e:
            print(f"Error removing image file: {e}")
    session_manager.end_session(sid)

@sio_server.event
async def upload_image(sid, data):
    """
    Handle image uploads from clients.
    
    Args:
        sid: Socket ID of the client
        data: Dictionary containing image data (base64-encoded) and filename
    """
    try:
        # Extract data
        image_data = data.get('image')
        filename = data.get('filename', f"image_{uuid.uuid4()}.jpg")
        
        if not image_data:
            await sio_server.emit('error', {'message': 'No image data provided'}, room=sid)
            return
        
        # Save the image
        image_path = save_image(
            image_data, 
            filename, 
            output_dir=settings.TEMP_IMAGE_DIR
        )
        
        # Update session with image info
        session_manager.update_session(sid, {
            'image_path': image_path,
            'filename': filename
        })
        
        # Extract metadata as a first step
        metadata = extract_metadata(image_path)
        session_manager.update_session(sid, {'metadata': metadata})
        
        await sio_server.emit('image_uploaded', {
            'success': True,
            'filename': filename,
            'message': "Image uploaded successfully. You can now ask questions about it."
        }, room=sid)
        
    except Exception as e:
        print(f"Error processing image: {e}")
        await sio_server.emit('error', {'message': f'Error processing image: {str(e)}'}, room=sid)

@sio_server.event
async def message(sid, data):
    """
    Process incoming messages from clients.
    
    Args:
        sid: Socket ID of the client
        data: Dictionary containing the message content
    """
    try:
        # Check if an image has been uploaded
        session_data = session_manager.get_session(sid)
        if not session_data or 'image_path' not in session_data:
            await sio_server.emit('message', {
                'role': 'system',
                'content': 'Please upload an image first before asking questions.'
            }, room=sid)
            return
        
        user_message = data.get('content', '')
        if not user_message:
            return
            
        # Add the user message to the conversation history
        session_manager.add_message(sid, {'role': 'user', 'content': user_message})
        
        # Send thinking indicator to client
        await sio_server.emit('typing', {'status': True}, room=sid)
        
        # Initialize the agent crew
        coordinator = CrewCoordinator(
            image_path=session_data['image_path'],
            metadata=session_data.get('metadata', {}),
            object_data=session_data.get('object_data', {}),
            message=user_message,
            conversation_history=session_manager.get_messages(sid)
        )
        
        # Get response from the agent crew
        response = await coordinator.get_response()
        
        # Add the response to the conversation history
        session_manager.add_message(sid, {'role': 'assistant', 'content': response})
        
        # Send the response to the client
        await sio_server.emit('message', {
            'role': 'assistant',
            'content': response
        }, room=sid)
        
        # Send typing indicator off
        await sio_server.emit('typing', {'status': False}, room=sid)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        await sio_server.emit('error', {'message': f'Error processing your request: {str(e)}'}, room=sid)
        await sio_server.emit('typing', {'status': False}, room=sid)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
