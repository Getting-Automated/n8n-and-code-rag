#!/usr/bin/env python3
"""Document ingestion functionality for RAG systems."""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Callable, Type, Tuple
from datetime import datetime
from dotenv import load_dotenv
import ssl
import time
import uuid
import json
import socket

# Import core modules
from .auth import GoogleDriveAuth
from .store import SupabaseStore
from .utils import DocumentProcessor

# Set a reasonable socket timeout for API calls
socket.setdefaulttimeout(60)  # 60 seconds timeout

# LangChain imports
try:
    # Try importing from recommended packages
    from langchain_community.document_loaders import UnstructuredFileIOLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.documents import Document
    
    # Check if langchain_google_community is installed, if not install it
    try:
        from langchain_google_community.drive import GoogleDriveLoader
    except ImportError:
        import subprocess
        import sys
        print("Installing langchain-google-community...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain-google-community"])
        from langchain_google_community.drive import GoogleDriveLoader
        
except ImportError:
    logging.warning("LangChain libraries not installed. Run: pip install langchain langchain_community langchain_openai langchain-google-community langchain-text-splitters")
    # Define stub classes for when imports fail
    class Document:
        def __init__(self, page_content="", metadata=None):
            self.page_content = page_content
            self.metadata = metadata or {}
    
    # Define OpenAIEmbeddings as a stub class
    class OpenAIEmbeddings:
        def __init__(self, *args, **kwargs):
            pass
        
        def embed_documents(self, texts):
            logging.warning("Using stub OpenAIEmbeddings - no actual embedding will occur")
            return [[0.0] * 1536 for _ in texts]  # Return empty vectors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def fetch_direct_permissions(file_id: str, google_auth: Any) -> List[Dict[str, Any]]:
    """Fetch permissions directly using Drive API with enhanced error handling.
    
    Args:
        file_id: Google Drive file ID
        google_auth: GoogleDriveAuth instance
        
    Returns:
        List of permission objects with user details
    """
    try:
        # Get the Drive service
        service = google_auth.get_drive_service()
        
        # Use fields approach for optimal performance
        file = service.files().get(
            fileId=file_id,
            fields="permissions(id,type,emailAddress,role,displayName)"
        ).execute()
        
        # Extract and return permissions
        permissions = file.get("permissions", [])
        logger.info(f"Successfully fetched {len(permissions)} permissions for {file_id}")
        return permissions
        
    except Exception as e:
        # Check for SSL errors
        if isinstance(e, ssl.SSLError) or "SSL" in str(e):
            logger.info(f"SSL connection issue detected - using basic metadata for {file_id} (this is normal and handled gracefully)")
        else:
            logger.error(f"Error fetching permissions for {file_id}: {str(e)}")
        return []

