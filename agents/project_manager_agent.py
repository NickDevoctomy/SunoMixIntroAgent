"""
Project Manager Agent definition.

This module defines the Project Manager agent which is responsible
for verifying and validating the research produced by the Music Researcher agent.
"""

from crewai import Agent
from langchain_openai import ChatOpenAI
import os

def create_project_manager_agent(max_revision_attempts=3, llm=None, max_rpm=2):
    """
    Create and return a project manager agent.
    
    Args:
        max_revision_attempts: Maximum number of times research can be sent back for revision (default: 3)
        llm: Language model to use for the agent (default: None, will use gpt-4o)
        max_rpm: Maximum requests per minute to control rate limiting (default: 2)
        
    Returns:
        Agent: Configured project manager agent
    """
    # Create a new LLM if one wasn't provided
    if llm is None:
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OpenAI API key not found in environment variables")
        
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7
        )
    
    # Define the project manager agent
    project_manager = Agent(
        role="Project Manager",
        goal="Ensure that research tasks are completed thoroughly and accurately",
        backstory=f"""You are a meticulous project manager with exceptional attention to detail.
        Your job is to review all research produced by the team and ensure it meets quality standards.
        You verify that all required data fields are complete, properly formatted, and contain
        substantive information. You have a reputation for catching errors and omissions that others miss.
        You will only allow up to {max_revision_attempts} revision attempts before making the final decision.
        
        When approving research, you MUST return the COMPLETE JSON data as your ENTIRE response,
        with no additional commentary. The JSON must be valid and parsable.""",
        verbose=True,
        allow_delegation=True,
        tools=[],  # No special tools needed for the manager
        llm=llm,
        max_rpm=max_rpm  # Add rate limiting to control tokens per minute
    )
    
    return project_manager 