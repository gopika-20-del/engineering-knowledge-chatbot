"""Database initialization and management for ChromaDB"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict
import chromadb
from backend.config import CHROMA_DB_PATH

class VectorDatabase:
    """ChromaDB vector database handler"""
    
    def __init__(self):
        """Initialize ChromaDB client with new API"""
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = None
        self._init_collection()
    
    def _init_collection(self):
        """Initialize or get the documents collection"""
        try:
            self.collection = self.client.get_collection(
                name="engineering_docs"
            )
        except:
            self.collection = self.client.create_collection(
                name="engineering_docs",
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_document(self, doc_id: str, content: str, metadata: Dict) -> None:
        """Add a document to the vector database"""
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata]
        )
    
    def search(self, query: str, n_results: int = 5, where: Optional[Dict] = None) -> List[Dict]:
        """Search documents using semantic similarity with optional metadata filter"""
        kwargs = {
            "query_texts": [query],
            "n_results": n_results
        }
        if where:
            kwargs["where"] = where
            
        results = self.collection.query(**kwargs)
        
        formatted_results = []
        if results['ids'] and len(results['ids']) > 0:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted_results.append({
                    'id': doc_id,
                    'document': results['documents'][0][i] if results['documents'] else "",
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0
                })
        
        return formatted_results
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the database"""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    def get_all_documents(self) -> List[Dict]:
        """Retrieve all documents"""
        try:
            results = self.collection.get()
            formatted_results = []
            if results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    formatted_results.append({
                        'id': doc_id,
                        'metadata': results['metadatas'][i] if results['metadatas'] else {}
                    })
            return formatted_results
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
    
    def close(self):
        """Close the database connection"""
        pass  # PersistentClient doesn't need to be closed

# Global instance
db = VectorDatabase()
