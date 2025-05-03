# Musical Artist Research Agent

> NOTE: This application was vibe-coded using Cursor so is probably nasty AF. 

A Crew AI application that uses OpenAI and real web search to research musical artists and provide detailed information about them.

## Features

- Researches musical artists using real web search via Tavily API
- Extracts full content from web pages for more comprehensive information
- Provides information on genre, band members, music style from reputable music sites
- Gathers style descriptions with verifiable source URLs
- Uses a project manager agent to verify research quality and completeness
- Delivers a comprehensive JSON report with artist information and style analysis

## Prerequisites

- Python 3.9+
- OpenAI API Key
- Tavily API Key
- Miniconda (recommended)

## Setup with Miniconda (Windows)

1. Install Miniconda using winget:
   ```
   winget install Anaconda.Miniconda3
   ```

2. Open the Miniconda Prompt (search for "Anaconda Prompt" in the Start menu)

3. Create a new conda environment:
   ```
   conda create -n music-agent python=3.9
   ```

4. Activate the environment:
   ```
   conda activate music-agent
   ```

5. Clone this repository and navigate to the project directory

6. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

7. Create a `.env` file in the root directory with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

## Alternative Setup (without Conda)

1. Ensure Python 3.9+ is installed
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with your API keys as shown above

## Usage

With your conda environment activated, run:

```
python main.py
```

When prompted, enter the name of a musical artist to research. The application will:
1. Research the artist using real web search results from Tavily
2. Extract full content from relevant web pages for deeper analysis
3. Gather style descriptions from music critics and publications
4. Verify the research quality and completeness using a project manager agent
5. Generate a comprehensive JSON report with detailed artist information and style analysis

## Strict Requirements

The system enforces the following strict requirements:
- 5 or more top tracks, each with both title and YouTube link
- 20+ style keywords with verifiable sources
- Each style keyword must include sources with full URLs for verification
- No separate sources array - all sources must be inline with each keyword
- Complete information for all required fields

## Code Structure

The project is organized by component types:

```
/
├── agents/             # Agent definitions
│   ├── __init__.py
│   ├── music_researcher_agent.py  # Music researcher agent
│   ├── music_generator_agent.py   # Music generator agent
│   └── project_manager_agent.py   # Project manager agent
├── tasks/              # Task definitions
│   ├── __init__.py
│   ├── music_research_task.py     # Task for researching artists
│   ├── music_generation_task.py   # Task for generating music
│   └── verification_task.py       # Task for verifying research
├── tools/              # Tool definitions
│   ├── __init__.py
│   ├── web_search_tool.py         # Web search tool using Tavily
│   ├── style_sources_tool.py      # Style research tool
│   ├── music_generation_tool.py   # Music generation with Suno
│   └── suno_tool.py               # Suno API interface
├── utils/              # Utility functions
│   ├── __init__.py
│   ├── json_extraction.py         # JSON parsing & extraction
│   └── file_operations.py         # File handling utilities
├── research_context.py            # Global context & session management
├── main.py                        # Application entry point
└── requirements.txt               # Dependencies
```

## Data Format

The application produces JSON in the following format:

```json
{
  "name": "Artist Name",
  "members": [
    "Member 1 (role)",
    "Member 2 (role)"
  ],
  "genre": [
    "Genre 1",
    "Genre 2"
  ],
  "years_established": "1990 - Present",
  "top_tracks": [
    {
      "title": "Track 1",
      "youtube_link": "https://www.youtube.com/watch?v=abcdefg"
    },
    // at least 5 tracks
  ],
  "style_keywords": [
    {
      "keyword": "melodic",
      "sources": [
        {
          "name": "Publication Name",
          "url": "https://full.url.to/source"
        }
      ]
    },
    // at least 20 keywords
  ]
}
```

## How It Works

The application uses specialized agents powered by OpenAI's GPT model:

### Music Research Specialist

This agent performs the initial research:
1. Conducts web searches using the Tavily API to find information about the artist
2. Extracts full content from top search results for more comprehensive analysis
3. Performs specialized searches focusing on the artist's musical style and reviews
4. Analyzes the gathered information to create a structured JSON report

### Project Manager

This agent verifies the research quality:
1. Reviews the JSON report produced by the research specialist
2. Checks for completeness, accuracy, and proper formatting
3. Verifies that all required information is included (5+ tracks, 20+ style keywords with URLs)
4. Either approves the research or delegates it back to the researcher with specific improvement instructions

The project manager can request up to 3 revisions before making a final decision.

### Music Generator

This agent creates music inspired by the researched artist:
1. Takes the artist data from the research phase
2. Extracts style keywords, genre, and other musical characteristics
3. Uses the Suno API to generate music that captures the artist's style
4. Provides download capabilities for the generated tracks

### Tools Organization

The application uses several tools organized in the `tools` directory:
1. **Web Search Tool**: Uses the Tavily API to perform real web searches
2. **Style Sources Tool**: Gathers detailed information about an artist's style from multiple sources
3. **Music Generation Tool**: Interfaces with the Suno API to generate music based on artist style
4. **Suno Tool**: Provides direct access to the Suno API for music generation

Each tool is implemented as a function factory that creates and returns a tool instance, 
following the same pattern used for agents and tasks.

## Future Development

Future enhancements may include:
1. User interface improvements for easier interaction
2. Additional music analysis capabilities
3. Support for batch processing multiple artists
4. Integration with music streaming platforms
5. Enhanced visualization of artist relationships and influences 