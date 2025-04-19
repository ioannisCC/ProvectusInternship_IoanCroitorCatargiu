"""
Web search functionality for retrieving concert information from online sources.
This is a bonus feature that enhances the bot when no documents are available.
"""

import os
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime

class WebSearchEngine:
    """Web search engine for retrieving concert information."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the web search engine.
        
        Args:
            api_key: API key for search service (optional, can use environment variable)
        """
        # If API key is provided, use it; otherwise try to get from environment
        self.api_key = api_key or os.environ.get("SERP_API_KEY")
        
        # List of common concert ticketing and information websites
        self.concert_websites = [
            "ticketmaster.com",
            "livenation.com",
            "songkick.com",
            "bandsintown.com",
            "eventbrite.com",
            "seatgeek.com",
            "viagogo.com",
            "stubhub.com",
            "axs.com",
            "ticketnetwork.com"
        ]
    
    def extract_artist_name(self, query: str) -> Optional[str]:
        """
        Extract artist name from the query.
        
        Args:
            query: User's question
            
        Returns:
            Optional[str]: Artist name if found, None otherwise
        """
        # Patterns to extract artist names from queries
        patterns = [
            r"(.*?) concerts?",
            r"(.*?) tours?",
            r"(.*?) performances?",
            r"(.*?) shows?",
            r"(.*?) tickets?",
            r"(.*?) playing",
            r"(.*?) performing",
            r"when will (.*?) be",
            r"when is (.*?) coming",
            r"where will (.*?) perform",
            r"where is (.*?) performing"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Extract and clean the artist name
                artist = match.group(1).strip()
                # Remove common words that might be captured but aren't part of the name
                for word in ["upcoming", "next", "future", "new", "latest", "where", "when", "is", "are", "the"]:
                    artist = re.sub(r'\b' + word + r'\b', '', artist, flags=re.IGNORECASE).strip()
                
                return artist
        
        return None
    
    def format_search_query(self, artist_name: str) -> str:
        """
        Format a search query for the artist's concerts.
        
        Args:
            artist_name: Artist name
            
        Returns:
            str: Formatted search query
        """
        return f"{artist_name} concerts tour 2025 2026 official"
    
    def search_using_requests(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Basic search implementation using requests and BeautifulSoup.
        This is a fallback method when no API key is available.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List[Dict]: List of search results with title, snippet, and link
        """
        # This is a simplified search function and not recommended for production use
        # A real implementation would use a proper search API
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Encode query for URL
        encoded_query = query.replace(" ", "+")
        
        # Create search URL (this is a basic example and might not work long-term)
        url = f"https://www.google.com/search?q={encoded_query}"
        
        try:
            # Send request
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract search results (this selector might need updates)
            search_results = []
            result_elements = soup.select("div.g")
            
            for element in result_elements[:num_results]:
                # Extract title, link, and snippet
                title_elem = element.select_one("h3")
                link_elem = element.select_one("a")
                snippet_elem = element.select_one("div.VwiC3b")
                
                if title_elem and link_elem and snippet_elem:
                    title = title_elem.get_text()
                    link = link_elem.get("href")
                    if link and link.startswith("/url?q="):
                        link = link.split("/url?q=")[1].split("&")[0]
                    snippet = snippet_elem.get_text()
                    
                    # Only include results from concert websites
                    if any(domain in link for domain in self.concert_websites):
                        search_results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet
                        })
            
            return search_results
        
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []
    
    def search_using_serpapi(self, query: str) -> List[Dict[str, Any]]:
        """
        Search using SerpAPI.
        
        Args:
            query: Search query
            
        Returns:
            List[Dict]: List of search results
        """
        # Check if API key is available
        if not self.api_key:
            return []
        
        try:
            from serpapi import GoogleSearch
            
            # Prepare search parameters
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": 10  # Number of results
            }
            
            # Execute search
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract organic results
            if "organic_results" in results:
                return results["organic_results"]
            
            return []
        
        except ImportError:
            print("SerpAPI library not installed. Please install it with: pip install google-search-results")
            return []
        except Exception as e:
            print(f"SerpAPI search error: {str(e)}")
            return []
    
    def scrape_concert_details(self, url: str) -> Dict[str, Any]:
        """
        Scrape concert details from a URL with improved cleaning and extraction.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dict: Extracted concert details
        """
        try:
            # Send request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script, style, and unwanted elements for cleaner text
            for element in soup(['script', 'style', 'footer', 'nav', 'aside']):
                element.decompose()
            
            # Extract content with cleaner formatting
            text_content = soup.get_text(" ", strip=True)
            
            # Clean up whitespace
            text_content = re.sub(r'\s+', ' ', text_content)
            
            # Look for dates with year 2025 or 2026
            date_patterns = [
                r'(\w+ \d{1,2},? 202[56])',  # January 15, 2025
                r'(\d{1,2} \w+ 202[56])',    # 15 January 2025
                r'(\d{1,2}/\d{1,2}/202[56])' # 01/15/2025
            ]
            
            dates = []
            for pattern in date_patterns:
                found_dates = re.findall(pattern, text_content)
                # Filter and clean dates
                for date in found_dates:
                    date = date.strip()
                    if date and not any(date == existing for existing in dates):
                        dates.append(date)
            
            # Look for tour information
            tour_info = re.search(r'([A-Z][a-zA-Z\s]+) Tour 202[56]', text_content)
            tour_name = tour_info.group(1) if tour_info else None
            
            # Look for venue names (common words/phrases that appear near dates)
            venue_patterns = [
                r'at (.*? (Arena|Stadium|Center|Centre|Theater|Theatre|Hall|Coliseum|Amphitheater|Amphitheatre|Park|Garden|Place|Square|Field))',
                r'in (.*? (Arena|Stadium|Center|Centre|Theater|Theatre|Hall|Coliseum|Amphitheater|Amphitheatre|Park|Garden|Place|Square|Field))',
                r'@ (.*? (Arena|Stadium|Center|Centre|Theater|Theatre|Hall|Coliseum|Amphitheater|Amphitheatre|Park|Garden|Place|Square|Field))'
            ]
            
            venues = []
            for pattern in venue_patterns:
                found_venues = re.findall(pattern, text_content, re.IGNORECASE)
                for venue in found_venues:
                    if isinstance(venue, tuple) and len(venue) > 0:
                        clean_venue = venue[0].strip()
                        if clean_venue and len(clean_venue) > 3 and not any(clean_venue == existing for existing in venues):
                            venues.append(clean_venue)
            
            # Look for cities and locations
            city_pattern = r'in ([A-Z][a-z]+(?:[ -][A-Z][a-z]+)*),\s*([A-Z]{2}|[A-Za-z]+)'
            cities = re.findall(city_pattern, text_content)
            
            # Try to find complete events (date + venue + city)
            event_patterns = [
                r'(\d{1,2}/\d{1,2}/202[56]) - (.*?) - (.*?(?:Arena|Stadium|Center|Theatre|Theater|Hall))',
                r'(\w+ \d{1,2},? 202[56]) - (.*?) @ (.*?(?:Arena|Stadium|Center|Theatre|Theater|Hall))',
                r'(\w+ \d{1,2},? 202[56])\s*[-–]\s*(.*?),\s*(.*?)(?=$|\n)'
            ]
            
            events = []
            for pattern in event_patterns:
                matches = re.findall(pattern, text_content)
                for match in matches:
                    if len(match) >= 3 and all(part.strip() for part in match):
                        events.append({
                            "date": match[0].strip(),
                            "location": match[1].strip(),
                            "venue": match[2].strip()
                        })
            
            # Look for ticket information
            ticket_info = None
            ticket_pattern = r'(?:Tickets|TICKETS).*?(?:will|available|on sale).*?(?:on|starting).*?(\w+ \d{1,2})'
            ticket_match = re.search(ticket_pattern, text_content)
            if ticket_match:
                ticket_info = ticket_match.group(0)
            
            return {
                "dates": dates,
                "venues": venues,
                "cities": cities,
                "events": events,
                "tour_name": tour_name,
                "ticket_info": ticket_info,
                "url": url,
                "text": text_content[:10000]  # Limit text content size
            }
        
        except Exception as e:
            print(f"Scraping error for {url}: {str(e)}")
            return {"error": str(e), "url": url}
    
    def search_concerts(self, artist_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Search for concert information for an artist.
        
        Args:
            artist_name: Artist name
            
        Returns:
            Tuple[bool, Dict]: Success flag and concert information
        """
        search_query = self.format_search_query(artist_name)
        
        # Try SerpAPI first if API key is available
        if self.api_key:
            search_results = self.search_using_serpapi(search_query)
        else:
            # Fall back to basic search
            search_results = self.search_using_requests(search_query)
        
        if not search_results:
            return False, {"error": "No search results found"}
        
        # Filter results to include only concert-related sites
        filtered_results = []
        for result in search_results:
            link = result.get("link", "")
            if any(site in link for site in self.concert_websites):
                filtered_results.append(result)
        
        if not filtered_results and search_results:
            # If no concert sites, use top 2 results
            filtered_results = search_results[:2]
        
        # Scrape concert details from filtered results
        concert_data = []
        for result in filtered_results[:2]:  # Limit to first 2 results to avoid too many requests
            link = result.get("link", "")
            details = self.scrape_concert_details(link)
            concert_data.append(details)
        
        # Compile results
        compiled_results = {
            "artist": artist_name,
            "sources": [result.get("link", "") for result in filtered_results[:3]],
            "concert_data": concert_data,
            "search_timestamp": datetime.now().isoformat()
        }
        
        return True, compiled_results
    
    def format_concert_response(self, artist_name: str, search_results: Dict[str, Any]) -> str:
        """
        Use the LLM to format concert information into a clean, concise response.
        
        Args:
            artist_name: Artist name
            search_results: Search results
            
        Returns:
            str: Formatted response
        """
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            
            # Compile the relevant data to send to the LLM
            extracted_data = {
                "artist": artist_name,
                "data": []
            }
            
            # Extract the most relevant pieces from each result
            for data in search_results.get("concert_data", []):
                clean_data = {
                    "text": data.get("text", "")[:5000],  # Limit text to 5000 chars
                    "dates": data.get("dates", []),
                    "venues": data.get("venues", []),
                    "cities": data.get("cities", []),
                    "ticket_info": data.get("ticket_info", "")
                }
                
                # Add event data if available
                if "events" in data and data["events"]:
                    clean_data["events"] = data["events"]
                    
                extracted_data["data"].append(clean_data)
            
            # Create the LLM chain
            llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
            
            prompt = ChatPromptTemplate.from_template("""
            You are a helpful assistant summarizing concert tour information in a clean, structured format.
            
            The following data was extracted from web searches about {artist}'s upcoming concerts in 2025-2026:
            
            {data}
            
            Please provide a brief, well-formatted summary of the concert information. Include:
            1. The tour name if mentioned
            2. Key confirmed tour dates (up to 10) with venues and cities
            3. Any ticket information
            
            Keep it concise, well-structured, and focused on the most reliable information.
            Format the response with Markdown to make it more readable.
            Include a brief disclaimer at the end that this information is from public sources.
            """)
            
            # Format the chain
            chain = prompt | llm
            
            # Get the formatted response
            formatted_response = chain.invoke({
                "artist": artist_name,
                "data": json.dumps(extracted_data, indent=2)
            }).content
            
            return formatted_response
        
        except Exception as e:
            print(f"Error using LLM to format response: {str(e)}")
            
            # Fallback to basic formatting if LLM fails
            response = [f"# {artist_name}'s Upcoming Concerts (2025-2026)"]
            response.append("\nBased on information gathered from public sources:")
            
            # Extract dates
            all_dates = []
            for data in search_results.get("concert_data", []):
                all_dates.extend(data.get("dates", []))
            
            # Remove duplicates
            unique_dates = sorted(list(set(all_dates)))
            
            if unique_dates:
                response.append("\n## Concert Dates")
                date_list = []
                for date in unique_dates[:8]:
                    date_list.append(f"- {date}")
                response.append("\n".join(date_list))
            
            # Add disclaimer
            response.append("\n---")
            response.append("*Please note: This information was gathered from public web sources and may not be complete or up-to-date.*")
            
            return "\n".join(response)