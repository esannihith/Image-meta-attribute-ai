"""
This module provides the SocketIO instance for the Flask application.
It is separated from main.py to avoid circular imports when used by routes.py.
"""
from flask_socketio import SocketIO

# Create a SocketIO instance that will be initialized by main.py
socketio = SocketIO()