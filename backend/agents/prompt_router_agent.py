from typing import Dict, Any, Optional, List, Tuple
import re
import os
from crewai import Agent
from langchain_groq import ChatGroq

class PromptRouterAgent:
    """
    A CrewAI-compatible Agent that classifies user prompts and routes them to
    the appropriate specialized agent.
    
    For MVP purposes, this will always route to the metadata agent, but includes
    the structure for proper intent classification and routing.
    """
    
    # Intent types
    INTENT_METADATA = "get_metadata"
    INTENT_GPS = "get_gps"
    INTENT_CAMERA = "get_camera"
    INTENT_DATE = "get_date"
    INTENT_GENERAL = "general_question"
    INTENT_UNKNOWN = "unknown"
    
    def __init__(
        self,
        name: str = "Prompt Router",
        llm: Optional[Any] = None,
        verbose: bool = False
    ):
        """
        Initialize the Prompt Router Agent.
        
        Args:
            name: Name of the agent            llm: Language model to use (defaults to ChatGroq)
            verbose: Whether to enable verbose logging
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
            role="Prompt Router",
            goal="Analyze user prompts and route them to the appropriate specialized agent",
            backstory="""You are an expert in natural language understanding and 
            intent classification. Your job is to analyze user prompts about images 
            and determine what kind of information they're looking for, then route 
            their question to the right specialized agent.""",
            verbose=verbose,
            llm=llm,
            allow_delegation=True
        )
        
        # Store configuration
        self.verbose = verbose
        self.llm = llm
        
        # Initialize intent patterns for rule-based classification
        self._initialize_intent_patterns()
    
    def _initialize_intent_patterns(self):
        """Initialize regex patterns for rule-based intent classification."""
        self.intent_patterns = {
            self.INTENT_GPS: [
                r"where was this (?:photo|image|picture) taken",
                r"location of (?:this|the) (?:photo|image|picture)",
                r"gps|coordinates|location|place|where",
                r"where is this"
            ],
            self.INTENT_CAMERA: [
                r"(?:what|which) camera",
                r"camera model|camera type",
                r"what kind of camera",
                r"what device|which device"
            ],
            self.INTENT_DATE: [
                r"when was this (?:photo|image|picture) taken",
                r"date|time|day|month|year",
                r"how old is this (?:photo|image|picture)"
            ],
            self.INTENT_METADATA: [
                r"metadata|exif|information|details|specs",
                r"tell me about this (?:photo|image|picture)",
                r"extract|analyze|examine"
            ]
        }
    
    def get_agent(self) -> Agent:
        """
        Get the CrewAI agent instance.
        
        Returns:
            The configured CrewAI Agent instance
        """
        return self.agent
        
    def classify_intent(self, prompt: str) -> Tuple[str, float]:
        """
        Classify the user's intent based on their prompt.
        
        For MVP, this uses a simple rule-based approach with regex patterns.
        In a production system, this would likely use a more sophisticated
        intent classification model.
        
        Args:
            prompt: The user's prompt/question
            
        Returns:
            Tuple of (intent_type, confidence_score)
        """
        prompt = prompt.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    # For MVP, we use a simple confidence score
                    return intent, 0.9
        
        # If no specific pattern matches, default to general metadata
        return self.INTENT_METADATA, 0.7
    
    def route_prompt(
        self,
        prompt: str,
        image_path: str
    ) -> Dict[str, Any]:
        """
        Route the user prompt to the appropriate handler.
        
        For MVP, this will always return metadata intent info,
        but includes the structure for proper routing.
        
        Args:
            prompt: The user's prompt/question
            image_path: Path to the image being referenced
            
        Returns:
            Dictionary containing the routing information
        """
        # Classify the intent
        intent, confidence = self.classify_intent(prompt)
        
        if self.verbose:
            print(f"Classified intent: {intent} (confidence: {confidence:.2f})")
        
        # For MVP, always route to metadata agent regardless of intent
        return {
            "prompt": prompt,
            "image_path": image_path,
            "intent": intent,
            "confidence": confidence,
            "route_to": "metadata_agent",  # Always route to metadata agent for MVP
            "metadata_request_type": self._get_metadata_request_type(intent)
        }
    
    def _get_metadata_request_type(self, intent: str) -> str:
        """
        Convert intent to a specific metadata request type.
        
        Args:
            intent: The classified intent
            
        Returns:
            Specific metadata request type
        """
        intent_to_request = {
            self.INTENT_GPS: "location",
            self.INTENT_CAMERA: "camera",
            self.INTENT_DATE: "datetime",
            self.INTENT_METADATA: "all"
        }
        
        return intent_to_request.get(intent, "all")
    
    def create_llm_based_classifier(self, prompt: str) -> Tuple[str, float]:
        """
        Demonstrate how to use LLM for intent classification
        (not used in MVP for efficiency, but shows the approach).
        
        Args:
            prompt: User prompt to classify
            
        Returns:
            Tuple of (intent_type, confidence_score)
        """
        # Example of how you would use the LLM for classification
        # Not used in MVP for simplicity and efficiency
        
        classification_prompt = f"""
        Classify the following user prompt into one of these categories:
        - get_metadata: General requests about image information
        - get_gps: Questions about where an image was taken
        - get_camera: Questions about what camera took the image
        - get_date: Questions about when an image was taken
        - general_question: Other questions about the image
        
        User prompt: "{prompt}"
        
        Format your response as a JSON object with 'intent' and 'confidence' keys.
        """
        
        # Example of how you would call the LLM (commented out for MVP)
        # response = self.llm.invoke(classification_prompt)
        # 
        # try:
        #     result = json.loads(response.content)
        #     return result["intent"], result["confidence"]
        # except:
        #     return self.INTENT_METADATA, 0.5
        
        # For MVP, just return metadata intent with medium confidence
        return self.INTENT_METADATA, 0.8


# Example usage:
# if __name__ == "__main__":
#     router = PromptRouterAgent(verbose=True)
#     
#     # Test with various prompts
#     test_prompts = [
#         "Where was this photo taken?",
#         "What camera was used for this picture?",
#         "When was this image taken?",
#         "Tell me about this photo's metadata"
#     ]
#     
#     for prompt in test_prompts:
#         result = router.route_prompt(prompt, "path/to/image.jpg")
#         print(f"Prompt: '{prompt}'")
#         print(f"Routing: {result}")
#         print()