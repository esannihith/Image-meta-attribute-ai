from typing import Dict, Any, Optional, List
import os
import json

from crewai import Task
from langchain_groq import ChatGroq

from agents.metadata_agent import MetadataAgent

class MetadataTask:
    """
    Task wrapper for metadata extraction and analysis using the MetadataAgent.
    
    This class provides convenient methods to create and execute tasks that
    extract metadata from images.
    """
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        verbose: bool = False
    ):
        """
        Initialize a new MetadataTask instance.
          Args:
            llm: Language model to use (defaults to ChatGroq)
            verbose: Whether to enable verbose logging
        """        # Set default LLM if none provided
        if llm is None:
            llm = ChatGroq(
                temperature=0,
                model="llama3-70b-8192",
            )
            
        # Initialize the metadata agent
        self.metadata_agent = MetadataAgent(
            llm=llm,
            verbose=verbose
        )
    
    def create_task(
        self, 
        image_path: str, 
        goal: str = "Extract all metadata from this image"
    ) -> Task:
        """
        Create a CrewAI Task for extracting metadata from an image.
        
        Args:
            image_path: Path to the image file
            goal: The user's goal or question about the image
            
        Returns:
            A configured CrewAI Task
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Create a task description based on the user goal
        description = f"""
        {goal}
        
        Image Path: {image_path}
        
        Extract all available metadata from the image, including:
        - Basic information (format, dimensions)
        - EXIF data (camera, datetime, settings)
        - GPS coordinates if available
        - Any other relevant technical information
        
        Present the information in a structured format that's easy to understand.
        """
        
        # Create the task using the metadata agent
        task = self.metadata_agent.create_metadata_task(
            image_path=image_path,
            description=description
        )
        
        return task
    
    def execute_task(
        self, 
        image_path: str, 
        goal: str = "Extract all metadata from this image"
    ) -> Dict[str, Any]:
        """
        Execute a metadata extraction task directly and return the results.
        
        This is a convenience method that creates and executes the task
        in one step, returning the structured metadata.
        
        Args:
            image_path: Path to the image file
            goal: The user's goal or question about the image
            
        Returns:
            Dictionary containing the extracted metadata
        """
        # For direct execution, we can use the agent's tool directly
        # This is more efficient than going through the CrewAI task system
        return self.metadata_agent.extract_metadata(image_path)
    
    def execute_analysis_task(
        self, 
        image_path: str, 
        goal: str = "Analyze this image and explain its metadata"
    ) -> str:
        """
        Execute a metadata analysis task and return a human-readable analysis.
        
        This method uses the full CrewAI task system to generate an analysis
        of the metadata using the LLM.
        
        Args:
            image_path: Path to the image file
            goal: The user's goal or question about the image
            
        Returns:
            String containing the analysis of the metadata
        """
        # Create the task
        task = self.create_task(image_path, goal)
        
        # Get the agent
        agent = self.metadata_agent.get_agent()
        
        # Execute the task
        result = agent.execute_task(task)
        
        return result


# Example usage:
# if __name__ == "__main__":
#     metadata_task = MetadataTask(verbose=True)
#     
#     # Example 1: Direct metadata extraction (just the structured data)
#     metadata = metadata_task.execute_task("path/to/image.jpg")
#     print(json.dumps(metadata["common"], indent=2))
#     
#     # Example 2: Analysis task (human-readable analysis through CrewAI)
#     analysis = metadata_task.execute_analysis_task(
#         "path/to/image.jpg", 
#         "Tell me when and where this photo was taken"
#     )
#     print(analysis)