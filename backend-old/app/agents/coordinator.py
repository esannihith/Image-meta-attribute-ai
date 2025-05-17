"""
CrewAI coordinator that manages the multi-agent workflow.
"""
import os
import sys
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from crewai.tasks.task_output import TaskOutput
import logging

# Enable debug logging for CrewAI and coordinator
logging.basicConfig(level=logging.DEBUG)
# Ensure crewai library logs are visible
logging.getLogger('crewai').setLevel(logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

sys.path.append(str(Path(__file__).resolve().parent.parent.parent)) 

from app.core.config import get_settings
from app.core.llm import get_llm, get_llm_response
from app.services.metadata_service import get_formatted_metadata
from app.agents.metadata_agent import MetadataAgent
from app.agents.prompt_interpreter import PromptInterpreterAgent
from app.agents.vision_formatter import VisionFormatterAgent
from app.agents.object_detection_agent import ObjectDetectionAgent

# Initialize settings
settings = get_settings()

class CrewCoordinator:
    """
    Coordinator for managing the multi-agent workflow using CrewAI.
    """
    
    def __init__(
        self,
        image_path: str,
        metadata: Dict[str, Any],
        object_data: Dict[str, Any],
        message: str,
        conversation_history: List[Dict[str, str]]
    ):
        """
        Initialize the coordinator with image data and user message.
        
        Args:
            image_path: Path to the uploaded image
            metadata: Extracted metadata from the image
            object_data: Object detection results (if available)
            message: User message/query
            conversation_history: Previous conversation messages
        """
        self.image_path = image_path
        self.metadata = metadata
        self.object_data = object_data
        self.message = message
        self.conversation_history = conversation_history
        
        # Get LLM model for agents
        self.llm = get_llm()
        
        # Initialize CrewAI agents
        self._setup_agents()
    
    def _setup_agents(self):
        """Set up the CrewAI agents"""
        # Prompt Interpreter Agent
        self.interpreter_agent = Agent(
            role="Prompt Interpreter",
            goal="Understand what the user is asking about the image and determine needed analysis",
            backstory="You are an expert at understanding user queries about images and determining what information they need.",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
        
        # Metadata Agent
        self.metadata_agent = Agent(
            role="Metadata Analyst",
            goal="Extract insights from image metadata",
            backstory="You are an expert at analyzing EXIF, IPTC, and XMP data from images to provide valuable information.",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
        
        # Object Detection Agent
        self.object_detection_agent = Agent(
            role="Object Detection Specialist",
            goal="Identify objects and elements in images",
            backstory="You are an expert at detecting and describing objects in images using computer vision technology.",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
        
        # Vision Formatter Agent
        self.vision_formatter_agent = Agent(
            role="Vision Response Formatter",
            goal="Create coherent, informative responses about images",
            backstory="You synthesize information from multiple sources to create helpful, conversational responses about images.",
            verbose=True,
            llm=self.llm,
            allow_delegation=False
        )
    
    async def get_response(self) -> str:
        """
        Process the user message and return a response using the agent crew.
        
        Returns:
            str: Response from the agent crew
        """
        # Debug start of CrewAI response flow
        logging.debug(f"[CrewCoordinator] Starting get_response for message: {self.message}")
        try:
            # Create tasks
            interpret_task = self._create_interpret_task()
            metadata_task = self._create_metadata_task()
            object_detection_task = self._create_object_detection_task()
            formatter_task = self._create_formatter_task()
            
            # Create crew with sequential process (verbose)
            logging.debug("[CrewCoordinator] Initializing Crew with verbose=True and sequential process")
            crew = Crew(
                agents=[
                    self.interpreter_agent,
                    self.metadata_agent,
                    self.object_detection_agent,
                    self.vision_formatter_agent
                ],
                tasks=[
                    interpret_task,
                    metadata_task,
                    object_detection_task,
                    formatter_task
                ],
                verbose=True,
                process=Process.sequential
            )
            
            # Run the Crew kickoff synchronously in executor
            loop = asyncio.get_event_loop()
            logging.debug("[CrewCoordinator] Kickoff the crew process now...")
            result = await loop.run_in_executor(None, crew.kickoff)
            logging.debug(f"[CrewCoordinator] Crew kickoff completed with result: {result}")
            return result
        
        except Exception as e:
            logging.error(f"Error in agent coordination: {e}", exc_info=True)
            # Fallback to the simpler approach if CrewAI fails
            return await self._fallback_response()
    
    def _create_interpret_task(self) -> Task:
        """Create task for prompt interpretation"""
        # Format conversation history as a string
        history_text = ""
        if self.conversation_history:
            history_text = "Previous conversation:\n"
            for msg in self.conversation_history[-3:]:  # Last 3 messages
                history_text += f"{msg['role']}: {msg['content']}\n"
        
        return Task(
            description=f"Analyze this user query about an image: '{self.message}'\n\n{history_text}",
            expected_output="JSON with query_type, requires_metadata, requires_object_detection, specific_field, and query_summary",
            agent=self.interpreter_agent
        )
    
    def _create_metadata_task(self) -> Task:
        """Create task for metadata analysis"""
        # Get formatted metadata for the task
        formatted_metadata = get_formatted_metadata(self.metadata)
        
        return Task(
            description=f"Analyze the following image metadata to answer the user's question: '{self.message}'\n\n{formatted_metadata}",
            expected_output="Detailed analysis of the metadata highlighting relevant information for the user's query",
            agent=self.metadata_agent,
            context=[{"task": "interpretation"}]  # References previous task
        )
    
    def _create_object_detection_task(self) -> Task:
        """Create task for object detection analysis"""
        objects_str = "No object detection data available."
        if self.object_data:
            objects_str = str(self.object_data)
            
        return Task(
            description=f"Analyze objects detected in the image to answer: '{self.message}'\n\nDetected objects: {objects_str}",
            expected_output="Analysis of detected objects relevant to the user's query",
            agent=self.object_detection_agent,
            context=[{"task": "interpretation"}]  # References previous task
        )
    
    def _create_formatter_task(self) -> Task:
        """Create task for formatting the final response"""
        return Task(
            description=f"Create a helpful response to: '{self.message}'\nUse metadata analysis and object detection results to form a comprehensive answer.",
            expected_output="Conversational, informative response that directly addresses the user's question",
            agent=self.vision_formatter_agent,
            context=[
                {"task": "interpretation"},
                {"task": "metadata analysis"},
                {"task": "object detection"}
            ]
        )
    
    async def _fallback_response(self) -> str:
        """Provide a fallback response if CrewAI process fails"""
        # This is similar to your original approach but simplified
        try:
            metadata_analysis = await self._analyze_metadata()
            object_analysis = await self._analyze_objects()
            
            system_message = """
You are a helpful assistant that specializes in analyzing images based on their metadata and detected objects.
Your response should be conversational, informative, and directly address the user's question.
Use the provided metadata and object detection analyses.
"""
            
            prompt = f"""
The user has uploaded an image and asked: "{self.message}"

Based on our analysis, here's what we know:

Metadata analysis:
{metadata_analysis}

Object detection analysis:
{object_analysis}

Please provide a helpful response that addresses the user's question.
"""
            
            return await get_llm_response(
                prompt=prompt,
                system_message=system_message
            )
            
        except Exception as e:
            return f"I encountered an error analyzing your image. Please try again. Error: {str(e)}"
            
    async def _analyze_metadata(self) -> str:
        """Analyze image metadata as a fallback"""
        try:
            metadata_agent = MetadataAgent()
            return await metadata_agent.analyze_metadata(
                metadata=self.metadata,
                message=self.message
            )
        except Exception as e:
            print(f"Error in metadata analysis fallback: {e}")
            return "Could not analyze image metadata."
            
    async def _analyze_objects(self) -> str:
        """Analyze objects in the image as a fallback"""
        try:
            object_agent = ObjectDetectionAgent()
            return await object_agent.analyze_objects(
                image_path=self.image_path,
                object_data=self.object_data,
                message=self.message
            )
        except Exception as e:
            print(f"Error in object detection fallback: {e}")
            return "Could not detect objects in the image."