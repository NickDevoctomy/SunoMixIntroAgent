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
from crewai import Crew, Process

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
    print("- No separate sources array - sources included inline with each keyword")
    print("- Complete information for all required fields\n")
    
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
    
    # Check if the OpenAI API key is available
    if "OPENAI_API_KEY" not in os.environ:
        print("ERROR: OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        exit(1)
    
    # Get the artist name from user input
    artist_name = input("Enter the name of a musical artist to research: ")
    
    # Create the agents
    music_researcher_agent = create_music_researcher_agent(max_rpm=MAX_RPM)
    project_manager_agent = create_project_manager_agent(
        max_revision_attempts=MAX_REVISION_ATTEMPTS,
        max_rpm=MAX_RPM
    )
    
    # Create the research and verification tasks
    research_task = create_artist_research_task(artist_name, music_researcher_agent)
    verification_task = create_verification_task(
        artist_name, 
        project_manager_agent, 
        max_revision_attempts=MAX_REVISION_ATTEMPTS
    )
    
    # Create and run the crew with both agents and their tasks
    # Use the sequential process to ensure tasks run in the correct order
    crew = Crew(
        agents=[music_researcher_agent, project_manager_agent],
        tasks=[research_task, verification_task],
        verbose=True,
        process=Process.sequential,  # Use Process.sequential instead of Crew.SEQUENTIAL
        rpm=MAX_RPM  # Apply rate limiting at the crew level as well
    )
    
    # Execute the crew
    result = crew.kickoff()
    
    # Process the result
    try:
        print("\n\n" + "="*50)
        print(f"VERIFIED RESULTS FOR {artist_name}")
        print("="*50 + "\n")
        
        # Extract and parse research result
        research_json = extract_json(result)
        if research_json:
            print(json.dumps(research_json, indent=2))
            
            # Save the verified JSON to the output directory
            save_result_to_file(research_json, artist_name, "verified", CONTEXT.output_dir)
        else:
            # Attempt to find JSON in the raw output
            print("Attempting to extract JSON from raw output...")
            # First try to get raw output
            raw_output = ""
            if hasattr(result, 'raw_output'):
                raw_output = result.raw_output
            elif hasattr(result, 'output'):
                raw_output = result.output
            else:
                raw_output = str(result)
                
            # Try to find JSON in the raw text
            json_data = extract_json(raw_output)
            if json_data:
                print(json.dumps(json_data, indent=2))
                
                # Save the verified JSON to the output directory
                save_result_to_file(json_data, artist_name, "verified", CONTEXT.output_dir)
            else:
                # If still no JSON, try to get the original research results from the first task
                print("No JSON found in Project Manager output, attempting to retrieve original research...")
                
                if hasattr(result, 'task_results') and len(result.task_results) >= 1:
                    original_research = result.task_results[0]
                    original_json = extract_json(original_research)
                    
                    if original_json:
                        print("UNVERIFIED RESEARCH RESULTS (Project Manager did not verify):")
                        print(json.dumps(original_json, indent=2))
                        
                        # Save the unverified JSON as a fallback
                        save_result_to_file(original_json, artist_name, "unverified", CONTEXT.output_dir)
                    else:
                        print("CREW RESULTS (no valid JSON found):")
                        print(raw_output)
                else:
                    print("CREW RESULTS (no valid JSON found):")
                    print(raw_output)
        
    except Exception as e:
        print(f"Error processing result: {str(e)}")
        print("Raw result:")
        print(result)
        # Try to access the raw task results as a last resort
        try:
            if hasattr(result, 'task_results') and len(result.task_results) >= 1:
                print("\nAttempting to extract from first task result:")
                original_json = extract_json(result.task_results[0])
                if original_json:
                    print(json.dumps(original_json, indent=2))
                    
                    # Save the emergency fallback JSON
                    save_result_to_file(original_json, artist_name, "emergency", CONTEXT.output_dir)
        except:
            pass


if __name__ == "__main__":
    main() 