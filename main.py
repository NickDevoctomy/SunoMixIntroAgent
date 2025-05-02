import os
import json
import re
import uuid
import time
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from bs4 import BeautifulSoup

# Import the context from the dedicated module
from research_context import CONTEXT

# Constants
MAX_REVISION_ATTEMPTS = 3  # Maximum number of times research can be sent back for revision

# Load environment variables
load_dotenv()

# Check if BeautifulSoup is installed, as it's required for fetching full content from URLs
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("WARNING: BeautifulSoup library not found. You'll need to install it for full URL content extraction.")
    print("Run: pip install beautifulsoup4")
    print("Continuing with limited functionality...\n")

# Import tools from their separate files - handle import errors gracefully
try:
    from web_search_tool import web_search
    from style_sources_tool import gather_style_sources
except ValueError as e:
    print(f"Error initializing tools: {str(e)}")
    print("\nTavily API key troubleshooting tips:")
    print("1. Make sure you have a .env file in the root directory with your Tavily API key")
    print("2. Check that the key format is correct: TAVILY_API_KEY=your_key_here (no quotes)")
    print("3. Verify your API key is valid in the Tavily dashboard")
    print("4. Ensure your account has sufficient credits for API calls")
    exit(1)

# Check if the OpenAI API key is available
if "OPENAI_API_KEY" not in os.environ:
    print("ERROR: OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
    exit(1)

# Initialize the OpenAI LLM
llm = ChatOpenAI(model="gpt-4o")

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
    llm=llm
)

# Define the project manager agent
project_manager = Agent(
    role="Project Manager",
    goal="Ensure that research tasks are completed thoroughly and accurately",
    backstory=f"""You are a meticulous project manager with exceptional attention to detail.
    Your job is to review all research produced by the team and ensure it meets quality standards.
    You verify that all required data fields are complete, properly formatted, and contain
    substantive information. You have a reputation for catching errors and omissions that others miss.
    You will only allow up to {MAX_REVISION_ATTEMPTS} revision attempts before making the final decision.
    
    When approving research, you MUST return the COMPLETE JSON data as your ENTIRE response,
    with no additional commentary. The JSON must be valid and parsable.""",
    verbose=True,
    allow_delegation=True,
    tools=[],  # No special tools needed for the manager
    llm=llm
)

# Define the research task
def create_artist_research_task(artist_name):
    return Task(
        description=f"""Research the musical artist named "{artist_name}" and provide information in a JSON format with the following structure:
        {{
            "name": "The artist's name",
            "members": ["List of band members with their roles e.g. 'John Doe (vocals, guitar)'"],
            "genre": ["List of music genres"],
            "years_established": "Year or time period when the artist/band was established",
            "top_tracks": [
                {{
                    "title": "Track title",
                    "youtube_link": "YouTube link to the song"
                }},
                // STRICTLY REQUIRE at least 5 top/popular tracks with both title and YouTube link
            ],
            "style_keywords": [
                {{
                    "keyword": "Style keyword",
                    "sources": [
                        {{
                            "name": "Source name (publication or website)",
                            "url": "Full URL to the source"
                        }}
                    ]
                }},
                // At least 20 style keywords with their sources
            ]
        }}
        
        The JSON must be valid and properly formatted with all the fields above. Make sure your response can be parsed with json.loads().
        Your entire response should be valid JSON and nothing else. Do not include any explanatory text.
        
        IMPORTANT REQUIREMENTS:
        1. Include EXACTLY 5 or more top tracks, each with both title and YouTube link
        2. For style_keywords, sources must include the FULL URL to verify the information
        3. Do NOT include a separate sources array - all sources should be inline within each style keyword
        4. Each style_keyword needs at least one source with full URL
        5. Include at least 20 style keywords total
        
        First, use the Web search tool with fetch_full_content=True to research the artist's general information.
        This will automatically retrieve full page content from top search results.
        
        Then use the Style sources tool with fetch_full_content=True to gather detailed information about their style from multiple sources.
        
        For the style_keywords, collect at least 20 unique descriptive terms that characterize the artist's music 
        and vocal style, making sure to link each keyword to sources with full URLs.
        
        Create realistic YouTube links for top tracks using the format https://www.youtube.com/watch?v=XXXX 
        where XXXX is a random ID. Use your knowledge to fill in any missing details.
        
        If you encounter errors with the search tools or URL fetching, include detailed error information in your response.
        """,
        agent=music_researcher,
        expected_output="A JSON object containing detailed information about the musical artist with style keywords from multiple sources"
    )

