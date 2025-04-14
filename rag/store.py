#!/usr/bin/env python3
"""Vector store interface for different vector database implementations."""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class VectorStoreInterface:
    """Abstract interface for vector database operations."""
    
    def __init__(self, collection_name: str):
        """Initialize a vector store interface.
        
        Args:
            collection_name: Name of the collection to use
        """
        self.collection_name = collection_name
    
    def add_documents(self, documents, metadatas, ids):
        """Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique IDs for the documents
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def query(self, query_text, n_results=5, where=None):
        """Query the vector store for similar documents.
        
        Args:
            query_text: Text to query
            n_results: Number of results to return
            where: Filter query based on metadata
            
        Returns:
            Dictionary with query results
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_collection_stats(self):
        """Get statistics about the collection.
        
        Returns:
            Dictionary with count of documents and other stats
        """
        raise NotImplementedError("Subclasses must implement this method")

class SupabaseStore(VectorStoreInterface):
    """A wrapper for Supabase vector database operations."""
    
    def __init__(
        self, 
        collection_name: str = "documents",
        create_table_if_not_exists: bool = True
    ):
        """Initialize the Supabase vector store.
        
        Args:
            collection_name: Name of the collection/table to use
            create_table_if_not_exists: Whether to create the table if it doesn't exist
        """
        super().__init__(collection_name)
        self.table_name = collection_name
        
        # Get Supabase credentials from environment
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip("'")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "").strip("'")
        
        # Try to get postgres URL directly or construct it
        self.postgres_url = os.getenv("SUPABASE_POSTGRES_URL", "").strip("'")
        
        # If postgres URL is not provided, try to construct it
        if not self.postgres_url:
            project_ref = os.getenv("SUPABASE_PROJECT_REF", "").strip("'")
            if not project_ref and self.supabase_url:
                # Extract project ref from supabase URL if available
                try:
                    project_ref = self.supabase_url.replace("https://", "").replace("http://", "").split(".")[0]
                except:
                    pass
            
            if project_ref:
                # We need a password for postgres connection
                # This is a fallback assuming default postgres user and trying to extract password from service key
                # This is a heuristic and may not always work
                password = "postgres"  # Default fallback
                try:
                    # Try to extract some unique string from the service key to use as password
                    if self.supabase_key and len(self.supabase_key) > 20:
                        # Use part of the service key as password
                        password = self.supabase_key.split(".")[1][:16]
                except:
                    logger.warning("Could not extract password from service key, using default")
                
                # Construct postgres URL
                self.postgres_url = f"postgres://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
                logger.info(f"Dynamically constructed postgres URL using project ref: {project_ref}")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Supabase credentials not found. Please set SUPABASE_URL and "
                "SUPABASE_SERVICE_KEY environment variables."
            )
        
        try:
            # Import and initialize Supabase client
            from supabase import create_client, Client
            
            logger.info(f"Initializing Supabase client with URL: {self.supabase_url}")
            
            # Check URL format and resolve hostname
            import socket
            url_hostname = self.supabase_url.replace("https://", "").replace("http://", "").split("/")[0]
            try:
                socket.gethostbyname(url_hostname)
                logger.info(f"Successfully resolved host: {url_hostname}")
            except socket.gaierror:
                logger.warning(f"Could not resolve host: {url_hostname}")
                # Try with project ID instead
                project_id = os.getenv("SUPABASE_PROJECT_ID", "").strip("'")
                if project_id:
                    new_url = f"https://{project_id}.supabase.co"
                    try:
                        new_hostname = new_url.replace("https://", "").replace("http://", "").split("/")[0]
                        socket.gethostbyname(new_hostname)
                        logger.info(f"Successfully resolved alternative host: {new_hostname}")
                        
                        # Update the URL
                        self.supabase_url = new_url
                        logger.info(f"Updated URL to: {self.supabase_url}")
                    except socket.gaierror:
                        logger.error(f"Could not resolve alternative host either: {new_hostname}")
                else:
                    logger.error("No SUPABASE_PROJECT_ID available to try as alternative")
            
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Successfully initialized Supabase client")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    def get_langchain_store(self, embedding_function):
        """Get a LangChain Supabase vector store.
        
        Args:
            embedding_function: The embedding function to use
            
        Returns:
            A LangChain SupabaseVectorStore instance
        """
        from langchain_community.vectorstores import SupabaseVectorStore
        
        try:
            # Determine the appropriate query function name based on table_name
            query_name = "match_documents"
            if self.table_name == "langchain_example":
                query_name = "match_langchain_documents"
            elif self.table_name == "langchain_docs":
                query_name = "match_langchain_docs"
            
            # Create the vector store
            store = SupabaseVectorStore(
                client=self.client,
                embedding=embedding_function,
                table_name=self.table_name,
                query_name=query_name
            )
            
            # Check available search methods for debugging
            search_methods = []
            if hasattr(store, 'similarity_search'):
                search_methods.append('similarity_search')
            if hasattr(store, 'similarity_search_with_score'):
                search_methods.append('similarity_search_with_score')
            if hasattr(store, 'search'):
                search_methods.append('search')
            if hasattr(store, 'get_relevant_documents'):
                search_methods.append('get_relevant_documents')
                
            logger.info(f"Available search methods: {', '.join(search_methods)}")
            
            # Add custom similarity_search_with_score method
            logger.info("Adding custom similarity_search_with_score method")
            def custom_similarity_search_with_score(self, query, k=4, filter=None):
                """Custom similarity_search_with_score implementation."""
                logger.info(f"Using custom similarity_search_with_score with k={k}")
                try:
                    # Generate embedding for the query
                    query_embedding = self._embedding.embed_query(query)
                    
                    # Define parameters with both match_count and max_results
                    params = {
                        "query_embedding": query_embedding,
                        "match_count": k,
                        "max_results": k
                    }
                    
                    if filter is not None:
                        logger.warning("Filters not fully implemented in custom method")
                    
                    # Make the query
                    logger.debug(f"Executing RPC with params: {params}")
                    response = self._client.rpc(self.query_name, params).execute()
                    
                    if not response.data:
                        return []
                    
                    # Process results
                    from langchain_core.documents import Document
                    results = []
                    for result in response.data:
                        document = Document(
                            page_content=result["content"],
                            metadata=result["metadata"]
                        )
                        results.append((document, result["similarity"]))
                    
                    logger.info(f"Custom method returned {len(results)} results with scores")
                    return results
                    
                except Exception as e:
                    logger.error(f"Error in custom similarity_search_with_score: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise
            
            # Add method to the instance
            import types
            store.similarity_search_with_score = types.MethodType(custom_similarity_search_with_score, store)
            
            # Add our own similarity_search method if needed
            if 'similarity_search' not in search_methods:
                logger.info("Adding custom similarity_search method")
                def custom_similarity_search(self, query, k=4, filter=None):
                    """Custom similarity_search implementation."""
                    logger.info(f"Using custom similarity_search with k={k}")
                    try:
                        # Use our custom similarity_search_with_score and extract just the documents
                        results_with_scores = self.similarity_search_with_score(query, k=k, filter=filter)
                        return [doc for doc, _ in results_with_scores]
                    except Exception as e:
                        logger.error(f"Error in custom_similarity_search: {str(e)}")
                        
                        # Fallback to original implementation if available
                        if hasattr(self, 'similarity_search_by_vector'):
                            logger.info("Falling back to similarity_search_by_vector")
                            query_embedding = self._embedding.embed_query(query)
                            return self.similarity_search_by_vector(query_embedding, k=k, filter=filter)
                        else:
                            logger.warning("No suitable search method found")
                            return []
                
                # Add method to the instance
                store.similarity_search = types.MethodType(custom_similarity_search, store)
            
            # Log success
            logger.info("Successfully created LangChain Supabase vector store")
            return store
        
        except Exception as e:
            logger.error(f"Failed to create LangChain Supabase vector store: {str(e)}")
            raise
    
    def query_raw(self, query_text: str, match_count: int = 5) -> Dict[str, Any]:
        """Perform a raw query directly using Supabase.
        
        Args:
            query_text: Text to query
            match_count: Number of matches to return
            
        Returns:
            Query results
        """
        # This method needs an embedding function to work properly
        logger.warning("query_raw() method called but is not fully implemented - needs embedding function")
        logger.info("Use LangChain or other interfaces for querying instead")
        
        # Return empty results
        return {"results": [], "message": "Direct query not implemented. Use LangChain interface instead."}
    
    def debug_metadata_retrieval(self, limit: int = 5) -> Dict[str, Any]:
        """Debug function to directly query metadata from Supabase without embeddings.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            Dictionary with debug information
        """
        logger.info(f"Attempting direct debug query of table {self.table_name} for metadata inspection")
        
        try:
            # Direct query to get metadata from the table
            response = self.client.table(self.table_name).select("id, metadata").limit(limit).execute()
            
            # Log the structure of the response for debugging
            logger.info(f"Supabase response structure: {type(response)}")
            if hasattr(response, 'data'):
                logger.info(f"Response data type: {type(response.data)}")
                logger.info(f"Response data length: {len(response.data)}")
                
                if len(response.data) > 0:
                    logger.info(f"First record keys: {response.data[0].keys() if isinstance(response.data[0], dict) else 'not a dict'}")
                    
                    # Check if metadata exists and what type it is
                    if isinstance(response.data[0], dict) and 'metadata' in response.data[0]:
                        metadata = response.data[0]['metadata']
                        logger.info(f"Metadata type: {type(metadata)}")
                        logger.info(f"Metadata content sample: {str(metadata)[:100]}")
                    else:
                        logger.warning("No metadata field found in the first record")
                
                return {
                    "status": "success",
                    "records_found": len(response.data),
                    "sample_data": response.data[:limit],
                    "message": "Direct metadata query completed"
                }
            else:
                logger.warning("No data attribute in Supabase response")
                return {
                    "status": "error", 
                    "message": "No data attribute in Supabase response",
                    "raw_response": str(response)
                }
        
        except Exception as e:
            logger.error(f"Error in debug_metadata_retrieval: {str(e)}")
            return {"status": "error", "message": str(e)}