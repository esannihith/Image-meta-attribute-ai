from typing import Dict, Any, Optional, List
import uuid
import os 
import json
from datetime import datetime

from crewai import Agent
from langchain_groq import ChatGroq

class ChatMessage:
    """Represents a single message in the chat history."""
    
    def __init__(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

class ChatManagerAgent:
    """
    A CrewAI-compatible agent that manages chat history and formats
    responses to user queries based on metadata output.
    
    This agent maintains the conversation context and generates
    natural language responses.
    """
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        verbose: bool = False,
        max_history: int = 10
    ):
        """
        Initialize the Chat Manager Agent.
        
        Args:            llm: Language model to use (defaults to ChatGroq)
            verbose: Whether to enable verbose logging
            max_history: Maximum number of messages to keep in history
        """        # Set default LLM if none provided
        if llm is None:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",  # Need to prefix with 'groq/' to work with litellm
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.5,  # Conservative setting for accurate information extraction
                max_tokens=15000  # Maximum tokens in the completion
            )
        
        # Create the CrewAI Agent
        self.agent = Agent(
            role="Conversation Manager",
            goal="Maintain conversation context and generate natural, helpful responses",
            backstory="""You are an expert in maintaining meaningful conversations 
            about images. You have excellent communication skills and can translate 
            technical metadata into clear, concise natural language that answers 
            user questions precisely while maintaining context.""",
            verbose=verbose,
            llm=llm,
            allow_delegation=False
        )
        
        # Initialize chat history
        self.history: List[ChatMessage] = []
        self.max_history = max_history
        self.verbose = verbose
        self.llm = llm
    
    def get_agent(self) -> Agent:
        """
        Get the CrewAI agent instance.
        
        Returns:
            The configured CrewAI Agent instance
        """
        return self.agent
    
    def add_user_message(self, content: str) -> ChatMessage:
        """
        Add a user message to the chat history.
        
        Args:
            content: The user's message content
            
        Returns:
            The created ChatMessage object
        """
        message = ChatMessage(role="user", content=content)
        self._add_to_history(message)
        
        if self.verbose:
            print(f"Added user message: {content}")
            
        return message
    
    def add_assistant_message(
        self, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """
        Add an assistant message to the chat history.
        
        Args:
            content: The assistant's message content
            metadata: Optional metadata associated with the message
            
        Returns:
            The created ChatMessage object
        """
        message = ChatMessage(role="assistant", content=content, metadata=metadata)
        self._add_to_history(message)
        
        if self.verbose:
            print(f"Added assistant message: {content}")
            
        return message
    
    def _add_to_history(self, message: ChatMessage) -> None:
        """
        Add a message to the history, respecting the max_history limit.
        
        Args:
            message: The ChatMessage to add
        """
        self.history.append(message)
        
        # Trim history if it exceeds max_history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def get_history(self, as_dict: bool = False) -> List[Any]:
        """
        Get the current chat history.
        
        Args:
            as_dict: Whether to return as list of dictionaries (True) or ChatMessage objects (False)
            
        Returns:
            List of chat history items
        """
        if as_dict:
            return [msg.to_dict() for msg in self.history]
        return self.history
    
    def generate_response(
        self, 
        user_prompt: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate a natural language response based on the user prompt and metadata.
        
        Args:
            user_prompt: The user's question or prompt
            metadata: The metadata extracted from the image
            
        Returns:
            A natural language response answering the user's question
        """
        # Add the user message to history
        self.add_user_message(user_prompt)
        
        # Format a response using the LLM
        response = self._format_response(user_prompt, metadata)
        
        # Add the assistant response to history
        self.add_assistant_message(response, metadata)
        
        return response
    
    def _format_response(
        self, 
        user_prompt: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """
        Format a natural language response based on the user prompt and metadata.
        
        Args:
            user_prompt: The user's question or prompt
            metadata: The metadata extracted from the image
            
        Returns:
            A formatted response string
        """
        # Get relevant context from previous messages
        context = self._get_conversation_context()
        
        # For simplicity in the MVP, we'll use a placeholder LLM function
        # In a production system, this would make a proper call to the LLM
        
        # Extract common metadata for easier access
        common_metadata = metadata.get("common", {})
        
        # Create a formatting prompt, including full metadata dump
        formatting_prompt = f"""
        You are an AI assistant helping with image analysis. Generate a natural language response
        to answer the user's question based on the image metadata provided.

        Previous conversation:
        {context}

        User question: {user_prompt}

        Summary of key metadata:
        - Format: {common_metadata.get('format', 'Unknown')}
        - Dimensions: {self._format_dimensions(common_metadata.get('dimensions', {}))}
        - Camera: {common_metadata.get('camera_model', 'Unknown')}
        - Date taken: {common_metadata.get('datetime', 'Unknown')}
        GPS information: {self._format_gps_info(metadata)}

        Full metadata details (JSON):
        {json.dumps(metadata, indent=2)}

        Your response should:
        1. Directly answer the user's question if possible
        2. Be conversational and natural
        3. Mention any significant metadata fields shown above
        4. Be concise but informative
        """
        
        # In MVP, we use the LLM directly instead of through the CrewAI agent
        # This is simpler and more efficient for this specific use case
        response = self.llm.invoke(formatting_prompt)
        
        # Extract content from LLM response
        if hasattr(response, 'content'):
            return response.content
        
        # Fallback for simple string responses
        return str(response)
    
    def _format_dimensions(self, dimensions: Dict[str, Any]) -> str:
        """Format image dimensions nicely."""
        if not dimensions:
            return "Unknown"
        
        width = dimensions.get('width', 'Unknown')
        height = dimensions.get('height', 'Unknown')
        
        if width != 'Unknown' and height != 'Unknown':
            return f"{width}x{height} pixels"
        
        return "Unknown dimensions"
    
    def _format_gps_info(self, metadata: Dict[str, Any]) -> str:
        """Format GPS information in a readable way."""
        # Check for GPS coordinates in common metadata
        common = metadata.get("common", {})
        if "coordinates" in common:
            coords = common["coordinates"]
            lat = coords.get("latitude")
            lon = coords.get("longitude")
            
            if lat is not None and lon is not None:
                return f"Latitude: {lat}, Longitude: {lon}"
        
        # Check for raw GPS data
        if "gps" in metadata:
            gps_data = metadata["gps"]
            if "latitude" in gps_data and "longitude" in gps_data:
                return f"Latitude: {gps_data['latitude']}, Longitude: {gps_data['longitude']}"
        
        return "No GPS information available"
    
    def _get_conversation_context(self) -> str:
        """Get formatted conversation context from history."""
        if not self.history:
            return "No previous conversation."
        
        # Format last few messages as context (skip the very last user message)
        context_messages = self.history[:-1][-3:]  # Last 3 messages excluding the most recent
        
        if not context_messages:
            return "No previous conversation."
        
        formatted_context = "\n".join([
            f"{msg.role.capitalize()}: {msg.content}" 
            for msg in context_messages
        ])
        
        return formatted_context


# Example usage:
# if __name__ == "__main__":
#     chat_manager = ChatManagerAgent(verbose=True)
#     
#     # Example metadata
#     sample_metadata = {
#         "common": {
#             "format": "JPEG",
#             "dimensions": {"width": 1920, "height": 1080},
#             "camera_model": "iPhone 13 Pro",
#             "datetime": "2023:04:15 14:30:22",
#             "coordinates": {"latitude": 40.7128, "longitude": -74.0060}
#         }
#     }
#     
#     # Generate responses to user questions
#     questions = [
#         "Where was this photo taken?",
#         "What camera was used?",
#         "When was the picture taken?"
#     ]
#     
#     for question in questions:
#         response = chat_manager.generate_response(question, sample_metadata)
#         print(f"\nQ: {question}")
#         print(f"A: {response}\n{'='*50}")
#         
#     # Get chat history
#     print("\nChat History:")
#     for msg in chat_manager.get_history(as_dict=True):
#         print(f"{msg['role'].upper()} ({msg['timestamp']}): {msg['content']}")