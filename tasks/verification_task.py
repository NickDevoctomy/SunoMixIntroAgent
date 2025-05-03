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
        description=f"""Review the markdown research document provided for "{artist_name}" and verify that it meets all requirements.
        
        The research should be in well-formatted markdown and must include ALL of the following sections:
        1. Artist Profile with basic information:
           - Name: The artist's full name
           - Members: A list of band members with their roles
           - Genre: A list of music genres
           - Years Active: When the artist/band was formed
        
        2. Top Tracks:
           - EXACTLY 5 OR MORE tracks, each with title and YouTube link in the format [Title](YouTube-Link)
        
        3. Style Analysis:
           - At least 20 unique style descriptors with brief explanations
           - Each style keyword must have sources with full URLs, not just publication names
        
        Your verification must check:
        1. Markdown formatting quality and readability
        2. Completeness of all required sections
        3. STRICT ADHERENCE to the requirement of 5+ top tracks with both title and link
        4. Style keywords have sources with FULL URLs (not just publication names)
        5. No placeholder text or "to be completed later" content
        6. At least 20 unique style keywords with proper citation
        7. Realistic information (no obviously fake or contradictory content)
        
        Important: You can only request revisions up to {max_revision_attempts} times. If after {max_revision_attempts} 
        attempts the research still has issues, you should make the best final decision based on what you have.
        Keep track of how many revision attempts have been made and provide that count in your response.
        
        If ANY requirements are not met and you haven't reached {max_revision_attempts} revision attempts, 
        delegate the task back to the Music Research Specialist with specific instructions on what needs to be 
        fixed or improved. Be explicit about what's missing or inadequate.
        
        If all requirements are met OR you've reached the maximum revision attempts, return the COMPLETE markdown document.
        You may make minor formatting improvements to the final document if needed, but preserve all the core content.
        
        Your response should either be:
        1. A delegation instruction with specific improvements needed and the current revision attempt count, OR
        2. The complete markdown document with all requirements satisfied
        
        CRITICAL INSTRUCTIONS FOR FINAL MARKDOWN:
        - DO NOT include any commentary about your process, revision counts, or verification
        - DO NOT include text like "Revision Attempt: X" or "All requirements are now satisfied"
        - DO NOT add text like "Here is the complete markdown document:"
        - Return ONLY the clean, final markdown content itself
        - Start directly with the markdown heading (e.g., "# Artist Profile: [Name]")
        
        IMPORTANT INSTRUCTIONS (FOLLOW THESE EXACTLY):
        - You are limited to requesting a maximum of {max_revision_attempts} revisions
        - Track the revision count in your responses when delegating
        - When approving research, return ONLY the markdown document itself with no additional text
        - Do not include any "verification complete" text or thinking process before or after the document
        """,
        agent=project_manager_agent,
        expected_output="Either the complete markdown document or specific instructions for improvements"
    ) 