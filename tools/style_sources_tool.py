"""
Style Sources Tool definition.

This module defines tools for gathering style information about musical artists
from multiple sources.
"""

from crewai.tools import tool
import requests
import json
import time
import uuid
import os
from bs4 import BeautifulSoup 
from dotenv import load_dotenv

# Import the context from the dedicated module
from research_context import CONTEXT

# Load environment variables
load_dotenv()

def create_style_sources_tool():
    """
    Create and return a style sources tool.
    
    Returns:
        Tool: Configured style sources tool
    """
    # Get Tavily API key
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    if not TAVILY_API_KEY:
        raise ValueError("ERROR: Tavily API key is required. Set TAVILY_API_KEY environment variable.")
        
    # Strip whitespace which can cause auth issues
    TAVILY_API_KEY = TAVILY_API_KEY.strip()
    
    # Function to save search results with GUID filename
    def save_style_sources_data(results):
        """Save style sources data to a file in the research directory with a GUID filename"""
        if not hasattr(CONTEXT, 'research_dir') or CONTEXT.research_dir is None:
            print("ERROR: CONTEXT.research_dir is not available, cannot save research data")
            return False
        
        # Create a GUID-based filename
        guid = str(uuid.uuid4())
        filename = f"style_sources_{guid}.json"
        filepath = CONTEXT.research_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"DEBUG: Saved style sources data to {filepath}")
            return True
        except Exception as e:
            print(f"DEBUG: Error saving style sources data: {str(e)}")
            return False

    @tool("Style sources gathering tool")
    def gather_style_sources(artist_name: str, fetch_full_content: bool = False, max_urls_to_fetch: int = 3):
        """Gather detailed information about an artist's musical style from multiple sources 
        using focused web searches for style, sound characteristics, and influences. 
        This tool is specifically designed to collect style keywords with their sources.
        
        Args:
            artist_name: Name of the musical artist to gather style information about
            fetch_full_content: Whether to fetch full page content from URLs
            max_urls_to_fetch: Maximum number of URLs to fetch full content from
        """
        try:
            # List of search queries focused on style information
            style_queries = [
                f"{artist_name} music style characteristics",
                f"{artist_name} sound description review",
                f"{artist_name} musical influences and genre",
                f"{artist_name} vocal style music critics",
                f"{artist_name} production sound signature"
            ]
            
            all_results = []
            all_sources = []
            
            # Make multiple searches to gather diverse information
            for query in style_queries:
                # Set up the Tavily API request
                url = "https://api.tavily.com/search"
                headers = {
                    "content-type": "application/json",
                    "Authorization": f"Bearer {TAVILY_API_KEY}"
                }
                
                payload = {
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 3  # Limit to 3 results per query to avoid overwhelming
                }
                
                print(f"DEBUG: Sending style sources API request for query: {query}")
                
                # Save the raw API request
                request_data = {
                    "request": {
                        "query": query,
                        "payload": payload
                    },
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "type": "style_sources_request"
                }
                save_style_sources_data(request_data)
                
                # Make the API request
                response = requests.post(url, json=payload, headers=headers)
                
                # Print status code for debugging
                print(f"DEBUG: Tavily API response status for style search: {response.status_code}")
                
                # Save the raw API response
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
                    "type": "style_sources_response"
                }
                save_style_sources_data(raw_response_data)
                
                # Handle errors
                if response.status_code != 200:
                    error_detail = f"Status code: {response.status_code}"
                    try:
                        error_json = response.json()
                        error_detail += f", Response: {error_json}"
                    except:
                        error_detail += f", Response text: {response.text[:200]}"
                        
                    print(f"DEBUG: Tavily API error for style sources: {error_detail}")
                    continue  # Continue with next query even if this one failed
                
                # Process successful response
                search_results = response.json()
                
                # Save the search results
                results_data = {
                    "query": query,
                    "results": search_results.get("results", []),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "type": "style_sources_results"
                }
                save_style_sources_data(results_data)
                
                # Process the results
                for result in search_results.get("results", []):
                    # Skip if we've already seen this URL
                    if result.get("url") in [source.get("url") for source in all_sources]:
                        continue
                        
                    current_result = {
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "content": result.get("content")
                    }
                    
                    all_results.append(current_result)
                    all_sources.append({
                        "name": result.get("title"),
                        "url": result.get("url")
                    })
                
                # Fetch full content if requested
                if fetch_full_content:
                    for i, result in enumerate(search_results.get("results", [])):
                        # Skip if we've already seen this URL or reached max limit
                        if i >= max_urls_to_fetch or result.get("url") in [source.get("full_content_url") for source in all_sources if "full_content_url" in source]:
                            continue
                            
                        print(f"DEBUG: Fetching full content from URL for style: {result.get('url')}")
                        full_content = CONTEXT.fetch_url_content(result.get("url"))
                        
                        # Save full content to a separate file
                        url_content_data = {
                            "url": result.get("url"),
                            "title": result.get("title"),
                            "snippet": result.get("content"),
                            "full_content": full_content,
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                            "type": "style_url_content"
                        }
                        
                        guid = str(uuid.uuid4())
                        url_filename = f"style_url_content_{guid}.json"
                        
                        if hasattr(CONTEXT, 'research_dir') and CONTEXT.research_dir is not None:
                            url_filepath = CONTEXT.research_dir / url_filename
                            try:
                                with open(url_filepath, 'w', encoding='utf-8') as f:
                                    json.dump(url_content_data, f, indent=2, ensure_ascii=False)
                                print(f"DEBUG: Saved style URL content to {url_filepath}")
                            except Exception as e:
                                print(f"DEBUG: Error saving style URL content: {str(e)}")
                        
                        # Add the full content to the corresponding result
                        for r in all_results:
                            if r["url"] == result.get("url"):
                                r["full_content"] = full_content
                                break
                
                # Add a delay between queries to avoid rate limiting
                if query != style_queries[-1]:
                    time.sleep(2)
            
            # Format the output for the agent
            formatted_output = f"Style information for {artist_name} from multiple sources:\n\n"
            
            for i, result in enumerate(all_results):
                formatted_output += f"Source {i+1}: {result.get('title')}\n"
                formatted_output += f"URL: {result.get('url')}\n"
                formatted_output += f"Content: {result.get('content')}\n"
                
                if "full_content" in result:
                    formatted_output += f"\nFull Content:\n{result.get('full_content')}\n"
                    
                formatted_output += "\n---\n\n"
            
            # Add a structured summary of all sources
            formatted_output += f"\nSummary of sources for {artist_name} style information:\n"
            for i, source in enumerate(all_sources):
                formatted_output += f"{i+1}. {source.get('name')} - {source.get('url')}\n"
                
            # Save the final formatted result
            final_result = {
                "artist_name": artist_name,
                "sources": all_sources,
                "results": all_results,
                "formatted_output": formatted_output,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "type": "style_sources_formatted"
            }
            save_style_sources_data(final_result)
            
            print(f"DEBUG: Successfully gathered style information from {len(all_sources)} sources")
            return formatted_output
            
        except Exception as e:
            error_message = f"Error gathering style sources: {str(e)}"
            print(f"DEBUG: {error_message}")
            
            # Save error information
            error_data = {
                "artist_name": artist_name,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "type": "style_sources_error"
            }
            save_style_sources_data(error_data)
            
            return error_message
    
    return gather_style_sources 