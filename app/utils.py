"""
Utility functions for the concert tour information service.
"""

import os
from typing import Optional, Dict, Any, Tuple
import re
from datetime import datetime

def load_env_variables() -> Dict[str, str]:
    """
    Load environment variables from .env file.
    
    Returns:
        Dict[str, str]: Dictionary of environment variables
    """
    env_vars = {}
    
    # Try to load from .env file if present
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value
    
    # Override with actual environment variables
    for key, value in os.environ.items():
        env_vars[key] = value
    
    return env_vars

def detect_query_type(query: str) -> str:
    """
    Detect the type of query (document ingestion or question).
    
    Args:
        query: User's query
        
    Returns:
        str: Query type ('ingest' or 'question')
    """
    # Patterns that indicate document ingestion
    ingest_patterns = [
        r"add this (document|info|information|text|content)",
        r"upload this (document|info|information|text|content)",
        r"ingest this (document|info|information|text|content)",
        r"store this (document|info|information|text|content)",
        r"process this (document|info|information|text|content)",
        r"save this (document|info|information|text|content)",
        r"include this (document|info|information|text|content)",
    ]
    
    for pattern in ingest_patterns:
        if re.search(pattern, query.lower()):
            return "ingest"
    
    return "question"

def extract_document_from_query(query: str) -> Optional[str]:
    """
    Extract document content from a query.
    
    Args:
        query: User's query
        
    Returns:
        Optional[str]: Document content if found, None otherwise
    """
    # Simple pattern: extract text between common delimiters
    delimiters = [
        (r"\[", r"\]"),  # Square brackets
        (r"\{", r"\}"),  # Curly braces
        (r"```", r"```"),  # Code blocks
        (r'"', r'"'),  # Double quotes
        (r"'", r"'"),  # Single quotes
    ]
    
    for start, end in delimiters:
        pattern = f"{start}(.*?){end}"
        match = re.search(pattern, query, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # Look for content after common phrases
    phrases = [
        "add this document to your database:",
        "add this document:",
        "ingest this document:",
        "process this document:",
        "here's the document:",
        "here is the document:",
    ]
    
    for phrase in phrases:
        if phrase in query.lower():
            parts = query.lower().split(phrase, 1)
            if len(parts) > 1:
                return parts[1].strip()
    
    # If no specific pattern matches, check if the query is long enough
    # to potentially contain a document (heuristic)
    if len(query) > 500:  # Arbitrary threshold
        # Try to find the command part vs. the content part
        potential_commands = [
            "please add this document",
            "can you add this document",
            "add this document",
            "ingest this document",
            "process this document",
        ]
        
        for cmd in potential_commands:
            if cmd in query.lower():
                cmd_pos = query.lower().find(cmd)
                cmd_end = cmd_pos + len(cmd)
                
                # Check if there's a delimiter after the command
                for delim in [":", "-", ".", "\n"]:
                    if delim in query[cmd_end:cmd_end+5]:
                        return query[cmd_end+query[cmd_end:cmd_end+5].find(delim)+1:].strip()
                
                # If no delimiter, just take everything after the command
                return query[cmd_end:].strip()
    
    return None

def format_current_time() -> str:
    """
    Format the current time as a string.
    
    Returns:
        str: Formatted current time
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_response(response_type: str, message: str, additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format the response to the user.
    
    Args:
        response_type: Type of response ('success', 'error', 'answer')
        message: Main response message
        additional_data: Additional data to include
        
    Returns:
        Dict[str, Any]: Formatted response
    """
    response = {
        "type": response_type,
        "message": message,
        "timestamp": format_current_time()
    }
    
    if additional_data:
        response.update(additional_data)
    
    return response

def parse_user_query(query: str) -> Tuple[str, Optional[str]]:
    """
    Parse the user query to determine intent and extract content.
    
    Args:
        query: User's query
        
    Returns:
        Tuple[str, Optional[str]]: Query type and document content (if applicable)
    """
    query_type = detect_query_type(query)
    
    if query_type == "ingest":
        document = extract_document_from_query(query)
        return query_type, document
    
    return query_type, None