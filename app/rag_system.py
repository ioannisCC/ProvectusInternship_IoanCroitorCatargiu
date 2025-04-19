"""
RAG (Retrieval Augmented Generation) system for storing and retrieving document information.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

# Vector database
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# For text chunking
from langchain.text_splitter import RecursiveCharacterTextSplitter

class RAGSystem:
    """RAG system for concert tour information retrieval."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the RAG system.
        
        Args:
            data_dir: Directory to store the vector database and metadata
        """
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize the sentence transformer model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize the text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize or load the vector database
        self.index_path = os.path.join(data_dir, "faiss_index.bin")
        self.metadata_path = os.path.join(data_dir, "document_metadata.json")
        
        if os.path.exists(self.index_path):
            # Load existing index
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            # Create new index
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.metadata = {
                "chunks": [],  # List of document chunks metadata
                "documents": []  # List of full document metadata
            }
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            np.ndarray: Matrix of embeddings
        """
        return self.model.encode(texts, show_progress_bar=False)
    
    def add_document(self, document_text: str, summary: str) -> str:
        """
        Add a document to the RAG system.
        
        Args:
            document_text: Full text of the document
            summary: Summary of the document
            
        Returns:
            str: Document ID
        """
        # Generate a unique ID for the document
        doc_id = str(uuid.uuid4())
        
        # Split document into chunks
        chunks = self.text_splitter.split_text(document_text)
        
        # Generate embeddings for chunks
        chunk_embeddings = self._generate_embeddings(chunks)
        
        # Add chunks to the index
        faiss.normalize_L2(chunk_embeddings)
        self.index.add(chunk_embeddings)
        
        # Update metadata
        start_idx = len(self.metadata["chunks"])
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "text": chunk,
                "document_id": doc_id,
                "chunk_id": start_idx + i,
                "position": i
            }
            self.metadata["chunks"].append(chunk_metadata)
        
        # Add document metadata
        document_metadata = {
            "id": doc_id,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "chunk_ids": list(range(start_idx, start_idx + len(chunks)))
        }
        self.metadata["documents"].append(document_metadata)
        
        # Save the updated index and metadata
        self._save()
        
        return doc_id
    
    def _save(self):
        """Save the index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f)
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks based on the query.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List[Dict]: List of relevant chunks with metadata
        """
        # Generate query embedding
        query_embedding = self._generate_embeddings([query])
        faiss.normalize_L2(query_embedding)
        
        # Search the index
        distances, indices = self.index.search(query_embedding, k)
        
        # Get the metadata for the retrieved chunks
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata["chunks"]):
                chunk = self.metadata["chunks"][idx]
                results.append({
                    "text": chunk["text"],
                    "document_id": chunk["document_id"],
                    "score": float(1.0 / (1.0 + distances[0][i]))  # Convert distance to score
                })
        
        return results
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Optional[Dict]: Document metadata or None if not found
        """
        for doc in self.metadata["documents"]:
            if doc["id"] == doc_id:
                return doc
        return None
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get all documents in the system.
        
        Returns:
            List[Dict]: List of document metadata
        """
        return self.metadata["documents"]
    
    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            List[Dict]: List of chunks for the document
        """
        return [chunk for chunk in self.metadata["chunks"] if chunk["document_id"] == doc_id]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system.
        
        Returns:
            Dict: Statistics about the system
        """
        return {
            "num_documents": len(self.metadata["documents"]),
            "num_chunks": len(self.metadata["chunks"]),
            "embedding_dimensions": self.model.get_sentence_embedding_dimension()
        }