from typing import Dict, Any, Optional
import os

from crewai import Agent, Task
from langchain_groq import ChatGroq

from tools.metadata_extractor import MetadataExtractorTool

class MetadataAgent:
    """
    A CrewAI Agent that extracts and analyzes metadata from images.
    
    This agent uses the MetadataExtractorTool to extract comprehensive
    metadata from images, including EXIF data, GPS coordinates, and other
    technical information.
    """
    def __init__(
        self,
        name: str = "Image Metadata Specialist",
        llm: Optional[Any] = None,
        verbose: bool = False
    ):
        """
        Initialize a new MetadataAgent instance.
        
        Args:
            name: Name of the agent
            llm: Language model to use (defaults to ChatGroq)
            verbose: Whether to enable verbose logging
        """
        # Initialize the metadata extraction tool
        self.metadata_tool = MetadataExtractorTool()
        
        # Set default LLM if none provided
        if llm is None:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",  # Need to prefix with 'groq/' to work with litellm
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.5,  # Conservative setting for accurate information extraction
                max_tokens=15000  # Maximum tokens in the completion
            )
            
        # Create the CrewAI Agent
        self.agent = Agent(
            role="Image Metadata Specialist",
            goal="Extract and analyze comprehensive metadata from images",
            backstory="""You are an expert in digital image analysis with deep 
            knowledge of image formats, EXIF data, and GPS coordinates. You can 
            extract valuable information from any image file and provide 
            meaningful insights based on the technical data.""",
            verbose=verbose,
            llm=llm,
            tools=[self.metadata_tool],
            allow_delegation=False
        )
    
    def get_agent(self) -> Agent:
        """
        Get the CrewAI agent instance.
        
        Returns:
            The configured CrewAI Agent instance
        """
        return self.agent
    
    def extract_metadata(self, image_path: str) -> Dict[str, Any]:
        """
        Extract metadata from an image directly.
        
        This is a convenience method for using the metadata tool directly
        without going through the CrewAI task system.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing the extracted metadata
        """
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}
        
        # Use the class instance of the tool
        return self.metadata_tool.extract_metadata(image_path)
    
    def create_metadata_task(self, image_path: str, description: str = None) -> Task:
        """
        Create a CrewAI Task for extracting and analyzing image metadata.
        
        Args:
            image_path: Path to the image file
            description: Optional custom description for the task
            
        Returns:
            A CrewAI Task configured for metadata extraction and analysis
        """
        if description is None:
            description = f"Extract and analyze metadata from the image at {image_path}"
        
        task = Task(
            description=description,
            expected_output="A comprehensive analysis of the image metadata including technical details, location information if available, and any other relevant insights.",
            agent=self.agent,
            context={"image_path": image_path},
            async_execution=False
        )
        
        return task

# Example usage:
# if __name__ == "__main__":
#     metadata_agent = MetadataAgent(verbose=True)
#     metadata = metadata_agent.extract_metadata("path/to/image.jpg")
#     print(metadata)
