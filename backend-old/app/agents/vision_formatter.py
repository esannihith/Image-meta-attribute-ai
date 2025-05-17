"""
Vision Formatter Agent for formatting final responses about images.
"""
from typing import Dict, Any, List, Optional
import json

from app.core.config import get_settings
from app.core.llm import get_llm_response

# Get application settings
settings = get_settings()

class VisionFormatterAgent:
    """
    Agent for formatting comprehensive responses about images by combining
    metadata analysis and object detection results.
    """
    def __init__(self):
        """Initialize the vision formatter agent."""
        self.settings = settings
    
    async def format_response(
        self,
        message: str,
        metadata_analysis: str,
        object_analysis: str,
        interpretation: Dict[str, Any],
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Create a conversational, informative response about an image.
        
        Args:
            message: User's question/prompt
            metadata_analysis: Analysis of the image metadata
            object_analysis: Analysis of objects detected in the image
            interpretation: The query interpretation information
            conversation_history: Previous conversation messages
            
        Returns:
            str: Conversational response addressing the user's query
        """
        # Format conversation history for context
        history_text = ""
        if conversation_history:
            history_text = "Previous conversation:\n"
            for msg in conversation_history[-2:]:  # Last 2 messages for brevity
                history_text += f"{msg['role']}: {msg['content']}\n"
        
        # Determine what analyses to include based on interpretation
        requires_metadata = interpretation.get("requires_metadata", True)
        requires_object_detection = interpretation.get("requires_object_detection", True)
        
        # Prepare analyses based on requirements
        analyses = []
        if requires_metadata and metadata_analysis:
            analyses.append(f"Metadata analysis:\n{metadata_analysis}")
        
        if requires_object_detection and object_analysis:
            analyses.append(f"Object detection analysis:\n{object_analysis}")
            
        # If no analyses available, add a placeholder
        if not analyses:
            analyses.append("No analyses were performed on this image.")
        
        # Combine all analyses
        combined_analysis = "\n\n".join(analyses)
        
        # Generate a conversational response using LLM
        system_message = """
You are an expert image analyst who can interpret and explain images based on metadata and object detection.
Your response should be conversational, informative, and directly address the user's question.
You should sound like a knowledgeable but friendly assistant, not like an AI.

Important guidelines:
1. Focus on answering the user's specific question first
2. Only mention information relevant to their query
3. Be conversational but concise
4. Never mention that you're using "metadata analysis" or "object detection" explicitly
5. Just present the information naturally as if you can see and analyze the image
"""
        
        prompt = f"""
The user has uploaded an image and asked: "{message}"

Based on the analyses, here's what we know about the image:

{combined_analysis}

{history_text}

Please provide a helpful, conversational response that addresses the user's question.
"""
        
        try:
            response = await get_llm_response(
                prompt=prompt,
                system_message=system_message
            )
            return response
        except Exception as e:
            print(f"Error getting formatted response: {e}")
            return self._create_fallback_response(message, metadata_analysis, object_analysis)
    
    def _create_fallback_response(
        self, 
        message: str,
        metadata_analysis: str,
        object_analysis: str
    ) -> str:
        """Create a simple fallback response if LLM fails"""
        response = f"Here's what I found in your image:\n\n"
        
        if metadata_analysis:
            response += "📸 " + metadata_analysis.split("\n")[0] + "\n\n"
            
        if object_analysis:
            response += "🔍 " + object_analysis.split("\n")[0] + "\n\n"
            
        if not metadata_analysis and not object_analysis:
            response = "I analyzed your image but couldn't extract any useful information. Could you try uploading it again or asking a different question?"
            
        return response