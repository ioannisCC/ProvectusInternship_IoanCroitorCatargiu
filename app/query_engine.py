"""
Query engine for answering questions about concert tours.
"""

import os
from typing import List, Dict, Any, Optional
import re

from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .rag_system import RAGSystem

class QueryEngine:
    """Query engine for answering concert tour questions."""
    
    def __init__(self, rag_system: RAGSystem, api_key: Optional[str] = None):
        """
        Initialize the query engine.
        
        Args:
            rag_system: RAG system for document retrieval
            api_key: OpenAI API key (if None, will try to get from environment)
        """
        self.rag_system = rag_system
        
        # Set API key from parameter or environment
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        
        # Initialize the LLM
        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        
        # Define the prompt templates
        self._setup_prompts()
        
        # Set up the answer generation chain
        self._setup_chain()
    
    def _setup_prompts(self):
        """Set up the prompt templates."""
        # Context combination prompt
        self.context_prompt = PromptTemplate.from_template(
            """Use the following pieces of concert tour information to answer the question at the end.
            If you don't know the answer, just say that you don't know. Don't try to make up an answer.
            
            {context}
            
            Question: {question}
            """
        )
        
        # Answer formatting prompt
        self.answer_prompt = PromptTemplate.from_template(
            """Based on the retrieved information about concert tours, provide a helpful answer to the user's question.
            
            Question: {question}
            
            Retrieved Information:
            {context}
            
            Instructions:
            1. Answer ONLY based on the information provided above.
            2. If the retrieved information doesn't contain the answer, say "I don't have information about that in my database."
            3. Be concise but thorough.
            4. Format dates, venues, and other details clearly.
            5. Do not reference the source documents or mention that you're using retrieved information.
            
            Answer:
            """
        )
    
    def _setup_chain(self):
        """Set up the answer generation chain."""
        self.chain = (
            {"context": self._get_context, "question": RunnablePassthrough()}
            | self.answer_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def _get_context(self, query: str) -> str:
        """
        Get relevant context for the query.
        
        Args:
            query: User's question
            
        Returns:
            str: Relevant context from documents
        """
        # Search for relevant chunks
        search_results = self.rag_system.search(query, k=6)
        
        if not search_results:
            return "No relevant information found."
        
        # Combine chunks into context
        context_parts = []
        for i, result in enumerate(search_results):
            context_parts.append(f"[Excerpt {i+1}]: {result['text']}")
        
        return "\n\n".join(context_parts)
    
    def extract_artist_name(self, query: str) -> Optional[str]:
        """
        Extract artist name from the query.
        
        Args:
            query: User's question
            
        Returns:
            Optional[str]: Artist name if found, None otherwise
        """
        # Common patterns for artist name extraction
        patterns = [
            r"Where is (.+?) planning to give concerts",
            r"Where will (.+?) be performing",
            r"When is (.+?) performing",
            r"When will (.+?) perform",
            r"(.+?)'s tour",
            r"(.+?) tour dates",
            r"(.+?) concert"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def is_tour_query(self, query: str) -> bool:
        """
        Check if the query is about tour information.
        
        Args:
            query: User's question
            
        Returns:
            bool: True if query is about tour information
        """
        tour_keywords = [
            "tour", "concert", "perform", "show", "stage", "ticket", 
            "venue", "arena", "stadium", "date", "location"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in tour_keywords)
    
    def answer_query(self, query: str) -> str:
        """
        Answer a question about concert tours.
        
        Args:
            query: User's question
            
        Returns:
            str: Answer to the question
        """
        # Check if the query is about tour information
        if not self.is_tour_query(query):
            return "I can only answer questions about concert tours. Please ask a question related to concerts, tours, or performances."
        
        # Answer the question
        try:
            answer = self.chain.invoke(query)
            return answer
        except Exception as e:
            return f"Sorry, I encountered an error while trying to answer your question. Error: {str(e)}"