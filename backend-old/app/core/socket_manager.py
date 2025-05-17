"""
Socket.IO manager for handling real-time communication with the frontend.
"""
import socketio
from fastapi import FastAPI
from app.core.config import get_settings

# Initialize settings
settings = get_settings()

# Create Socket.IO server instance
sio_server = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:5173"],
    logger=False,        # turn off event payload logging
    engineio_logger=False
)

# Create ASGI app by wrapping Socket.IO server
sio_app = socketio.ASGIApp(
    socketio_server=sio_server,
    socketio_path='socket.io'
)