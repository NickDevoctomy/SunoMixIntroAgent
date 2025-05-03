"""
Music Researcher Agent definition.

This module defines the Music Research Specialist agent which is responsible
for gathering comprehensive information about musical artists.
"""

from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os

# Import tools from the tools package
from tools import create_web_search_tool, create_style_sources_tool

def create_music_researcher_agent(llm=None, max_rpm=2, use_anthropic=False):
    """
    Create and return a music researcher agent.
    
    Args:
        llm: Language model to use for the agent (default: None, will create based on use_anthropic)
        max_rpm: Maximum requests per minute to control rate limiting (default: 2)
        use_anthropic: Whether to use Anthropic Claude instead of OpenAI (default: False)
        
    Returns:
        Agent: Configured music researcher agent
    """
    # Create a new LLM if one wasn't provided
    if llm is None:
        if use_anthropic:
            if "ANTHROPIC_API_KEY" not in os.environ:
                raise ValueError("Anthropic API key not found in environment variables")
            
            llm = ChatAnthropic(
                model="anthropic/claude-3-5-haiku-20241022",
                temperature=0.7,
                anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
                max_tokens=8192  # Claude 3.5 Haiku's maximum output token limit
            )
        else:
            if "OPENAI_API_KEY" not in os.environ:
                raise ValueError("OpenAI API key not found in environment variables")
            
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.7,
                # Add truncation_strategy to handle large messages
                model_kwargs={
                    "truncation_strategy": {
                        "type": "auto",
                        "max_context_length": 28000  # Keep below the 30k TPM limit
                    }
                }
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