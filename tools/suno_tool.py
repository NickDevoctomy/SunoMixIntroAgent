"""
Suno API Tool definition.

This module defines the Suno API tool which is used for music generation.
"""

import os
import requests
import json
import time
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SunoTool:
    """Tool for creating music using the Suno API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Suno API tool.
        
        Args:
            api_key: Suno API key. If not provided, will look for SUNO_API_KEY in environment variables.
        """
        self.api_key = api_key or os.getenv("SUNO_API_KEY")
        if not self.api_key:
            raise ValueError("Suno API key is required. Set SUNO_API_KEY environment variable or pass it to the constructor.")
        
        self.base_url = "https://api.suno.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_music(self, 
                      prompt: str, 
                      title: Optional[str] = None, 
                      style_prompt: Optional[str] = None,
                      duration: Optional[str] = None,
                      genre: Optional[List[str]] = None,
                      bpm: Optional[int] = None,
                      key: Optional[str] = None,
                      vocals: Optional[str] = "with_vocals",
                      wait_for_completion: bool = True,
                      max_wait_time: int = 300) -> Dict[str, Any]:
        """Generate music using Suno API.
        
        Args:
            prompt: Main prompt describing the music to generate
            title: Title for the generated track
            style_prompt: Additional style instructions
            duration: Duration of the track (e.g., "short", "medium", "long")
            genre: List of genres for the track
            bpm: Beats per minute
            key: Musical key (e.g., "C major")
            vocals: Whether to include vocals ("with_vocals" or "instrumental")
            wait_for_completion: Whether to wait for the generation to complete
            max_wait_time: Maximum time to wait in seconds
            
        Returns:
            Dictionary containing the response from Suno API
        """
        # Build request data
        data = {
            "prompt": prompt,
            "vocals": vocals
        }
        
        # Add optional parameters if provided
        if title:
            data["title"] = title
        if style_prompt:
            data["style_prompt"] = style_prompt
        if duration:
            data["duration"] = duration
        if genre:
            data["genre"] = genre
        if bpm:
            data["bpm"] = bpm
        if key:
            data["key"] = key
        
        # Create generation request
        try:
            response = requests.post(
                f"{self.base_url}/generations", 
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            generation_data = response.json()
            generation_id = generation_data.get("id")
            
            if not generation_id:
                return {"error": "No generation ID returned", "data": generation_data}
            
            # If not waiting for completion, return immediately
            if not wait_for_completion:
                return {"status": "pending", "generation_id": generation_id, "data": generation_data}
            
            # Wait for generation to complete
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status_response = requests.get(
                    f"{self.base_url}/generations/{generation_id}",
                    headers=self.headers
                )
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data.get("status")
                if status == "complete":
                    return {"status": "complete", "generation_id": generation_id, "data": status_data}
                elif status == "failed":
                    return {"status": "failed", "generation_id": generation_id, "data": status_data}
                
                # Wait before checking again
                time.sleep(5)
            
            return {"status": "timeout", "generation_id": generation_id, "message": "Generation timed out"}
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def list_generations(self, limit: int = 10) -> Dict[str, Any]:
        """List recent generations.
        
        Args:
            limit: Maximum number of generations to retrieve
            
        Returns:
            Dictionary containing the list of generations
        """
        try:
            response = requests.get(
                f"{self.base_url}/generations?limit={limit}",
                headers=self.headers
            )
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_generation(self, generation_id: str) -> Dict[str, Any]:
        """Get details of a specific generation.
        
        Args:
            generation_id: ID of the generation to retrieve
            
        Returns:
            Dictionary containing the generation details
        """
        try:
            response = requests.get(
                f"{self.base_url}/generations/{generation_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def download_audio(self, generation_id: str, output_path: str) -> Dict[str, Any]:
        """Download the generated audio file.
        
        Args:
            generation_id: ID of the generation to download
            output_path: Path where the audio file should be saved
            
        Returns:
            Dictionary indicating success or failure
        """
        try:
            # First get the generation details to confirm it's complete and get the audio URL
            details = self.get_generation(generation_id)
            if "error" in details:
                return details
            
            generation_data = details.get("data", {})
            status = generation_data.get("status")
            
            if status != "complete":
                return {"error": f"Generation not complete. Current status: {status}"}
            
            # Get the audio URL from the generation data
            audio_url = None
            for media in generation_data.get("media", []):
                if media.get("content_type") == "audio/mpeg":
                    audio_url = media.get("url")
                    break
            
            if not audio_url:
                return {"error": "No audio URL found in generation data"}
            
            # Download the audio file
            audio_response = requests.get(audio_url)
            audio_response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(audio_response.content)
            
            return {"status": "success", "message": f"Audio downloaded to {output_path}"}
            
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
        except IOError as e:
            return {"error": f"File error: {str(e)}"}

def create_suno_tool(api_key: Optional[str] = None) -> SunoTool:
    """
    Create and return a SunoTool instance.
    
    Args:
        api_key: Optional API key. If not provided, will be read from environment variables.
        
    Returns:
        SunoTool: Configured SunoTool instance
    """
    return SunoTool(api_key=api_key) 