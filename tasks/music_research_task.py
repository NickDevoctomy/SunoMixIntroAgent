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
        description=f"""Research the musical artist named "{artist_name}" and provide comprehensive information in a well-structured markdown format.
        
        Your markdown document should include the following sections with proper headers (# for main headers, ## for subheaders):
        
        # Artist Profile: {artist_name}
        
        ## Basic Information
        - **Name**: The artist's full name
        - **Members**: List of band members with their roles (e.g., 'John Doe (vocals, guitar)')
        - **Genre**: List of music genres
        - **Years Active**: When the artist/band was established
        
        ## Top Tracks
        Include a list of at least 5 top/popular tracks, each with title and YouTube link.
        For each track, format it as follows:
        - [Track Title](YouTube link)
        
        ## Style Analysis
        This section should contain at least 20 style keywords that characterize the artist's music.
        For each keyword, include:
        - **Keyword**: Brief explanation of how this applies to the artist
          - Source: [Publication/Website Name](Full URL to the source)
        
        Make sure your markdown is properly formatted with appropriate headers, bullet points, and emphasis.
        
        IMPORTANT REQUIREMENTS:
        1. Include EXACTLY 5 or more top tracks, each with both title and YouTube link
        2. For style keywords, sources must include the FULL URL to verify the information
        3. Include at least 20 style keywords total, each with source citation
        4. Format everything in clean, readable markdown with proper sections
        
        First, use the Web search tool with fetch_full_content=True to research the artist's general information.
        This will automatically retrieve full page content from top search results.
        
        Then use the Style sources tool with fetch_full_content=True to gather detailed information about their style from multiple sources.
        
        For the style_keywords, collect at least 20 unique descriptive terms that characterize the artist's music 
        and vocal style, making sure to link each keyword to sources with full URLs.
        
        Create realistic YouTube links for top tracks using the format https://www.youtube.com/watch?v=XXXX 
        where XXXX is a random ID if you can't find the actual links.
        
        If you encounter errors with the search tools or URL fetching, include detailed error information in your response.
        """,
        agent=music_researcher_agent,
        expected_output="A comprehensive markdown document containing detailed information about the musical artist with style keywords from multiple sources"
    ) 