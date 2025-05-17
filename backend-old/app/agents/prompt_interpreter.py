"""
Prompt Interpreter Agent for understanding user queries.
"""
from typing import Dict, Any, List
import json
import re

from app.core.config import get_settings
from app.core.llm import get_llm_response

# Get application settings
settings = get_settings()

class PromptInterpreterAgent:
    """
    Agent for interpreting user prompts about images and determining what information is needed.
    """
    def __init__(self):
        """Initialize the prompt interpreter agent."""
        self.settings = settings
        
        # Common query patterns for metadata
        self.metadata_patterns = {
            "camera": r"camera|device|phone|shot with|taken with|equipment",
            "location": r"where|location|place|geo|gps|coordinates",
            "time": r"when|date|time|year|month|day|hour",
            "settings": r"settings|iso|aperture|shutter|exposure|f-stop|focal length",
            "general_metadata": r"metadata|exif|info|data|details"
        }
        
        # Common query patterns for object detection
        self.object_patterns = {
            "objects": r"object|thing|item|detect|identify|recognize|spot|see",
            "people": r"person|people|human|man|woman|child|face|crowd",
            "animals": r"animal|dog|cat|bird|pet|wildlife",
            "vehicles": r"car|vehicle|truck|bike|motorcycle|transportation",
            "count": r"how many|count|number of"
        }
    
    async def interpret_query(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Interpret what the user is asking about the image.
        
        Args:
            message: The user's question/prompt
            conversation_history: Previous conversation messages
            
        Returns:
            Dict: Information about the query, including what type of analysis is needed
        """
        # Simple rule-based interpretation for common queries
        requires_metadata = self._check_pattern_match(message, self.metadata_patterns)
        requires_object_detection = self._check_pattern_match(message, self.object_patterns)
        
        # Default to both if we can't determine or if the message is very simple
        if not requires_metadata and not requires_object_detection:
            simple_queries = ["what's in this", "what is this", "tell me about", "describe", "analyze"]
            if any(q in message.lower() for q in simple_queries) or len(message) < 20:
                requires_metadata = True
                requires_object_detection = True
            
        # For more complex queries, use LLM to interpret
        if len(message) > 20 or conversation_history:
            try:
                llm_interpretation = await self._get_llm_interpretation(message, conversation_history)
                
                # Override rule-based decisions with LLM if more confident
                if "requires_metadata" in llm_interpretation:
                    requires_metadata = llm_interpretation["requires_metadata"]
                if "requires_object_detection" in llm_interpretation:
                    requires_object_detection = llm_interpretation["requires_object_detection"]
                    
                # Return the LLM interpretation with our additions
                llm_interpretation.update({
                    "requires_metadata": requires_metadata,
                    "requires_object_detection": requires_object_detection
                })
                
                return llm_interpretation
                    
            except Exception as e:
                print(f"Error getting LLM interpretation: {e}")
                # Continue with rule-based interpretation if LLM fails
        
        # Return simple interpretation
        return {
            "query_type": "general" if (requires_metadata and requires_object_detection) else 
                          "metadata" if requires_metadata else 
                          "object_detection",
            "requires_metadata": requires_metadata,
            "requires_object_detection": requires_object_detection,
            "specific_field": self._get_specific_field(message),
            "query_summary": f"Query about {'metadata and objects' if (requires_metadata and requires_object_detection) else 'metadata' if requires_metadata else 'objects'}"
        }
    
    def _check_pattern_match(self, message: str, patterns: Dict[str, str]) -> bool:
        """Check if the message matches any patterns in the dictionary"""
        message = message.lower()
        
        for category, pattern in patterns.items():
            if re.search(pattern, message):
                return True
        
        return False
    
    def _get_specific_field(self, message: str) -> str:
        """Determine if the query is looking for a specific field of information"""
        message = message.lower()
        
        # Check for specific metadata fields
        for category, pattern in self.metadata_patterns.items():
            if re.search(pattern, message):
                return category
        
        # Check for specific object types
        for category, pattern in self.object_patterns.items():
            if re.search(pattern, message):
                return category
        
        return "general"
    
    async def _get_llm_interpretation(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to interpret the query in more detail.
        
        Args:
            message: User message
            conversation_history: Previous conversation
            
        Returns:
            Dict: Detailed interpretation of the query
        """
        # Format conversation history
        history_text = ""
        if conversation_history:
            history_text = "\nPrevious conversation context (most recent first):\n"
            for msg in conversation_history[-3:]:  # Last 3 messages
                history_text += f"{msg['role']}: {msg['content']}\n"
        
        system_message = """
You are an expert at analyzing queries about images. Your job is to determine what the user wants to know from an image.
Output a JSON object with the following fields:
- query_type: One of "metadata", "object_detection", or "general"
- requires_metadata: Boolean indicating if metadata analysis is needed (camera info, location, etc.)
- requires_object_detection: Boolean indicating if object detection is needed
- specific_field: What specific aspect the user is asking about (e.g., "camera", "location", "objects", "people", etc.)
- query_summary: A brief summary of what the user is asking about
"""
        
        prompt = f"""
Analyze this query about an image: "{message}"{history_text}

Output a JSON object with your analysis.
"""
        
        try:
            response = await get_llm_response(
                prompt=prompt,
                system_message=system_message
            )
            
            # Extract JSON from response
            try:
                # Try to parse the entire response as JSON
                interpretation = json.loads(response)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the response
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    interpretation = json.loads(match.group(0))
                else:
                    # Fallback to simple interpretation
                    interpretation = {
                        "query_type": "general",
                        "requires_metadata": True,
                        "requires_object_detection": True,
                        "specific_field": "general",
                        "query_summary": "General query about the image"
                    }
            
            return interpretation
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            raise