#!/usr/bin/env python3
"""Query functionality for RAG systems."""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

# Import core modules
from .store import SupabaseStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def query_langchain(
    query: str,
    collection_name: str = "langchain_docs",
    top_k: int = 5,
    metadata_filter: Optional[Dict[str, Any]] = None,
    user_email: Optional[str] = None,
    enforce_security: bool = False
) -> Dict[str, Any]:
    """Query documents using LangChain.
    
    Args:
        query: The query text
        collection_name: The collection name to query
        top_k: Maximum number of results to return
        metadata_filter: Metadata filters to apply
        user_email: User email for security filtering
        enforce_security: Whether to enforce security filtering
        
    Returns:
        Dictionary with query results
    """
    logger.info(f"Querying LangChain collection '{collection_name}' for: {query}")
    
    try:
        # Import required LangChain modules
        from langchain_openai import OpenAIEmbeddings
        
        # Initialize embedding model
        embeddings = OpenAIEmbeddings()
        
        # Initialize Supabase store
        store = SupabaseStore(collection_name=collection_name)
        vectorstore = store.get_langchain_store(embeddings)
        
        # Apply security filtering if requested
        if enforce_security:
            logger.info(f"Enforcing security filters for user: {user_email}")
            security_filter = build_security_filter(user_email)
            
            # Combine security filter with any existing metadata filter
            if metadata_filter:
                combined_filter = {**metadata_filter, **security_filter}
            else:
                combined_filter = security_filter
                
            metadata_filter = combined_filter
        
        # Log the filter being used
        if metadata_filter:
            logger.info(f"Using metadata filter: {metadata_filter}")
        
        # Execute the query
        if metadata_filter:
            # Search with metadata filter
            try:
                logger.info(f"Attempting similarity_search_with_score with k={top_k}")
                results_with_scores = vectorstore.similarity_search_with_score(
                    query=query,
                    k=top_k,
                    filter=metadata_filter
                )
                
                # Process results
                results = []
                for doc, score in results_with_scores:
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": score
                    })
                    
                logger.info(f"Found {len(results)} results with metadata filtering")
            except Exception as e:
                logger.error(f"Error with similarity_search_with_score: {str(e)}")
                # Log the traceback for more details
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                logger.info("Falling back to similarity_search")
                
                # Fall back to regular search without scoring
                docs = vectorstore.similarity_search(
                    query=query,
                    k=top_k,
                    filter=metadata_filter
                )
                
                # Process results without scores
                results = []
                for doc in docs:
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": None  # No similarity score available
                    })
                    
                logger.info(f"Found {len(results)} results with fallback method")
        else:
            # Search without metadata filter
            try:
                logger.info(f"Attempting similarity_search_with_score with k={top_k}")
                results_with_scores = vectorstore.similarity_search_with_score(
                    query=query,
                    k=top_k
                )
                
                # Process results
                results = []
                for doc, score in results_with_scores:
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": score
                    })
                    
                logger.info(f"Found {len(results)} results without filtering")
            except Exception as e:
                logger.error(f"Error with similarity_search_with_score: {str(e)}")
                # Log the traceback for more details
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                logger.info("Falling back to similarity_search")
                
                # Fall back to regular search without scoring
                docs = vectorstore.similarity_search(
                    query=query,
                    k=top_k
                )
                
                # Process results without scores
                results = []
                for doc in docs:
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": None  # No similarity score available
                    })
                    
                logger.info(f"Found {len(results)} results with fallback method")
        
        # Return results with additional information
        return {
            "query": query,
            "collection": collection_name,
            "results": results,
            "count": len(results),
            "filter_applied": metadata_filter is not None,
            "security_filtered": enforce_security
        }
        
    except Exception as e:
        logger.error(f"Error querying documents with LangChain: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "query": query,
            "collection": collection_name,
            "results": [],
            "count": 0,
            "error": str(e)
        }

def build_security_filter(user_email: Optional[str] = None) -> Dict[str, Any]:
    """Build security filter based on user email.
    
    Args:
        user_email: User email for security filtering
        
    Returns:
        Security filter dictionary
    """
    # If no user email is provided, only return public documents
    if not user_email:
        return {"access_summary.is_public": True}
    
    # For a specific user, return documents they have access to
    # This includes:
    # 1. Documents they own
    # 2. Documents they have edit access to
    # 3. Documents they have view access to
    # 4. Documents they have comment access to
    # 5. Public documents
    
    # Use the $or operator to match any of these conditions
    return {
        "$or": [
            {"access_summary.owners": user_email},
            {"access_summary.editors": user_email},
            {"access_summary.viewers": user_email},
            {"access_summary.commenters": user_email},
            {"access_summary.is_public": True}
        ]
    }

def format_results(results: Dict[str, Any], max_content_length: int = 200) -> str:
    """Format query results for display.
    
    Args:
        results: Query results dictionary
        max_content_length: Maximum content length to show
        
    Returns:
        Formatted string
    """
    if not results or not results.get("results"):
        return "No results found."
    
    formatted = f"Found {results['count']} results for query: '{results['query']}'\n\n"
    
    for i, item in enumerate(results["results"]):
        content = item["content"]
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
            
        metadata = item["metadata"]
        similarity = item.get("similarity")
        
        formatted += f"Result {i+1}:\n"
        formatted += f"Content: {content}\n"
        
        if similarity is not None:
            formatted += f"Similarity: {similarity:.4f}\n"
            
        # Show key metadata fields
        if "title" in metadata:
            formatted += f"Title: {metadata['title']}\n"
        if "file_name" in metadata:
            formatted += f"File: {metadata['file_name']}\n"
        
        formatted += "\n"
    
    return formatted