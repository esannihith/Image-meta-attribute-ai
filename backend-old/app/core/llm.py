"""
LLM integration with Groq API.
"""
import json
import asyncio
from typing import List, Dict, Any, Optional
from groq import AsyncGroq
from app.core.config import get_settings
from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel

# Initialize settings
settings = get_settings()

# Initialize Groq client
async_client = AsyncGroq(api_key=settings.GROQ_API_KEY)

def get_llm() -> BaseChatModel:
    """
    Return a LangChain-compatible ChatGroq client for use in CrewAI agents.
    """
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=0.7,
        max_tokens=1000
    )


async def get_llm_response(
    prompt: str,
    system_message: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str:
    """
    Get a response from the LLM using the Groq API.
    
    Args:
        prompt: User prompt
        system_message: Optional system message to provide context
        messages: Optional list of previous messages for conversation context
        temperature: Temperature parameter for generation
        max_tokens: Maximum number of tokens to generate
        
    Returns:
        str: LLM response text
    """
    try:
        # Build messages list
        message_list = []
        
        # Add system message if provided
        if system_message:
            message_list.append({
                "role": "system",
                "content": system_message
            })
        
        # Add conversation history if provided
        if messages:
            message_list.extend(messages)
        
        # Add current user message
        message_list.append({
            "role": "user",
            "content": prompt
        })
        
        # Call the Groq API
        response = await async_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=message_list,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract and return the response text
        if response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "I couldn't generate a response. Please try again."
    
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        return f"Error: I encountered an issue while processing your request. {str(e)}"

async def get_structured_analysis(
    data: Dict[str, Any],
    query: str,
    system_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a structured analysis of data from the LLM.
    
    Args:
        data: Data to analyze
        query: User query about the data
        system_message: Optional system message to provide context
        
    Returns:
        Dict: Structured response with analysis
    """
    try:
        # Convert data to a JSON string
        data_str = json.dumps(data, indent=2)
        
        # Create a prompt that asks for JSON output
        prompt = f"""
Please analyze this data based on the user's query and provide a structured response.

DATA:
{data_str}

USER QUERY:
{query}

Respond with a JSON object that includes:
1. "answer": a conversational answer to the query
2. "highlights": key points from the data related to the query
3. "missing_info": any information that would be helpful but is missing from the data

The JSON must be valid and properly formatted.
"""
        
        # Default system message if none provided
        if not system_message:
            system_message = "You are an AI assistant that provides structured analysis of data. Always respond with valid JSON."
        
        # Get response from LLM
        response_text = await get_llm_response(
            prompt=prompt,
            system_message=system_message,
            temperature=0.1  # Low temperature for more deterministic/structured output
        )
        
        # Try to parse the response as JSON
        try:
            # Extract JSON if it's within delimiters
            if "```json" in response_text and "```" in response_text.split("```json", 1)[1]:
                json_str = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
                return json.loads(json_str)
            else:
                # Try parsing the whole response
                return json.loads(response_text)
                
        except json.JSONDecodeError:
            # If parsing fails, return a formatted error response
            return {
                "answer": "I was unable to analyze the data properly. The response format was incorrect.",
                "highlights": [],
                "missing_info": ["The analysis could not be completed due to a formatting error."]
            }
    
    except Exception as e:
        print(f"Error getting structured analysis: {e}")
        return {
            "answer": f"Error: I encountered an issue while analyzing the data. {str(e)}",
            "highlights": [],
            "missing_info": ["The analysis could not be completed due to an error."]
        }