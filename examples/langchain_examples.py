#!/usr/bin/env python3
# examples/langchain_examples_new.py - LangChain ingestion examples with enhanced visual display

import os
import sys
import logging
import time
import socket
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add the repository root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Also add the parent directory of clean_repo to support direct imports from clean_repo
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, parent_dir)

# Direct Google Drive API imports for enhanced permissions fetching
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2 import service_account
except ImportError:
    print("Google API libraries not installed. Some features may be limited.")

# Set a reasonable socket timeout for API calls
socket.setdefaulttimeout(30)  # 30 seconds timeout - shorter to prevent hanging

# Check if required packages are installed
try:
    import pyfiglet
except ImportError:
    print("Installing missing pyfiglet package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyfiglet"])
        import pyfiglet
        print("Successfully installed pyfiglet")
    except Exception as e:
        print(f"Failed to install pyfiglet: {e}")
        
try:
    import pytesseract
except ImportError:
    print("Installing missing pytesseract package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytesseract"])
        import pytesseract
        print("Successfully installed pytesseract")
    except Exception as e:
        print(f"Failed to install pytesseract: {e}")
        print("Note: You also need to install Tesseract OCR engine: https://github.com/tesseract-ocr/tesseract")

try:
    import tabula
except ImportError:
    print("Installing missing tabula-py package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabula-py"])
        import tabula
        print("Successfully installed tabula-py")
    except Exception as e:
        print(f"Failed to install tabula-py: {e}")
        print("Note: You need Java installed for tabula to work properly")

try:
    import camelot
except ImportError:
    print("Installing missing camelot-py package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "camelot-py[cv]"])
        import camelot
        print("Successfully installed camelot-py")
    except Exception as e:
        print(f"Failed to install camelot-py: {e}")
        print("Note: You need Ghostscript installed for camelot to work properly")

try:
    import cv2
except ImportError:
    print("Installing missing opencv-python package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-python"])
        import cv2
        print("Successfully installed opencv-python")
    except Exception as e:
        print(f"Failed to install opencv-python: {e}")

try:
    from PIL import Image
