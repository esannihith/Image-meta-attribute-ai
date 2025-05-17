"""
Configuration settings for the application.
Uses Pydantic settings management with environment variables.
"""
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """Application settings defined as environment variables."""
    
    # LLM Configuration
    GROQ_API_KEY: str = Field(default="", description="API key for Groq LLM service")
    LLM_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Default LLM model to use")
    
    # Roboflow Configuration
    ROBOFLOW_API_KEY: str = Field(default="", description="API key for Roboflow object detection")
    ROBOFLOW_WORKSPACE: str = Field(default="", description="Roboflow workspace name")
    ROBOFLOW_PROJECT: str = Field(default="", description="Roboflow project name")
    ROBOFLOW_MODEL_VERSION: int = Field(default=1, description="Roboflow model version to use")
    
    # Socket.IO Configuration
    SOCKET_CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173", 
        description="Comma-separated list of allowed origins for CORS"
    )
    
    # Application Paths
    TEMP_IMAGE_DIR: str = Field(
        default="./temp_images", 
        description="Directory for temporary image storage"
    )
    
    # Agent Configuration
    ENABLE_OBJECT_DETECTION: bool = Field(
        default=False, 
        description="Whether to enable object detection (requires Roboflow)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings, using LRU cache to avoid re-reading environment variables.
    
    Returns:
        Settings: Application settings object
    """
    return Settings()
