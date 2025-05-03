"""
Markdown Writing Tool definition.

This module defines a tool for writing markdown files to the output directory.
"""

from crewai.tools import tool
import os
from pathlib import Path
import time

# Import the context from the dedicated module
from research_context import CONTEXT

def create_markdown_writing_tool():
    """
    Create and return a markdown writing tool.
    
    Returns:
        Tool: Configured markdown writing tool
    """
    
    @tool("Markdown writing tool")
    def write_markdown_file(content: str, artist_name: str) -> str:
        """Write markdown content to a file in the output directory.
        
        Args:
            content: The markdown content to write to the file
            artist_name: Name of the artist, used for file naming
            
        Returns:
            A message indicating the result of the operation
        """
        try:
            # Check if the output directory exists
            if not hasattr(CONTEXT, 'output_dir') or CONTEXT.output_dir is None:
                return "ERROR: Output directory is not available. Cannot save markdown file."
            
            # Create a filename from the artist name
            sanitized_name = artist_name.lower().replace(' ', '_')
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            markdown_filename = f"{sanitized_name}_profile_{timestamp}.md"
            markdown_filepath = CONTEXT.output_dir / markdown_filename
            
            # Write the content to the file
            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return f"Successfully wrote markdown file to: {markdown_filepath}"
            
        except Exception as e:
            return f"Error writing markdown file: {str(e)}"
    
    return write_markdown_file 