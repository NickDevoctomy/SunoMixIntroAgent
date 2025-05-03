"""
Music Generator Agent definition.

This module defines the Music Generator agent which is responsible
for generating music based on an artist's style using the Suno API.
"""

from crewai import Agent
from langchain_openai import ChatOpenAI
import os

# Import tools from the tools package
from tools import create_music_generation_tool

def create_music_generator_agent(llm=None, max_rpm=2):
    """
    Create and return a music generator agent.
    
    This agent is responsible for analyzing artist data and generating
    music in a similar style using the Suno API.
    
    Args:
        llm: Language model to use for the agent (default: None, will use gpt-4o)
        max_rpm: Maximum requests per minute to control rate limiting (default: 2)
        
    Returns:
        Agent: Configured music generator agent
    """
    try:
        # Get the tools from the tools package
        generate_music, download_music = create_music_generation_tool()
    except Exception as e:
        print(f"Music generator agent cannot be created: {str(e)}")
        return None
    
    # Create a new LLM if one wasn't provided
    if llm is None:
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OpenAI API key not found in environment variables")
        
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7
        )
    
    # Define the music generator agent
    music_generator = Agent(
        role="Music Generator",
        goal="Generate original music in the style of a researched artist using AI",
        backstory="""You are an expert music producer and composer with a deep understanding of musical styles 
        and genres. You can analyze an artist's style characteristics and create original music that captures 
        their essence while being a unique composition. You have extensive knowledge of music theory, 
        composition techniques, and production styles across various genres.""",
        verbose=True,
        allow_delegation=False,
        tools=[generate_music, download_music],
        llm=llm,
        max_rpm=max_rpm
    )
    
    return music_generator 