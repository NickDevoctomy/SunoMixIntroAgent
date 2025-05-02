from crewai.tools import tool
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import uuid

# Import the context from the dedicated module
from research_context import CONTEXT

# Load environment variables
load_dotenv()

# Get Tavily API key
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("ERROR: Tavily API key is required. Set TAVILY_API_KEY environment variable.")

# Debug key format - print first/last few characters without exposing the full key
print(f"DEBUG: Tavily API key format check - Length: {len(TAVILY_API_KEY)}, Starts with: {TAVILY_API_KEY[:4]}..., Ends with: ...{TAVILY_API_KEY[-4:]}")
# Strip whitespace which can cause auth issues
TAVILY_API_KEY = TAVILY_API_KEY.strip()

# Function to save search results with GUID filename
def save_raw_web_search(results):
    """Save raw web search results to a file in the research directory with a GUID filename"""
    if not hasattr(CONTEXT, 'research_dir') or CONTEXT.research_dir is None:
        print("ERROR: CONTEXT.research_dir is not available, cannot save research data")
        return False
    
    # Create a GUID-based filename
    guid = str(uuid.uuid4())
    filename = f"web_search_{guid}.json"
    filepath = CONTEXT.research_dir / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"DEBUG: Saved raw web search results to {filepath}")
        return True
    except Exception as e:
        print(f"DEBUG: Error saving raw web search results: {str(e)}")
        return False

@tool("Web search tool")
def web_search(query: str, fetch_full_content: bool = False, max_urls_to_fetch: int = 2):
    """Search the web for information about musical artists including biography, 
    band members, genre, years active, and popular tracks using Tavily search API.
    
    Args:
        query: The search query to use
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
        
        # Simplified payload with only required parameters
        payload = {
            "query": f"{query} band music biography members genre tracks",
            "search_depth": "basic",  # Use basic to avoid higher credit usage
            "max_results": 5
        }
        
        print(f"DEBUG: Sending Tavily API request for: {query}")
        print(f"DEBUG: Using research directory: {CONTEXT.research_dir}")
        
        # SAVE THE RAW API REQUEST IMMEDIATELY with GUID filename
        request_data = {
            "request": {
                "query": query,
                "payload": payload
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "tavily_request"
        }
        save_raw_web_search(request_data)
        print(f"DEBUG: Saved Tavily request data")
        
        # Make the API request
        response = requests.post(url, json=payload, headers=headers)
        
        # Print status code for debugging
        print(f"DEBUG: Tavily API response status: {response.status_code}")
        
        # SAVE THE RAW API RESPONSE IMMEDIATELY with GUID filename
        raw_response_data = {
            "request": {
                "query": query,
                "payload": payload
            },
            "response": {
                "status_code": response.status_code,
                "text": response.text
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "tavily_response"
        }
        save_raw_web_search(raw_response_data)
        print(f"DEBUG: Saved Tavily API response data")
        
        # Provide detailed error information
        if response.status_code != 200:
            error_detail = f"Status code: {response.status_code}"
            try:
                error_json = response.json()
                error_detail += f", Response: {error_json}"
            except:
                error_detail += f", Response text: {response.text[:200]}"
                
            print(f"DEBUG: Tavily API error: {error_detail}")
            return f"Error searching the web: {error_detail}"
            
        response.raise_for_status()
        search_results = response.json()
        
        # Check if we have any results
        if not search_results.get("results"):
            print("DEBUG: Tavily API returned no results")
            return f"No search results found for {query}. Please try a different query."
        
        # Save the search results with GUID filename
        results_data = {
            "query": query,
            "results": search_results.get("results", []),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "tavily_results"
        }
        save_raw_web_search(results_data)
        print(f"DEBUG: Saved {len(search_results.get('results', []))} search results")
        
        # Format the results
        formatted_results = f"Search results for {query}:\n\n"
        
        # Process each result
        for i, result in enumerate(search_results.get("results", [])):
            formatted_results += f"Title: {result.get('title')}\n"
            formatted_results += f"URL: {result.get('url')}\n"
            
            # Add the snippet content from Tavily
            formatted_results += f"Content: {result.get('content')}\n"
            
            # Optionally fetch full content from top URLs
            if fetch_full_content and i < max_urls_to_fetch:
                print(f"DEBUG: Fetching full content from URL: {result.get('url')}")
                full_content = CONTEXT.fetch_url_content(result.get('url'))
                formatted_results += f"\nFull Content:\n{full_content}\n"
                
                # Save the full content to a separate file with GUID
                url_content_data = {
                    "url": result.get('url'),
                    "title": result.get('title'),
                    "snippet": result.get('content'),
                    "full_content": full_content,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "type": "url_content"
                }
                
                # Create a GUID-based filename for the URL content
                guid = str(uuid.uuid4())
                url_filename = f"url_content_{guid}.json"
                
                # Use the context's research directory
                if not hasattr(CONTEXT, 'research_dir') or CONTEXT.research_dir is None:
                    print("ERROR: CONTEXT.research_dir is not available, cannot save URL content")
                else:
                    url_filepath = CONTEXT.research_dir / url_filename
                    
                    try:
                        with open(url_filepath, 'w', encoding='utf-8') as f:
                            json.dump(url_content_data, f, indent=2, ensure_ascii=False)
                        print(f"DEBUG: Saved URL content to {url_filepath}")
                    except Exception as e:
                        print(f"DEBUG: Error saving URL content: {str(e)}")
                
                # Add a small delay between requests to avoid rate limiting
                if i < max_urls_to_fetch - 1:
                    time.sleep(1)
                    
            formatted_results += "\n\n"
        
        print(f"DEBUG: Successfully retrieved {len(search_results.get('results', []))} results from Tavily")
        return formatted_results
    except Exception as e:
        print(f"DEBUG: Exception in web_search: {str(e)}")
        
        # Save the error information with GUID filename
        error_data = {
            "query": query,
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": "web_search_error"
        }
        
        # Create a GUID-based filename for the error
        guid = str(uuid.uuid4())
        error_filename = f"web_search_error_{guid}.json"
        
        # Use the context's research directory
        if not hasattr(CONTEXT, 'research_dir') or CONTEXT.research_dir is None:
            print("ERROR: CONTEXT.research_dir is not available, cannot save error information")
        else:
            error_filepath = CONTEXT.research_dir / error_filename
            
            try:
                with open(error_filepath, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, indent=2, ensure_ascii=False)
                print(f"DEBUG: Saved error information to {error_filepath}")
            except Exception as save_error:
                print(f"DEBUG: Error saving error information: {str(save_error)}")
        
        return f"Error searching the web: {str(e)}" 