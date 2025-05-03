"""
File operations utility module.

This module contains functions for saving results to files and handling
other file-related operations.
"""

import json
from pathlib import Path

def save_result_to_file(data, artist_name, file_type, output_dir):
    """
    Save JSON data to a file in the specified output directory.
    
    Args:
        data (dict): JSON data to save
        artist_name (str): Name of the artist, used for file naming
        file_type (str): Type of data being saved (e.g., 'verified', 'unverified', 'emergency')
        output_dir (Path): Directory where the file should be saved
        
    Returns:
        Path: Path to the saved file
    """
    # Create a filename from the artist name and file type
    output_filename = f"{artist_name.replace(' ', '_').lower()}_{file_type}.json"
    output_filepath = output_dir / output_filename
    
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n{file_type.capitalize()} results saved to: {output_filepath}")
        return output_filepath
    except Exception as save_error:
        print(f"\nError saving {file_type} results: {str(save_error)}")
        return None 