# Define the verification task
def create_verification_task(artist_name):
    return Task(
        description=f"""Review the research provided for "{artist_name}" and verify that it meets all requirements.
        
        The research should be in valid JSON format and must include ALL of the following fields:
        - name: The artist's full name
        - members: A list of band members with their roles
        - genre: A list of music genres
        - years_established: When the artist/band was formed
        - top_tracks: EXACTLY 5 OR MORE tracks, each with title and YouTube link
        - style_keywords: At least 20 unique style descriptors
          Each style_keyword must have sources with full URLs (not just publication names)
        
        Your verification must check:
        1. JSON format validity (can be parsed with json.loads())
        2. Completeness of all required fields
        3. STRICT ADHERENCE to the requirement of 5+ top tracks with both title and link
        4. Style keywords have sources with FULL URLs (not just publication names)
        5. No placeholder text or comments like "// additional sources"
        6. No separate sources array - all sources should be inline within style keywords
        7. Realistic data (no obviously fake information)
        
        Important: You can only request revisions up to {MAX_REVISION_ATTEMPTS} times. If after {MAX_REVISION_ATTEMPTS} 
        attempts the research still has issues, you should make the best final decision based on what you have.
        Keep track of how many revision attempts have been made and provide that count in your response.
        
        If ANY requirements are not met and you haven't reached {MAX_REVISION_ATTEMPTS} revision attempts, 
        delegate the task back to the Music Research Specialist with specific instructions on what needs to be 
        fixed or improved. Be explicit about what's missing or inadequate.
        
        If all requirements are met OR you've reached the maximum revision attempts, return the COMPLETE JSON data 
        in a format that can be parsed with json.loads(). DO NOT include any intro text like "Here's the verified JSON:" 
        or thoughts about your review process - ONLY return the valid JSON object.
        
        Your response should either be:
        1. A delegation instruction with specific improvements needed and the current revision attempt count, OR
        2. The complete JSON data exactly as received or with minor fixes (if at max revisions)
        
        IMPORTANT INSTRUCTIONS (FOLLOW THESE EXACTLY):
        - You are limited to requesting a maximum of {MAX_REVISION_ATTEMPTS} revisions
        - Track the revision count in your responses
        - When approving research, you MUST return the COMPLETE JSON data as your ENTIRE response
        - DO NOT output your thoughts, reasoning, or decision process
        - DO NOT include any markdown formatting, just the raw JSON
        - ONLY the JSON data should be in your output when approving
        """,
        agent=project_manager,
        expected_output="Either raw JSON data or specific instructions for improvements"
    )

