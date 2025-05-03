"""
Music Research Application using CrewAI for artist research and analysis.

This application utilizes multiple agents to research musical artists
and gather comprehensive information about their style from various sources.
"""

import os
import json
import time
import datetime
from pathlib import Path
from dotenv import load_dotenv
from crewai import Crew, Process, LLM

# Import the context from the dedicated module
from research_context import CONTEXT

# Import agents from their separate files
from agents.music_researcher_agent import create_music_researcher_agent
from agents.project_manager_agent import create_project_manager_agent

# Import tasks from their separate files
from tasks.music_research_task import create_artist_research_task
from tasks.verification_task import create_verification_task

# Import utility functions
from utils.json_extraction import extract_json
from utils.file_operations import save_result_to_file

# Constants
MAX_REVISION_ATTEMPTS = 3  # Maximum number of times research can be sent back for revision
MAX_RPM = 2  # Maximum requests per minute to control rate limiting
MAX_CONTEXT_LENGTH = 40000  # Increased for Claude 3.5 Haiku's 45k TPM limit
USE_ANTHROPIC = True  # Set to True to use Anthropic Claude, False to use OpenAI

# Load environment variables
load_dotenv()

def main():
    """
    Main function to run the Music Research Application.
    This function handles user input, creates and runs agents and tasks,
    and processes the results.
    """
    print("\n=== Tavily Music Research Agent with URL Content Extraction ===")
    print("This tool performs web research on musical artists using the Tavily API.")
    print("It now includes the ability to fetch and extract content from the URLs returned by Tavily.")
    print(f"A project manager agent will verify research quality with up to {MAX_REVISION_ATTEMPTS} revision attempts.\n")
    print("STRICT REQUIREMENTS:")
    print("- 5 or more top tracks with both title and YouTube link")
    print("- 20+ style keywords, each with sources that include full URLs")
    print("- Properly formatted markdown with clear sections")
    print("- Complete information for all required fields\n")
    
    # Display which LLM provider is being used
    provider = "Anthropic Claude 3.5 Haiku" if USE_ANTHROPIC else "OpenAI GPT-4o"
    print(f"Using {provider} as the LLM provider\n")
    
    # Create session directories IMMEDIATELY at startup
    # This must be done before any other code that might use the context
    session_id, research_dir, output_dir = CONTEXT.create_session_directories()
    
    # Check for dependencies
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("NOTE: The BeautifulSoup library is required for full URL content extraction.")
        print("Run: pip install beautifulsoup4")
        answer = input("Would you like to continue without full URL content extraction? (y/n): ")
        if answer.lower() != 'y':
            print("Exiting. Please install BeautifulSoup and try again.")
            exit(0)
    
    # Check if the appropriate API key is available
    if USE_ANTHROPIC and "ANTHROPIC_API_KEY" not in os.environ:
        print("ERROR: Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")
        exit(1)
    elif not USE_ANTHROPIC and "OPENAI_API_KEY" not in os.environ:
        print("ERROR: OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        exit(1)
    
    # Get the artist name from user input
    artist_name = input("Enter the name of a musical artist to research: ")
    
    # Create the agents with the appropriate LLM provider
    music_researcher_agent = create_music_researcher_agent(max_rpm=MAX_RPM, use_anthropic=USE_ANTHROPIC)
    project_manager_agent = create_project_manager_agent(
        max_revision_attempts=MAX_REVISION_ATTEMPTS,
        max_rpm=MAX_RPM,
        use_anthropic=USE_ANTHROPIC
    )
    
    # Create the research and verification tasks
    research_task = create_artist_research_task(artist_name, music_researcher_agent)
    verification_task = create_verification_task(
        artist_name, 
        project_manager_agent, 
        max_revision_attempts=MAX_REVISION_ATTEMPTS
    )
    
    # Configure memory parameters appropriately for the selected LLM
    model_kwargs = {}
    if not USE_ANTHROPIC:
        # OpenAI-specific configuration
        model_kwargs = {
            "truncation_strategy": {
                "type": "auto",
                "max_context_length": MAX_CONTEXT_LENGTH
            }
        }
    
    # Create and run the crew with both agents and their tasks
    # Use the sequential process to ensure tasks run in the correct order
    crew = Crew(
        agents=[music_researcher_agent, project_manager_agent],
        tasks=[research_task, verification_task],
        verbose=True,
        process=Process.sequential,  # Use Process.sequential instead of Crew.SEQUENTIAL
        rpm=MAX_RPM,  # Apply rate limiting at the crew level as well
        model_kwargs=model_kwargs
    )
    
    # Execute the crew
    result = crew.kickoff()
    
    # Process the result
    try:
        print("\n\n" + "="*50)
        print(f"VERIFIED RESULTS FOR {artist_name}")
        print("="*50 + "\n")
        
        # Simply print the markdown result and save to file
        markdown_result = str(result)
        print(markdown_result)
        
        # Save the verified markdown to the output directory
        markdown_filename = f"{artist_name.lower().replace(' ', '_')}_profile.md"
        markdown_filepath = CONTEXT.output_dir / markdown_filename
        
        try:
            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_result)
            print(f"\nMarkdown saved to: {markdown_filepath}")
        except Exception as e:
            print(f"\nError saving markdown to file: {str(e)}")
            
    except Exception as e:
        print(f"Error processing result: {str(e)}")
        print("Raw result:")
        print(result)
        # Try to access the raw task results as a last resort
        try:
            if hasattr(result, 'task_results') and len(result.task_results) >= 1:
                print("\nAttempting to extract from first task result:")
                print(result.task_results[0])
                
                # Try to save the emergency result
                emergency_filename = f"{artist_name.lower().replace(' ', '_')}_emergency.md"
                emergency_filepath = CONTEXT.output_dir / emergency_filename
                
                with open(emergency_filepath, 'w', encoding='utf-8') as f:
                    f.write(str(result.task_results[0]))
                print(f"\nEmergency markdown saved to: {emergency_filepath}")
        except Exception as inner_e:
            print(f"Error accessing task results: {str(inner_e)}")


if __name__ == "__main__":
    main() 