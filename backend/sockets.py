import os
import logging
from flask import request
from flask_socketio import emit

from crews.metadata_crew import MetadataCrew
from agents.chat_manager_agent import ChatManagerAgent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize chat manager for conversation history
chat_manager = ChatManagerAgent(verbose=True)

def register_socket_events(socketio):
    """
    Register all Socket.IO event handlers.
    
    Args:
        socketio: The Flask-SocketIO instance
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection event."""
        logger.info(f"Client connected: {request.sid}")
        emit('connection_response', {
            'status': 'connected',
            'message': 'Connected to Image Analysis API'
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection event."""
        logger.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('analyze_image')
    def handle_analyze_image(data):
        """
        Handle image analysis request.
        
        Args:
            data: Dictionary containing image information
                - image_path: Path to the uploaded image
                - prompt (optional): User prompt or question about the image
        """
        try:
            logger.info(f"Analyze image request: {data}")
            
            # Check if image_path is provided
            if 'image_path' not in data:
                emit('error', {
                    'message': 'Missing image_path in request'
                })
                return
            
            image_path = data['image_path']
            
            # For security, if the path is not absolute, assume it's in the uploads folder
            if not os.path.isabs(image_path):
                uploads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
                image_path = os.path.join(uploads_folder, image_path)
              # Verify the file exists
            if not os.path.exists(image_path):
                emit('error', {
                    'message': f'Image file not found: {image_path}'
                })
                return
            
            # Emit typing indicator
            emit('typing', {'status': True})
            
            # Extract metadata using MetadataCrew
            metadata_crew = MetadataCrew(verbose=True)
            
            # Check if there's a prompt for analysis or just metadata extraction
            if 'prompt' in data and data['prompt']:
                prompt = data['prompt']
                logger.info(f"Analyzing image with prompt: {prompt}")
                
                # Run metadata analysis with the prompt
                result = metadata_crew.run(image_path, prompt)
                
                # For analysis results (string responses), we format through chat manager
                if isinstance(result, str):
                    # Extract metadata separately for the chat manager
                    metadata = metadata_crew.run_extraction(image_path)
                    
                    # Generate a conversational response
                    response = chat_manager.generate_response(prompt, metadata)
                    
                    # Emit metadata result with conversational response
                    emit('metadata_result', {
                        'metadata': metadata,
                        'analysis': response,
                        'original_prompt': prompt
                    })
                else:
                    # If result is already structured metadata, emit directly
                    emit('metadata_result', {
                        'metadata': result,
                        'analysis': None,
                        'original_prompt': prompt
                    })
            else:
                # No prompt, just extract metadata
                logger.info("Extracting image metadata (no prompt)")
                metadata = metadata_crew.run_extraction(image_path)
                
                # Emit metadata result
                emit('metadata_result', {
                    'metadata': metadata,
                    'analysis': None,
                    'original_prompt': None
                })
            
            # Turn off typing indicator
            emit('typing', {'status': False})
            
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}", exc_info=True)
            
            # Turn off typing indicator
            emit('typing', {'status': False})
            
            # Emit error event
            emit('error', {
                'message': f"Error analyzing image: {str(e)}"
            })

    @socketio.on('message')
    @socketio.on('user_message')
    def handle_user_message(data):
        """
        Handle chat message from client.
        """
        try:
            logger.info(f"User message event received: {data}")
            if 'content' not in data:
                emit('error', {
                    'message': 'Missing content in message'
                })
                return
            
            content = data['content']
            logger.info(f"Received message: {content}")
            
            # Emit typing indicator
            emit('typing', {'status': True})
            
            # Check if there's an image path associated with the message
            if 'image_path' in data and data['image_path']:
                image_path = data['image_path']
                
                # For security, if the path is not absolute, assume it's in the uploads folder
                if not os.path.isabs(image_path):
                    uploads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
                    image_path = os.path.join(uploads_folder, image_path)                
                if os.path.exists(image_path):
                    # Extract metadata from the image
                    metadata_crew = MetadataCrew(verbose=True)
                    metadata = metadata_crew.run_extraction(image_path)

                    # Generate a response using the chat manager
                    response = chat_manager.generate_response(content, metadata)

                    # Emit the response
                    emit('message', {
                        'role': 'assistant',
                        'content': response
                    })
                else:
                    # Image path provided but file doesn't exist
                    logger.error(f"Image file not found: {image_path}")
                    emit('message', {
                        'role': 'assistant',
                        'content': "I couldn't find the image file. Please try uploading it again."
                    })
            else:
                # Look for recently uploaded images in the uploads folder
                uploads_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
                image_files = [f for f in os.listdir(uploads_folder) if os.path.isfile(os.path.join(uploads_folder, f)) 
                              and f.endswith(('.jpg', '.jpeg', '.png', '.gif', '.tiff'))]
                
                if image_files:
                    # Sort by modification time (most recent first)
                    image_files.sort(key=lambda f: os.path.getmtime(os.path.join(uploads_folder, f)), reverse=True)
                      # Use the most recently uploaded image
                    latest_image = os.path.join(uploads_folder, image_files[0])
                    logger.info(f"Using most recent image: {latest_image}")
                    
                    # Extract metadata from the image
                    metadata_crew = MetadataCrew(verbose=True)
                    metadata = metadata_crew.run_extraction(latest_image)
                    
                    # Generate a response using the chat manager
                    response = chat_manager.generate_response(content, metadata)
                    
                    # Emit the response
                    emit('message', {
                        'role': 'assistant',
                        'content': response
                    })
                else:
                    # No image path, and no images in uploads folder
                    emit('message', {
                        'role': 'assistant',
                        'content': "I need an image to analyze. Please upload an image first."
                    })
            
            # Turn off typing indicator
            emit('typing', {'status': False})
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            
            # Turn off typing indicator
            emit('typing', {'status': False})
            
            # Emit error event
            emit('error', {
                'message': f"Error handling message: {str(e)}"
            })
    
    @socketio.on('clear_image')
    def handle_clear_image(data):
        """
        Handle image clearing event.
        
        Args:
            data: Dictionary (can be empty)
        """
        logger.info("Client cleared image")
        emit('message', {
            'role': 'system',
            'content': "Image cleared. You can upload a new image to analyze."
        })