def main():
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
    
    # Get the artist name from user input
    artist_name = input("Enter the name of a musical artist to research: ")
    
    # Create the research and verification tasks
    research_task = create_artist_research_task(artist_name)
    verification_task = create_verification_task(artist_name)
    
    # Create and run the crew with both agents and their tasks
    # Use the sequential process to ensure tasks run in the correct order
    crew = Crew(
        agents=[music_researcher, project_manager],
        tasks=[research_task, verification_task],
        verbose=True,
        process=Process.sequential  # Use Process.sequential instead of Crew.SEQUENTIAL
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
            output_filename = f"{artist_name.replace(' ', '_').lower()}_verified.json"
            output_filepath = CONTEXT.output_dir / output_filename
            
            try:
                with open(output_filepath, 'w', encoding='utf-8') as f:
                    json.dump(research_json, f, indent=2, ensure_ascii=False)
                print(f"\nVerified results saved to: {output_filepath}")
            except Exception as save_error:
                print(f"\nError saving verified results: {str(save_error)}")
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
            json_data = find_json_in_text(raw_output)
            if json_data:
                print(json.dumps(json_data, indent=2))
                
                # Save the verified JSON to the output directory
                output_filename = f"{artist_name.replace(' ', '_').lower()}_verified.json"
                output_filepath = CONTEXT.output_dir / output_filename
                
                try:
                    with open(output_filepath, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    print(f"\nVerified results saved to: {output_filepath}")
                except Exception as save_error:
                    print(f"\nError saving verified results: {str(save_error)}")
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
                        output_filename = f"{artist_name.replace(' ', '_').lower()}_unverified.json"
                        output_filepath = CONTEXT.output_dir / output_filename
                        
                        try:
                            with open(output_filepath, 'w', encoding='utf-8') as f:
                                json.dump(original_json, f, indent=2, ensure_ascii=False)
                            print(f"\nUnverified results saved to: {output_filepath}")
                        except Exception as save_error:
                            print(f"\nError saving unverified results: {str(save_error)}")
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
                    output_filename = f"{artist_name.replace(' ', '_').lower()}_emergency.json"
                    output_filepath = CONTEXT.output_dir / output_filename
                    
                    try:
                        with open(output_filepath, 'w', encoding='utf-8') as f:
                            json.dump(original_json, f, indent=2, ensure_ascii=False)
                        print(f"\nEmergency results saved to: {output_filepath}")
                    except Exception as save_error:
                        print(f"\nError saving emergency results: {str(save_error)}")
        except:
            pass


def find_json_in_text(text):
    """More aggressive JSON extraction from text."""
    try:
        # Try to find opening and closing braces
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            
            # Try to parse it directly
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try basic cleanup on common issues
                cleaned_str = json_str.replace("// STRICTLY REQUIRE", "").replace("// At least 20", "")
                cleaned_str = re.sub(r'//.*?\n', '\n', cleaned_str)  # Remove any // comments
                
                try:
                    return json.loads(cleaned_str)
                except:
                    # If still failing, try a more aggressive regex approach
                    import re
                    json_pattern = r'({[\s\S]*})'
                    matches = re.findall(json_pattern, text)
                    
                    for potential_json in matches:
                        # Clean up each potential match
                        cleaned_json = re.sub(r'//.*?[\r\n]', '\n', potential_json)  # Remove comments
                        try:
                            return json.loads(cleaned_json)
                        except:
                            continue
                    
                    # Try one more approach - look for code blocks that might contain JSON
                    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
                    code_matches = re.findall(code_block_pattern, text)
                    
                    for code_block in code_matches:
                        if code_block.strip().startswith('{') and code_block.strip().endswith('}'):
                            cleaned_block = re.sub(r'//.*?[\r\n]', '\n', code_block)  # Remove comments
                            try:
                                return json.loads(cleaned_block)
                            except:
                                continue
    except:
        pass
        
    return None

def parse_json_from_agent_output(raw_output):
    """Parse JSON from agent output text and try multiple approaches."""
    # Try parsing the whole thing as JSON first
    try:
        return json.loads(raw_output)
    except:
        pass
    
    # Try to extract JSON from markdown code blocks
    try:
        code_block_pattern = r'```(?:json)?(.+?)```'
        matches = re.findall(code_block_pattern, raw_output, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match.strip())
            except:
                continue
    except:
        pass
    
    # Try to find JSON objects using regex
    try:
        json_pattern = r'({.+})'
        matches = re.findall(json_pattern, raw_output, re.DOTALL)
        
        for match in matches:
            try:
                # Clean up the match, removing comments
                cleaned_match = re.sub(r'//.*?[\r\n]', '\n', match)
                return json.loads(cleaned_match)
            except:
                continue
    except:
        pass
    
    # Try to find JSON between braces
    try:
        start_idx = raw_output.find('{')
        end_idx = raw_output.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_text = raw_output[start_idx:end_idx]
            
            # Clean up the JSON text
            cleaned_json = re.sub(r'//.*?[\r\n]', '\n', json_text)
            
            try:
                return json.loads(cleaned_json)
            except:
                pass
    except:
        pass
    
    return None

def extract_json(text):
    """Extract and parse JSON from text using multiple approaches."""
    try:
        # If the result is already a proper object, try to access the output
        if hasattr(text, 'output'):
            return extract_json(text.output)
        if hasattr(text, 'raw_output'):
            return extract_json(text.raw_output)
        if hasattr(text, 'result'):
            return extract_json(text.result)
        
        # If we have an outputs list, try the first element
        if hasattr(text, 'outputs') and len(text.outputs) > 0:
            return extract_json(text.outputs[0])
        
        # If it's a task_results list, try each result
        if hasattr(text, 'task_results') and len(text.task_results) > 0:
            for result in text.task_results:
                json_data = extract_json(result)
                if json_data:
                    return json_data
        
        # If it's a string, try parsing it
        if isinstance(text, str):
            # First try direct JSON parsing
            try:
                return json.loads(text)
            except:
                # If that fails, try our custom JSON extraction methods
                json_data = find_json_in_text(text)
                if json_data:
                    return json_data
                    
                # If still no result, try the more advanced approach
                return parse_json_from_agent_output(text)
    except:
        pass
    
    return None


if __name__ == "__main__":
    main() 