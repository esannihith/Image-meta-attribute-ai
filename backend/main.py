from flask import Flask, Blueprint, jsonify
from flask_cors import CORS
import os

# Import socketio instance from socketio_server
from socketio_server import socketio

# Initialize Flask application
app = Flask(__name__)

# Configure CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# Load configuration
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev_key_for_development_only"),
    DEBUG=os.environ.get("DEBUG", "True") == "True",
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # Limit upload size to 16MB
    UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
)

# Initialize SocketIO with our Flask app
socketio.init_app(
    app,
    cors_allowed_origins="*",  # Allow all origins for development
    async_mode="threading",    # Use threading mode
    path="/socket.io"          # Match frontend Socket.IO path
)

# Create a blueprint for API routes
api = Blueprint('api', __name__, url_prefix='/api')

# Register route for health check
@app.route('/')
def health_check():
    """Health check endpoint to verify the API is running."""
    return jsonify({
        "status": "healthy",
        "message": "Image analysis API is running"
    })

# API routes for metadata
@api.route('/metadata', methods=['GET'])
def get_metadata_info():
    """Return information about metadata extraction capabilities."""
    return jsonify({
        "capabilities": [
            "EXIF data extraction",
            "GPS coordinate parsing",
            "Camera model identification",
            "Date and time information"
        ]
    })

# Register blueprints
app.register_blueprint(api)

# Import and register routes blueprint
from routes import routes_bp
app.register_blueprint(routes_bp)

# Import and initialize socket event handlers
from sockets import register_socket_events
register_socket_events(socketio)

def create_app():
    """
    Factory function to create and configure the Flask app.
    This is useful for testing and potential future extensions.
    """
    return app

if __name__ == "__main__":
    # Start the application with SocketIO
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"Starting Image Analysis API on {host}:{port}")
    socketio.run(app, host=host, port=port)