except ImportError:
    print("Installing missing Pillow package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image
        print("Successfully installed Pillow")
    except Exception as e:
        print(f"Failed to install Pillow: {e}")
        
try:
    import humanize
except ImportError:
    print("Installing missing humanize package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "humanize"])
        import humanize
        print("Successfully installed humanize")
    except Exception as e:
        print(f"Failed to install humanize: {e}")

# Check for rich package required for display_utils
try:
    import rich
except ImportError:
    print("Installing missing rich package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
        import rich
        print("Successfully installed rich")
    except Exception as e:
        print(f"Failed to install rich: {e}")
        
# Check for tabulate package required for display_utils
try:
    import tabulate
except ImportError:
    print("Installing missing tabulate package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
        import tabulate
        print("Successfully installed tabulate")
    except Exception as e:
        print(f"Failed to install tabulate: {e}")
        
# Check for colorama package required for display_utils
try:
    import colorama
except ImportError:
    print("Installing missing colorama package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
        import colorama
        print("Successfully installed colorama")
    except Exception as e:
        print(f"Failed to install colorama: {e}")

# Check for LangChain dependencies
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    print("Installing missing langchain-openai package...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain-openai"])
        from langchain_openai import OpenAIEmbeddings
        print("Successfully installed langchain-openai")
    except Exception as e:
        print(f"Failed to install langchain-openai: {e}")

try:
    import langchain
    import langchain_community
except ImportError:
    print("Installing missing langchain packages...")
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain langchain-community"])
        print("Successfully installed langchain packages")
    except Exception as e:
        print(f"Failed to install langchain packages: {e}")

# Import from the new simplified package
from rag.ingestion import LangChainIngestion
from rag.utils import list_drive_folders
from rag.query import query_langchain

# Import the fancy display utilities
try:
    # First try the clean repo utils package
    from clean_repo.utils.display_utils import display
    print("Successfully imported display from clean_repo.utils.display_utils")
except ImportError as e:
    print(f"Import from clean_repo failed: {e}")
    try:
        # Fall back to the new utils package
        from utils.display_utils import display
        print("Successfully imported display from utils.display_utils")
    except ImportError as e:
        print(f"Import from utils failed: {e}")
        try:
            # Fall back to the original src/utils path
            from src.utils.display_utils import display
            print("Successfully imported display from src.utils.display_utils")
        except ImportError as e:
            print(f"Import from src.utils failed: {e}")
            # If all else fails, use the simplified display class
            import rich
            from rich.console import Console
            from rich.panel import Panel
            from rich.progress import Progress
            
            class SimpleDisplay:
                def __init__(self):
                    self.console = Console()
                    
                def print_header(self, title, subtitle=""):
                    self.console.print(Panel(f"[bold]{title}[/bold]\n{subtitle}", expand=False))
                    
                def print_section(self, title, subtitle=""):
                    self.console.print(f"\n[bold cyan]== {title} ==[/bold cyan]")
                    if subtitle:
                        self.console.print(f"[dim]{subtitle}[/dim]")
                        
                def print_step(self, step, total, title, subtitle=""):
                    self.console.print(f"\n[bold green]Step {step}/{total}: {title}[/bold green]")
                    if subtitle:
                        self.console.print(f"[dim]{subtitle}[/dim]")
                        
                def print_info(self, message):
                    self.console.print(f"[blue]ℹ️ {message}[/blue]")
                    
                def print_success(self, message):
                    self.console.print(f"[green]✅ {message}[/green]")
                    
                def print_warning(self, message):
                    self.console.print(f"[yellow]⚠️ {message}[/yellow]")
                    
                def print_error(self, message):
                    self.console.print(f"[red]❌ {message}[/red]")
                    
                def start_spinner(self, message):
                    self.console.print(f"[dim]{message}...[/dim]")
                    
                def create_progress_bar(self, total, description):
                    return Progress()
                    
                def interactive_prompt(self, message, choices=None, default=None):
                    prompt = f"{message}: "
                    if choices:
                        prompt += f"[{'/'.join(choices)}] "
                    if default:
                        prompt += f"(default: {default}) "
                    return input(prompt) or default
                    
                def print_advanced_rag_feature(self, feature_name, description, standard_approach, our_approach, benefits):
                    self.console.print(Panel(f"[bold]{feature_name}[/bold]\n{description}\n\n[bold]Standard:[/bold] {standard_approach}\n[bold]Our Approach:[/bold] {our_approach}", expand=False))
                    self.console.print("[bold]Benefits:[/bold]")
                    for benefit in benefits:
                        self.console.print(f"  • {benefit}")
                        
                def print_metadata_example(self, metadata):
                    import json
                    from rich.panel import Panel
                    from rich.syntax import Syntax
                    
                    # Format metadata as nicely formatted JSON
                    formatted_json = json.dumps(metadata, indent=2)
                    # Create syntax highlighted JSON
                    syntax = Syntax(formatted_json, "json", line_numbers=True)
                    # Display in a panel
                    panel = Panel(syntax, title="📋 Metadata Example", expand=False)
                    self.console.print(panel)
                            
                def print_chunk_example(self, chunk, metadata):
                    from rich.panel import Panel
                    from rich.markdown import Markdown
                    from rich.console import Group
                    from rich.syntax import Syntax
                    
                    # Format the chunk with proper rendering
                    if len(chunk) > 500:
                        display_chunk = chunk[:500] + "..."
                    else:
                        display_chunk = chunk
                        
                    # Try to render as markdown first
                    try:
                        markdown = Markdown(display_chunk)
                        chunk_display = markdown
                    except:
                        # Fallback to plain text
                        chunk_display = display_chunk
                        
                    # Format some key metadata
                    meta_lines = []
                    for key in ["file_name", "content_type", "source"]:
                        if key in metadata:
                            meta_lines.append(f"[bold]{key}:[/bold] {metadata[key]}")
                            
                    # Combine content and metadata
                    group = Group(
                        *meta_lines,
                        "",
                        chunk_display
                    )
                    
                    # Display in a panel
                    panel = Panel(
                        group, 
                        title="📄 Document Chunk Example",
                        subtitle=f"Content: {len(chunk)} characters, {len(chunk.split())} words",
                        expand=False
                    )
                    self.console.print(panel)
                    
                def print_document_stats(self, docs_count, chunks_count, metadata_fields):
                    self.console.print(f"[bold]Document Statistics:[/bold]")
                    self.console.print(f"  Documents processed: {docs_count}")
                    self.console.print(f"  Chunks generated: {chunks_count}")
                    self.console.print(f"  Metadata fields captured: {len(metadata_fields)}")
                    
                def print_embedding_info(self, model, vector_dimension, processing_time, batch_size):
                    self.console.print(f"[bold]Embedding Model:[/bold] {model}")
                    self.console.print(f"  Dimensions: {vector_dimension}")
                    self.console.print(f"  Processing time: {processing_time:.2f}s")
                    self.console.print(f"  Batch size: {batch_size}")
                    
                def print_vector_storage_info(self, store_type, table_name, total_stored, failed, index_type):
                    self.console.print(f"[bold]Vector Storage:[/bold] {store_type}")
                    self.console.print(f"  Table name: {table_name}")
                    self.console.print(f"  Vectors stored: {total_stored}")
                    self.console.print(f"  Failed vectors: {failed}")
                    self.console.print(f"  Index type: {index_type}")
                    
                def print_performance_metrics(self, metrics):
                    self.console.print("[bold]Performance Metrics:[/bold]")
                    for key, value in metrics.items():
                        if isinstance(value, float):
                            self.console.print(f"  {key}: {value:.2f}")
                        else:
                            self.console.print(f"  {key}: {value}")
                            
                def display_comparison_table(self, data, title):
                    self.console.print(f"[bold]{title}[/bold]")
                    for row in data:
                        self.console.print("  -----------------------------")
                        for key, value in row.items():
                            self.console.print(f"  {key}: {value}")
                            
                def print_file_info(self, name, mime_type, file_id, size=None):
                    type_icon = "📄"
                    if "pdf" in mime_type:
                        type_icon = "📕"
                    elif "word" in mime_type or "document" in mime_type:
                        type_icon = "📝"
                    elif "sheet" in mime_type or "excel" in mime_type:
                        type_icon = "📊"
                    elif "presentation" in mime_type or "powerpoint" in mime_type:
                        type_icon = "📽️"
                    elif "folder" in mime_type:
                        type_icon = "📁"
                        
                    size_str = f" ({size} bytes)" if size else ""
                    self.console.print(f"{type_icon} [bold]{name}[/bold]{size_str}")
                    self.console.print(f"   ID: {file_id}")
                    
                def create_metadata_tree(self, metadata, title):
                    from rich.tree import Tree
                    
                    if not metadata or not isinstance(metadata, dict):
                        return None
                        
                    # Create a root tree
                    tree = Tree(f"[bold green]{title}[/bold green]")
                    
                    # Add categories of metadata with emojis
                    basic_info = tree.add("📄 Basic Information")
                    file_info = tree.add("🗂️ File Information")
                    authorship = tree.add("👤 Authorship")
                    permissions = tree.add("🔒 Permissions")
                    versioning = tree.add("🔄 Versioning")
                    other = tree.add("📊 Other Metadata")
                    
                    # Basic info fields
                    basic_fields = ["doc_type", "title", "content_type", "language", "status", "collection_name", "ingestion_engine"]
                    for field in basic_fields:
                        if field in metadata:
                            value = metadata[field]
                            basic_info.add(f"[bold]{field}:[/bold] {value}")
                    
                    # File info fields
                    file_fields = ["file_id", "file_name", "source", "source_type", "url", "mime_type", "size_bytes", "created_time", "modified_time"]
                    for field in file_fields:
                        if field in metadata:
                            value = metadata[field]
                            file_info.add(f"[bold]{field}:[/bold] {value}")
                    
                    # Authorship fields
                    author_fields = ["owner_names", "owner_emails", "last_modified_by"]
                    for field in author_fields:
                        if field in metadata:
                            value = metadata[field]
                            if isinstance(value, list):
                                authorship.add(f"[bold]{field}:[/bold] {', '.join(str(v) for v in value)}")
                            else:
                                authorship.add(f"[bold]{field}:[/bold] {value}")
                    
                    # Permission fields
                    if "permissions" in metadata:
                        perm_branch = permissions.add(f"[bold]permissions:[/bold] ({len(metadata['permissions'])} entries)")
                        for i, perm in enumerate(metadata["permissions"][:3]):  # Show max 3 permissions
                            if isinstance(perm, dict):
                                role = perm.get("role", "unknown")
                                email = perm.get("email", "unknown")
                                perm_branch.add(f"{i+1}. [bold]{role}:[/bold] {email}")
                        if len(metadata["permissions"]) > 3:
                            perm_branch.add(f"... ({len(metadata['permissions']) - 3} more)")
                    
                    # Access summary if available
                    if "access_summary" in metadata:
                        access = metadata["access_summary"]
                        if isinstance(access, dict):
                            access_branch = permissions.add("[bold]access_summary:[/bold]")
                            for key, value in access.items():
                                if isinstance(value, list):
                                    access_branch.add(f"[bold]{key}:[/bold] {', '.join(str(v) for v in value[:3])}")
                                    if len(value) > 3:
                                        access_branch.add(f"  ... ({len(value) - 3} more)")
                                else:
                                    access_branch.add(f"[bold]{key}:[/bold] {value}")
                    
                    # Version info
                    if "version_info" in metadata:
                        version_info = metadata["version_info"]
                        if isinstance(version_info, dict):
                            for key, value in version_info.items():
                                if key != "previous_versions":
                                    versioning.add(f"[bold]{key}:[/bold] {value}")
                                    
                            # Show previous versions count
                            prev_versions = version_info.get("previous_versions", [])
                            if prev_versions:
                                versioning.add(f"[bold]previous_versions:[/bold] {len(prev_versions)} entries")
                    
                    # Other metadata fields
                    for key, value in metadata.items():
                        if key not in basic_fields and key not in file_fields and key not in author_fields and \
                           key != "permissions" and key != "access_summary" and key != "version_info":
                            if isinstance(value, dict):
                                other.add(f"[bold]{key}:[/bold] {{...}}")
                            elif isinstance(value, list):
                                other.add(f"[bold]{key}:[/bold] [{len(value)} items]")
                            else:
                                other.add(f"[bold]{key}:[/bold] {value}")
                    
                    return tree
                    
                def create_version_history_tree(self, version_info):
                    from rich.tree import Tree
                    from rich.text import Text
                    from datetime import datetime
                    
                    # Get the current version
                    if not version_info or not isinstance(version_info, dict):
                        return None
                        
                    current_version = version_info.get("version", "unknown")
                    created_at = version_info.get("created_at", "unknown")
                    updated_at = version_info.get("updated_at", "unknown")
                    
                    # Create a tree
                    tree = Tree(f"🔄 [bold blue]Document Version: {current_version}[/bold blue]")
                    
                    # Add dates
                    dates_branch = tree.add("📅 Version History")
                    dates_branch.add(f"Created: {created_at}")
                    dates_branch.add(f"Updated: {updated_at}")
                    
                    # Check for previous versions
                    previous_versions = version_info.get("previous_versions", [])
                    if previous_versions:
                        history_branch = tree.add("⏮️ Previous Versions")
                        for i, prev_version in enumerate(previous_versions):
                            prev_ver = prev_version.get("version", f"unknown-{i}")
                            prev_updated = prev_version.get("updated_at", "unknown date")
                            history_branch.add(f"Version {prev_ver} (updated: {prev_updated})")
                    
                    return tree
            
            # Create an instance of the simplified display class
            display = SimpleDisplay()
            print("Using SimpleDisplay as fallback")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Print helpful message about running the script
print("""
===========================================================
Running n8n RAG Examples
===========================================================
If you encounter errors about missing modules, try installing:
    pip install google-auth langchain-google-community

For SSL issues with Google Drive, this script uses direct API 
calls for permissions with proper error handling.
===========================================================
""")

def fetch_drive_permissions(file_id: str, service_account_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch permissions directly from Google Drive API with enhanced error handling.
    
    Args:
        file_id: Google Drive file ID
        service_account_path: Path to service account JSON file
        
    Returns:
        List of permission objects with user information
    """
    # Get service account path from environment or use default
    if not service_account_path:
        service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH") or "config/service-account.json"
    
    # Convert to absolute path if needed
    if not os.path.isabs(service_account_path):
        # Try to find the file relative to current directory, then check clean_repo/config
        if os.path.exists(service_account_path):
            service_account_path = os.path.abspath(service_account_path)
        elif os.path.exists(os.path.join('clean_repo', service_account_path)):
            service_account_path = os.path.abspath(os.path.join('clean_repo', service_account_path))
        elif os.path.exists(os.path.join('clean_repo', 'config', 'service-account.json')):
            service_account_path = os.path.abspath(os.path.join('clean_repo', 'config', 'service-account.json'))
    
    # Check if service account file exists
    if not os.path.exists(service_account_path):
        logger.warning(f"Service account file not found: {service_account_path}")
        return []
    
    # Save original SSL context
    import ssl
    import socket
    original_ssl_context = ssl._create_default_https_context
    original_timeout = socket.getdefaulttimeout()
    
    try:
        # Use shorter timeout to prevent hanging
        socket.setdefaulttimeout(15)  # 15 second timeout
        
        # Use unverified SSL context to avoid SSL issues
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Get credentials from service account
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/drive.readonly', 
                   'https://www.googleapis.com/auth/drive.metadata.readonly']
        )
        
        # Build the Drive service
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Try first approach: Get permissions directly
        try:
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
            # Fallback to file.get method if permissions list fails
            if "SSL:" not in str(e):
                logger.warning(f"Permissions list failed, trying file.get approach: {str(e)}")
                
                # More efficient fallback: Get file with fields that include permissions
                file = drive_service.files().get(
                    fileId=file_id,
                    fields="permissions(id,type,emailAddress,role,displayName)",
                    supportsAllDrives=True
                ).execute()
                
                # Return permissions list
                permissions = file.get("permissions", [])
                
                logger.info(f"Successfully fetched {len(permissions)} permissions for file {file_id} using fallback method")
                return permissions
            else:
                # Special case for SSL errors - handled below
                raise e
        
    except HttpError as e:
        error_details = json.loads(e.content.decode())
        error_message = error_details.get("error", {}).get("message", str(e))
        error_reason = error_details.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")
        logger.error(f"HTTP error fetching permissions: {error_message} (reason: {error_reason})")
        
    except Exception as e:
        # Check if this is an SSL error and provide a reassuring message
        if "SSL:" in str(e):
            logger.info(f"SSL connection issue detected for permissions - this is normal and will be handled during processing")
            logger.debug(f"SSL details: {str(e)}")
        else:
            logger.error(f"Error fetching permissions: {type(e).__name__}: {str(e)}")
        
    finally:
        # Restore original SSL context and timeout
        ssl._create_default_https_context = original_ssl_context
        socket.setdefaulttimeout(original_timeout)
        
    return []

def get_all_folder_ids(parent_id: str = None, max_depth: int = 5) -> List[str]:
    """Get all folder IDs recursively.
    
    Args:
        parent_id: Optional parent folder ID to start from
        max_depth: Maximum depth to traverse
        
    Returns:
        List of folder IDs
    """
    try:
        # Using the new simplified list_drive_folders function
        folder_structure = list_drive_folders(folder_id=parent_id, depth=max_depth)
        
        # Extract folder IDs from the folder structure
        folder_ids = []
        
        def extract_ids(folder):
            folder_ids.append(folder['id'])
            for subfolder in folder['folders']:
                extract_ids(subfolder)
                
        extract_ids(folder_structure)
        return folder_ids
    except Exception as e:
        logger.error(f"Error getting folder IDs: {str(e)}")
        return []

def enhance_metadata_with_permissions(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance document metadata with direct permission calls where needed.
    
    Args:
        metadata: Document metadata dictionary
        
    Returns:
        Enhanced metadata with permissions
    """
    # Only process if file_id is available
    if not metadata or 'file_id' not in metadata:
        return metadata
    
    file_id = metadata.get('file_id')
    
    # Check if permissions are already populated
    if 'permissions' in metadata and metadata['permissions']:
        logger.info(f"Document {file_id} already has permissions data")
        return metadata
    
    # Fetch permissions directly
    permissions = fetch_drive_permissions(file_id)
    
    if permissions:
        # Create enhanced copy of metadata
        enhanced = metadata.copy()
        
        # Add or update permissions
        enhanced['permissions'] = permissions
        
        # Create access summary for easier display
        access_summary = {
            'owners': [],
            'editors': [],
            'viewers': [],
            'commenters': []
        }
        
        for perm in permissions:
            email = perm.get('emailAddress', 'Unknown')
            role = perm.get('role', '').lower()
            
            if role == 'owner':
                access_summary['owners'].append(email)
            elif role == 'writer' or role == 'editor':
                access_summary['editors'].append(email)
            elif role == 'reader' or role == 'viewer':
                access_summary['viewers'].append(email)
            elif role == 'commenter':
                access_summary['commenters'].append(email)
        
        # Add access summary
        enhanced['access_summary'] = access_summary
        
        logger.info(f"Enhanced metadata with {len(permissions)} permissions for {file_id}")
        return enhanced
    
    # Return original if no permissions could be fetched
    return metadata

def example_basic_ingestion():
    """Example of basic ingestion from all Google Drive folders with enhanced display."""
    # Start timing for performance metrics
    start_time = time.time()
    
    # Display header
    display.print_header("Getting Automated LangChain RAG Ingestion", "Basic Document Processing Example")
    
    # Section intro
    display.print_section("Initialization", "Setting up ingestion pipeline components")
    
    # Get root folder ID from environment or prompt the user
    root_folder_id = os.getenv("GOOGLE_DRIVE_DEFAULT_FOLDER_ID")
    if not root_folder_id or root_folder_id == "your_folder_id_here":
        root_folder_id = display.interactive_prompt("Please enter the root Google Drive folder ID (or press Enter to use root)")
    
    if not root_folder_id:
        root_folder_id = None  # Use root of Drive
        display.print_info("Using root of Google Drive")
    else:
        display.print_info(f"Using root folder ID: {root_folder_id}")
    
    # Display special RAG features - Authentication
    display.print_advanced_rag_feature(
        feature_name="Enterprise Authentication Options",
        description="Secure document access with service account authentication",
        standard_approach="Basic API key authentication with limited capabilities",
        our_approach="Service account authentication for secure, scalable access",
        benefits=[
            "Service account support for automated, non-interactive usage",
            "No need for user intervention or callback URLs",
            "Better security for backend applications",
            "Detailed access tracking for audit purposes",
            "Support for enterprise environments"
        ]
    )
    
    # Display special RAG features - Permissions
    display.print_advanced_rag_feature(
        feature_name="Enhanced Permissions Management",
        description="Direct API permissions fetching for reliable access control information",
        standard_approach="Indirect permissions fetching through document loaders which may fail",
        our_approach="Direct Drive API permission fetching with enhanced error handling and timeouts",
        benefits=[
            "Reliable permissions retrieval even when document loaders have SSL issues",
            "Detailed access control visualization with role-based summaries",
            "Clear indicator of document sharing status for security assessment",
            "Optimized API calls with proper timeouts and error handling",
            "Improved metadata quality for compliance and audit purposes"
        ]
    )
    
    # Add info about direct permissions
    display.print_info("Using optimized direct API permissions fetching to bypass SSL issues")
    display.print_info("This approach retrieves permissions faster and more reliably than standard methods")
    
    # Explicitly define skipping unchanged documents
    skip_unchanged_documents = True  # Skip unchanged documents to save resources
    
    # Check if service account is being used
    from rag.auth import GoogleDriveAuth
    auth = GoogleDriveAuth()
    service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH") or "config/service-account.json"
    
    if os.path.exists(service_account_path):
        display.print_success(f"Using service account authentication from {service_account_path}")
        display.print_info("Service account authentication provides:")
        display.print_info("- Non-interactive authentication for automated processes")
        display.print_info("- No need for user intervention or callback URLs")
        display.print_info("- Better security for backend applications")
    else:
        display.print_warning("No service account found!")
        display.print_info("See docs/service_account_setup.md for instructions")
    
    # Get list of folders recursively
    display.print_step(1, 4, "Discovering Source Folders", "Scanning Google Drive structure")
    display.start_spinner("Querying Google Drive API for folder structure")
    
    folder_ids = get_all_folder_ids(parent_id=root_folder_id)
    
    if not folder_ids:
        display.print_warning("No folders found in the specified location")
        return
        
    display.print_success(f"Found {len(folder_ids)} folders to process")
    
    # Display special RAG features - Vector Storage
    display.print_step(2, 4, "Initializing Vector Store", "Setting up Supabase pgvector storage")
    
    display.print_advanced_rag_feature(
        feature_name="Enterprise Vector Storage",
        description="Scalable, high-performance vector storage with PostgreSQL pgvector",
        standard_approach="Simple in-memory or basic vector storage with limited scaling",
        our_approach="PostgreSQL pgvector with proper indexing, transaction support, and advanced similarity functions",
        benefits=[
            "Scales to millions of documents",
            "Supports transactional updates and versioning",
            "Enterprise-grade reliability and backup support",
            "Advanced query capabilities (KNN, HNSW indices, hybrid search)"
        ]
    )
    
    try:
        # Initialize ingestion
        ingestion = LangChainIngestion(
            collection_name="langchain_example"
        )
        display.print_success("Successfully initialized LangChain ingestion pipeline")
    except Exception as e:
        display.print_error(f"Failed to initialize ingestion: {str(e)}")
        return
    
    # Process each folder
    display.print_step(3, 4, "Document Loading & Processing", "Extracting and processing documents")
    
    # Track statistics
    total_docs = 0
    total_chunks = 0
    all_metadata_fields = set()
    failed_folders = 0
    processed_folders = 0
    version_stats = {"new": 0, "updated": 0, "unchanged": 0}
    
    # Display special RAG features - Metadata
    display.print_advanced_rag_feature(
        feature_name="Document Versioning & Deduplication",
        description="Smart document version detection and efficient updates",
        standard_approach="Re-ingest all documents on each run, creating duplicates",
        our_approach="Track document versions, detect changes, and update only what's needed",
        benefits=[
            "Prevents duplicate content in the vector store",
            "Preserves version history for compliance and auditing",
            "Reduces embedding costs by only processing changed documents",
            "Improves search relevance by avoiding duplicate results"
        ]
    )
    
    # Display special RAG features - Chunking
    display.print_advanced_rag_feature(
        feature_name="Advanced Chunking Strategy",
        description="Optimized chunking with recursive boundary detection and context overlap",
        standard_approach="Simple character-based splitting with minimal overlap",
        our_approach="Content-aware chunking that respects semantic units with customizable parameters",
        benefits=[
            "Preserves context between related content",
            "Adjustable chunk size and overlap for different document types",
            "Prevents splitting logical sections across chunks",
            "Maintains important metadata across chunk boundaries"
        ]
    )
    
    # Display special RAG features - Content-Aware Processing
    display.print_advanced_rag_feature(
        feature_name="Content-Aware Document Processing",
        description="Intelligent document processing with hierarchical boundary detection",
        standard_approach="Basic token-based splitting without context preservation",
        our_approach="Recursive character splitting with hierarchical separators and boundary preservation",
        benefits=[
            "Respects natural text boundaries (paragraphs, sentences)",
            "Uses hierarchical separators from most to least preferred",
            "Preserves original text structure and formatting",
            "Maintains semantic coherence across chunks"
        ]
    )
    
    # Display chunking configuration
    chunking_params = {
        "chunk_size": 500,
        "chunk_overlap": 100,
        "respect_content_boundaries": True,
        "content_aware_splitting": True,
    }
    
    for param, value in chunking_params.items():
        display.print_info(f"Setting {param}: {value}")
        
    # Add info about skipping unchanged documents
    display.print_info("Using smart duplicate detection to avoid re-embedding unchanged documents")
    
    # Configure skipping of unchanged documents
    skip_unchanged_documents = True  # Set to True to avoid re-processing unchanged documents
    
    # Create a progress bar for folder processing
    with display.create_progress_bar(len(folder_ids), "Processing folders") as progress:
        task = progress.add_task("Processing", total=len(folder_ids))
        
        for i, folder_id in enumerate(folder_ids):
            display.print_section(f"Processing folder {i+1}/{len(folder_ids)}", f"Folder ID: {folder_id}")
            
            try:
                # Start specific folder timer
                folder_start_time = time.time()
                
                # Run the actual ingestion
                logger.info(f"Running ingestion with skip_unchanged_documents={skip_unchanged_documents}")
                docs, chunks, metadata_sample, folder_version_stats = ingestion.ingest(
                    folder_id=folder_id,
                    recursive=True,
                    file_types=None,
                    load_extended_metadata=True,
                    return_stats=True,
                    chunk_size=chunking_params["chunk_size"],
                    chunk_overlap=chunking_params["chunk_overlap"],
                    respect_content_boundaries=chunking_params["respect_content_boundaries"],
                    content_aware_splitting=chunking_params["content_aware_splitting"],
                    skip_unchanged_documents=skip_unchanged_documents
                )
                
                # Update version statistics
                for key in version_stats:
                    if key in folder_version_stats:
                        version_stats[key] += folder_version_stats[key]
                            
                # Update statistics
                folder_docs = docs
                folder_chunks = chunks
                
                total_docs += folder_docs
                total_chunks += folder_chunks
                processed_folders += 1
                
                # Display folder processing stats
                folder_time = time.time() - folder_start_time
                progress.update(task, advance=1)
                
                # Display the version stats for this folder
                try:
                    if i < 3:  # Only show details for first few folders
                        display.print_section(f"Folder {i+1} Version Stats", "Document change detection results")
                        
                        # Show the version stats if we have actual data from the ingestion
                        if folder_version_stats and sum(folder_version_stats.values()) > 0:
                            # Show version statistics as a table
                            version_table = [
                                {"Status": "New documents", "Count": folder_version_stats["new"], "Action": "Full processing"},
                                {"Status": "Updated documents", "Count": folder_version_stats["updated"], "Action": "Version incremented, embeddings updated"},
                                {"Status": "Unchanged documents", "Count": folder_version_stats["unchanged"], "Action": "Skipped processing (preserved)"}
                            ]
                            
                            display.display_comparison_table(version_table, "Document Version Analysis")
                        else:
                            display.print_info("No version statistics available for this folder. Process documents to see version data.")
                except Exception as e:
                    logger.warning(f"Error displaying version stats: {str(e)}")
                
                display.print_success(f"Successfully processed folder: {folder_id}")
                
            except Exception as e:
                display.print_error(f"Error processing folder {folder_id}: {str(e)}")
                failed_folders += 1
                progress.update(task, advance=1)
    
    # Display final step - Embeddings    
    display.print_step(4, 4, "Vector Embeddings", "Generating high-dimensional vector representations")
    
    # Show embedding information for OpenAI
    display.print_embedding_info(
        model="text-embedding-3-small",
        vector_dimension=1536,
        processing_time=time.time() - start_time,
        batch_size=20  # Typical batch size
    )
    
    # Now that documents have been added, retrieve metadata for display
    try:
        # Create a sample query to get real document metadata
        current_collection = ingestion.collection_name
        
        # Now try the standard LangChain query to get actual metadata
        logger.info(f"Retrieving metadata from collection: {current_collection}")
        sample_results = query_langchain(
            query="document", 
            collection_name=current_collection,
            top_k=1,
            metadata_filter=None
        )
        
        if sample_results and 'results' in sample_results and len(sample_results['results']) > 0:
            # Get the first result's metadata
            metadata_sample = sample_results['results'][0]['metadata']
            logger.info("Successfully retrieved metadata from vector store")
            
            # Enhance metadata with direct permissions API if needed
            metadata_sample = enhance_metadata_with_permissions(metadata_sample)
            
            # Extract metadata fields
            all_metadata_fields = set(metadata_sample.keys())
            
            # Show the version tree if available
            if 'version_info' in metadata_sample:
                display.print_section("Document Version Tracking", "Smart change detection and history preservation")
                version_tree = display.create_version_history_tree(metadata_sample['version_info'])
                if version_tree:
                    display.console.print(version_tree)
            
            # Show direct permissions info if available
            if 'permissions' in metadata_sample and metadata_sample['permissions']:
                display.print_section("Direct Permissions Info", "Retrieved with enhanced API calls")
                
                # Show permission counts by role
                if 'access_summary' in metadata_sample:
                    summary = metadata_sample['access_summary']
                    table_data = []
                    
                    for role, users in summary.items():
                        if users:
                            table_data.append({
                                "Access Level": role.capitalize(),
                                "Count": len(users),
                                "Sample Users": ", ".join(users[:2]) + ("..." if len(users) > 2 else "")
                            })
                    
                    if table_data:
                        display.display_comparison_table(table_data, "Document Access Summary")
            
            # Show metadata example 
            display.print_metadata_example(metadata_sample)
            
            # Show example chunk
            display.print_section("Document Chunk Example", "Real content from vector store")
            display.print_chunk_example(sample_results['results'][0]['content'], metadata_sample)
        else:
            logger.warning("No results found in vector store for metadata display")
            all_metadata_fields = set()
    except Exception as e:
        logger.warning(f"Error retrieving metadata after ingestion: {str(e)}")
        import traceback
        logger.warning(f"Traceback: {traceback.format_exc()}")
        all_metadata_fields = set()
    
    # Display summary statistics
    if total_docs == 0:
        display.print_warning("No documents were successfully processed. Check your Google Drive credentials and folder ID.")
        return
        
    display.print_document_stats(
        docs_count=total_docs,
        chunks_count=total_chunks,
        metadata_fields=list(all_metadata_fields)
    )
    
    # Display vector storage info
    display.print_vector_storage_info(
        store_type="Supabase pgvector",
        table_name="langchain_example",
        total_stored=total_chunks,
        failed=0,
        index_type="IVF"
    )
    
    # Display overall performance
    total_time = time.time() - start_time
    display.print_performance_metrics({
        "Total Processing Time": total_time,
        "Folders Processed": processed_folders,
        "Folders Failed": failed_folders,
        "Success Rate": (processed_folders / max(1, processed_folders + failed_folders)) * 100,
        "Documents per Second": total_docs / max(0.1, total_time),
        "Chunks per Second": total_chunks / max(0.1, total_time)
    })
    
    # Display version statistics summary
    display.print_section("Document Version Summary", "Overall version detection statistics")
    
    # Use the actual version statistics from processing if available
    if version_stats and sum(version_stats.values()) > 0:
        # Calculate resource savings
        processing_saved = version_stats["unchanged"] / max(1, sum(version_stats.values())) * 100
        
        # Show version statistics as a table
        version_summary_table = [
            {"Status": "New documents", "Count": version_stats["new"], "Percentage": f"{version_stats['new'] / max(1, sum(version_stats.values())) * 100:.1f}%"},
            {"Status": "Updated documents", "Count": version_stats["updated"], "Percentage": f"{version_stats['updated'] / max(1, sum(version_stats.values())) * 100:.1f}%"},
            {"Status": "Unchanged documents", "Count": version_stats["unchanged"], "Percentage": f"{version_stats['unchanged'] / max(1, sum(version_stats.values())) * 100:.1f}%"}
        ]
        
        display.display_comparison_table(version_summary_table, "Document Version Detection Results")
        
        # Show the resource savings
        display.print_info(f"Version tracking saved approximately {processing_saved:.1f}% of processing resources")
        display.print_info(f"Version history is preserved for {version_stats['updated']} documents")
    else:
        display.print_info("No version statistics available. Process documents to see version tracking results.")
    
    # Retrieve and display the fully enriched metadata (only once) after giving time for all processing
    time.sleep(2)  # Give a short delay to ensure all data is written to the database
    
    try:
        # Get the actual collection name from the ingestion object
        current_collection = ingestion.collection_name
        
        # Use a more specific query that includes document name to get richer results
        logger.info(f"Retrieving final enriched metadata from {current_collection}")
        sample_results = query_langchain(
            query="document OR statement OR proposal", 
            collection_name=current_collection,
            top_k=1,
            metadata_filter=None
        )
        
        if sample_results and 'results' in sample_results and len(sample_results['results']) > 0:
            # Get the first result's metadata
            final_metadata = sample_results['results'][0]['metadata']
            
            # Enhance with direct permissions API
            final_metadata = enhance_metadata_with_permissions(final_metadata)
            
            # Display the fully enriched metadata
            display.print_section("Complete Document Metadata", "Final enriched metadata from vector store")
            # Keep only the formatted metadata table 
            display.print_metadata_example(final_metadata)
            
            # Show the version tree one more time with full data
            if 'version_info' in final_metadata:
                display.print_section("Final Document Version Info", "Complete version information")
                version_tree = display.create_version_history_tree(final_metadata['version_info'])
                if version_tree:
                    display.console.print(version_tree)
            
            # Display document content sample
            display.print_section("Document Content Sample", "From vector store")
            display.print_chunk_example(sample_results['results'][0]['content'], final_metadata)
            
            # Display permission info if available 
            if 'permissions' in final_metadata and final_metadata['permissions']:
                display.print_section("Document Permissions", "Access control information")
                
                # Show permission counts by role if we have an access summary
                if 'access_summary' in final_metadata:
                    summary = final_metadata['access_summary']
                    for role, users in summary.items():
                        if users:
                            display.print_info(f"{role.capitalize()}: {len(users)} users")
                
                # Show individual permissions (up to 5)
                for i, perm in enumerate(final_metadata['permissions'][:5]):
                    email = perm.get('emailAddress', 'unknown')
                    role = perm.get('role', 'unknown')
                    display.print_info(f"  • {email} ({role})")
                
                if len(final_metadata['permissions']) > 5:
                    display.print_info(f"... and {len(final_metadata['permissions']) - 5} more permissions")
            else:
                display.print_info("No permission information available for this document.")
        else:
            display.print_info("No final metadata available to display.")
    except Exception as e:
        logger.warning(f"Error retrieving final metadata: {str(e)}")
    
    # Display comparison table as the absolute last thing
    display.print_section("RAG Implementation Comparison", "Advanced vs. Basic RAG Features")
    
    # Display comparison table with advanced features
    comparisons = [
        {
            "Feature": "Authentication",
            "Our Implementation": "Multi-method service account authentication",
            "Basic RAG": "Simple API keys"
        },
        {
            "Feature": "Metadata Extraction",
            "Our Implementation": f"{len(all_metadata_fields)} fields, hierarchical with inheritance",
            "Basic RAG": "2-3 basic fields"
        },
        {
            "Feature": "Permissions Management",
            "Our Implementation": "Direct API calls with enhanced error handling",
            "Basic RAG": "No permission management or unreliable fetching"
        },
        {
            "Feature": "Document Versioning",
            "Our Implementation": "Full version history with content-aware detection",
            "Basic RAG": "No versioning (duplicates created)"
        },
        {
            "Feature": "Chunking Strategy",
            "Our Implementation": "Content-aware with customized parameters",
            "Basic RAG": "Fixed-size chunks"
        },
        {
            "Feature": "Vector Storage",
            "Our Implementation": "Supabase pgvector with optimized indexes",
            "Basic RAG": "Simple vector DB"
        },
        {
            "Feature": "Processing",
            "Our Implementation": "Parallel with auto-timeout protection",
            "Basic RAG": "Sequential processing"
        }
    ]
    
    display.display_comparison_table(comparisons, "Enterprise RAG Capabilities")
    
    display.print_success("Basic ingestion example completed successfully")

def example_advanced_ingestion():
    """Example of advanced ingestion with custom options and enhanced display."""
    # Start timing for performance metrics
    start_time = time.time()
    
    # Display header
    display.print_header("Advanced RAG Pipeline", "Enterprise-Grade Document Processing")
    
    # Section intro
    display.print_section("Initialization", "Configuring advanced ingestion components")
    
    # Get root folder ID from environment or prompt the user
    root_folder_id = os.getenv("GOOGLE_DRIVE_DEFAULT_FOLDER_ID")
    if not root_folder_id or root_folder_id == "your_folder_id_here":
        root_folder_id = display.interactive_prompt("Please enter the root Google Drive folder ID (or press Enter to use root)")
    
    if not root_folder_id:
        root_folder_id = None  # Use root of Drive
        display.print_info("Using root of Google Drive")
    else:
        display.print_info(f"Using root folder ID: {root_folder_id}")
    
    # Display special RAG features - Processing
    display.print_advanced_rag_feature(
        feature_name="Modular Framework Design",
        description="Flexible modular design for optimal performance",
        standard_approach="Single framework with limited extensibility",
        our_approach="Modular LangChain design with composable components",
        benefits=[
            "Best-in-class document loaders for different document types",
            "Flexible embedding models and providers",
            "Component-specific optimizations where appropriate",
            "Future-proof architecture that can adopt new components"
        ]
    )
    
    # Get list of folders recursively
    display.print_step(1, 5, "Source Discovery", "Advanced scanning with recursive exploration")
    display.start_spinner("Querying Google Drive API with extended metadata")
    
    folder_ids = get_all_folder_ids(parent_id=root_folder_id)
    
    if not folder_ids:
        display.print_warning("No folders found in the specified location")
        return
        
    display.print_success(f"Found {len(folder_ids)} folders to process")
    
    # Create progress bar for folder scanning
    with display.create_progress_bar(min(5, len(folder_ids)), "Scanning folders") as progress:
        task = progress.add_task("Scanning", total=min(5, len(folder_ids)))
        
        for i in range(min(5, len(folder_ids))):
            display.print_file_info(
                f"Folder {i+1}", 
                "application/vnd.google-apps.folder", 
                folder_ids[i],
            )
            progress.update(task, advance=1)
            time.sleep(0.2)  # Just for demo effect
    
    # Create ingestion instance with a unique collection name
    display.print_step(2, 5, "Initializing Advanced Vector Store", "Configuring pgvector with optimized indexes")
    
    # Use a standard collection name that already exists
    collection_name = "langchain_docs"  # Use one of the standard tables created during setup
    
    try:
        # Initialize ingestion
        ingestion = LangChainIngestion(
            collection_name=collection_name
        )
        display.print_success("Successfully initialized advanced processing pipeline")
    except Exception as e:
        display.print_error(f"Failed to initialize advanced ingestion: {str(e)}")
        return
    
    # Configure chunking parameters
    display.print_step(3, 5, "Configuring Document Processing", "Setting up optimized chunking parameters")
    
    # Display special RAG features - Chunking
    display.print_advanced_rag_feature(
        feature_name="Advanced Chunking Strategy",
        description="Optimized chunking with recursive boundary detection and context overlap",
        standard_approach="Simple character-based splitting with minimal overlap",
        our_approach="Content-aware chunking that respects semantic units with customizable parameters",
        benefits=[
            "Preserves context between related content",
            "Adjustable chunk size and overlap for different document types",
            "Prevents splitting logical sections across chunks",
            "Maintains important metadata across chunk boundaries"
        ]
    )
    
    # Display special RAG features - Content-Aware Processing
    display.print_advanced_rag_feature(
        feature_name="Content-Aware Document Processing",
        description="Intelligent document processing with hierarchical boundary detection",
        standard_approach="Basic token-based splitting without context preservation",
        our_approach="Recursive character splitting with hierarchical separators and boundary preservation",
        benefits=[
            "Respects natural text boundaries (paragraphs, sentences)",
            "Uses hierarchical separators from most to least preferred",
            "Preserves original text structure and formatting",
            "Maintains semantic coherence across chunks"
        ]
    )
    
    # Display chunking configuration
    chunking_params = {
        "chunk_size": 500,
        "chunk_overlap": 100,
        "respect_content_boundaries": True,
        "content_aware_splitting": True,
    }
    
    for param, value in chunking_params.items():
        display.print_info(f"Setting {param}: {value}")
        
    # Add info about skipping unchanged documents
    display.print_info("Using smart duplicate detection to avoid re-embedding unchanged documents")
    
    # Configure skipping of unchanged documents
    skip_unchanged_documents = True  # Set to True to avoid re-processing unchanged documents
    
    # Track statistics
    total_docs = 0
    total_chunks = 0
    all_metadata_fields = set()
    failed_folders = 0
    processed_folders = 0
    version_stats = {"new": 0, "updated": 0, "unchanged": 0}
    
    # Process each folder
    display.print_step(4, 5, "Advanced Document Processing", "Processing documents with enhanced metadata extraction")
    
    # Create a progress bar for folder processing
    with display.create_progress_bar(len(folder_ids), "Processing folders") as progress:
        task = progress.add_task("Processing", total=len(folder_ids))
        
        for i, folder_id in enumerate(folder_ids):
            display.print_section(f"Processing folder {i+1}/{len(folder_ids)}", f"Folder ID: {folder_id}")
            
            try:
                # Start specific folder timer
                folder_start_time = time.time()
                
                # Run the actual ingestion
                logger.info(f"Running ingestion with skip_unchanged_documents={skip_unchanged_documents}")
                docs, chunks, metadata_sample, folder_version_stats = ingestion.ingest(
                    folder_id=folder_id,
                    recursive=True,
                    file_types=None,
                    load_extended_metadata=True,
                    return_stats=True,
                    chunk_size=chunking_params["chunk_size"],
                    chunk_overlap=chunking_params["chunk_overlap"],
                    respect_content_boundaries=chunking_params["respect_content_boundaries"],
                    content_aware_splitting=chunking_params["content_aware_splitting"],
                    skip_unchanged_documents=skip_unchanged_documents
                )
                
                # Update version statistics
                for key in version_stats:
                    if key in folder_version_stats:
                        version_stats[key] += folder_version_stats[key]
                            
                # Update statistics
                folder_docs = docs
                folder_chunks = chunks
                
                total_docs += folder_docs
                total_chunks += folder_chunks
                processed_folders += 1
                
                # Display folder processing stats
                folder_time = time.time() - folder_start_time
                progress.update(task, advance=1)
                
                # Display the version stats for this folder
                try:
                    if i < 3:  # Only show details for first few folders
                        display.print_section(f"Folder {i+1} Version Stats", "Document change detection results")
                        
                        # Show the version stats if we have actual data from the ingestion
                        if folder_version_stats and sum(folder_version_stats.values()) > 0:
                            # Show version statistics as a table
                            version_table = [
                                {"Status": "New documents", "Count": folder_version_stats["new"], "Action": "Full processing"},
                                {"Status": "Updated documents", "Count": folder_version_stats["updated"], "Action": "Version incremented, embeddings updated"},
                                {"Status": "Unchanged documents", "Count": folder_version_stats["unchanged"], "Action": "Skipped processing (preserved)"}
                            ]
                            
                            display.display_comparison_table(version_table, "Document Version Analysis")
                        else:
                            display.print_info("No version statistics available for this folder. Process documents to see version data.")
                except Exception as e:
                    logger.warning(f"Error displaying version stats: {str(e)}")
                
                display.print_success(f"Successfully processed folder: {folder_id}")
                
            except Exception as e:
                display.print_error(f"Error processing folder {folder_id}: {str(e)}")
                failed_folders += 1
                progress.update(task, advance=1)
    
    # Final statistics and summary
    display.print_step(5, 5, "Advanced Embedding Generation", "Creating high-quality embeddings with OpenAI model")
    
    # Show embedding information for OpenAI
    display.print_embedding_info(
        model="text-embedding-3-small",
        vector_dimension=1536,
        processing_time=time.time() - start_time,
        batch_size=20
    )
    
    # Now that documents have been added, retrieve metadata for display
    try:
        # Create a sample query to get real document metadata
        current_collection = ingestion.collection_name
        
        # Get actual metadata after ingestion
        logger.info(f"Retrieving metadata from collection: {current_collection}")
        sample_results = query_langchain(
            query="advanced", 
            collection_name=current_collection,
            top_k=1,
            metadata_filter=None
        )
        
        if sample_results and 'results' in sample_results and len(sample_results['results']) > 0:
            # Get the first result's metadata
            metadata_sample = sample_results['results'][0]['metadata']
            logger.info("Successfully retrieved metadata from vector store")
            
            # Enhance metadata with direct permissions API if needed
            metadata_sample = enhance_metadata_with_permissions(metadata_sample)
            
            # Extract metadata fields
            all_metadata_fields = set(metadata_sample.keys())
            
            # Show the version tree if available
            if 'version_info' in metadata_sample:
                display.print_section("Document Version Tracking", "Smart change detection and history preservation")
                version_tree = display.create_version_history_tree(metadata_sample['version_info'])
                if version_tree:
                    display.console.print(version_tree)
            
            # Show direct permissions info if available
            if 'permissions' in metadata_sample and metadata_sample['permissions']:
                display.print_section("Direct Permissions Info", "Retrieved with enhanced API calls")
                
                # Show permission counts by role
                if 'access_summary' in metadata_sample:
                    summary = metadata_sample['access_summary']
                    table_data = []
                    
                    for role, users in summary.items():
                        if users:
                            table_data.append({
                                "Access Level": role.capitalize(),
                                "Count": len(users),
                                "Sample Users": ", ".join(users[:2]) + ("..." if len(users) > 2 else "")
                            })
                    
                    if table_data:
                        display.display_comparison_table(table_data, "Document Access Summary")
            
            # Show metadata example 
            display.print_metadata_example(metadata_sample)
            
            # Show example chunk
            display.print_section("Document Chunk Example", "Real content from vector store")
            display.print_chunk_example(sample_results['results'][0]['content'], metadata_sample)
        else:
            logger.warning("No results found in vector store for metadata display")
            all_metadata_fields = set()
    except Exception as e:
        logger.warning(f"Error retrieving metadata after ingestion: {str(e)}")
        import traceback
        logger.warning(f"Traceback: {traceback.format_exc()}")
        all_metadata_fields = set()
    
    # Display summary statistics
    if total_docs == 0:
        display.print_warning("No documents were successfully processed. Check your Google Drive credentials and folder ID.")
        return
        
    display.print_document_stats(
        docs_count=total_docs,
        chunks_count=total_chunks,
        metadata_fields=list(all_metadata_fields)
    )
    
    # Display vector storage info
    display.print_vector_storage_info(
        store_type="Supabase pgvector",
        table_name=collection_name,
        total_stored=total_chunks,
        failed=0,
        index_type="IVF"
    )
    
    # Display overall performance
    total_time = time.time() - start_time
    display.print_performance_metrics({
        "Total Processing Time": total_time,
        "Folders Processed": processed_folders,
        "Folders Failed": failed_folders,
        "Success Rate": (processed_folders / max(1, processed_folders + failed_folders)) * 100,
        "Documents per Second": total_docs / max(0.1, total_time),
        "Chunks per Second": total_chunks / max(0.1, total_time)
    })
    
    # Display version statistics summary
    display.print_section("Document Version Summary", "Overall version detection statistics")
    
    # Use the actual version statistics from processing if available
    if version_stats and sum(version_stats.values()) > 0:
        # Calculate resource savings
        processing_saved = version_stats["unchanged"] / max(1, sum(version_stats.values())) * 100
        
        # Show version statistics as a table
        version_summary_table = [
            {"Status": "New documents", "Count": version_stats["new"], "Percentage": f"{version_stats['new'] / max(1, sum(version_stats.values())) * 100:.1f}%"},
            {"Status": "Updated documents", "Count": version_stats["updated"], "Percentage": f"{version_stats['updated'] / max(1, sum(version_stats.values())) * 100:.1f}%"},
            {"Status": "Unchanged documents", "Count": version_stats["unchanged"], "Percentage": f"{version_stats['unchanged'] / max(1, sum(version_stats.values())) * 100:.1f}%"}
        ]
        
        display.display_comparison_table(version_summary_table, "Document Version Detection Results")
        
        # Show the resource savings
        display.print_info(f"Version tracking saved approximately {processing_saved:.1f}% of processing resources")
        display.print_info(f"Version history is preserved for {version_stats['updated']} documents")
    else:
        display.print_info("No version statistics available. Process documents to see version tracking results.")
    
    # Retrieve and display the fully enriched metadata (only once) after giving time for all processing
    time.sleep(2)  # Give a short delay to ensure all data is written to the database
    
    try:
        # Get the actual collection name from the ingestion object
        current_collection = ingestion.collection_name
        
        # Use a more specific query that includes document name to get richer results
        logger.info(f"Retrieving final enriched metadata from {current_collection}")
        sample_results = query_langchain(
            query="document OR report OR analysis", 
            collection_name=current_collection,
            top_k=1,
            metadata_filter=None
        )
        
        if sample_results and 'results' in sample_results and len(sample_results['results']) > 0:
            # Get the first result's metadata
            final_metadata = sample_results['results'][0]['metadata']
            
            # Enhance with direct permissions API
            final_metadata = enhance_metadata_with_permissions(final_metadata)
            
            # Display the fully enriched metadata
            display.print_section("Complete Document Metadata", "Final enriched metadata from vector store")
            # Keep only the formatted metadata table 
            display.print_metadata_example(final_metadata)
            
            # Show the version tree one more time with full data
            if 'version_info' in final_metadata:
                display.print_section("Final Document Version Info", "Complete version information")
                version_tree = display.create_version_history_tree(final_metadata['version_info'])
                if version_tree:
                    display.console.print(version_tree)
            
            # Display document content sample
            display.print_section("Document Content Sample", "From vector store")
            display.print_chunk_example(sample_results['results'][0]['content'], final_metadata)
            
            # Display permission info if available 
            if 'permissions' in final_metadata and final_metadata['permissions']:
                display.print_section("Document Permissions", "Access control information")
                
                # Show permission counts by role if we have an access summary
                if 'access_summary' in final_metadata:
                    summary = final_metadata['access_summary']
                    for role, users in summary.items():
                        if users:
                            display.print_info(f"{role.capitalize()}: {len(users)} users")
                
                # Show individual permissions (up to 5)
                for i, perm in enumerate(final_metadata['permissions'][:5]):
                    email = perm.get('emailAddress', 'unknown')
                    role = perm.get('role', 'unknown')
                    display.print_info(f"  • {email} ({role})")
                
                if len(final_metadata['permissions']) > 5:
                    display.print_info(f"... and {len(final_metadata['permissions']) - 5} more permissions")
            else:
                display.print_info("No permission information available for this document.")
        else:
            display.print_info("No final metadata available to display.")
    except Exception as e:
        logger.warning(f"Error retrieving final metadata: {str(e)}")
    
    # Display comparison table as the absolute last thing
    display.print_section("RAG Implementation Comparison", "Advanced vs. Basic RAG Features")
    
    # Display comparison table with advanced features
    comparisons = [
        {
            "Feature": "Authentication",
            "Our Implementation": "Multi-method service account authentication",
            "Basic RAG": "Simple API keys"
        },
        {
            "Feature": "Metadata Extraction",
            "Our Implementation": f"{len(all_metadata_fields)} fields, hierarchical with inheritance",
            "Basic RAG": "2-3 basic fields"
        },
        {
            "Feature": "Permissions Management",
            "Our Implementation": "Direct API calls with enhanced error handling",
            "Basic RAG": "No permission management or unreliable fetching"
        },
        {
            "Feature": "Document Versioning",
            "Our Implementation": "Full version history with content-aware detection",
            "Basic RAG": "No versioning (duplicates created)"
        },
        {
            "Feature": "Chunking Strategy",
            "Our Implementation": "Content-aware with customized parameters",
            "Basic RAG": "Fixed-size chunks"
        },
        {
            "Feature": "Vector Storage",
            "Our Implementation": "Supabase pgvector with optimized indexes",
            "Basic RAG": "Simple vector DB"
        },
        {
            "Feature": "Processing",
            "Our Implementation": "Parallel with auto-timeout protection",
            "Basic RAG": "Sequential processing"
        }
    ]
    
    display.display_comparison_table(comparisons, "Enterprise RAG Capabilities")
    
    display.print_success("Advanced ingestion example completed successfully")

def example_specific_files_ingestion():
    """Example of ingesting specific files by ID with enhanced display."""
    # Start timing for performance metrics
    start_time = time.time()
    
    # Display header
    display.print_header("Targeted Document Processing", "Specific Files RAG Ingestion")
    
    # Get file IDs (comma-separated list)
    file_ids_input = display.interactive_prompt("Enter comma-separated Google Drive file IDs to ingest (or press Enter to use example IDs)")
    
    if not file_ids_input.strip():
        # Use example IDs
        file_ids = ["1JoBfk9V2H_1BHteeK0jhw2D5y8BZYmAf", "1_nmPU93-Kby8RfdS2CdXd9kLueCUAVut"]
        display.print_info("Using example file IDs for demonstration")
    else:
        # Convert comma-separated string to list
        file_ids = [file_id.strip() for file_id in file_ids_input.split(",")]
    
    display.print_section("File Selection", "Processing specific documents by ID")
    
    for file_id in file_ids:
        display.print_info(f"Selected file ID: {file_id}")
    
    # Display special RAG features - Targeted Processing
    display.print_advanced_rag_feature(
        feature_name="Targeted Document Processing",
        description="Precision document processing with fine-grained control",
        standard_approach="Bulk processing with limited filtering options",
        our_approach="Document-specific processing with tailored parameters for each file",
        benefits=[
            "Process only the documents you need",
            "Apply different parameters to different document types",
            "Optimize resource usage by avoiding unnecessary processing",
            "Fine-tune chunking and embedding on a per-document basis"
        ]
    )
    
    # Create ingestion instance
    display.print_step(1, 3, "Initializing Vector Store", "Setting up Supabase for specific files")
    
    collection_name = "langchain_docs"  # Use one of the standard tables created during setup
    
    try:
        # Initialize ingestion
        ingestion = LangChainIngestion(
            collection_name=collection_name
        )
        display.print_success("Successfully initialized targeted ingestion pipeline")
    except Exception as e:
        display.print_error(f"Failed to initialize targeted ingestion: {str(e)}")
        return
    
    # Process files step
    display.print_step(2, 3, "Processing Selected Files", "Extracting and embedding specific documents")
    
    # Track statistics
    total_chunks = 0
    
    try:
        # Run ingestion for specific files
        docs, chunks, metadata_sample, version_stats = ingestion.ingest(
            file_ids=file_ids,
            load_extended_metadata=True,
            return_stats=True
        )
        
        total_chunks = chunks
        
        with display.create_progress_bar(len(file_ids), "Processing files") as progress:
            task = progress.add_task("Processing", total=len(file_ids))
            
            for i, file_id in enumerate(file_ids):
                # Just show the file ID until we have actual metadata
                display.print_info(f"Processing file ID: {file_id}")
                progress.update(task, advance=1)
        
        # Show embedding information for specific files
        display.print_embedding_info(
            model="text-embedding-3-small",
            vector_dimension=1536,
            processing_time=time.time() - start_time,
            batch_size=len(file_ids)  # Batch size matches file count for targeted processing
        )
        
        display.print_success("Successfully ingested specific files")
        
        # Now that documents have been added, retrieve metadata for display
        try:
            # Create a sample query to get real document metadata
            current_collection = ingestion.collection_name
            
            # Get actual metadata after ingestion
            logger.info(f"Retrieving metadata from collection: {current_collection}")
            sample_results = query_langchain(
                query="document", 
                collection_name=current_collection,
                top_k=1,
                metadata_filter=None
            )
            
            if sample_results and 'results' in sample_results and len(sample_results['results']) > 0:
                # Use the metadata from the first result
                metadata_sample = sample_results['results'][0]['metadata']
                logger.info("Successfully retrieved metadata from vector store")
                display.print_section("Document Metadata", "From vector store")
                display.print_metadata_example(metadata_sample)
                
                # Show example content
                display.print_section("Document Content Sample", "From vector store")
                display.print_chunk_example(sample_results['results'][0]['content'], metadata_sample)
            else:
                display.print_info("No document metadata available to display. Add documents to the vector store first.")
        except Exception as e:
            logger.warning(f"Error retrieving real metadata: {str(e)}")
            display.print_info("Error retrieving document metadata. Add documents to the vector store first.")
        
    except Exception as e:
        display.print_error(f"Error ingesting specific files: {str(e)}")
    
    # Final step
    display.print_step(3, 3, "Finalizing Vector Storage", "Completing targeted document processing")
    
    # Display vector storage info
    display.print_vector_storage_info(
        store_type="Supabase pgvector",
        table_name=collection_name,
        total_stored=total_chunks,
        failed=0,
        index_type="IVF"
    )
    
    # Display overall performance
    total_time = time.time() - start_time
    display.print_performance_metrics({
        "Total Processing Time": total_time,
        "Files Processed": len(file_ids),
        "Processing Time per File": total_time / len(file_ids),
        "Chunks Generated": total_chunks,
        "Chunks per File": total_chunks / len(file_ids)
    })
    
    # Retrieve and display the fully enriched metadata (only once) after giving time for all processing
    time.sleep(2)  # Give a short delay to ensure all data is written to the database
    
    try:
        # Get the actual collection name from the ingestion object
        current_collection = ingestion.collection_name
        
        # Use a more specific query using file IDs we processed
        logger.info(f"Retrieving final enriched metadata from {current_collection}")
        
        # Build a targeted query based on the file IDs
        file_query = " OR ".join([f"file_id:{file_id}" for file_id in file_ids[:2]])
        sample_results = query_langchain(
            query=file_query or "document", 
            collection_name=current_collection,
            top_k=1,
            metadata_filter=None
        )
        
        if sample_results and 'results' in sample_results and len(sample_results['results']) > 0:
            # Get the first result's metadata
            final_metadata = sample_results['results'][0]['metadata']
            
            # Enhance with direct permissions API
            final_metadata = enhance_metadata_with_permissions(final_metadata)
            
            # Display the fully enriched metadata
            display.print_section("Complete Document Metadata", "Final enriched metadata from vector store")
            # Keep only the formatted metadata table 
            display.print_metadata_example(final_metadata)
            
            # Show the version tree one more time with full data
            if 'version_info' in final_metadata:
                display.print_section("Final Document Version Info", "Complete version information")
                version_tree = display.create_version_history_tree(final_metadata['version_info'])
                if version_tree:
                    display.console.print(version_tree)
            
            # Display document content sample
            display.print_section("Document Content Sample", "From vector store")
            display.print_chunk_example(sample_results['results'][0]['content'], final_metadata)
            
            # Display permission info if available 
            if 'permissions' in final_metadata and final_metadata['permissions']:
                display.print_section("Document Permissions", "Access control information")
                
                # Show permission counts by role if we have an access summary
                if 'access_summary' in final_metadata:
                    summary = final_metadata['access_summary']
                    for role, users in summary.items():
                        if users:
                            display.print_info(f"{role.capitalize()}: {len(users)} users")
                
                # Show individual permissions (up to 5)
                for i, perm in enumerate(final_metadata['permissions'][:5]):
                    email = perm.get('emailAddress', 'unknown')
                    role = perm.get('role', 'unknown')
                    display.print_info(f"  • {email} ({role})")
                
                if len(final_metadata['permissions']) > 5:
                    display.print_info(f"... and {len(final_metadata['permissions']) - 5} more permissions")
            else:
                display.print_info("No permission information available for this document.")
        else:
            display.print_info("No final metadata available to display.")
    except Exception as e:
        logger.warning(f"Error retrieving final metadata: {str(e)}")
    
    # Display comparison table as the absolute last thing
    display.print_section("Targeted RAG Processing", "Precision vs. Bulk Processing")
    
    # Display comparison table specific to targeted processing
    comparisons = [
        {
            "Feature": "Processing Scope",
            "Our Implementation": "Targeted specific documents",
            "Basic RAG": "Entire folders or collections"
        },
        {
            "Feature": "Resource Efficiency",
            "Our Implementation": "Process only what's needed",
            "Basic RAG": "Process everything regardless of need"
        },
        {
            "Feature": "Content Tracking",
            "Our Implementation": "Content-change detection avoids unnecessary re-embedding",
            "Basic RAG": "Always regenerates embeddings"
        },
        {
            "Feature": "Update Granularity",
            "Our Implementation": "File-level precision updates",
            "Basic RAG": "Bulk or nothing approach"
        }
    ]
    
    display.display_comparison_table(comparisons, "Targeted vs. Bulk Processing")
    
    display.print_success("Specific files ingestion example completed successfully")

def example_enhanced_media_ingestion():
    """Example of ingesting media files with OCR, table extraction, and image analysis."""
    # Start timing for performance metrics
    start_time = time.time()
    
    # Display header
    display.print_header("Advanced Media Processing", "OCR, Table Extraction, and Image Analysis")
    
    # Get file IDs (comma-separated list)
    file_ids_input = display.interactive_prompt("Enter comma-separated Google Drive file IDs to ingest (images, PDFs) or press Enter to use example IDs")
    
    if not file_ids_input.strip():
        # Use example IDs - include image and PDF IDs if available
        file_ids = ["1JoBfk9V2H_1BHteeK0jhw2D5y8BZYmAf", "1_nmPU93-Kby8RfdS2CdXd9kLueCUAVut"]
        display.print_info("Using example file IDs for demonstration")
    else:
        # Convert comma-separated string to list
        file_ids = [file_id.strip() for file_id in file_ids_input.split(",")]
    
    display.print_section("Media File Selection", "Processing media files with enhanced extraction")
    
    for file_id in file_ids:
        display.print_info(f"Selected file ID: {file_id}")
    
    # Display special RAG features - Media Processing
    display.print_advanced_rag_feature(
        feature_name="Advanced Media Extraction",
        description="Comprehensive media processing with OCR, table extraction, and image analysis",
        standard_approach="Basic text extraction without media content understanding",
        our_approach="Multi-modal extraction with OCR, table formatting, and visual analysis",
        benefits=[
            "Convert images to searchable text with OCR",
            "Extract and format tables from PDFs",
            "Analyze image content for enhanced context",
            "Preserve visual and tabular information in vector database"
        ]
    )
    
    # Display OCR features
    display.print_advanced_rag_feature(
        feature_name="Advanced OCR Processing",
        description="High-quality text extraction from images with pre-processing",
        standard_approach="Simple OCR without image enhancement",
        our_approach="Enhanced OCR with image pre-processing and confidence scoring",
        benefits=[
            "Image pre-processing improves text recognition quality",
            "Grayscale conversion and adaptive thresholding for better results",
            "OCR confidence scoring to assess extraction reliability",
            "Word count statistics for extracted content"
        ]
    )
    
    # Display table extraction features
    display.print_advanced_rag_feature(
        feature_name="Intelligent Table Extraction",
        description="Extract tabular data from PDFs with structure preservation",
        standard_approach="Flat text extraction with table structure loss",
        our_approach="Multi-engine table detection with structure preservation",
        benefits=[
            "Detect and parse complex tables in PDF documents",
            "Preserve table structure for better understanding",
            "Format tables with row/column relationships intact",
            "Fallback mechanisms for different table types"
        ]
    )
    
    # Display image analysis features
    display.print_advanced_rag_feature(
        feature_name="Computer Vision Analysis",
        description="Extract meaningful context from images through CV techniques",
        standard_approach="No image content understanding",
        our_approach="Computer vision analysis for context extraction",
        benefits=[
            "Face detection for identifying people in images",
            "Image complexity assessment",
            "Color analysis for content understanding",
            "Descriptive text generation from visual features"
        ]
    )
    
    # Create ingestion instance
    display.print_step(1, 4, "Initializing Media Processing Pipeline", "Setting up enhanced ingestion with media capabilities")
    
    collection_name = "media_enhanced"  # Use a dedicated collection for media-enhanced content
    
    try:
        # Initialize ingestion
        ingestion = LangChainIngestion(
            collection_name=collection_name
        )
        display.print_success("Successfully initialized enhanced media processing pipeline")
    except Exception as e:
        display.print_error(f"Failed to initialize media processing: {str(e)}")
        return
    
    # Verify dependencies
    display.print_step(2, 4, "Verifying Dependencies", "Checking for required media processing libraries")
    
    dependencies = [
        {"name": "Tesseract OCR", "check": "import pytesseract", "install": "pip install pytesseract", "note": "Also requires Tesseract OCR engine installation"},
        {"name": "OpenCV", "check": "import cv2", "install": "pip install opencv-python"},
        {"name": "PIL/Pillow", "check": "from PIL import Image", "install": "pip install Pillow"},
        {"name": "Tabula", "check": "import tabula", "install": "pip install tabula-py", "note": "Requires Java runtime"},
        {"name": "Camelot", "check": "import camelot", "install": "pip install camelot-py[cv]", "note": "Requires Ghostscript"}
    ]
    
    missing_deps = []
    for dep in dependencies:
        try:
            exec(dep["check"])
            display.print_success(f"✅ {dep['name']} is installed")
        except ImportError:
            missing_deps.append(dep)
            display.print_warning(f"❌ {dep['name']} is missing - install with: {dep['install']}")
            if "note" in dep:
                display.print_info(f"   Note: {dep['note']}")
    
    if missing_deps:
        display.print_warning("Some dependencies are missing. Example will continue but may have limited functionality.")
        display.print_info("Some features may be automatically installed during processing.")
    
    # Process media files
    display.print_step(3, 4, "Processing Media Files", "Applying OCR, table extraction, and image analysis")
    
    # Track statistics
    total_chunks = 0
    media_stats = {
        "images_processed": 0,
        "tables_extracted": 0,
        "ocr_word_count": 0
    }
    
    try:
        # Run ingestion for media files with enhanced processing enabled
        docs, chunks, metadata_sample, version_stats = ingestion.ingest(
            file_ids=file_ids,
            load_extended_metadata=True,
            return_stats=True,
            enable_enhanced_media_processing=True  # Enable the new enhanced media processing
        )
        
        total_chunks = chunks
        
        with display.create_progress_bar(len(file_ids), "Processing media files") as progress:
            task = progress.add_task("Processing", total=len(file_ids))
            
            for i, file_id in enumerate(file_ids):
                # Just show the file ID until we have actual metadata
                display.print_info(f"Processing media file ID: {file_id}")
                progress.update(task, advance=1)
        
        # Show embedding information 
        display.print_embedding_info(
            model="text-embedding-3-small",
            vector_dimension=1536,
            processing_time=time.time() - start_time,
            batch_size=len(file_ids)
        )
        
        display.print_success("Successfully processed media files with enhanced extraction")
        
        # Now retrieve metadata for display to show the enhanced extraction results
        try:
            # Create a sample query to get real document metadata after processing
            current_collection = ingestion.collection_name
            
            # Get actual metadata from processed media files
            logger.info(f"Retrieving metadata from collection: {current_collection}")
            
            # Try to query specifically for media content
            media_query = "image OR table OR ocr OR pdf"
            sample_results = query_langchain(
                query=media_query, 
                collection_name=current_collection,
                top_k=2,  # Get a couple of results to increase chances of finding media
                metadata_filter=None
            )
            
            if sample_results and 'results' in sample_results and len(sample_results['results']) > 0:
                # Process results and find examples of each media type
                ocr_example = None
                table_example = None
                image_analysis_example = None
                
                # Scan results for different media types
                for result in sample_results['results']:
                    metadata = result['metadata']
                    content = result['content']
                    
                    # Detect media type from metadata
                    if metadata.get('extraction_method') == 'ocr' or 'ocr_confidence' in metadata:
                        ocr_example = (content, metadata)
                        media_stats['images_processed'] += 1
                        media_stats['ocr_word_count'] += metadata.get('ocr_word_count', 0)
                    elif metadata.get('extraction_method') == 'table' or metadata.get('content_type') == 'pdf_tables':
                        table_example = (content, metadata)
                        media_stats['tables_extracted'] += metadata.get('tables_count', 0)
                    elif metadata.get('extraction_method') == 'image_analysis':
                        image_analysis_example = (content, metadata)
                        media_stats['images_processed'] += 1
                    
                # Show OCR example if available
                if ocr_example:
                    display.print_section("OCR Text Extraction Example", "Text extracted from image")
                    text, metadata = ocr_example
                    display.print_metadata_example(metadata)
                    display.print_chunk_example(text, metadata)
                    
                    # Show OCR statistics
                    display.print_info(f"OCR confidence score: {metadata.get('ocr_confidence', 'N/A')}")
                    display.print_info(f"Words extracted: {metadata.get('ocr_word_count', 'N/A')}")
                    display.print_info(f"Image dimensions: {metadata.get('image_width', 'N/A')}x{metadata.get('image_height', 'N/A')}")
                
                # Show table extraction example if available
                if table_example:
                    display.print_section("Table Extraction Example", "Tables extracted from PDF")
                    text, metadata = table_example
                    display.print_metadata_example(metadata)
                    display.print_chunk_example(text, metadata)
                    
                    # Show table statistics
                    display.print_info(f"Tables extracted: {metadata.get('tables_count', 'N/A')}")
                    display.print_info(f"Extraction engine: {metadata.get('table_extraction_engine', 'N/A')}")
                    display.print_info(f"Table text length: {metadata.get('tables_text_length', 'N/A')} characters")
                
                # Show image analysis example if available
                if image_analysis_example:
                    display.print_section("Image Analysis Example", "Visual content understanding")
                    text, metadata = image_analysis_example
                    display.print_metadata_example(metadata)
                    display.print_chunk_example(text, metadata)
                    
                    # Show image analysis statistics
                    if 'faces_detected' in metadata:
                        display.print_info(f"Faces detected: {metadata.get('faces_detected', 'N/A')}")
                    display.print_info(f"Image complexity: {metadata.get('edge_complexity', 'N/A')}")
                    display.print_info(f"Image dimensions: {metadata.get('image_width', 'N/A')}x{metadata.get('image_height', 'N/A')}")
                
                # If no specific examples found, show generic metadata
                if not (ocr_example or table_example or image_analysis_example):
                    # Use the first result's metadata
                    display.print_section("Document Metadata", "No specialized media processing detected")
                    metadata_sample = sample_results['results'][0]['metadata']
                    display.print_metadata_example(metadata_sample)
                    
                    # Show example content
                    display.print_section("Document Content Sample", "From vector store")
                    display.print_chunk_example(sample_results['results'][0]['content'], metadata_sample)
            else:
                display.print_info("No document metadata available to display. Add media files to the vector store first.")
        except Exception as e:
            logger.warning(f"Error retrieving media processing results: {str(e)}")
            display.print_info("Error retrieving document metadata. Add media files to the vector store first.")
        
    except Exception as e:
        display.print_error(f"Error processing media files: {str(e)}")
    
    # Final evaluation
    display.print_step(4, 4, "Media Analysis Results", "Enhanced information extraction metrics")
    
    # Display vector storage info
    display.print_vector_storage_info(
        store_type="Supabase pgvector",
        table_name=collection_name,
        total_stored=total_chunks,
        failed=0,
        index_type="IVF"
    )
    
    # Display overall performance
    total_time = time.time() - start_time
    display.print_performance_metrics({
        "Total Processing Time": total_time,
        "Files Processed": len(file_ids),
        "Processing Time per File": total_time / len(file_ids),
        "Chunks Generated": total_chunks,
        "Chunks per File": total_chunks / len(file_ids),
        "Images Processed": media_stats["images_processed"],
        "Tables Extracted": media_stats["tables_extracted"],
        "OCR Words Extracted": media_stats["ocr_word_count"]
    })
    
    # Display comparison table for enhanced vs basic processing
    display.print_section("Enhanced vs Basic Media Processing", "Comparison of capabilities")
    
    # Display comparison table specific to media processing
    comparisons = [
        {
            "Feature": "Image Content",
            "Enhanced Processing": "Full text extraction via OCR + visual analysis",
            "Basic Processing": "No text extraction from images"
        },
        {
            "Feature": "PDF Tables",
            "Enhanced Processing": "Structured table extraction with formatting preserved",
            "Basic Processing": "Tables flattened to plain text, structure lost"
        },
        {
            "Feature": "Media Context",
            "Enhanced Processing": "Contextual information about visual content",
            "Basic Processing": "No understanding of visual elements"
        },
        {
            "Feature": "Search Relevance",
            "Enhanced Processing": "Can find information inside images and tables",
            "Basic Processing": "Cannot find content in images or formatted tables"
        }
    ]
    
    display.display_comparison_table(comparisons, "Media Processing Comparison")
    
    display.print_success("Enhanced media ingestion example completed successfully")

if __name__ == "__main__":
    # Display the examples menu with enhanced visuals
    display.print_header("LangChain RAG Examples", "Advanced Document Processing Demonstrations")
    
    # Add a note about SSL handling
    display.print_info("Note: This demo connects to Google Drive API and may show SSL connection messages.")
    display.print_info("These are normal and handled gracefully - metadata will be properly retrieved.")
    display.print_info("Full metadata will still be available at the end of processing.")
    
    # Add a note about sample documents
    display.print_info("If no valid Google Drive credentials are found, sample documents will be used.")
    display.print_info("To use your own documents, provide a valid service-account.json in the config folder.")
    
    table = [
        {"Option": "1", "Example": "Basic ingestion", "Description": "Process all folders with standard settings"}, 
        {"Option": "2", "Example": "Advanced ingestion", "Description": "Process with optimized parameters and enhanced features"},
        {"Option": "3", "Example": "Specific files", "Description": "Target individual documents with precision processing"},
        {"Option": "4", "Example": "Enhanced media", "Description": "Process images and PDFs with OCR, table extraction, and image analysis"}
    ]
    
    display.display_comparison_table(table, "Available Examples")
    
    choice = display.interactive_prompt(
        "Select an example to run", 
        choices=["1", "2", "3", "4"],
        default="1"
    )
    
    if choice == "1":
        example_basic_ingestion()
    elif choice == "2":
        example_advanced_ingestion()
    elif choice == "3":
        example_specific_files_ingestion()
    elif choice == "4":
        example_enhanced_media_ingestion()
    else:
        display.print_error("Invalid choice. Please select 1, 2, 3, or 4.")
        sys.exit(1)