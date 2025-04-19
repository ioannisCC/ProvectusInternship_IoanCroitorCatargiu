"""
Streamlit UI for the Concert Tour Information Service.
"""

import streamlit as st
import os
from dotenv import load_dotenv

from app.document_processor import DocumentProcessor
from app.rag_system import RAGSystem
from app.query_engine import QueryEngine
from app.web_search import WebSearchEngine
from app.utils import parse_user_query

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Concert Tour Information Service",
    page_icon="🎵",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "documents" not in st.session_state:
    st.session_state.documents = []

if "rag_system" not in st.session_state:
    st.session_state.rag_system = RAGSystem()

if "document_processor" not in st.session_state:
    st.session_state.document_processor = DocumentProcessor()

if "query_engine" not in st.session_state:
    st.session_state.query_engine = QueryEngine(st.session_state.rag_system)
    
if "web_search" not in st.session_state:
    st.session_state.web_search = WebSearchEngine()

if "web_search_enabled" not in st.session_state:
    st.session_state.web_search_enabled = True

# Function to update document list
def update_document_list():
    """Update the list of documents in the session state."""
    documents = st.session_state.rag_system.get_all_documents()
    st.session_state.documents = documents

# App title and description
st.title("🎵 Concert Tour Information Service")
st.markdown("""
This service helps you manage and retrieve information about upcoming concert tours in 2025-2026.
You can add new tour documents or ask questions about existing tours.
""")

# Create sidebar
st.sidebar.title("Documents")
st.sidebar.markdown("Ingested concert tour documents:")

# Update document list on sidebar
update_document_list()
if st.session_state.documents:
    for doc in st.session_state.documents:
        with st.sidebar.expander(f"Document {doc['id'][:8]}"):
            st.write(f"**Summary:** {doc['summary']}")
            st.write(f"**Added:** {doc['timestamp']}")
else:
    st.sidebar.info("No documents ingested yet.")

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["Chat", "Add Document", "Settings"])

# Chat tab
with tab1:
    st.header("Ask about Concert Tours")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about concert tours..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Try to answer from the database first
                response = st.session_state.query_engine.answer_query(prompt)
                
                # Check if no information was found
                no_info_indicators = [
                    "I don't have information about",
                    "I don't know",
                    "No relevant information found",
                    "I couldn't find any",
                    "I don't have any",
                    "in my database",
                    "not found in the database"
                ]
                
                web_search_enabled = st.session_state.get("web_search_enabled", True)
                
                # If no info found and web search is enabled, try web search
                if any(indicator in response for indicator in no_info_indicators) and web_search_enabled:
                    search_info_placeholder = st.empty()
                    search_info_placeholder.info("No information found in database. Searching the web...")
                    
                    # Extract artist name
                    artist_name = st.session_state.web_search.extract_artist_name(prompt)
                    
                    if artist_name:
                        # Try web search
                        with st.spinner(f"Searching for information about {artist_name}..."):
                            success, results = st.session_state.web_search.search_concerts(artist_name)
                        
                        if success and results:
                            search_info_placeholder.empty()  # Remove the info message
                            web_response = st.session_state.web_search.format_concert_response(artist_name, results)
                            st.markdown(web_response)
                            
                            # Update response for chat history
                            response = web_response
                        else:
                            search_info_placeholder.empty()  # Remove the info message
                            st.warning("No concert information could be found online.")
                            st.markdown(response)
                    else:
                        search_info_placeholder.empty()  # Remove the info message
                        st.markdown(response)
                else:
                    st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

# Add Document tab
with tab2:
    st.header("Add Concert Tour Document")
    
    # Text area for document input
    document_text = st.text_area(
        "Paste or type your concert tour document here:",
        height=300,
        placeholder="Example: Taylor Swift's 'Eras Tour' continues in 2025 with dates across Europe..."
    )
    
    # Process document button
    if st.button("Process Document"):
        if document_text:
            with st.spinner("Processing document..."):
                # Process the document
                is_relevant, summary = st.session_state.document_processor.process_document(document_text)
                
                if not is_relevant:
                    st.error("The document doesn't appear to be related to concert tours in 2025-2026. Please provide a relevant document.")
                else:
                    # Add document to RAG system
                    doc_id = st.session_state.rag_system.add_document(document_text, summary)
                    
                    # Display success message
                    st.success("Document successfully added to the database!")
                    st.info(f"Document Summary: {summary}")
                    
                    # Update document list
                    update_document_list()
        else:
            st.warning("Please enter document text before processing.")

# Add settings tab
with tab3:
    st.header("Settings")
    
    # Web search settings
    st.subheader("Web Search (Bonus Feature)")
    
    # Toggle for web search
    web_search_enabled = st.toggle(
        "Enable web search when no document information is available",
        value=st.session_state.web_search_enabled
    )
    
    # Update session state
    st.session_state.web_search_enabled = web_search_enabled
    
    if web_search_enabled:
        st.success("Web search is enabled. If no information is found in the database, the system will attempt to search for concert information online.")
        
        # API key input for SerpAPI (optional)
        st.subheader("SerpAPI Configuration (Optional)")
        st.info("For better web search results, you can provide a SerpAPI key. If not provided, a basic web scraper will be used.")
        
        api_key = st.text_input(
            "SerpAPI Key (optional)",
            value=os.environ.get("SERP_API_KEY", ""),
            type="password"
        )
        
        if api_key:
            if st.button("Save API Key"):
                os.environ["SERP_API_KEY"] = api_key
                st.session_state.web_search = WebSearchEngine(api_key=api_key)
                st.success("API Key saved successfully!")
    else:
        st.info("Web search is disabled. The system will only use information from ingested documents.")

    st.subheader("Document Processing")
    # Add button to clear all documents (for testing/development)
    if st.button("Clear All Documents", type="secondary"):
        if st.session_state.documents:
            confirm = st.checkbox("Confirm deletion of all documents")
            if confirm:
                # Reinitialize the RAG system
                st.session_state.rag_system = RAGSystem()
                st.session_state.documents = []
                st.success("All documents have been removed from the database.")
        else:
            st.info("No documents to clear.")

# System info in sidebar
with st.sidebar.expander("System Info"):
    stats = st.session_state.rag_system.get_statistics()
    st.write(f"**Documents:** {stats['num_documents']}")
    st.write(f"**Text Chunks:** {stats['num_chunks']}")
    st.write(f"**Embedding Dimensions:** {stats['embedding_dimensions']}")
    st.write(f"**Web Search:** {'Enabled' if st.session_state.get('web_search_enabled', True) else 'Disabled'}")