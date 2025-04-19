"""
Main entry point for the concert tour information service.
"""

import os
import argparse
from dotenv import load_dotenv

from app.document_processor import DocumentProcessor
from app.rag_system import RAGSystem
from app.query_engine import QueryEngine
from app.utils import parse_user_query, format_response

def setup_environment():
    """Set up the environment and load environment variables."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Ensure required directories exist
    os.makedirs("data", exist_ok=True)

def process_command(command: str) -> dict:
    """
    Process a user command and return a response.
    
    Args:
        command: User command
        
    Returns:
        dict: Response to the user
    """
    query_type, document_content = parse_user_query(command)
    
    if query_type == "ingest":
        if not document_content:
            return format_response(
                "error", 
                "I couldn't identify any document content to ingest. Please make sure to include the document content in your request."
            )
        
        # Process the document
        processor = DocumentProcessor()
        is_relevant, summary = processor.process_document(document_content)
        
        if not is_relevant:
            return format_response(
                "error",
                "The document doesn't appear to be related to concert tours in 2025-2026. "
                "I can only process documents about upcoming concert tours."
            )
        
        # Add document to RAG system
        rag_system = RAGSystem()
        doc_id = rag_system.add_document(document_content, summary)
        
        return format_response(
            "success",
            "Thank you for sharing! Your document has been successfully added to the database.",
            {
                "document_id": doc_id,
                "summary": summary
            }
        )
    else:  # query_type == "question"
        # Answer the question
        rag_system = RAGSystem()
        query_engine = QueryEngine(rag_system)
        
        answer = query_engine.answer_query(command)
        
        return format_response(
            "answer",
            answer
        )

def cli_interface():
    """Command-line interface for the application."""
    parser = argparse.ArgumentParser(description="Concert Tour Information Service")
    parser.add_argument("--query", type=str, help="User query")
    
    args = parser.parse_args()
    
    if args.query:
        response = process_command(args.query)
        print(f"{response['type'].upper()}: {response['message']}")
        
        if 'summary' in response:
            print(f"SUMMARY: {response['summary']}")
    else:
        print("Interactive mode. Type 'exit' to quit.")
        while True:
            query = input("\nYour query: ")
            if query.lower() == "exit":
                break
                
            response = process_command(query)
            print(f"\n{response['message']}")
            
            if 'summary' in response:
                print(f"\nSummary: {response['summary']}")

if __name__ == "__main__":
    setup_environment()
    cli_interface()