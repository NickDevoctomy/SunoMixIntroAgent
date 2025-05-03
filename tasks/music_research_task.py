"""
Music Research Task definition.

This module defines the task for researching musical artists,
which will be assigned to the Music Research Specialist agent.
"""

from crewai import Task

def create_artist_research_task(artist_name, music_researcher_agent):
    """
    Create a task for researching a musical artist.
    
    Args:
        artist_name (str): Name of the artist to research
        music_researcher_agent: Agent to assign the task to
        
    Returns:
        Task: Configured research task
    """
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
        agent=music_researcher_agent,
        expected_output="A JSON object containing detailed information about the musical artist with style keywords from multiple sources"
    ) 