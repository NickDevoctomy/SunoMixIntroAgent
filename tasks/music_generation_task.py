"""
Music Generation Task definition.

This module defines the task for generating music in the style of a researched artist,
which will be assigned to the Music Generator agent.
"""

from crewai import Task
import json

def create_music_generation_task(artist_json, music_generator_agent, output_path=None):
    """
    Create a task for generating music in the style of a researched artist.
    
    Args:
        artist_json (str or dict): JSON data about the artist, either as a string or dict
        music_generator_agent: Agent to assign the task to
        output_path (str, optional): Path where the generated music should be saved
        
    Returns:
        Task: Configured music generation task
    """
    # Convert dict to string if needed
    if isinstance(artist_json, dict):
        artist_data = json.dumps(artist_json)
    else:
        artist_data = artist_json
    
    # Extract the artist name for better prompting
    try:
        artist_info = json.loads(artist_data) if isinstance(artist_data, str) else artist_data
        artist_name = artist_info.get("name", "the artist")
    except:
        artist_name = "the artist"
    
    # Create the output path instruction if provided
    output_instruction = ""
    if output_path:
        output_instruction = f" Save the generated track to {output_path}."
    
    return Task(
        description=f"""Generate an original piece of music in the style of {artist_name} based on the provided artist information.
        
        You have detailed data about {artist_name}'s musical style including genre, key characteristics, and style keywords.
        Use this information to create an original composition that captures the essence of {artist_name}'s sound while being
        a unique piece of music.
        
        Here is the artist data to use as inspiration:
        {artist_data}
        
        Follow these steps:
        1. Analyze the style keywords and genre information carefully
        2. Create a prompt for music generation that captures the essence of {artist_name}'s style
        3. Use the generate_music tool to create a track with this prompt
        4. Once generated, use the download_music tool to download the audio file{output_instruction}
        5. Provide a brief description of how your generated track reflects {artist_name}'s style
        
        Your response should include:
        - The generation prompt you used
        - The generated track ID
        - Download information
        - A brief explanation of how the music reflects {artist_name}'s style
        """,
        agent=music_generator_agent,
        expected_output="Generated music information including track ID, download details, and style explanation"
    ) 