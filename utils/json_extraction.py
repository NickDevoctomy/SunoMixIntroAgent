"""
JSON extraction utilities for handling agent outputs.

This module contains functions to parse and extract JSON data from text,
handling various formats and potential invalid JSON structures.
"""

import json
import re

def find_json_in_text(text):
    """
    More aggressive JSON extraction from text.
    
    Args:
        text (str): Text that might contain JSON data
        
    Returns:
        dict: Extracted JSON object or None if not found
    """
    try:
        # Try to find opening and closing braces
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            
            # Try to parse it directly
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try basic cleanup on common issues
                cleaned_str = json_str.replace("// STRICTLY REQUIRE", "").replace("// At least 20", "")
                cleaned_str = re.sub(r'//.*?\n', '\n', cleaned_str)  # Remove any // comments
                
                try:
                    return json.loads(cleaned_str)
                except:
                    # If still failing, try a more aggressive regex approach
                    import re
                    json_pattern = r'({[\s\S]*})'
                    matches = re.findall(json_pattern, text)
                    
                    for potential_json in matches:
                        # Clean up each potential match
                        cleaned_json = re.sub(r'//.*?[\r\n]', '\n', potential_json)  # Remove comments
                        try:
                            return json.loads(cleaned_json)
                        except:
                            continue
                    
                    # Try one more approach - look for code blocks that might contain JSON
                    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)```'
                    code_matches = re.findall(code_block_pattern, text)
                    
                    for code_block in code_matches:
                        if code_block.strip().startswith('{') and code_block.strip().endswith('}'):
                            cleaned_block = re.sub(r'//.*?[\r\n]', '\n', code_block)  # Remove comments
                            try:
                                return json.loads(cleaned_block)
                            except:
                                continue
    except:
        pass
        
    return None


def parse_json_from_agent_output(raw_output):
    """
    Parse JSON from agent output text using multiple approaches.
    
    Args:
        raw_output (str): Raw text output from an agent
        
    Returns:
        dict: Parsed JSON object or None if parsing fails
    """
    # Try parsing the whole thing as JSON first
    try:
        return json.loads(raw_output)
    except:
        pass
    
    # Try to extract JSON from markdown code blocks
    try:
        code_block_pattern = r'```(?:json)?(.+?)```'
        matches = re.findall(code_block_pattern, raw_output, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match.strip())
            except:
                continue
    except:
        pass
    
    # Try to find JSON objects using regex
    try:
        json_pattern = r'({.+})'
        matches = re.findall(json_pattern, raw_output, re.DOTALL)
        
        for match in matches:
            try:
                # Clean up the match, removing comments
                cleaned_match = re.sub(r'//.*?[\r\n]', '\n', match)
                return json.loads(cleaned_match)
            except:
                continue
    except:
        pass
    
    # Try to find JSON between braces
    try:
        start_idx = raw_output.find('{')
        end_idx = raw_output.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_text = raw_output[start_idx:end_idx]
            
            # Clean up the JSON text
            cleaned_json = re.sub(r'//.*?[\r\n]', '\n', json_text)
            
            try:
                return json.loads(cleaned_json)
            except:
                pass
    except:
        pass
    
    return None


def extract_json(text):
    """
    Extract and parse JSON from text using multiple approaches.
    
    This function handles various object types and structures to find and extract JSON data.
    
    Args:
        text: Text or object containing potential JSON data
        
    Returns:
        dict: Parsed JSON object or None if extraction fails
    """
    try:
        # If the result is already a proper object, try to access the output
        if hasattr(text, 'output'):
            return extract_json(text.output)
        if hasattr(text, 'raw_output'):
            return extract_json(text.raw_output)
        if hasattr(text, 'result'):
            return extract_json(text.result)
        
        # If we have an outputs list, try the first element
        if hasattr(text, 'outputs') and len(text.outputs) > 0:
            return extract_json(text.outputs[0])
        
        # If it's a task_results list, try each result
        if hasattr(text, 'task_results') and len(text.task_results) > 0:
            for result in text.task_results:
                json_data = extract_json(result)
                if json_data:
                    return json_data
        
        # If it's a string, try parsing it
        if isinstance(text, str):
            # First try direct JSON parsing
            try:
                return json.loads(text)
            except:
                # If that fails, try our custom JSON extraction methods
                json_data = find_json_in_text(text)
                if json_data:
                    return json_data
                    
                # If still no result, try the more advanced approach
                return parse_json_from_agent_output(text)
    except:
        pass
    
    return None 