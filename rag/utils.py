#!/usr/bin/env python3
"""Common utility functions for document processing and handling."""

import os
import uuid
import logging
import concurrent.futures
from typing import List, Dict, Any, Optional, Union, Callable, Tuple
from datetime import datetime
import json
import time
import ssl
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Utility class for document processing."""
    
    @staticmethod
    def process_documents_parallel(documents, process_func, max_workers=4):
        """Process multiple documents in parallel.
        
        Args:
            documents: List of documents to process
            process_func: Function to process each document
            max_workers: Maximum number of parallel workers
            
        Returns:
            Tuple of (texts, metadatas, ids)
        """
        texts = []
        metadatas = []
        ids = []
        
        logger.info(f"Processing {len(documents)} documents in parallel with {max_workers} workers")
        
        # Process documents in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all documents for processing
            future_to_document = {executor.submit(process_func, doc): doc for doc in documents}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_document):
                document = future_to_document[future]
                try:
                    text, metadata = future.result()
                    
                    # Generate a unique ID for the document
                    if metadata.get('file_id'):
                        doc_id = metadata['file_id']
                    else:
                        doc_id = str(uuid.uuid4())
                    
                    # Add to output lists
                    texts.append(text)
                    metadatas.append(metadata)
                    ids.append(doc_id)
                    
                except Exception as e:
                    logger.error(f"Error processing document: {str(e)}")
        
        return texts, metadatas, ids
    
    @staticmethod
    def extract_google_drive_metadata(base_metadata, drive_item=None, auth_info=None):
        """Extract and standardize Google Drive metadata.
        
        Args:
            base_metadata: Base metadata dictionary
            drive_item: Google Drive item object
            auth_info: Authorization information
            
        Returns:
            Standardized metadata dictionary
        """
        metadata = base_metadata.copy() if base_metadata else {}
        
        # Extract file ID from various possible locations
        file_id = metadata.get('file_id') or metadata.get('source', '').split('://')[-1] or metadata.get('id', '')
        
        # Add standard properties
        if file_id:
            metadata['file_id'] = file_id
        
        # If we have drive_item, extract additional metadata
        if drive_item:
            metadata['source_type'] = 'google_drive'
            metadata['url'] = f"https://drive.google.com/file/d/{drive_item.get('id')}/view"
            
            # Extract basic properties
            for prop in ['name', 'mimeType', 'createdTime', 'modifiedTime', 'shared', 'starred', 'trashed', 'version', 'size', 'thumbnailLink']:
                if prop in drive_item:
                    # Convert property name to snake_case
                    snake_prop = ''.join(['_' + c.lower() if c.isupper() else c for c in prop]).lstrip('_')
                    metadata[snake_prop] = drive_item[prop]
            
            # Standardize names (id -> file_id, name -> title, etc.)
            if 'name' in metadata and 'title' not in metadata:
                metadata['title'] = metadata['name']
            
            # Handle owner information
            if 'owners' in drive_item:
                metadata['owner_names'] = [owner.get('displayName') for owner in drive_item['owners']]
                metadata['owner_emails'] = [owner.get('emailAddress') for owner in drive_item['owners']]
            
            # Handle last modifying user
            if 'lastModifyingUser' in drive_item:
                metadata['last_modified_by'] = drive_item['lastModifyingUser'].get('displayName')
            
            # Handle parent folders
            if 'parents' in drive_item:
                metadata['parent_folders'] = drive_item['parents']
        
        # Add auth/permission information if available
        if auth_info and 'permissions' in auth_info:
            metadata['permissions'] = auth_info['permissions']
            
            # Extract owners, editors, viewers, and commenters
            access_summary = {
                'owners': [],
                'editors': [],
                'viewers': [],
                'commenters': [],
                'is_public': False
            }
            
            for perm in auth_info['permissions']:
                role = perm.get('role', '').lower()
                email = perm.get('emailAddress')
                perm_type = perm.get('type')
                
                # Check if document is public
                if perm_type == 'anyone':
                    access_summary['is_public'] = True
                
                # Add email to appropriate role list
                if email:
                    if role == 'owner':
                        access_summary['owners'].append(email)
                    elif role == 'writer':
                        access_summary['editors'].append(email)
                    elif role == 'reader':
                        access_summary['viewers'].append(email)
                    elif role == 'commenter':
                        access_summary['commenters'].append(email)
            
            metadata['access_summary'] = access_summary
        
        return metadata
    
    @staticmethod
    def enrich_metadata(metadata, doc_type=None, additional_metadata=None):
        """Enrich metadata with standard fields.
        
        Args:
            metadata: Base metadata dictionary
            doc_type: Document type
            additional_metadata: Additional metadata to add
            
        Returns:
            Enriched metadata dictionary
        """
        enriched = metadata.copy()
        
        # Add standard metadata fields
        enriched['doc_type'] = doc_type or enriched.get('doc_type', 'unknown')
        enriched['processed_at'] = datetime.now().isoformat()
        
        # Add language if not present
        if 'language' not in enriched:
            enriched['language'] = 'en'
        
        # Add content type based on mime_type if available
        if 'mime_type' in enriched and 'content_type' not in enriched:
            mime_type = enriched['mime_type'].lower()
            if 'pdf' in mime_type:
                enriched['content_type'] = 'pdf'
            elif 'word' in mime_type or 'docx' in mime_type or 'doc' in mime_type:
                enriched['content_type'] = 'document'
            elif 'sheet' in mime_type or 'excel' in mime_type or 'xlsx' in mime_type:
                enriched['content_type'] = 'spreadsheet'
            elif 'presentation' in mime_type or 'ppt' in mime_type:
                enriched['content_type'] = 'presentation'
            elif 'text' in mime_type:
                enriched['content_type'] = 'text'
            elif 'image' in mime_type:
                enriched['content_type'] = 'image'
            else:
                enriched['content_type'] = 'other'
        
        # Add processing status
        enriched['status'] = 'processed'
        
        # Add version info if not present
        if 'version_info' not in enriched:
            enriched['version_info'] = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        # Add any additional metadata
        if additional_metadata:
            enriched.update(additional_metadata)
        
        return enriched
    
    @staticmethod
    def check_document_version(doc_id, metadata, content, supabase_client=None, table_name=None):
        """Check if document version needs updating.
        
        Args:
            doc_id: Document ID
            metadata: Document metadata
            content: Document content
            supabase_client: Supabase client
            table_name: Table name
            
        Returns:
            Tuple of (needs_update, existing_metadata, content_changed, metadata_update_only)
            - needs_update: True if document needs version update
            - existing_metadata: Existing document metadata or None if document is new
            - content_changed: True if content has changed, False if only metadata changed
            - metadata_update_only: True if only metadata changed but not content
        """
        if not supabase_client or not table_name:
            # No way to check versions, assume it's new
            return False, None, False, False
        
        try:
            # Check if document exists
            response = supabase_client.table(table_name).select("id, metadata, content").eq("id", doc_id).execute()
            
            if hasattr(response, 'data') and response.data:
                # Document exists, check if it needs updating
                existing_doc = response.data[0]
                existing_metadata = existing_doc.get('metadata', {})
                existing_content = existing_doc.get('content', '')
                
                # Initialize flags
                needs_update = False
                content_changed = False
                metadata_update_only = False
                
                # Check if content has changed - only this should trigger a re-embedding
                if content != existing_content:
                    logger.info(f"Document {doc_id} content has changed, will update version and re-embed")
                    needs_update = True
                    content_changed = True
                
                # Check if modified_time has changed (if available)
                elif metadata.get('modified_time') and existing_metadata.get('modified_time'):
                    if metadata['modified_time'] > existing_metadata['modified_time']:
                        logger.info(f"Document {doc_id} modified time has changed, but content is identical - SKIPPING update")
                        # We don't mark it for update since content is the same
                        needs_update = False
                        content_changed = False
                        metadata_update_only = True
                
                # No changes detected
                if not needs_update and not metadata_update_only:
                    logger.info(f"Document {doc_id} has not changed, will not update")
                
                return needs_update, existing_metadata, content_changed, metadata_update_only
            else:
                # Document doesn't exist
                logger.info(f"Document {doc_id} is new, will create")
                return False, None, False, False
                
        except Exception as e:
            logger.warning(f"Error checking document version: {str(e)}")
            # Assume it needs updating in case of error
            return True, None, True, False

def list_drive_folders(auth=None, folder_id=None, depth=1):
    """List folders in Google Drive.
    
    Args:
        auth: GoogleDriveAuth instance
        folder_id: ID of the folder to list (None for root)
        depth: How many levels to traverse
        
    Returns:
        Dictionary of folder structure
    """
    if auth is None:
        from .auth import GoogleDriveAuth
        auth = GoogleDriveAuth()
    
    service = auth.get_drive_service()
    
    def get_folder_details(folder_id, current_depth=0):
        """Recursively get folder details."""
        if current_depth >= depth:
            return {"name": "...", "id": folder_id, "folders": []}
        
        if folder_id:
            # Get folder details
            folder = service.files().get(fileId=folder_id, fields="name,id").execute()
            name = folder.get("name", "Unknown")
            
            # Get subfolders
            query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        else:
            # Root folder
            name = "My Drive"
            
            # Get top-level folders
            query = "mimeType='application/vnd.google-apps.folder' and 'root' in parents and trashed=false"
        
        # Get subfolders
        results = service.files().list(q=query, fields="files(id, name)").execute()
        subfolders = results.get("files", [])
        
        # Recursively get subfolder details
        subfolder_details = []
        for subfolder in subfolders:
            if current_depth + 1 < depth:
                subfolder_details.append(get_folder_details(subfolder["id"], current_depth + 1))
            else:
                subfolder_details.append({"name": subfolder["name"], "id": subfolder["id"], "folders": []})
        
        return {
            "name": name,
            "id": folder_id,
            "folders": subfolder_details
        }
    
    return get_folder_details(folder_id)

def process_with_timeout(func, *args, timeout=180, **kwargs):
    """Execute a function with a timeout to prevent hanging.
    
    Args:
        func: Function to execute
        timeout: Maximum execution time in seconds
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function or None if timeout
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.warning(f"Function {func.__name__} timed out after {timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"Function {func.__name__} failed with error: {str(e)}")
            return None
            
def get_drive_permissions(file_id, drive_service, use_unverified_context=True, timeout=15):
    """Get Google Drive permissions directly with enhanced error handling.
    
    Args:
        file_id: Google Drive file ID
        drive_service: Google Drive API service instance
        use_unverified_context: Whether to use unverified SSL context
        timeout: Timeout in seconds (reduced to 15s to prevent long hangs)
        
    Returns:
        List of permissions or empty list if error
    """
    # Save original SSL context
    original_ssl_context = ssl._create_default_https_context
    original_timeout = socket.getdefaulttimeout()
    
    try:
        # Apply timeout
        socket.setdefaulttimeout(timeout)
        
        # Use unverified context if requested (helps with SSL issues)
        if use_unverified_context:
            ssl._create_default_https_context = ssl._create_unverified_context
        
        # Get permissions with the correct parameters
        permissions_response = drive_service.permissions().list(
            fileId=file_id,
            fields="permissions(id, type, emailAddress, role, displayName)",
            supportsAllDrives=True,
            pageSize=100
        ).execute()
        
        permissions = permissions_response.get('permissions', [])
        
        # Handle pagination if there are more permissions
        page_token = permissions_response.get('nextPageToken')
        while page_token:
            next_page = drive_service.permissions().list(
                fileId=file_id,
                fields="permissions(id, type, emailAddress, role, displayName)",
                supportsAllDrives=True,
                pageSize=100,
                pageToken=page_token
            ).execute()
            permissions.extend(next_page.get('permissions', []))
            page_token = next_page.get('nextPageToken')
        
        logger.info(f"Successfully fetched {len(permissions)} permissions for {file_id}")
        return permissions
    
    except Exception as e:
        # Check if this is an SSL error and provide a reassuring message
        if "SSL:" in str(e):
            logger.info(f"SSL connection issue detected for permissions - this is normal and will be handled during processing")
            logger.debug(f"SSL details: {str(e)}")
        else:
            logger.warning(f"Could not fetch permissions for file {file_id}: {str(e)}")
        
        return []
    
    finally:
        # Restore original SSL context and timeout
        ssl._create_default_https_context = original_ssl_context
        socket.setdefaulttimeout(original_timeout)

def process_documents_parallel(processor_func, documents, max_workers=None, chunk_size=1, timeout_per_doc=60):
    """Process a list of documents in parallel.
    
    Args:
        processor_func: Function to process each document
        documents: List of documents to process
        max_workers: Maximum number of parallel workers
        chunk_size: Number of documents to process per worker
        timeout_per_doc: Maximum time per document in seconds
        
    Returns:
        List of processing results
    """
    if not documents:
        return []
        
    # Determine number of workers based on CPU count
    if max_workers is None:
        max_workers = min(len(documents), os.cpu_count() or 4)
    
    logger.info(f"Processing {len(documents)} documents in parallel with {max_workers} workers")
    results = []
    
    # Use ThreadPoolExecutor instead of ProcessPoolExecutor to avoid pickle errors
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for i, doc in enumerate(documents):
            future = executor.submit(processor_func, doc)
            futures[future] = i
            
        # Track completion and apply timeout
        start_time = time.time()
        completed = 0
        for future in concurrent.futures.as_completed(futures.keys()):
            doc_index = futures[future]
            try:
                # Check if this document has been processing too long
                if time.time() - start_time > timeout_per_doc:
                    logger.warning(f"Document {doc_index} processing timed out after {timeout_per_doc} seconds")
                    results.append((None, None))
                else:
                    result = future.result(timeout=timeout_per_doc)
                    results.append(result)
                    completed += 1
                    logger.debug(f"Completed document {doc_index} ({completed}/{len(documents)})")
            except concurrent.futures.TimeoutError:
                logger.warning(f"Document {doc_index} timed out during result collection")
                results.append((None, None))
            except Exception as e:
                logger.error(f"Error processing document {doc_index}: {str(e)}")
                results.append((None, None))
                
    return results