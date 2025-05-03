"""
Music Researcher Agent definition.

This module defines the Music Research Specialist agent which is responsible
for gathering comprehensive information about musical artists.
"""

from crewai import Agent
from langchain_openai import ChatOpenAI
import os

# Import tools from the tools package
from tools import create_web_search_tool, create_style_sources_tool

def create_music_researcher_agent(llm=None, max_rpm=2):
    """
    Create and return a music researcher agent.
    
    Args:
        llm: Language model to use for the agent (default: None, will use gpt-4o)
        max_rpm: Maximum requests per minute to control rate limiting (default: 2)
        
    Returns:
        Agent: Configured music researcher agent
    """
    # Create a new LLM if one wasn't provided
    if llm is None:
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OpenAI API key not found in environment variables")
        
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7
        )
    
    # Get the tools from the tools package
    web_search = create_web_search_tool()
    gather_style_sources = create_style_sources_tool()
    
    # Define the music researcher agent
    music_researcher = Agent(
        role="Music Research Specialist",
        goal="Research musical artists and provide comprehensive information about their style from multiple sources",
        backstory="""You are an expert in music research with deep knowledge about different genres, 
        artists, and music history. You have access to numerous resources and can identify key 
        characteristics of an artist's sound from multiple perspectives and sources. You're known 
        for your thorough analysis that combines factual information with a wide range of critical opinions.""",
        verbose=True,
        allow_delegation=True,
        tools=[web_search, gather_style_sources],
        llm=llm,
        max_rpm=max_rpm  # Add rate limiting to control tokens per minute
    )
    
    return music_researcher 