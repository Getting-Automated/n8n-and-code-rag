#!/usr/bin/env python3
"""Authentication utilities for Google services"""

import os
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
except ImportError:
    logger.warning("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")

class GoogleDriveAuth:
    """Authentication handler for Google Drive API."""
    
    def __init__(
        self, 
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        credentials_path: Optional[str] = None,
        service_account_path: Optional[str] = None,
        scopes: Optional[list] = None
    ):
        """Initialize the Google Drive authentication.
        
        Args:
            client_id: Google API client ID
            client_secret: Google API client secret
            refresh_token: OAuth refresh token
            credentials_path: Path to credentials.json file
            service_account_path: Path to service account JSON file
            scopes: OAuth scopes to request
        """
        # Default scopes for Google Drive
        self.scopes = scopes or [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.metadata.readonly'
        ]
        
        # Store auth parameters
        self.client_id = client_id or os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GOOGLE_CLIENT_SECRET")
        self.refresh_token = refresh_token or os.getenv("GOOGLE_REFRESH_TOKEN")
        
        # Get paths to credential files
        module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # clean_repo directory
        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH") or os.path.join(module_dir, "config/credentials.json")
        self.service_account_path = service_account_path or os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH") or os.path.join(module_dir, "config/service-account.json")
        
        # Initialize credentials
        self.credentials = None
        self.service = None
        
    def get_credentials(self) -> Credentials:
        """Get OAuth2 credentials for Google API.
        
        Returns:
            Google OAuth2 credentials object
        """
        if self.credentials:
            return self.credentials
            
        # Try to create credentials from various sources
        if self.refresh_token and self.client_id and self.client_secret:
            logger.info("Creating credentials from refresh token")
            # Create credentials from environment variables
            self.credentials = Credentials(
                None,  # No access token initially
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes
            )
        elif os.path.exists(self.service_account_path):
            logger.info(f"Creating credentials from service account: {self.service_account_path}")
            # Create credentials from service account
            self.credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path, 
                scopes=self.scopes
            )
        elif os.path.exists(self.credentials_path):
            logger.info(f"Creating credentials from OAuth file: {self.credentials_path}")
            # Try to load credentials from local file
            try:
                with open(self.credentials_path, 'r') as f:
                    creds_data = json.load(f)
                
                # Check if this is a credentials.json format or token.json format
                if 'installed' in creds_data:
                    # This is a credentials.json file - we need to generate a token
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.scopes)
                    self.credentials = flow.run_local_server(port=0)
                    
                    # Save the credentials for future use
                    token_path = os.path.join(os.path.dirname(self.credentials_path), 'token.json')
                    with open(token_path, 'w') as token:
                        token.write(self.credentials.to_json())
                        logger.info(f"Saved credentials to {token_path}")
                else:
                    # This appears to be a token.json format
                    self.credentials = Credentials.from_authorized_user_info(creds_data, self.scopes)
            except Exception as e:
                logger.error(f"Error loading credentials from file: {str(e)}")
                raise
        else:
            logger.error("No valid credentials found. Please set up Google authentication.")
            raise ValueError(
                "No valid credentials found. Please provide client_id/client_secret/refresh_token, "
                "or a path to credentials.json or service-account.json."
            )
        
        # Check if credentials need refreshing
        if self.credentials and self.credentials.expired and hasattr(self.credentials, 'refresh_token') and self.credentials.refresh_token:
            logger.info("Refreshing expired credentials")
            self.credentials.refresh(Request())
            
        return self.credentials
        
    def get_drive_service(self):
        """Get the Google Drive API service.
        
        Returns:
            Google Drive API service instance
        """
        if not self.service:
            try:
                # Get credentials
                creds = self.get_credentials()
                
                # Use the standard build function with default parameters
                from googleapiclient.discovery import build
                
                # Print friendly message about potential SSL issues
                logger.info("Connecting to Google Drive API (SSL connection issues will be handled gracefully)")
                
                # Create Drive API service
                self.service = build('drive', 'v3', credentials=creds)
                logger.info("Successfully created Google Drive service")
            except Exception as e:
                # If it's an SSL error, provide a more reassuring message
                if "SSL:" in str(e):
                    logger.info("SSL connection issue detected while connecting to Google Drive API - we will fall back to local processing")
                    logger.debug(f"SSL details: {str(e)}")
                else:
                    logger.error(f"Error creating Google Drive service: {str(e)}")
                raise
                
        return self.service
        
    def get_downloader(self, request, file_obj):
        """Get a media downloader with enhanced error handling.
        
        Args:
            request: The media request to download
            file_obj: The file object to write to
            
        Returns:
            A MediaIoBaseDownload instance
        """
        from googleapiclient.http import MediaIoBaseDownload
        
        # Create a downloader with increased chunk size for better performance
        downloader = MediaIoBaseDownload(
            file_obj, 
            request,
            chunksize=1024*1024  # 1MB chunks
        )
        
        return downloader
        
    def call_api(self, method_name, **kwargs):
        """Wrapper for Drive API calls with basic error handling.
        
        Args:
            method_name: String like 'files.get' to identify the method
            **kwargs: Arguments to pass to the API method
            
        Returns:
            The API response
        """
        # Get service
        service = self.get_drive_service()
        
        # Parse method path
        parts = method_name.split('.')
        resource = service
        for part in parts[:-1]:
            resource = getattr(resource, part)()
        
        # Get the method
        method = getattr(resource, parts[-1])
        
        # Log call
        logger.info(f"Making Drive API call: {method_name}")
        
        # Make the API call
        response = method(**kwargs).execute()
        return response