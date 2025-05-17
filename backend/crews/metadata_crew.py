from typing import Dict, Any, Optional, Union, List
import os
import logging

from crewai import Crew, Agent, Task
from langchain_groq import ChatGroq

from agents.metadata_agent import MetadataAgent
from tasks.metadata_tasks import MetadataTask

# Configure logging
logger = logging.getLogger(__name__)


class MetadataCrew:
    """
    A CrewAI Crew for processing image metadata.
    
    This crew combines the MetadataAgent and MetadataTask to create
    a complete workflow for extracting and analyzing image metadata.
    """
    
    def __init__(
        self,
        llm: Optional[Any] = None,
        verbose: bool = False,
        max_rpm: int = 10,
        sequential: bool = True
    ):
        """
        Initialize a new MetadataCrew instance.
          Args:
            llm: Language model to use (defaults to ChatGroq)
            verbose: Whether to enable verbose logging
            max_rpm: Maximum requests per minute to the LLM
            sequential: Whether to run tasks sequentially (True) or in parallel (False)
        """        # Set default LLM if none provided
        if llm is None:
            llm = ChatGroq(
                temperature=0,
                model="llama3-70b-8192",
            )
            
        # Initialize metadata agent and task handler
        self.metadata_agent = MetadataAgent(
            llm=llm,
            verbose=verbose
        )
        
        self.metadata_task = MetadataTask(
            llm=llm,
            verbose=verbose
        )
        
        # Store configuration
        self.verbose = verbose
        self.sequential = sequential
        self.max_rpm = max_rpm
        self.llm = llm
        
        # Initialize the crew (will be created when needed)
        self._crew = None
    
    def _create_crew(self, tasks: List[Task]) -> Crew:
        """
        Create a CrewAI Crew with the metadata agent and specified tasks.
        
        Args:
            tasks: List of tasks for the crew to execute
            
        Returns:
            Configured CrewAI Crew
        """
        return Crew(
            agents=[self.metadata_agent.get_agent()],
            tasks=tasks,
            verbose=self.verbose,
            process=self.sequential,
            max_rpm=self.max_rpm,
        )
    
    def run(
        self, 
        image_path: str, 
        goal: str = "Extract and analyze all metadata from this image"
    ) -> Union[Dict[str, Any], str]:
        """
        Run the metadata extraction and analysis workflow.
        
        This is the main entry point for the metadata processing flow.
        
        Args:
            image_path: Path to the image file
            goal: The user's goal or question about the image
            
        Returns:
            Metadata dictionary or analysis string, depending on the goal
        """
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}
        
        # Check if the goal seems to be asking for analysis vs. raw data
        analysis_keywords = ["explain", "analyze", "describe", "tell me", "what can you", "interpret"]
        is_analysis_request = any(keyword in goal.lower() for keyword in analysis_keywords)
        
        # For simple metadata extraction, bypass the crew system for efficiency
        if not is_analysis_request:
            return self.metadata_agent.extract_metadata(image_path)
        
        # For analysis requests, use the full CrewAI system
        task = self.metadata_task.create_task(image_path, goal)
        
        # Create crew with the task
        self._crew = self._create_crew([task])
        
        # Run the crew and return results
        result = self._crew.kickoff()
        return result
    
    def run_extraction(self, image_path: str) -> Dict[str, Any]:
        """
        Run just the metadata extraction without analysis.
        
        This is a convenience method that directly extracts metadata
        without using the CrewAI system.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing the extracted metadata
        """
        result =  self.metadata_agent.extract_metadata(image_path)
        return result
    
    def run_analysis(self, image_path: str, question: str) -> str:
        """
        Run a metadata analysis with a specific question.
        
        This method uses the full CrewAI system to analyze metadata
        based on a specific question.
        
        Args:
            image_path: Path to the image file
            question: Specific question about the image metadata
            
        Returns:
            String containing the analysis results
        """
        task = self.metadata_task.create_task(image_path, question)
        self._crew = self._create_crew([task])
        return self._crew.kickoff()


# Example usage:
# if __name__ == "__main__":
#     metadata_crew = MetadataCrew(verbose=True)
#     
#     # Example 1: Simple metadata extraction
#     metadata = metadata_crew.run_extraction("path/to/image.jpg")
#     print(f"Image format: {metadata['common']['format']}")
#     
#     # Example 2: Run with analysis
#     analysis = metadata_crew.run(
#         "path/to/image.jpg",
#         "Tell me when and where this photo was taken"
#     )
#     print(analysis)