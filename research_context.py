import os
import uuid
import time
import datetime
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Create a context object to store global state
class ResearchContext:
    # Singleton instance
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResearchContext, cls).__new__(cls)
            cls._instance.session_id = None
            cls._instance.research_dir = None
            cls._instance.output_dir = None
            cls._instance.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        return cls._instance
    
    def create_session_directories(self):
        """Create session directories and set up paths"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_id = f"{timestamp}_{str(uuid.uuid4())}"
        base_dir = Path("sessions") / self.session_id
        
        self.research_dir = base_dir / "research"
        self.output_dir = base_dir / "output"
        
        # Create directories
        self.research_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Session ID: {self.session_id}")
        print(f"Research directory: {self.research_dir}")
        print(f"Output directory: {self.output_dir}")
        
        return self.session_id, self.research_dir, self.output_dir
    
    def fetch_url_content(self, url, timeout=10):
        """Fetch and extract text content from a URL"""
        try:
            headers = {
                "User-Agent": self.user_agent
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
                
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text (remove extra whitespace)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit text length to avoid overwhelming response
            if len(text) > 5000:
                text = text[:5000] + "... [content truncated]"
                
            return text
        except Exception as e:
            print(f"DEBUG: Error fetching URL {url}: {str(e)}")
            return f"Error fetching content from {url}: {str(e)}"

# Create a global instance
CONTEXT = ResearchContext() 