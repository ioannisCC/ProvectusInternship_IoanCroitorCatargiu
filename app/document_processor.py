"""
Document processor for concert tour information.
Handles document validation, analysis, and summarization.
"""

import re
import spacy
from typing import Dict, List, Tuple, Optional

# Load SpaCy for NLP tasks
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not found, download it
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

class DocumentProcessor:
    """Process and analyze concert tour documents."""
    
    # Keywords that indicate a document is about concert tours
    CONCERT_KEYWORDS = [
        "concert", "tour", "performance", "venue", "artist", "band", "musician",
        "stage", "ticket", "audience", "show", "live", "perform", "music", "gig",
        "festival", "arena", "stadium", "hall", "theater", "theatre", "amphitheatre",
        "acoustic", "backstage", "crowd", "fan", "setlist", "booking", "sold out",
        "world tour", "opening act", "headliner", "special guest"
    ]
    
    # Years we're interested in for the tours
    TARGET_YEARS = ["2025", "2026"]
    
    def __init__(self):
        """Initialize the document processor."""
        pass
    
    def is_relevant_document(self, text: str) -> bool:
        """
        Check if the document is relevant to concert tours in 2025-2026.
        
        Args:
            text: Document text to analyze
            
        Returns:
            bool: True if document is relevant, False otherwise
        """
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Check for year relevance (2025-2026)
        year_relevant = any(year in text for year in self.TARGET_YEARS)
        if not year_relevant:
            return False
        
        # Check for concert keywords
        keyword_count = sum(1 for keyword in self.CONCERT_KEYWORDS if keyword.lower() in text_lower)
        
        # Document is relevant if it contains at least 3 concert-related keywords
        return keyword_count >= 3
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from the document.
        
        Args:
            text: Document text
            
        Returns:
            Dict: Dictionary of entity types and their values
        """
        doc = nlp(text)
        entities = {}
        
        # Extract people (artists, bands)
        entities["artists"] = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        
        # Extract locations (venues, cities)
        entities["locations"] = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC", "FAC"]]
        
        # Extract dates
        entities["dates"] = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
        
        # Extract organizations (promoters, venues)
        entities["organizations"] = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        
        return entities
    
    def extract_tour_dates(self, text: str) -> List[Dict[str, str]]:
        """
        Extract tour dates, venues, and cities from text.
        
        Args:
            text: Document text
            
        Returns:
            List[Dict]: List of dictionaries with date, venue, and city information
        """
        # This is a simplified implementation - in a production system, 
        # you'd want to use more advanced pattern matching or ML-based extraction
        
        # Example pattern: "January 15, 2025 - Madison Square Garden, New York"
        date_pattern = r'(\w+ \d{1,2},? \d{4}) - (.*?), (.*?)(?=\n|\w+ \d{1,2},? \d{4}|$)'
        matches = re.findall(date_pattern, text)
        
        tour_dates = []
        for match in matches:
            if len(match) >= 3:
                tour_dates.append({
                    "date": match[0],
                    "venue": match[1].strip(),
                    "city": match[2].strip()
                })
        
        return tour_dates
    
    def summarize_document(self, text: str) -> str:
        """
        Generate a concise summary of the concert tour document.
        
        Args:
            text: Document text
            
        Returns:
            str: Summary of the document
        """
        # Extract entities
        entities = self.extract_entities(text)
        
        # Extract tour dates
        tour_dates = self.extract_tour_dates(text)
        
        # Create summary
        summary_parts = []
        
        # Add artists
        if entities["artists"]:
            unique_artists = list(set(entities["artists"]))
            if len(unique_artists) == 1:
                summary_parts.append(f"Artist: {unique_artists[0]}")
            else:
                summary_parts.append(f"Artists: {', '.join(unique_artists[:5])}")
                if len(unique_artists) > 5:
                    summary_parts[-1] += f" and {len(unique_artists) - 5} more"
        
        # Add tour dates
        if tour_dates:
            summary_parts.append(f"Tour includes {len(tour_dates)} dates")
            # Add a few example dates
            examples = tour_dates[:3]
            date_examples = []
            for example in examples:
                date_examples.append(f"{example['date']} at {example['venue']} in {example['city']}")
            summary_parts.append(f"Including: {'; '.join(date_examples)}")
            if len(tour_dates) > 3:
                summary_parts[-1] += f" and {len(tour_dates) - 3} more locations"
        
        # Add locations (cities/countries)
        if entities["locations"]:
            unique_locations = list(set(entities["locations"]))
            if len(unique_locations) <= 5:
                summary_parts.append(f"Locations: {', '.join(unique_locations)}")
            else:
                summary_parts.append(f"Covering {len(unique_locations)} locations")
        
        # Combine summary
        if summary_parts:
            summary = " | ".join(summary_parts)
            return summary
        else:
            return "Concert tour document ingested. No specific details could be extracted automatically."
    
    def process_document(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Process the document: validate, analyze, and summarize.
        
        Args:
            text: Document text
            
        Returns:
            Tuple: (is_relevant, summary) - boolean indicating if document is relevant
                   and a summary string if relevant, None otherwise
        """
        # Check if document is relevant
        is_relevant = self.is_relevant_document(text)
        
        if not is_relevant:
            return False, None
        
        # Generate summary
        summary = self.summarize_document(text)
        
        return True, summary