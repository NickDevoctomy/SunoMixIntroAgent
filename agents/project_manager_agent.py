"""
Project Manager Agent definition.

This module defines the Project Manager agent which is responsible
for verifying and validating the research produced by the Music Researcher agent.
"""

from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os

def create_project_manager_agent(max_revision_attempts=3, llm=None, max_rpm=2, use_anthropic=False):
    """
    Create and return a project manager agent.
    
    Args:
        max_revision_attempts: Maximum number of times research can be sent back for revision (default: 3)
        llm: Language model to use for the agent (default: None, will create based on use_anthropic)
        max_rpm: Maximum requests per minute to control rate limiting (default: 2)
        use_anthropic: Whether to use Anthropic Claude instead of OpenAI (default: False)
        
    Returns:
        Agent: Configured project manager agent
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
                max_tokens=45000  # Claude 3.5 Haiku has a higher TPM limit (45k)
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