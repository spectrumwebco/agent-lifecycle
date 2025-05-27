"""
RAGflow integration for the python_agent app.

This module provides integration with RAGflow vector database,
enabling deep search and understanding capabilities.
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from django.conf import settings

logger = logging.getLogger(__name__)


class RAGflowClient:
    """
    Client for interacting with RAGflow vector database.
    
    This client provides methods for storing, retrieving, and searching
    documents in the RAGflow vector database.
    """
    
    def __init__(self, host=None, port=None, api_key=None, index_name=None):
        """
        Initialize the RAGflow client.
        
        Args:
            host: RAGflow host
            port: RAGflow port
            api_key: RAGflow API key
            index_name: RAGflow index name
        """
        vector_db_config = getattr(settings, 'VECTOR_DB_CONFIG', {})
        
        self.host = host or vector_db_config.get('host', 'localhost')
        self.port = port or vector_db_config.get('port', 8000)
        self.api_key = api_key or vector_db_config.get('api_key', '')
        self.index_name = index_name or vector_db_config.get('index_name', 'agent-docs')
        
        self.base_url = f"http://{self.host}:{self.port}"
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for RAGflow API requests.
        
        Returns:
            Dict[str, str]: Headers for RAGflow API requests
        """
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        
        return headers
    
    def store_document(self, document: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store a document in the RAGflow vector database.
        
        Args:
            document: Document to store
            metadata: Metadata for the document
            
        Returns:
            Dict[str, Any]: Response from RAGflow
        """
        try:
            url = f"{self.base_url}/api/v1/documents"
            
            payload = {
                'index_name': self.index_name,
                'document': document,
                'metadata': metadata or {},
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error storing document in RAGflow: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def store_documents(self, documents: List[Dict[str, Any]], metadata: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Store multiple documents in the RAGflow vector database.
        
        Args:
            documents: Documents to store
            metadata: Metadata for the documents
            
        Returns:
            Dict[str, Any]: Response from RAGflow
        """
        try:
            url = f"{self.base_url}/api/v1/documents/batch"
            
            if metadata is None:
                metadata = [{} for _ in documents]
            
            payload = {
                'index_name': self.index_name,
                'documents': documents,
                'metadata': metadata,
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error storing documents in RAGflow: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def search(self, query: str, top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for documents in the RAGflow vector database.
        
        Args:
            query: Query to search for
            top_k: Number of results to return
            filter_metadata: Metadata filter for the search
            
        Returns:
            Dict[str, Any]: Search results
        """
        try:
            url = f"{self.base_url}/api/v1/search"
            
            payload = {
                'index_name': self.index_name,
                'query': query,
                'top_k': top_k,
                'filter_metadata': filter_metadata or {},
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error searching in RAGflow: {e}")
            return {'status': 'error', 'message': str(e), 'results': []}
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """
        Get a document from the RAGflow vector database.
        
        Args:
            document_id: ID of the document to get
            
        Returns:
            Dict[str, Any]: Document
        """
        try:
            url = f"{self.base_url}/api/v1/documents/{document_id}"
            
            params = {
                'index_name': self.index_name,
            }
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error getting document from RAGflow: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document from the RAGflow vector database.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            Dict[str, Any]: Response from RAGflow
        """
        try:
            url = f"{self.base_url}/api/v1/documents/{document_id}"
            
            params = {
                'index_name': self.index_name,
            }
            
            response = requests.delete(
                url,
                headers=self._get_headers(),
                params=params
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error deleting document from RAGflow: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def update_document(self, document_id: str, document: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update a document in the RAGflow vector database.
        
        Args:
            document_id: ID of the document to update
            document: Updated document
            metadata: Updated metadata for the document
            
        Returns:
            Dict[str, Any]: Response from RAGflow
        """
        try:
            url = f"{self.base_url}/api/v1/documents/{document_id}"
            
            payload = {
                'index_name': self.index_name,
                'document': document,
                'metadata': metadata or {},
            }
            
            response = requests.put(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error updating document in RAGflow: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def semantic_search(self, query: str, top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform semantic search in the RAGflow vector database.
        
        This method performs a semantic search, which uses deep understanding
        to find documents that are semantically similar to the query.
        
        Args:
            query: Query to search for
            top_k: Number of results to return
            filter_metadata: Metadata filter for the search
            
        Returns:
            Dict[str, Any]: Search results
        """
        try:
            url = f"{self.base_url}/api/v1/semantic_search"
            
            payload = {
                'index_name': self.index_name,
                'query': query,
                'top_k': top_k,
                'filter_metadata': filter_metadata or {},
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error performing semantic search in RAGflow: {e}")
            return {'status': 'error', 'message': str(e), 'results': []}
    
    def hybrid_search(self, query: str, top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform hybrid search in the RAGflow vector database.
        
        This method performs a hybrid search, which combines keyword search
        and semantic search to find documents that match the query.
        
        Args:
            query: Query to search for
            top_k: Number of results to return
            filter_metadata: Metadata filter for the search
            
        Returns:
            Dict[str, Any]: Search results
        """
        try:
            url = f"{self.base_url}/api/v1/hybrid_search"
            
            payload = {
                'index_name': self.index_name,
                'query': query,
                'top_k': top_k,
                'filter_metadata': filter_metadata or {},
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error performing hybrid search in RAGflow: {e}")
            return {'status': 'error', 'message': str(e), 'results': []}


ragflow_client = RAGflowClient()
