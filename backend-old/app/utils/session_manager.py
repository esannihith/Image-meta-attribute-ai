"""
Session management utility for tracking user state across socket connections.
"""
import time
from typing import Dict, Any, List, Optional

class SessionManager:
    """
    Manager for handling user sessions and conversation history.
    Maintains state for each connected client including uploaded images,
    conversation history, and extracted metadata.
    """
    
    def __init__(self):
        """Initialize the session manager with an empty sessions dict."""
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, sid: str) -> None:
        """
        Create a new session for the given socket ID.
        
        Args:
            sid: Socket ID of the client
        """
        self.sessions[sid] = {
            'created_at': time.time(),
            'messages': [],
            'metadata': {},
            'object_data': {}
        }
    
    def end_session(self, sid: str) -> None:
        """
        End and remove a session for the given socket ID.
        
        Args:
            sid: Socket ID of the client
        """
        if sid in self.sessions:
            del self.sessions[sid]
    
    def get_session(self, sid: str) -> Optional[Dict[str, Any]]:
        """
        Get session data for the given socket ID.
        
        Args:
            sid: Socket ID of the client
        
        Returns:
            Dict or None: Session data if exists, None otherwise
        """
        return self.sessions.get(sid)
    
    def update_session(self, sid: str, data: Dict[str, Any]) -> None:
        """
        Update session data for the given socket ID.
        
        Args:
            sid: Socket ID of the client
            data: Data to update in the session
        """
        if sid in self.sessions:
            self.sessions[sid].update(data)
    
    def add_message(self, sid: str, message: Dict[str, str]) -> None:
        """
        Add a message to the conversation history for a session.
        
        Args:
            sid: Socket ID of the client
            message: Message data with 'role' and 'content' keys
        """
        if sid in self.sessions:
            if 'messages' not in self.sessions[sid]:
                self.sessions[sid]['messages'] = []
            self.sessions[sid]['messages'].append(message)
    
    def get_messages(self, sid: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            sid: Socket ID of the client
            
        Returns:
            List: List of messages in the conversation history
        """
        if sid in self.sessions and 'messages' in self.sessions[sid]:
            return self.sessions[sid]['messages']
        return []
    
    def clear_messages(self, sid: str) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            sid: Socket ID of the client
        """
        if sid in self.sessions:
            self.sessions[sid]['messages'] = []