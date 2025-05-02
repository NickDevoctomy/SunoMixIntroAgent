from crewai.tools import tool
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import uuid

# Load environment variables
load_dotenv()

# Get Tavily API key
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("ERROR: Tavily API key is required. Set TAVILY_API_KEY environment variable.")

# Strip whitespace which can cause auth issues
TAVILY_API_KEY = TAVILY_API_KEY.strip()

# Import the context from the dedicated module
from research_context import CONTEXT

# Function to save style sources results with GUID filename
def save_raw_style_sources(results):
    """Save raw style sources results to a file in the research directory with a GUID filename"""
    if not hasattr(CONTEXT, 'research_dir') or CONTEXT.research_dir is None:
        print("ERROR: CONTEXT.research_dir is not available, cannot save style research data")
        return False
    
    # Create a GUID-based filename
    guid = str(uuid.uuid4())
    filename = f"style_sources_{guid}.json"
    filepath = CONTEXT.research_dir / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"DEBUG: Saved raw style sources results to {filepath}")
        return True
    except Exception as e:
        print(f"DEBUG: Error saving raw style sources results: {str(e)}")
        return False

@tool("Style sources tool")
def gather_style_sources(artist_name: str, fetch_full_content: bool = False, max_urls_to_fetch: int = 3):
    """Gather multiple sources of information specifically about an artist's musical style
    using the Tavily search API to find real critics, reviews and style descriptions.
    
    Args:
        artist_name: The name of the artist to research
        fetch_full_content: Whether to fetch full content from top URLs
        max_urls_to_fetch: Maximum number of URLs to fetch full content from
    """
    try:
        # Set up the Tavily API request
        url = "https://api.tavily.com/search"
        # Use the updated Authorization format (Bearer token)
        headers = {
            "content-type": "application/json",
            "Authorization": f"Bearer {TAVILY_API_KEY}"
        }
        
        # Create a specialized query focused on music style
        style_query = f"{artist_name} music style sound characteristics reviews critics"
        
        payload = {
            "query": style_query,
            "search_depth": "advanced",
            "include_domains": [
                "pitchfork.com", 
                "rollingstone.com",
                "nme.com",
                "theguardian.com",
                "stereogum.com",
                "tinymixtapes.com",
                "thefader.com",
                "popmatters.com",
                "spin.com",
                "consequenceofsound.net",
                "musicomh.com",
                "drownedinsound.com",
                "pastemagazine.com",
                "exclaim.ca",
                "clashmusic.com",
                "thequietus.com",
                "uncut.co.uk",
                "slantmagazine.com",
                "factmag.com",
                "avclub.com"
            ],
            "max_results": 15
        }
        
        print(f"DEBUG: Sending Tavily API request for style information about: {artist_name}")
        print(f"DEBUG: Using research directory: {CONTEXT.research_dir}")
        
        # SAVE THE RAW API STYLE REQUEST IMMEDIATELY with GUID filename
        style_request_data = {
            "request": {
                "artist_name": artist_name,
                "payload": payload
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "style_request"
        }
        save_raw_style_sources(style_request_data)
        print(f"DEBUG: Saved style request data")
        
        # Make the API request
        response = requests.post(url, json=payload, headers=headers)
        
        # Print status code for debugging
        print(f"DEBUG: Tavily API response status: {response.status_code}")
        
        # SAVE THE RAW API RESPONSE IMMEDIATELY with GUID filename
        raw_response_data = {
            "request": {
                "artist_name": artist_name,
                "payload": payload
            },
            "response": {
                "status_code": response.status_code,
                "text": response.text
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "style_sources_response"
        }
        save_raw_style_sources(raw_response_data)
        print(f"DEBUG: Saved style API response data")
        
        # Provide detailed error information
        if response.status_code != 200:
            error_detail = f"Status code: {response.status_code}"
            try:
                error_json = response.json()
                error_detail += f", Response: {error_json}"
            except:
                error_detail += f", Response text: {response.text[:200]}"
                
            print(f"DEBUG: Tavily API error: {error_detail}")
            return f"Error gathering style sources: {error_detail}"
        
        response.raise_for_status()
        search_results = response.json()
        
        # Save the raw API results
        results_data = {
            "artist_name": artist_name,
            "results": search_results.get("results", []),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "style_results"
        }
        save_raw_style_sources(results_data)
        print(f"DEBUG: Saved {len(search_results.get('results', []))} style results")
        
        # Format the results
        formatted_results = f"Style information for {artist_name} from multiple sources:\n\n"
        
        # Process each result
        for i, result in enumerate(search_results.get("results", [])):
            formatted_results += f"Source: {result.get('title')}\n"
            formatted_results += f"URL: {result.get('url')}\n"
            formatted_results += f"Description: {result.get('content')}\n"
            
            # Optionally fetch full content from top URLs
            if fetch_full_content and i < max_urls_to_fetch:
                print(f"DEBUG: Fetching full content from URL: {result.get('url')}")
                full_content = CONTEXT.fetch_url_content(result.get('url'))
                formatted_results += f"\nFull Content:\n{full_content}\n"
                
                # Save the style source URL content with GUID
                style_content_data = {
                    "artist_name": artist_name,
                    "url": result.get('url'),
                    "title": result.get('title'),
                    "snippet": result.get('content'),
                    "full_content": full_content,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "type": "style_url_content"
                }
                
                # Create a GUID-based filename for the style URL content
                guid = str(uuid.uuid4())
                style_filename = f"style_url_{guid}.json"
                
                # Use the context's research directory
                if not hasattr(CONTEXT, 'research_dir') or CONTEXT.research_dir is None:
                    print("ERROR: CONTEXT.research_dir is not available, cannot save style URL content")
                else:
                    style_filepath = CONTEXT.research_dir / style_filename
                    
                    try:
                        with open(style_filepath, 'w', encoding='utf-8') as f:
                            json.dump(style_content_data, f, indent=2, ensure_ascii=False)
                        print(f"DEBUG: Saved style URL content to {style_filepath}")
                    except Exception as e:
                        print(f"DEBUG: Error saving style URL content: {str(e)}")
                
                # Add a small delay between requests to avoid rate limiting
                if i < max_urls_to_fetch - 1:
                    time.sleep(1)
                    
            formatted_results += "\n\n"
            
        print(f"DEBUG: Successfully retrieved {len(search_results.get('results', []))} style sources for {artist_name}")
        return formatted_results
    except Exception as e:
        print(f"DEBUG: Exception in gather_style_sources: {str(e)}")
        
        # Save the error information with GUID filename
        error_data = {
            "artist_name": artist_name,
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "style_sources_error"
        }
        
        # Create a GUID-based filename for the error
        guid = str(uuid.uuid4())
        error_filename = f"style_error_{guid}.json"
        
        # Use the context's research directory
        if not hasattr(CONTEXT, 'research_dir') or CONTEXT.research_dir is None:
            print("ERROR: CONTEXT.research_dir is not available, cannot save style error information")
        else:
            error_filepath = CONTEXT.research_dir / error_filename
            
            try:
                with open(error_filepath, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, indent=2, ensure_ascii=False)
                print(f"DEBUG: Saved style error information to {error_filepath}")
            except Exception as save_error:
                print(f"DEBUG: Error saving style error information: {str(save_error)}")
        
        return f"Error gathering style sources: {str(e)}" 