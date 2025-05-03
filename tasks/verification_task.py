"""
Verification Task definition.

This module defines the task for verifying research output,
which will be assigned to the Project Manager agent.
"""

from crewai import Task

def create_verification_task(artist_name, project_manager_agent, max_revision_attempts=3):
    """
    Create a task for verifying research about a musical artist.
    
    Args:
        artist_name (str): Name of the artist whose research is being verified
        project_manager_agent: Agent to assign the task to
        max_revision_attempts (int): Maximum number of revision attempts allowed (default: 3)
        
    Returns:
        Task: Configured verification task
    """
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
        
        Important: You can only request revisions up to {max_revision_attempts} times. If after {max_revision_attempts} 
        attempts the research still has issues, you should make the best final decision based on what you have.
        Keep track of how many revision attempts have been made and provide that count in your response.
        
        If ANY requirements are not met and you haven't reached {max_revision_attempts} revision attempts, 
        delegate the task back to the Music Research Specialist with specific instructions on what needs to be 
        fixed or improved. Be explicit about what's missing or inadequate.
        
        If all requirements are met OR you've reached the maximum revision attempts, return the COMPLETE JSON data 
        in a format that can be parsed with json.loads(). DO NOT include any intro text like "Here's the verified JSON:" 
        or thoughts about your review process - ONLY return the valid JSON object.
        
        Your response should either be:
        1. A delegation instruction with specific improvements needed and the current revision attempt count, OR
        2. The complete JSON data exactly as received or with minor fixes (if at max revisions)
        
        IMPORTANT INSTRUCTIONS (FOLLOW THESE EXACTLY):
        - You are limited to requesting a maximum of {max_revision_attempts} revisions
        - Track the revision count in your responses
        - When approving research, you MUST return the COMPLETE JSON data as your ENTIRE response
        - DO NOT output your thoughts, reasoning, or decision process
        - DO NOT include any markdown formatting, just the raw JSON
        - ONLY the JSON data should be in your output when approving
        """,
        agent=project_manager_agent,
        expected_output="Either raw JSON data or specific instructions for improvements"
    ) 