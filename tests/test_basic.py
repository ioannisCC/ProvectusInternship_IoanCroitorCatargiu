"""
Basic tests for the concert tour information service.
"""

import unittest
import os
import shutil
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.document_processor import DocumentProcessor
from app.rag_system import RAGSystem
from app.utils import parse_user_query, extract_document_from_query

class TestDocumentProcessor(unittest.TestCase):
    """Test the document processor functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        self.processor = DocumentProcessor()
        
        # Example concert tour document
        self.valid_document = """
        BTS "World Tour 2025-2026" Announced
        
        BTS has announced their comeback world tour for 2025-2026. The tour will begin in Seoul, South Korea
        with three nights at the Olympic Stadium on February 15-17, 2025. The group will then travel to Tokyo,
        Japan for performances at the Tokyo Dome on March 5-7, 2025.
        
        The North American leg will include:
        - Los Angeles, CA - SoFi Stadium - April 12-13, 2025
        - Chicago, IL - Soldier Field - April 25, 2025
        - New York, NY - MetLife Stadium - May 3-4, 2025
        
        European dates include:
        - London, UK - Wembley Stadium - June 7-8, 2025
        - Paris, France - Stade de France - June 15, 2025
        - Berlin, Germany - Olympiastadion - June 22, 2025
        
        Tickets go on sale December 1, 2024. VIP packages will be available.
        """
        
        # Non-relevant document
        self.invalid_document = """
        New Smartphone Release in 2025
        
        TechCorp is planning to release their new flagship smartphone in early 2025.
        The device will feature a revolutionary display technology and advanced AI capabilities.
        Pre-orders will start in December 2024 with a retail price of $999.
        """
    
    def test_document_relevance(self):
        """Test if documents are correctly identified as relevant or not."""
        # Valid document should be identified as relevant
        self.assertTrue(self.processor.is_relevant_document(self.valid_document))
        
        # Invalid document should be identified as not relevant
        self.assertFalse(self.processor.is_relevant_document(self.invalid_document))
    
    def test_entity_extraction(self):
        """Test entity extraction from documents."""
        entities = self.processor.extract_entities(self.valid_document)
        
        # Check for BTS in artists
        self.assertTrue(any("BTS" in artist for artist in entities["artists"]))
        
        # Check for some locations
        locations = " ".join(entities["locations"])
        self.assertTrue("Seoul" in locations or "Tokyo" in locations or "London" in locations)
        
        # Check for dates
        self.assertTrue(len(entities["dates"]) > 0)
    
    def test_summarization(self):
        """Test document summarization."""
        summary = self.processor.summarize_document(self.valid_document)
        
        # Summary should mention BTS
        self.assertIn("BTS", summary)
        
        # Summary should indicate it's a tour
        tour_keywords = ["tour", "concerts", "performances", "shows", "dates"]
        self.assertTrue(any(keyword in summary.lower() for keyword in tour_keywords))

class TestRAGSystem(unittest.TestCase):
    """Test the RAG system functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a test data directory
        self.test_data_dir = "test_data"
        os.makedirs(self.test_data_dir, exist_ok=True)
        
        # Initialize the RAG system with the test data directory
        self.rag_system = RAGSystem(data_dir=self.test_data_dir)
        
        # Example concert tour document
        self.test_document = """
        Adele "30 Tour" Coming in 2025
        
        Adele has announced her "30 Tour" starting in 2025. The tour will include dates in:
        - London, UK - O2 Arena - January 15-18, 2025
        - Paris, France - AccorHotels Arena - January 25-26, 2025
        - New York, USA - Madison Square Garden - February 10-15, 2025
        - Los Angeles, USA - Crypto.com Arena - March 1-5, 2025
        
        This will be Adele's first tour since 2016. Special guests will be announced later.
        Ticket prices range from $60 to $300.
        """
        
        # Example summary
        self.test_summary = "Artist: Adele | Tour: 30 Tour | Dates: January-March 2025 | Locations: London, Paris, New York, Los Angeles"
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the test data directory
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)
    
    def test_document_addition_and_retrieval(self):
        """Test adding a document and retrieving it."""
        # Add the document
        doc_id = self.rag_system.add_document(self.test_document, self.test_summary)
        
        # Verify the document was added
        self.assertIsNotNone(doc_id)
        
        # Retrieve the document
        document = self.rag_system.get_document_by_id(doc_id)
        
        # Check if the retrieved document matches
        self.assertIsNotNone(document)
        self.assertEqual(document["summary"], self.test_summary)
    
    def test_search_functionality(self):
        """Test searching for relevant information."""
        # Add the document
        self.rag_system.add_document(self.test_document, self.test_summary)
        
        # Search for Adele
        results = self.rag_system.search("When is Adele performing in New York?")
        
        # Check if we got results
        self.assertTrue(len(results) > 0)
        
        # Check if the results contain relevant information
        combined_text = " ".join([result["text"] for result in results])
        self.assertTrue("Adele" in combined_text or "New York" in combined_text)

class TestUtilities(unittest.TestCase):
    """Test utility functions."""
    
    def test_parse_query(self):
        """Test parsing user queries."""
        # Test ingest query
        ingest_query = "Please add this document to your database: [Concert info for Taylor Swift]"
        query_type, document = parse_user_query(ingest_query)
        
        self.assertEqual(query_type, "ingest")
        self.assertIsNotNone(document)
        
        # Test question query
        question_query = "When is BTS performing in London?"
        query_type, document = parse_user_query(question_query)
        
        self.assertEqual(query_type, "question")
        self.assertIsNone(document)
    
    def test_extract_document(self):
        """Test extracting document content from queries."""
        # Test with square brackets
        query1 = "Please add this document: [This is a test document about concerts in 2025]"
        doc1 = extract_document_from_query(query1)
        self.assertEqual(doc1, "This is a test document about concerts in 2025")
        
        # Test with phrase followed by content
        query2 = "Here's the document: This is another test document."
        doc2 = extract_document_from_query(query2)
        self.assertEqual(doc2, "This is another test document.")

if __name__ == "__main__":
    unittest.main()