class LangChainIngestion:
    """Document ingestion pattern using LangChain."""
    
    def __init__(
        self, 
        collection_name: str = "langchain_docs"
    ):
        """Initialize the LangChain ingestion pattern.
        
        Args:
            collection_name: Name of the collection to store documents
        """
        self.collection_name = collection_name
        
        # Initialize Google Drive auth
        self.google_auth = GoogleDriveAuth()
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings()
        
        # Initialize Supabase store
        try:
            self.supabase_store = SupabaseStore(collection_name=self.collection_name)
            self.vectorstore = self.supabase_store.get_langchain_store(self.embeddings)
            logger.info("Successfully initialized Supabase store and vector store")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase store: {str(e)}")
            raise
    
    def load_documents_from_drive(
        self, 
        folder_id: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        file_types: Optional[List[str]] = None,
        recursive: bool = False,
        load_auth: bool = False,
        load_extended_metadata: bool = False,
        custom_query: Optional[str] = None,
        file_loader_cls: Optional[Type] = None,
        file_loader_kwargs: Optional[Dict[str, Any]] = None,
        max_results: Optional[int] = None
    ) -> List:
        """Load documents from Google Drive.
        
        Args:
            folder_id: ID of the Google Drive folder
            file_ids: List of specific file IDs to load (optional)
            file_types: List of file extensions to include (e.g., ['pdf', 'docx'])
            recursive: Whether to recursively search subfolders
            load_auth: Whether to load auth identities
            load_extended_metadata: Whether to load extended metadata
            custom_query: Custom query string for Google Drive search
            file_loader_cls: Optional file loader class for non-Google document types
            file_loader_kwargs: Optional kwargs for the file loader
            max_results: Maximum number of results to return
            
        Returns:
            List of LangChain documents
        """
        logger.info("Loading documents from Google Drive")
        
        # Get credentials
        creds = self.google_auth.get_credentials()
        service = self.google_auth.get_drive_service()
        
        # Verify the folder exists and we have access
        if folder_id:
            try:
                folder = service.files().get(
                    fileId=folder_id,
                    supportsAllDrives=True
                ).execute()
                logger.info(f"Successfully accessed folder: {folder.get('name', folder_id)}")
            except Exception as e:
                logger.error(f"Error accessing folder {folder_id}: {str(e)}")
                raise ValueError(f"Could not access folder with ID {folder_id}: {str(e)}")
        
        # List files in the folder to manually process if needed
        folder_files = []
        documents = []  # Initialize the documents list before use
        
        if folder_id:
            try:
                query = f"'{folder_id}' in parents and trashed=false"
                files = service.files().list(
                    q=query,
                    supportsAllDrives=True,
                    fields="files(id, name, mimeType, createdTime, modifiedTime)"
                ).execute()
                folder_files = files.get('files', [])
                logger.info(f"Found {len(folder_files)} files in the specified folder")
                for item in folder_files[:5]:  # Show first 5 files for debugging
                    logger.info(f"  - {item.get('name')} ({item.get('id')}) [MIME: {item.get('mimeType')}]")
            except Exception as e:
                logger.error(f"Error listing files in folder {folder_id}: {str(e)}")
        
        # Specially handle DOCX files which can have issues with LangChain loader
        docx_files = [file for file in folder_files if file.get('mimeType') == 
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        
        if docx_files:
            logger.info(f"Found {len(docx_files)} DOCX files to manually process")
            
            # Process DOCX files manually
            import io
            import docx2txt
            from googleapiclient.http import MediaIoBaseDownload
            
            for file in docx_files:
                file_id = file.get('id')
                file_name = file.get('name')
                
                try:
                    # Download the file content
                    request = service.files().get_media(fileId=file_id)
                    file_content = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_content, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    
                    # Reset the pointer to the beginning of the file content
                    file_content.seek(0)
                    
                    # Extract text using docx2txt
                    text = docx2txt.process(file_content)
                    
                    # Create metadata
                    metadata = {
                        "source": f"google-drive://{file_id}",
                        "file_id": file_id,
                        "file_name": file_name,
                        "mime_type": file.get('mimeType'),
                        "created_time": file.get('createdTime'),
                        "modified_time": file.get('modifiedTime')
                    }
                    
                    # Create document
                    doc = Document(page_content=text, metadata=metadata)
                    documents.append(doc)
                    logger.info(f"Successfully processed DOCX file: {file_name}")
                    
                except Exception as e:
                    logger.error(f"Error processing DOCX file {file_name}: {str(e)}")
                    continue
        
        # Initialize loader kwargs
        loader_kwargs = {
            "credentials": creds,
            "recursive": recursive
        }
        
        if folder_id:
            loader_kwargs["folder_id"] = folder_id
            logger.info(f"Targeting folder ID: {folder_id}")
        elif file_ids:
            loader_kwargs["file_ids"] = file_ids
            logger.info(f"Targeting specific files: {file_ids}")
        else:
            raise ValueError("Either folder_id or file_ids must be provided")
        
        # Add file_types if provided
        if file_types:
            loader_kwargs["file_types"] = file_types
            logger.info(f"Filtering by file types: {file_types}")
        
        # Add auth loading if requested
        if load_auth:
            loader_kwargs["load_auth"] = True
            
        # Add extended metadata loading if requested
        if load_extended_metadata:
            loader_kwargs["load_extended_metadata"] = True
            
        # Disable automatic permissions fetching through LangChain to avoid SSL issues
        # We'll fetch permissions directly using our optimized method
        loader_kwargs["load_permissions"] = False
        
        # Add custom query if provided
        if custom_query:
            loader_kwargs["query"] = custom_query
        
        # Add file loader if provided
        if file_loader_cls:
            loader_kwargs["file_loader_cls"] = file_loader_cls
            if file_loader_kwargs:
                loader_kwargs["file_loader_kwargs"] = file_loader_kwargs
        
        # Try using LangChain's loaders for non-DOCX files
        non_docx_files_count = len(folder_files) - len(docx_files)
        if non_docx_files_count > 0 or file_ids:
            # Try to use the community GoogleDriveLoader
            try:
                from langchain_google_community.drive import GoogleDriveLoader
                
                # Print the absolute path to help with debugging
                if 'folder_id' in loader_kwargs:
                    logger.info(f"GoogleDriveLoader targeting folder: {loader_kwargs['folder_id']}")
                elif 'file_ids' in loader_kwargs:
                    logger.info(f"GoogleDriveLoader targeting files: {loader_kwargs['file_ids']}")
                
                # Try using service account explicitly - using the same one our GoogleDriveAuth class is using
                service_account_path = self.google_auth.service_account_path
                
                # Check if service account file exists
                if os.path.exists(service_account_path):
                    logger.info(f"Service account file exists: {service_account_path}")
                    # Get service account credentials and pass explicitly
                    try:
                        from google.oauth2 import service_account
                        credentials = service_account.Credentials.from_service_account_file(
                            service_account_path,
                            scopes=['https://www.googleapis.com/auth/drive.readonly',
                                    'https://www.googleapis.com/auth/drive.metadata.readonly']
                        )
                        
                        # Add credentials to loader kwargs
                        loader_kwargs["credentials"] = credentials
                        
                        # Explicitly disable service account usage - we'll use our credentials directly
                        loader_kwargs["service_account_path"] = None
                        
                        # Set token_file to None to prevent looking for credentials.json
                        loader_kwargs["token_file"] = None
                    except ImportError as e:
                        logger.error(f"Error importing Google service_account module: {str(e)}")
                        logger.error("This likely means the google-auth package is not installed correctly.")
                        logger.error("Try running: pip install google-auth")
                else:
                    logger.warning(f"Service account file not found at: {service_account_path}")
                
                # Initialize the loader with our kwargs
                loader = GoogleDriveLoader(**loader_kwargs)
                if max_results:
                    loader.num_results = max_results
                logger.info("Using GoogleDriveLoader from langchain-google-community")
                
            except ImportError as e:
                logger.error(f"Failed to import GoogleDriveLoader: {str(e)}")
                logger.error("This likely means langchain-google-community is not installed correctly.")
                logger.error("Using sample documents for demonstration.")
                
                # Create sample documents for demonstration
                for i in range(3):
                    sample_doc = Document(
                        page_content=f"This is sample document {i+1} (import error). The GoogleDriveLoader could not be imported. " + 
                                    f"Please install langchain-google-community with: pip install langchain-google-community",
                        metadata={
                            "source": f"import-error-{i+1}",
                            "file_id": f"import-error-{i+1}",
                            "file_name": f"Import Error Sample {i+1}.txt",
                            "mime_type": "text/plain",
                            "created_time": datetime.now().isoformat(),
                            "modified_time": datetime.now().isoformat()
                        }
                    )
                    documents.append(sample_doc)
                    
                logger.info(f"Created {len(documents)} import error sample documents")
                return documents
            
            # Load documents from LangChain loader
            try:
                langchain_docs = loader.load()
                logger.info(f"Loaded {len(langchain_docs)} documents from LangChain GoogleDriveLoader")
                
                # Log some details about the first few documents
                for i, doc in enumerate(langchain_docs[:3]):
                    if i >= 3:
                        break
                    logger.info(f"Document {i+1} - Source: {doc.metadata.get('source', 'unknown')}")
                    logger.info(f"  Metadata: {str(list(doc.metadata.keys()))}")
                    content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                    logger.info(f"  Content preview: {content_preview}")
                
                # Add LangChain loaded documents to our manually processed ones
                documents.extend(langchain_docs)
                
            except Exception as e:
                error_msg = str(e)
                if "credentials.json was not found" in error_msg or "/config/credentials.json" in error_msg:
                    logger.warning("Google Drive credentials issue detected. Using sample documents for demonstration.")
                    
                    # Create sample documents for demonstration purposes
                    for i in range(3):
                        sample_doc = Document(
                            page_content=f"This is sample document {i+1} (fallback). It contains text that demonstrates the RAG pipeline functionality. " + 
                                        f"You can replace this with your actual Google Drive documents by configuring the proper credentials.",
                            metadata={
                                "source": f"fallback-sample-{i+1}",
                                "file_id": f"fallback-id-{i+1}",
                                "file_name": f"Fallback Sample {i+1}.txt",
                                "mime_type": "text/plain",
                                "created_time": datetime.now().isoformat(),
                                "modified_time": datetime.now().isoformat()
                            }
                        )
                        documents.append(sample_doc)
                        
                    logger.info(f"Created {len(documents)} fallback sample documents for demonstration")
                else:
                    logger.error(f"Error loading documents with LangChain: {error_msg}")
                    raise
        
        # Report total documents found
        logger.info(f"Total documents loaded: {len(documents)}")
        if len(documents) == 0:
            logger.warning("No documents found. Check the folder ID and permissions.")
            
        return documents
    
    def process_document(self, document: Document) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Process a single document to extract text and metadata.
        
        Args:
            document: LangChain document object
            
        Returns:
            Tuple of (text, metadata)
        """
        try:
            # Extract the text content
            text = document.page_content
            
            # Extract the base metadata
            base_metadata = document.metadata
            
            # Ensure file_id is present
            file_id = base_metadata.get('file_id', None)
            if not file_id:
                # Try to extract from source
                source = base_metadata.get('source', '')
                if '://' in source:
                    file_id = source.split('://')[-1]
                    base_metadata['file_id'] = file_id
            
            # Check if this is a Google Drive document
            source_type = 'google_drive' if file_id else 'unknown'
            
            # Get drive item and auth info if this is a Google Drive document
            drive_item = None
            auth_info = None
            
            if file_id and source_type == 'google_drive':
                try:
                    # Get Drive service
                    drive_service = self.google_auth.get_drive_service()
                    
                    # Use our new optimized direct permissions fetching with shorter timeout
                    from rag.utils import get_drive_permissions
                    
                    # Get permissions with enhanced SSL and timeout handling
                    permissions = get_drive_permissions(
                        file_id=file_id,
                        drive_service=drive_service,
                        use_unverified_context=True,  # Use unverified SSL context to avoid SSL errors
                        timeout=15  # Use a shorter timeout to prevent hanging
                    )
                    
                    # Create a simple drive item with essential metadata
                    drive_item = {
                        'id': file_id,
                        'name': base_metadata.get('file_name', 'Unknown'),
                        'mimeType': base_metadata.get('mime_type', 'Unknown'),
                        'createdTime': base_metadata.get('created_time', ''),
                        'modifiedTime': base_metadata.get('modified_time', ''),
                    }
                    
                    # Structure auth info with permissions
                    auth_info = {
                        'permissions': permissions
                    }
                    
                    logger.info(f"Successfully fetched {len(permissions)} permissions for {file_id}")
                    
                except Exception as e:
                    logger.warning(f"Error fetching Google Drive permissions: {str(e)}")
                    # Create minimal structures even if permissions fetch fails
                    drive_item = {
                        'id': file_id,
                        'name': base_metadata.get('file_name', 'Unknown'),
                        'mimeType': base_metadata.get('mime_type', 'Unknown'),
                        'createdTime': base_metadata.get('created_time', ''),
                        'modifiedTime': base_metadata.get('modified_time', ''),
                    }
                    auth_info = {
                        'permissions': []
                    }
        
            else:
                # No file_id or auth
                drive_item = None
                auth_info = None
        
            # Enrich metadata with Google Drive specific fields - if we have them
            metadata = DocumentProcessor.extract_google_drive_metadata(
                base_metadata=base_metadata,
                drive_item=drive_item,
                auth_info=auth_info
            )
            
            # Add standard metadata fields
            metadata = DocumentProcessor.enrich_metadata(
                metadata=metadata,
                doc_type='google_drive',
                additional_metadata={
                    'ingestion_engine': 'langchain',
                    'collection_name': self.collection_name
                }
            )
            
            return text, metadata
        
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return None, None
    
    def process_image_ocr(self, image_data: bytes, file_name: str, file_id: str, mime_type: str) -> Tuple[str, Dict[str, Any]]:
        """Process an image file with OCR to extract text.
        
        Args:
            image_data: Raw binary image data
            file_name: Name of the file
            file_id: ID of the file
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (extracted_text, metadata with OCR info)
        """
        try:
            import io
            from PIL import Image
            import pytesseract
            import cv2
            import numpy as np
            
            # Create metadata
            metadata = {
                "source": f"google-drive://{file_id}",
                "file_id": file_id,
                "file_name": file_name,
                "mime_type": mime_type,
                "extraction_method": "ocr",
                "ocr_engine": "pytesseract",
                "content_type": "image"
            }
            
            # Convert binary data to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Save image dimensions in metadata
            metadata["image_width"] = image.width
            metadata["image_height"] = image.height
            
            # Convert to OpenCV format for preprocessing
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image to improve OCR quality
            # Convert to grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            # Apply adaptive thresholding
            processed = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(processed)
            
            # Add OCR confidence data
            ocr_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
            avg_conf = sum(ocr_data['conf']) / len(ocr_data['conf']) if ocr_data['conf'] else 0
            metadata["ocr_confidence"] = avg_conf
            
            # Add OCR statistics
            word_count = len([word for word in ocr_data['text'] if word.strip()])
            metadata["ocr_word_count"] = word_count
            
            logger.info(f"Successfully extracted {word_count} words from image: {file_name}")
            
            return text, metadata
        
        except Exception as e:
            logger.error(f"Error processing image with OCR: {str(e)}")
            # Return minimal text and metadata in case of failure
            return f"[OCR PROCESSING ERROR for {file_name}: {str(e)}]", {
                "source": f"google-drive://{file_id}",
                "file_id": file_id,
                "file_name": file_name,
                "mime_type": mime_type,
                "extraction_error": str(e)
            }
    
    def extract_tables_from_pdf(self, pdf_data: bytes, file_name: str, file_id: str, mime_type: str) -> Tuple[str, Dict[str, Any]]:
        """Extract tables from PDF files.
        
        Args:
            pdf_data: Raw binary PDF data
            file_name: Name of the file
            file_id: ID of the file
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (extracted_table_text, metadata with table info)
        """
        try:
            import io
            import os
            import tempfile
            import pandas as pd
            
            # Create a temporary file to save the PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(pdf_data)
            
            try:
                # Create metadata
                metadata = {
                    "source": f"google-drive://{file_id}",
                    "file_id": file_id,
                    "file_name": file_name,
                    "mime_type": mime_type,
                    "extraction_method": "table",
                    "content_type": "pdf_tables"
                }
                
                # First try with tabula-py
                try:
                    import tabula
                    tables = tabula.read_pdf(temp_path, pages='all', multiple_tables=True)
                    metadata["table_extraction_engine"] = "tabula"
                    metadata["tables_count"] = len(tables)
                    
                    table_texts = []
                    for i, table in enumerate(tables):
                        table_texts.append(f"\n--- Table {i+1} ---\n")
                        table_texts.append(table.to_string(index=False))
                        
                    logger.info(f"Successfully extracted {len(tables)} tables with tabula from: {file_name}")
                    
                except Exception as tabula_error:
                    logger.warning(f"Tabula extraction failed: {str(tabula_error)}, trying camelot")
                    
                    # Fall back to camelot
                    try:
                        import camelot
                        tables = camelot.read_pdf(temp_path, pages='all')
                        metadata["table_extraction_engine"] = "camelot"
                        metadata["tables_count"] = len(tables)
                        
                        table_texts = []
                        for i, table in enumerate(tables):
                            table_texts.append(f"\n--- Table {i+1} ---\n")
                            table_texts.append(table.df.to_string(index=False))
                            
                        logger.info(f"Successfully extracted {len(tables)} tables with camelot from: {file_name}")
                        
                    except Exception as camelot_error:
                        logger.error(f"Camelot extraction also failed: {str(camelot_error)}")
                        return f"[TABLE EXTRACTION ERROR for {file_name}: {str(camelot_error)}]", metadata
                
                # Join all table texts
                all_tables_text = "\n\n".join(table_texts)
                
                # Add tables text statistics
                metadata["tables_text_length"] = len(all_tables_text)
                metadata["tables_text_lines"] = all_tables_text.count('\n')
                
                return all_tables_text, metadata
                
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        except Exception as e:
            logger.error(f"Error extracting tables from PDF: {str(e)}")
            # Return minimal text and metadata in case of failure
            return f"[TABLE EXTRACTION ERROR for {file_name}: {str(e)}]", {
                "source": f"google-drive://{file_id}",
                "file_id": file_id,
                "file_name": file_name,
                "mime_type": mime_type,
                "extraction_error": str(e)
            }
    
    def process_image_analysis(self, image_data: bytes, file_name: str, file_id: str, mime_type: str) -> Tuple[str, Dict[str, Any]]:
        """Analyze image content and extract descriptive text.
        
        Args:
            image_data: Raw binary image data
            file_name: Name of the file
            file_id: ID of the file
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (image_description, metadata with image analysis)
        """
        try:
            import io
            import cv2
            import numpy as np
            from PIL import Image
            
            # Create metadata
            metadata = {
                "source": f"google-drive://{file_id}",
                "file_id": file_id,
                "file_name": file_name,
                "mime_type": mime_type,
                "extraction_method": "image_analysis",
                "content_type": "image"
            }
            
            # Convert binary data to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Save image dimensions and format in metadata
            metadata["image_width"] = image.width
            metadata["image_height"] = image.height
            metadata["image_format"] = image.format
            metadata["image_mode"] = image.mode
            
            # Convert to OpenCV format for analysis
            img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Extract basic image features
            # Color analysis
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            color_data = {
                "dominant_hue": np.median(hsv[:,:,0]),
                "dominant_saturation": np.median(hsv[:,:,1]),
                "dominant_value": np.median(hsv[:,:,2])
            }
            metadata["color_analysis"] = color_data
            
            # Edge detection for complexity estimation
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edge_ratio = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            metadata["edge_complexity"] = edge_ratio
            
            # Try to detect faces if present
            try:
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    metadata["faces_detected"] = len(faces)
                    face_data = []
                    for (x, y, w, h) in faces:
                        face_data.append({"x": int(x), "y": int(y), "width": int(w), "height": int(h)})
                    metadata["face_locations"] = face_data
                    
                    # Generate description with face info
                    description = f"Image contains {len(faces)} human face(s). "
                else:
                    description = "No human faces detected in the image. "
            except Exception as face_error:
                logger.warning(f"Face detection error: {str(face_error)}")
                description = "Image content analysis. "
            
            # Add file properties
            description += f"Image dimensions: {image.width}x{image.height}. "
            
            # Add complexity assessment
            if edge_ratio > 0.1:
                description += "The image appears to be complex with many details. "
            else:
                description += "The image appears to be relatively simple without many details. "
            
            # Color assessment
            saturation = color_data["dominant_saturation"]
            if saturation > 100:
                description += "Colors are vivid and saturated. "
            else:
                description += "Colors are muted or less saturated. "
                
            brightness = color_data["dominant_value"]
            if brightness > 150:
                description += "Overall brightness is high. "
            elif brightness < 70:
                description += "Overall brightness is low (dark image). "
            else:
                description += "Image has moderate brightness. "
            
            logger.info(f"Successfully analyzed image content for: {file_name}")
            
            return description, metadata
        
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            # Return minimal text and metadata in case of failure
            return f"[IMAGE ANALYSIS ERROR for {file_name}: {str(e)}]", {
                "source": f"google-drive://{file_id}",
                "file_id": file_id,
                "file_name": file_name,
                "mime_type": mime_type,
                "extraction_error": str(e)
            }
    
    def process_document_with_enhanced_media(self, document: Document) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Process a document with enhanced media extraction (OCR, tables, images).
        
        This enhances the standard document processing with special handling for:
        1. Images - using OCR and image analysis
        2. PDFs - with table extraction
        3. Other media - with appropriate extraction methods
        
        Args:
            document: LangChain document object
            
        Returns:
            Tuple of (text, metadata)
        """
        try:
            # Extract the base metadata
            base_metadata = document.metadata
            
            # Get file info
            file_id = base_metadata.get('file_id', None)
            if not file_id:
                # Try to extract from source
                source = base_metadata.get('source', '')
                if '://' in source:
                    file_id = source.split('://')[-1]
                    base_metadata['file_id'] = file_id
                    
            file_name = base_metadata.get('file_name', 'Unknown')
            mime_type = base_metadata.get('mime_type', 'Unknown')
            
            # Check if this document needs enhanced processing
            is_image = mime_type.startswith('image/')
            is_pdf = mime_type == 'application/pdf'
            needs_ocr = is_image or 'extracted_text' in base_metadata
            needs_table_extraction = is_pdf
            needs_image_analysis = is_image
            
            # If no special processing needed, use standard processing
            if not (needs_ocr or needs_table_extraction or needs_image_analysis):
                return self.process_document(document)
                
            # Need to download the file for enhanced processing
            if file_id:
                try:
                    # Get service
                    service = self.google_auth.get_drive_service()
                    
                    # Download the file content
                    from googleapiclient.http import MediaIoBaseDownload
                    import io
                    
                    request = service.files().get_media(fileId=file_id)
                    file_content = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_content, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                    
                    # Reset the pointer to the beginning
                    file_content.seek(0)
                    file_data = file_content.read()
                    
                    # Process based on file type
                    if needs_ocr and is_image:
                        text, metadata = self.process_image_ocr(file_data, file_name, file_id, mime_type)
                        
                        # If requested, also perform image analysis
                        if needs_image_analysis:
                            analysis_text, analysis_metadata = self.process_image_analysis(file_data, file_name, file_id, mime_type)
                            # Merge text and metadata
                            text = f"{text}\n\n[IMAGE ANALYSIS]:\n{analysis_text}"
                            # Combine metadata but preserve extraction method as OCR
                            for key, value in analysis_metadata.items():
                                if key not in metadata and key != "extraction_method":
                                    metadata[key] = value
                                    
                        # Add enhanced processing flag
                        metadata["enhanced_processing"] = True
                        return text, metadata
                        
                    elif needs_image_analysis:
                        text, metadata = self.process_image_analysis(file_data, file_name, file_id, mime_type)
                        # Add enhanced processing flag
                        metadata["enhanced_processing"] = True
                        return text, metadata
                        
                    elif needs_table_extraction and is_pdf:
                        # First extract tables
                        tables_text, tables_metadata = self.extract_tables_from_pdf(file_data, file_name, file_id, mime_type)
                        
                        # Now process the normal text content
                        original_text = document.page_content
                        
                        # Combine the texts with clear separation
                        combined_text = f"{original_text}\n\n[EXTRACTED TABLES]:\n{tables_text}"
                        
                        # Combine metadata
                        combined_metadata = base_metadata.copy()
                        for key, value in tables_metadata.items():
                            if key not in combined_metadata:
                                combined_metadata[key] = value
                                
                        # Further process the combined metadata
                        combined_metadata["enhanced_processing"] = True
                        combined_metadata["content_type"] = "pdf_with_tables"
                        
                        # Process the combined metadata through the standard pipeline
                        text, metadata = self.process_document(Document(
                            page_content=combined_text,
                            metadata=combined_metadata
                        ))
                        return text, metadata
                    
                except Exception as download_error:
                    logger.error(f"Error downloading file for enhanced processing: {str(download_error)}")
                    # Fall back to standard processing if download failed
                    return self.process_document(document)
            
            # If we get here, use standard processing
            return self.process_document(document)
            
        except Exception as e:
            logger.error(f"Error in enhanced media processing: {str(e)}")
            return self.process_document(document)  # Fall back to standard processing

    def ingest(
        self, 
        folder_id: Optional[str] = None,
        file_ids: Optional[List[str]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        file_types: Optional[List[str]] = None,
        recursive: bool = False,
        load_auth: bool = False,
        load_extended_metadata: bool = True,
        custom_query: Optional[str] = None,
        max_results: Optional[int] = None,
        file_loader_cls: Optional[Type] = None,
        file_loader_kwargs: Optional[Dict[str, Any]] = None,
        return_stats: bool = False,
        respect_content_boundaries: bool = True,
        content_aware_splitting: bool = True,
        skip_unchanged_documents: bool = False,
        enable_enhanced_media_processing: bool = False
    ) -> Union[None, Tuple[int, int, Dict[str, Any], Dict[str, int]]]:
        """Ingest documents from Google Drive into the vector store.
        
        Args:
            folder_id: ID of the Google Drive folder
            file_ids: List of specific file IDs to load (optional)
            chunk_size: Size of each text chunk
            chunk_overlap: Overlap between chunks
            file_types: List of file extensions to include
            recursive: Whether to recursively search subfolders
            load_auth: Whether to load auth identities
            load_extended_metadata: Whether to load extended metadata
            custom_query: Custom query string for Google Drive search
            max_results: Maximum number of results to return
            file_loader_cls: Optional file loader class for non-Google document types
            file_loader_kwargs: Optional kwargs for the file loader
            return_stats: Whether to return statistics about the ingestion
            respect_content_boundaries: Whether to respect content boundaries
            content_aware_splitting: Whether to use content-aware splitting
            skip_unchanged_documents: Whether to skip unchanged documents
            enable_enhanced_media_processing: Whether to enable enhanced media processing
            
        Returns:
            If return_stats is True, returns a tuple of:
            - Number of documents processed
            - Number of chunks generated
            - Sample metadata dictionary
            - Version statistics (new, updated, unchanged)
            Otherwise returns None
        """
        # Load documents
        documents = self.load_documents_from_drive(
            folder_id=folder_id,
            file_ids=file_ids,
            file_types=file_types,
            recursive=recursive,
            load_auth=load_auth,
            load_extended_metadata=load_extended_metadata,
            custom_query=custom_query,
            max_results=max_results,
            file_loader_cls=file_loader_cls,
            file_loader_kwargs=file_loader_kwargs
        )
        
        if not documents:
            logger.warning("No documents found. Check the folder ID and permissions.")
            if return_stats:
                return 0, 0, {}, {"new": 0, "updated": 0, "unchanged": 0}
            return
        
        # Process documents if we have any
        total_docs = len(documents)
        if total_docs > 0:
            logger.info(f"Processing {total_docs} documents")
            
            # Process documents in parallel with timeout protection
            from rag.utils import process_documents_parallel
            
            # Set a shorter timeout per document to prevent hanging
            timeout_per_doc = 45  # 45 seconds per document
            
            # Select the appropriate document processing function based on whether enhanced media processing is enabled
            if enable_enhanced_media_processing:
                logger.info("Using enhanced media processing (OCR, tables, image analysis)")
                doc_processor = self.process_document_with_enhanced_media
            else:
                logger.info("Using standard document processing")
                doc_processor = self.process_document
            
            # Process documents in parallel
            processed_docs = process_documents_parallel(
                doc_processor, 
                documents, 
                max_workers=4,  # Use 4 workers max
                timeout_per_doc=timeout_per_doc
            )
            
            # Filter out None results from timeouts
            processed_docs = [doc for doc in processed_docs if doc[0] is not None]
            
            # Now split into chunks using RecursiveCharacterTextSplitter
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            
            # Create text splitter with provided parameters
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
                keep_separator=respect_content_boundaries
            )
            
            # Process each document and prepare for the vector store
            chunked_texts = []
            chunked_metadatas = []
            chunked_ids = []
            
            for text, metadata in processed_docs:
                if not text:
                    logger.warning(f"Skipping document with empty content: {metadata.get('file_name', 'unknown')}")
                    continue
                
                # Generate a unique ID for the document if not present
                doc_id = metadata.get('file_id', str(uuid.uuid4()))
                
                # Split text into chunks
                doc_chunks = text_splitter.split_text(text)
                
                for j, chunk in enumerate(doc_chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata['chunk'] = j
                    chunk_metadata['parent_id'] = doc_id
                    chunk_id = f"{doc_id}-chunk-{j}"
                    
                    chunked_texts.append(chunk)
                    chunked_metadatas.append(chunk_metadata)
                    chunked_ids.append(chunk_id)
            
            logger.info(f"Created {len(chunked_texts)} chunks from {len(processed_docs)} documents")
            
            # Track version statistics
            version_stats = {"new": 0, "updated": 0, "unchanged": 0}
            
            # Store in vector database
            logger.info(f"Passing skip_unchanged_documents={skip_unchanged_documents} to _store_in_supabase")
            self._store_in_supabase(chunked_texts, chunked_metadatas, chunked_ids, version_stats, skip_unchanged_documents)
            
            # Return statistics if requested
            if return_stats:
                # Get a sample metadata for display
                sample_metadata = chunked_metadatas[0] if chunked_metadatas else {}
                
                # Count unique parent documents
                unique_parent_docs = len(set(meta.get('parent_id') for meta in chunked_metadatas))
                
                return unique_parent_docs, len(chunked_texts), sample_metadata, version_stats
        
        # Return empty statistics if no documents
        return 0, 0, {}, {"new": 0, "updated": 0, "unchanged": 0}
            
    def _store_in_supabase(self, texts, metadatas, ids, version_stats, skip_unchanged_documents=False):
        """Store documents in Supabase with version tracking.
        
        Args:
            texts: List of document texts
            metadatas: List of document metadatas
            ids: List of document IDs
            version_stats: Dictionary to track version statistics
            skip_unchanged_documents: Whether to skip processing unchanged documents
        """
        logger.info(f"Storing {len(texts)} chunks in Supabase vector store...")
        logger.info(f"Skip unchanged documents setting: {skip_unchanged_documents}")
        
        try:
            # Get Supabase client if available
            supabase_client = getattr(self.vectorstore, '_client', None)
            
            # Check each document to see if it already exists and needs updating
            new_texts = []
            new_metadatas = []
            new_ids = []
            update_texts = []
            update_metadatas = []
            update_ids = []
            skip_count = 0
            
            # Check each document to see if it already exists and needs updating
            for i, (text, metadata, doc_id) in enumerate(zip(texts, metadatas, ids)):
                # Check if document exists and needs updating
                needs_update, existing_metadata, content_changed, metadata_update_only = DocumentProcessor.check_document_version(
                    doc_id=doc_id,
                    metadata=metadata,
                    content=text,
                    supabase_client=supabase_client,
                    table_name=self.collection_name
                )
                
                if existing_metadata:
                    # Document exists
                    if needs_update:
                        # Document needs update - increment version
                        if 'version_info' in existing_metadata:
                            # Get existing version
                            version_info = existing_metadata['version_info']
                            current_version = version_info.get('version', '1.0')
                            
                            # Increment version
                            version_parts = current_version.split('.')
                            if len(version_parts) >= 2:
                                major, minor = version_parts[0], version_parts[1]
                                new_minor = str(int(minor) + 1)
                                new_version = f"{major}.{new_minor}"
                            else:
                                new_version = f"{current_version}.1"
                            
                            # Update version info
                            new_version_info = {
                                'version': new_version,
                                'created_at': version_info.get('created_at', datetime.now().isoformat()),
                                'updated_at': datetime.now().isoformat(),
                                'previous_versions': version_info.get('previous_versions', []) + [{
                                    'version': current_version,
                                    'updated_at': version_info.get('updated_at', datetime.now().isoformat()),
                                    'content_changed': content_changed
                                }]
                            }
                            
                            # Update metadata with new version info
                            metadata['version_info'] = new_version_info
                            
                            # Also add a flag indicating if content changed
                            metadata['content_changed'] = content_changed
                        
                        # Add to update list
                        update_texts.append(text)
                        update_metadatas.append(metadata)
                        update_ids.append(doc_id)
                        
                        logger.info(f"Document {doc_id} will be updated to version {new_version} (content changed: {content_changed})")
                    elif metadata_update_only:
                        # Only metadata changed, like modified_time - we skip re-embedding
                        # but we want to track it in statistics
                        if 'metadata_only_skipped' not in version_stats:
                            version_stats['metadata_only_skipped'] = 0
                        version_stats['metadata_only_skipped'] += 1
                        
                        logger.info(f"Document {doc_id} has metadata changes only, skipping re-embedding")
                        skip_count += 1
                    else:
                        # Document hasn't changed
                        if skip_unchanged_documents:
                            # Skip this document as it hasn't changed
                            skip_count += 1
                            if 'unchanged' not in version_stats:
                                version_stats['unchanged'] = 0
                            version_stats['unchanged'] += 1
                            
                            logger.info(f"Document {doc_id} hasn't changed, skipping")
                        else:
                            # Even though unchanged, we'll process it since skip_unchanged_documents is False
                            update_texts.append(text)
                            update_metadatas.append(metadata)
                            update_ids.append(doc_id)
                            logger.info(f"Document {doc_id} hasn't changed, but processing anyway")
                else:
                    # Document doesn't exist, add to new list
                    new_texts.append(text)
                    new_metadatas.append(metadata)
                    new_ids.append(doc_id)
            
            # Insert new documents
            if new_texts:
                logger.info(f"Adding {len(new_texts)} new documents to Supabase")
                self.vectorstore.add_texts(
                    texts=new_texts,
                    metadatas=new_metadatas,
                    ids=new_ids
                )
            
            # Update existing documents
            if update_texts:
                logger.info(f"Updating {len(update_texts)} existing documents in Supabase")
                for i, (text, metadata, doc_id) in enumerate(zip(update_texts, update_metadatas, update_ids)):
                    try:
                        # Check if content has changed or just metadata
                        content_changed = metadata.get('content_changed', True)
                        
                        # If content_changed is True, we need to delete and re-add
                        # If it's False (only metadata changed), we can still optimize in future
                        
                        # For now, we need to delete and re-add in both cases
                        # Most vector DBs don't support updating just metadata without regenerating embeddings
                        
                        # Delete the existing document
                        if hasattr(self.vectorstore, 'delete'):
                            self.vectorstore.delete(doc_id)
                        elif supabase_client:
                            supabase_client.table(self.collection_name).delete().eq('id', doc_id).execute()
                        
                        # Add the updated document
                        self.vectorstore.add_texts(
                            texts=[text],
                            metadatas=[metadata],
                            ids=[doc_id]
                        )
                        
                        # if content_changed:
                        #     logger.info(f"Successfully updated document {doc_id} (version {metadata['version_info']['version']}) - content changed")
                        # else:
                        #     logger.info(f"Successfully updated document {doc_id} (version {metadata['version_info']['version']}) - only metadata changed")
                            
                        # Track statistics based on content change status
                        if 'content_changed_stats' not in version_stats:
                            version_stats['content_changed_stats'] = {'content': 0, 'metadata_only': 0}
                        
                        if content_changed:
                            version_stats['content_changed_stats']['content'] += 1
                        else:
                            version_stats['content_changed_stats']['metadata_only'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error updating document {doc_id}: {str(e)}")
            
            logger.info(f"Successfully processed {len(texts)} document chunks:")
            logger.info(f"  - {len(new_texts)} new documents added")
            
            # Display specific update statistics if available
            if 'content_changed_stats' in version_stats:
                content_changes = version_stats['content_changed_stats']['content']
                metadata_changes = version_stats['content_changed_stats']['metadata_only']
                total_updates = content_changes + metadata_changes
                
                logger.info(f"  - {total_updates} documents updated:")
                logger.info(f"    * {content_changes} with content changes")
                logger.info(f"    * {metadata_changes} with metadata changes only")
            else:
                logger.info(f"  - {len(update_texts)} documents updated")
            
            # Report on skipped documents
            unchanged_count = version_stats.get('unchanged', skip_count)
            metadata_only_skipped = version_stats.get('metadata_only_skipped', 0)
            
            if metadata_only_skipped > 0:
                logger.info(f"  - {unchanged_count - metadata_only_skipped} documents unchanged (no changes)")
                logger.info(f"  - {metadata_only_skipped} documents with metadata changes only (skipped re-embedding)")
            else:
                logger.info(f"  - {unchanged_count} documents skipped (unchanged)")
            
            # Update version statistics
            version_stats['new'] = len(new_texts)
            version_stats['updated'] = len(update_texts)
            version_stats['unchanged'] = skip_count
            
            # You may also want to track metadata-only changes that were skipped
            # Initialize if not present
            if 'metadata_only_skipped' not in version_stats:
                version_stats['metadata_only_skipped'] = 0
                
            # Add skipped_metadata_changes to statistics display
            if version_stats.get('metadata_only_skipped', 0) > 0:
                logger.info(f"  - {version_stats['metadata_only_skipped']} documents with only metadata changes (skipped re-embedding)")
        
        except Exception as e:
            logger.error(f"Error storing documents in Supabase: {str(e)}")
            raise

# Enhanced document ingestion with improved extraction
def ingest_documents_enhanced(
    source_path: str, 
    store: str = "supabase",
    collection_name: str = "langchain_docs",
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> None:
    """Ingest documents with enhanced extraction.
    
    Args:
        source_path: Path to the document or directory to ingest
        store: Vector store type ("supabase", "chroma", etc.)
        collection_name: Collection name in the vector store
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
    """
    pass  # Implementation pending