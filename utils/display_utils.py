#!/usr/bin/env python3
"""
Advanced terminal output utilities for displaying RAG pipeline progress,
statistics, and results in a visually appealing and informative way.
"""

import time
import json
import sys
from typing import Dict, List, Any, Optional, Union, Callable
import humanize
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.syntax import Syntax
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout
from rich import box
from rich.prompt import Prompt, Confirm
from pyfiglet import Figlet
import colorama
from colorama import Fore, Style
from tabulate import tabulate

# Initialize colorama for cross-platform color support
colorama.init()

# Initialize rich console
console = Console()

class DisplayManager:
    """Manages advanced terminal displays for the RAG pipeline."""
    
    def __init__(self, show_advanced_output: bool = True, color_enabled: bool = True):
        """Initialize the display manager.
        
        Args:
            show_advanced_output: Whether to show advanced/detailed output
            color_enabled: Whether to use colored output
        """
        self.show_advanced_output = show_advanced_output
        self.color_enabled = color_enabled
        self.console = console
        self.start_time = time.time()
        
    def print_header(self, title: str, subtitle: Optional[str] = None):
        """Print a fancy header with optional subtitle.
        
        Args:
            title: The main title text
            subtitle: Optional subtitle text
        """
        if not self.show_advanced_output:
            print(f"\n=== {title} ===")
            if subtitle:
                print(f"{subtitle}\n")
            return
            
        f = Figlet(font='slant')
        header_text = f.renderText(title)
        
        self.console.print("\n")
        self.console.print(Panel(
            Text(header_text, style="bold blue"),
            subtitle=subtitle,
            expand=False,
            border_style="blue",
            padding=(1, 3)
        ))
        self.console.print("\n")
        
    def print_section(self, title: str, description: Optional[str] = None):
        """Print a section header.
        
        Args:
            title: The section title
            description: Optional description
        """
        if not self.show_advanced_output:
            print(f"\n--- {title} ---")
            if description:
                print(f"{description}")
            return
        
        self.console.print(f"\n[bold cyan]■ {title}[/bold cyan]")
        if description:
            self.console.print(f"  [dim]{description}[/dim]")
            
    def print_step(self, step_num: int, total_steps: int, title: str, description: Optional[str] = None):
        """Print a step header within a section.
        
        Args:
            step_num: Current step number
            total_steps: Total number of steps
            title: Step title
            description: Optional step description
        """
        if not self.show_advanced_output:
            print(f"\n[{step_num}/{total_steps}] {title}")
            if description:
                print(f"  {description}")
            return
            
        self.console.print(f"\n[bold green]Step {step_num}/{total_steps}:[/bold green] [yellow]{title}[/yellow]")
        if description:
            self.console.print(f"  [dim]{description}[/dim]")
            
    def print_info(self, message: str, prefix: Optional[str] = None):
        """Print an info message.
        
        Args:
            message: The info message
            prefix: Optional prefix to add
        """
        prefix_text = f"{prefix}: " if prefix else ""
        
        if not self.show_advanced_output:
            print(f"INFO: {prefix_text}{message}")
            return
            
        self.console.print(f"[blue]ℹ[/blue] {prefix_text}[white]{message}[/white]")
        
    def print_success(self, message: str):
        """Print a success message.
        
        Args:
            message: The success message
        """
        if not self.show_advanced_output:
            print(f"SUCCESS: {message}")
            return
            
        self.console.print(f"[bold green]✓[/bold green] {message}")
        
    def print_warning(self, message: str):
        """Print a warning message.
        
        Args:
            message: The warning message
        """
        if not self.show_advanced_output:
            print(f"WARNING: {message}")
            return
            
        self.console.print(f"[bold yellow]⚠[/bold yellow] {message}")
        
    def print_error(self, message: str):
        """Print an error message.
        
        Args:
            message: The error message
        """
        if not self.show_advanced_output:
            print(f"ERROR: {message}")
            return
            
        self.console.print(f"[bold red]✗[/bold red] {message}")
        
    def print_file_info(self, file_name: str, mime_type: str, file_id: str, size: Optional[int] = None):
        """Print file information.
        
        Args:
            file_name: Name of the file
            mime_type: MIME type of the file
            file_id: ID of the file
            size: Optional size of the file in bytes
        """
        if not self.show_advanced_output:
            size_str = f" ({humanize.naturalsize(size)})" if size else ""
            print(f"File: {file_name}{size_str} [{mime_type}] ID: {file_id}")
            return
            
        size_str = f" ({humanize.naturalsize(size)})" if size else ""
        
        # Get file extension and use it for icon selection
        ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
        icon = self._get_file_icon(ext, mime_type)
        
        self.console.print(f"[bold]{icon}[/bold] [cyan]{file_name}[/cyan]{size_str}")
        self.console.print(f"  [dim]Type:[/dim] [yellow]{mime_type}[/yellow]")
        self.console.print(f"  [dim]ID:[/dim] [blue]{file_id}[/blue]")
        
    def _get_file_icon(self, extension: str, mime_type: str) -> str:
        """Get an appropriate icon for a file based on its extension or MIME type.
        
        Args:
            extension: File extension
            mime_type: MIME type
            
        Returns:
            An icon character representing the file type
        """
        if 'pdf' in extension or 'pdf' in mime_type:
            return "📄"
        elif 'doc' in extension or 'word' in mime_type:
            return "📝"
        elif 'xls' in extension or 'sheet' in mime_type:
            return "📊"
        elif 'ppt' in extension or 'presentation' in mime_type:
            return "📽️"
        elif 'txt' in extension or 'text' in mime_type:
            return "📄"
        elif 'jpg' in extension or 'jpeg' in extension or 'png' in extension or 'image' in mime_type:
            return "🖼️"
        else:
            return "📄"
            
    def create_progress_bar(self, total: int, description: str) -> Progress:
        """Create a rich progress bar.
        
        Args:
            total: Total number of items to process
            description: Description of the process
            
        Returns:
            A Progress object for tracking progress
        """
        if not self.show_advanced_output:
            return None
            
        return Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=50),
            TaskProgressColumn(),
            TimeElapsedColumn()
        )
        
    def print_document_stats(self, docs_count: int, chunks_count: int, metadata_fields: List[str]):
        """Print statistics about processed documents.
        
        Args:
            docs_count: Number of documents processed
            chunks_count: Number of chunks generated
            metadata_fields: List of metadata fields captured
        """
        if not self.show_advanced_output:
            print(f"\nDocument Stats:")
            print(f"- Documents: {docs_count}")
            print(f"- Chunks: {chunks_count}")
            print(f"- Avg chunks per doc: {chunks_count/max(1, docs_count):.1f}")
            print(f"- Metadata fields: {', '.join(metadata_fields[:5])}...")
            return
            
        table = Table(title="📊 Document Processing Statistics", box=box.ROUNDED)
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Documents Processed", str(docs_count))
        table.add_row("Chunks Generated", str(chunks_count))
        
        # Avoid division by zero
        chunks_per_doc = chunks_count / max(1, docs_count) if docs_count > 0 else 0
        table.add_row("Chunks per Document", f"{chunks_per_doc:.1f}")
        
        table.add_row("Processing Time", f"{time.time() - self.start_time:.2f}s")
        
        metadata_display = ", ".join(metadata_fields[:7])
        if len(metadata_fields) > 7:
            metadata_display += ", ..."
            
        table.add_row("Metadata Fields", metadata_display)
        
        self.console.print(table)
        
    def print_embedding_info(self, model: str, vector_dimension: int, processing_time: float, batch_size: int = 0):
        """Print information about the embedding process.
        
        Args:
            model: Embedding model name
            vector_dimension: Dimension of vectors
            processing_time: Time taken for embedding in seconds
            batch_size: Batch size used for embedding
        """
        if not self.show_advanced_output:
            print(f"\nEmbedding Info:")
            print(f"- Model: {model}")
            print(f"- Dimensions: {vector_dimension}")
            print(f"- Processing time: {processing_time:.2f}s")
            if batch_size:
                print(f"- Batch size: {batch_size}")
            return
            
        panel = Panel(
            Text.from_markup(
                f"[bold]Model:[/bold] [green]{model}[/green]\n"
                f"[bold]Vector Dimension:[/bold] [blue]{vector_dimension}[/blue]\n"
                f"[bold]Processing Time:[/bold] [yellow]{processing_time:.2f}s[/yellow]" +
                (f"\n[bold]Batch Size:[/bold] [magenta]{batch_size}[/magenta]" if batch_size else "")
            ),
            title="🔢 Embedding Information",
            border_style="cyan"
        )
        
        self.console.print(panel)
        
    def print_metadata_example(self, metadata: Dict[str, Any]):
        """Print an example of the document metadata.
        
        Args:
            metadata: A metadata dictionary to display
        """
        if not self.show_advanced_output:
            print(f"\nMetadata Example:")
            for key, value in list(metadata.items())[:5]:
                print(f"- {key}: {value}")
            if len(metadata) > 5:
                print("- ...")
            return
            
        # Create a nicely formatted JSON representation
        json_str = json.dumps(metadata, indent=2)
        
        self.console.print(Panel(
            Syntax(json_str, "json", theme="monokai", line_numbers=True),
            title="📋 Metadata Example",
            border_style="green",
            expand=False
        ))
        
    def print_chunk_example(self, text: str, metadata: Dict[str, Any]):
        """Print an example of a document chunk with its metadata.
        
        Args:
            text: Chunk text content
            metadata: Chunk metadata
        """
        if not self.show_advanced_output:
            print(f"\nChunk Example (first 100 chars):")
            print(f"{text[:100]}...")
            print("Metadata:")
            for key, value in list(metadata.items())[:3]:
                print(f"- {key}: {value}")
            if len(metadata) > 3:
                print("- ...")
            return
            
        layout = Layout()
        layout.split_column(
            Layout(Panel(
                Text(text[:500] + "..." if len(text) > 500 else text, 
                     style="white"),
                title="📄 Chunk Content Preview",
                border_style="blue",
                padding=(1, 2)
            )),
            Layout(Panel(
                Syntax(json.dumps(metadata, indent=2), "json", theme="monokai"),
                title="🏷️  Chunk Metadata",
                border_style="green",
                padding=(1, 2)
            ))
        )
        
        self.console.print(layout)
        
    def print_vector_storage_info(self, store_type: str, table_name: str, 
                                  total_stored: int, failed: int = 0,
                                  index_type: Optional[str] = None):
        """Print information about the vector storage.
        
        Args:
            store_type: Type of vector store (e.g., 'Supabase', 'Chroma')
            table_name: Name of the table or collection
            total_stored: Total number of vectors stored
            failed: Number of storage operations that failed
            index_type: Type of index used (if applicable)
        """
        if not self.show_advanced_output:
            print(f"\nVector Storage:")
            print(f"- Type: {store_type}")
            print(f"- Table/Collection: {table_name}")
            print(f"- Vectors stored: {total_stored}")
            if failed:
                print(f"- Failed operations: {failed}")
            if index_type:
                print(f"- Index type: {index_type}")
            return
            
        # Use a different icon based on the store type
        icon = "💾" if store_type.lower() == "supabase" else "🧠"
        
        success_rate = ((total_stored - failed) / total_stored * 100) if total_stored > 0 else 0
        
        table = Table(title=f"{icon} Vector Storage Summary", box=box.ROUNDED)
        
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Store Type", store_type)
        table.add_row("Table/Collection", table_name)
        table.add_row("Total Vectors", str(total_stored))
        
        if failed:
            table.add_row("Failed Operations", f"[red]{failed}[/red]")
            table.add_row("Success Rate", f"{success_rate:.1f}%")
            
        if index_type:
            table.add_row("Index Type", index_type)
            
        self.console.print(table)
        
    def print_performance_metrics(self, metrics: Dict[str, Union[float, int]]):
        """Print performance metrics.
        
        Args:
            metrics: Dictionary of metrics to display
        """
        if not self.show_advanced_output:
            print(f"\nPerformance Metrics:")
            for key, value in metrics.items():
                if isinstance(value, float):
                    print(f"- {key}: {value:.2f}")
                else:
                    print(f"- {key}: {value}")
            return
            
        table = Table(title="⚡ Performance Metrics", box=box.ROUNDED)
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in metrics.items():
            if isinstance(value, float):
                formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)
                
            table.add_row(key, formatted_value)
            
        self.console.print(table)
        
    def print_advanced_rag_feature(self, feature_name: str, description: str, 
                                  standard_approach: str, our_approach: str,
                                  benefits: List[str]):
        """Highlight an advanced RAG feature with comparison to standard approaches.
        
        Args:
            feature_name: Name of the feature
            description: Description of the feature
            standard_approach: How it's done in standard/basic RAG
            our_approach: How our implementation does it
            benefits: List of benefits of our approach
        """
        if not self.show_advanced_output:
            print(f"\nAdvanced Feature: {feature_name}")
            print(f"- Description: {description}")
            print(f"- Standard approach: {standard_approach}")
            print(f"- Our approach: {our_approach}")
            print("- Benefits:")
            for benefit in benefits:
                print(f"  * {benefit}")
            return
            
        panel = Panel(
            Text.from_markup(
                f"[bold cyan]{feature_name}[/bold cyan]\n\n"
                f"{description}\n\n"
                f"[bold red]Standard Approach:[/bold red]\n"
                f"{standard_approach}\n\n"
                f"[bold green]Our Advanced Approach:[/bold green]\n"
                f"{our_approach}\n\n"
                f"[bold blue]Benefits:[/bold blue]"
            ),
            title="⭐ Advanced RAG Feature",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        # Print benefits as a bulleted list
        for benefit in benefits:
            self.console.print(f"  [bold blue]•[/bold blue] {benefit}")
            
    def create_metadata_tree(self, metadata: Dict[str, Any], title: str = "Metadata Structure") -> Tree:
        """Create a tree visualization of metadata hierarchy.
        
        Args:
            metadata: The metadata dictionary
            title: Title for the tree
            
        Returns:
            A Tree object representing the metadata structure
        """
        if not self.show_advanced_output:
            return None
            
        tree = Tree(f"[bold]{title}[/bold]")
        
        def add_to_tree(node, data, parent_key=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    display_key = f"[cyan]{key}[/cyan]"
                    
                    if isinstance(value, (dict, list)):
                        branch = node.add(display_key)
                        add_to_tree(branch, value, key)
                    else:
                        value_str = str(value)
                        if len(value_str) > 50:
                            value_str = value_str[:47] + "..."
                            
                        if key.endswith("_id") or key == "id":
                            node.add(f"{display_key}: [blue]{value_str}[/blue]")
                        elif "date" in key or "time" in key:
                            node.add(f"{display_key}: [yellow]{value_str}[/yellow]")
                        elif key == "source" or "source" in key:
                            node.add(f"{display_key}: [green]{value_str}[/green]")
                        else:
                            node.add(f"{display_key}: {value_str}")
            elif isinstance(data, list):
                if data and all(isinstance(x, dict) for x in data):
                    # For lists of dictionaries, show only the first N items
                    for i, item in enumerate(data[:3]):
                        item_node = node.add(f"[magenta]Item {i}[/magenta]")
                        add_to_tree(item_node, item)
                    if len(data) > 3:
                        node.add(f"[dim]... {len(data) - 3} more items ...[/dim]")
                else:
                    # For simple lists or mixed content
                    values = []
                    for item in data[:5]:
                        if isinstance(item, (dict, list)):
                            item_type = type(item).__name__
                            values.append(f"[{item_type}]")
                        else:
                            item_str = str(item)
                            if len(item_str) > 30:
                                item_str = item_str[:27] + "..."
                            values.append(item_str)
                            
                    display_value = ", ".join(values)
                    if len(data) > 5:
                        display_value += f", ... ({len(data) - 5} more)"
                    node.add(f"[magenta]List[/magenta]: {display_value}")
        
        add_to_tree(tree, metadata)
        return tree
        
    def create_tree(self, title: str) -> Tree:
        """Create a simple tree with a title.
        
        Args:
            title: Title for the tree
            
        Returns:
            A Tree object with the given title
        """
        if not self.show_advanced_output:
            return None
            
        return Tree(f"[bold]{title}[/bold]")
        
    def create_version_history_tree(self, version_info: Dict[str, Any], title: str = "Document Version History") -> Tree:
        """Create a tree visualization of document version history.
        
        Args:
            version_info: The version_info metadata dictionary
            title: Title for the tree
            
        Returns:
            A Tree object representing the version history
        """
        if not self.show_advanced_output:
            return None
            
        tree = Tree(f"[bold]{title}[/bold]")
        
        current_version = version_info.get('version', '1.0')
        created_at = version_info.get('created_at', 'unknown')
        updated_at = version_info.get('updated_at', created_at)
        
        # Add current version
        version_node = tree.add(f"[green]Current: v{current_version} ({updated_at})[/green]")
        
        # Add previous versions
        previous_versions = version_info.get('previous_versions', [])
        if previous_versions:
            history_node = version_node.add("[yellow]Version History[/yellow]")
            
            for i, prev in enumerate(previous_versions):
                prev_version = prev.get('version', f"v{i}")
                prev_date = prev.get('updated_at', 'unknown')
                
                # Add details about this version
                version_entry = f"v{prev_version} ({prev_date})"
                if 'last_editor' in prev:
                    version_entry += f" - {prev.get('last_editor')}"
                    
                history_node.add(f"[blue]{version_entry}[/blue]")
        else:
            version_node.add("[dim]No previous versions[/dim]")
            
        return tree
        
    def display_comparison_table(self, comparisons: List[Dict[str, Any]], title: str = "Comparison"):
        """Display a comparison table between different approaches.
        
        Args:
            comparisons: List of dictionaries with comparison data
            title: Title for the comparison table
        """
        if not self.show_advanced_output:
            print(f"\n{title}:")
            headers = comparisons[0].keys()
            # Convert all values to strings
            rows = [[str(value) for value in comp.values()] for comp in comparisons]
            print(tabulate(rows, headers=headers, tablefmt="simple"))
            return
            
        table = Table(title=f"🔍 {title}", box=box.ROUNDED)
        
        # Add columns from the first comparison item
        if comparisons:
            for key in comparisons[0].keys():
                style = "cyan" if key == "Feature" else None
                table.add_column(key, style=style)
                
            # Add rows
            for comp in comparisons:
                values = []
                for key, value in comp.items():
                    # Apply styling based on column type
                    if key == "Our Approach" or key == "Our Implementation":
                        values.append(f"[green]{value}[/green]")
                    elif key == "Basic Approach" or key == "Basic RAG":
                        values.append(f"[red]{value}[/red]")
                    else:
                        # Convert any non-string values to strings
                        values.append(str(value))
                        
                table.add_row(*values)
                
            self.console.print(table)
    
    def interactive_prompt(self, message: str, choices: Optional[List[str]] = None, 
                          default: Optional[str] = None) -> str:
        """Display an interactive prompt for user input.
        
        Args:
            message: Prompt message
            choices: Optional list of choices
            default: Optional default value
            
        Returns:
            User's response
        """
        if not self.show_advanced_output or not choices:
            if default:
                user_input = input(f"{message} [{default}]: ") or default
            else:
                user_input = input(f"{message}: ")
            return user_input
            
        return Prompt.ask(
            message,
            choices=choices if choices else None,
            default=default
        )
    
    def confirm_prompt(self, question: str, default: bool = False) -> bool:
        """Display a yes/no confirmation prompt.
        
        Args:
            question: Question to ask
            default: Default answer (True=Yes, False=No)
            
        Returns:
            Boolean indicating user's response
        """
        if not self.show_advanced_output:
            default_str = "Y/n" if default else "y/N"
            response = input(f"{question} [{default_str}]: ").strip().lower()
            
            if not response:
                return default
            
            return response.startswith('y')
            
        return Confirm.ask(question, default=default)

    def start_spinner(self, message: str) -> None:
        """Start a spinner with a message (simplified version).
        
        Args:
            message: Message to display with the spinner
        """
        if not self.show_advanced_output:
            print(f"{message}...")
            return
            
        # In a real implementation, this would create and return a spinner object
        # For simplicity, we're just printing the message
        self.console.print(f"[bold cyan]{message}...[/bold cyan]")

# Instantiate a global display manager for use throughout the application
display = DisplayManager(show_advanced_output=True, color_enabled=True)

# Sample usage function to demonstrate the display utilities
def demo_display_utilities():
    """Demo function to showcase the display utilities."""
    # Header
    display.print_header("RAG Document Processor", "Advanced Document Ingestion Demo")
    
    # Section
    display.print_section("Document Loading", "Loading documents from Google Drive")
    
    # Step
    display.print_step(1, 4, "Authenticating with Google Drive", "Setting up credentials and access")
    
    # Info messages
    display.print_info("Using service account authentication")
    display.print_success("Successfully authenticated with Google Drive")
    
    # File info
    display.print_file_info(
        "Important Document.pdf", 
        "application/pdf", 
        "1Ab3CdEfGhIjKlMnOpQrStUvWxYz", 
        2048576
    )
    
    # Progress with example data
    with display.create_progress_bar(10, "Processing documents") as progress:
        task = progress.add_task("Processing", total=10)
        for i in range(10):
            time.sleep(0.2)
            progress.update(task, advance=1)
            
    # Display document stats
    display.print_document_stats(
        docs_count=5,
        chunks_count=23,
        metadata_fields=["file_name", "source", "created_time", "mime_type", 
                       "page_number", "chunk", "embedding_model"]
    )
    
    # Display embedding info
    display.print_embedding_info(
        model="text-embedding-ada-002",
        vector_dimension=1536,
        processing_time=3.45,
        batch_size=20
    )
    
    # Example metadata
    example_metadata = {
        "source": "google-drive://1Ab3CdEfGhIjKlMnOpQrStUvWxYz",
        "file_name": "Important Document.pdf",
        "mime_type": "application/pdf",
        "created_time": "2023-05-15T10:23:45Z",
        "modified_time": "2023-10-01T15:30:22Z",
        "page_number": 3,
        "chunk": 2,
        "parent_id": "doc-1234",
        "embedding_model": "text-embedding-ada-002",
        "auth": {
            "user": "john.doe@example.com",
            "permissions": ["read", "write"]
        },
        "document_stats": {
            "total_pages": 15,
            "word_count": 3245,
            "language": "en"
        }
    }
    
    # Display metadata example
    display.print_metadata_example(example_metadata)
    
    # Display chunk example
    display.print_chunk_example(
        "This document outlines the procedures for handling sensitive information "
        "according to the company's data protection policy. All employees must adhere "
        "to these guidelines when processing customer data.",
        example_metadata
    )
    
    # Display vector storage info
    display.print_vector_storage_info(
        store_type="Supabase pgvector",
        table_name="documents",
        total_stored=23,
        failed=0,
        index_type="HNSW"
    )
    
    # Display performance metrics
    display.print_performance_metrics({
        "Total Processing Time": 12.34,
        "Documents per Second": 0.41,
        "Chunks per Second": 1.87,
        "Memory Usage (MB)": 156,
        "API Calls": 8
    })
    
    # Display advanced feature info
    display.print_advanced_rag_feature(
        feature_name="Hierarchical Metadata Extraction",
        description="Extraction and preservation of document metadata throughout the RAG pipeline",
        standard_approach="Basic extraction of filename and creation date only",
        our_approach="Rich hierarchical metadata extraction including document structure, authorship, "
                    "permissions, versioning, and context preservation across chunks",
        benefits=[
            "Enables advanced filtering and faceted search",
            "Preserves document context for better retrieval",
            "Supports detailed provenance tracking",
            "Enables security-aware search results"
        ]
    )
    
    # Display metadata tree
    tree = display.create_metadata_tree(example_metadata)
    if tree:
        display.console.print(tree)
        
    # Display comparison table
    comparisons = [
        {
            "Feature": "Document Sources",
            "Our Approach": "Multiple flexible loaders",
            "Basic Approach": "Limited file types"
        },
        {
            "Feature": "Metadata Extraction",
            "Our Approach": "Rich, hierarchical with source tracking",
            "Basic Approach": "Basic metadata or none"
        },
        {
            "Feature": "Chunking Strategy",
            "Our Approach": "Intelligent, content-aware with overlap",
            "Basic Approach": "Simple fixed-size chunks"
        },
        {
            "Feature": "Vector Storage",
            "Our Approach": "Multiple options (Supabase pgvector, ChromaDB)",
            "Basic Approach": "Limited options"
        }
    ]
    
    display.display_comparison_table(comparisons, "RAG Implementation Comparison")
    
    # Interactive prompt example
    choice = display.interactive_prompt(
        "Select a processing method",
        choices=["basic", "advanced", "expert"],
        default="advanced"
    )
    display.print_info(f"Selected: {choice}")
    
    # Confirmation prompt
    confirmed = display.confirm_prompt("Would you like to process all documents?", default=True)
    display.print_info(f"Process all: {'Yes' if confirmed else 'No'}")

if __name__ == "__main__":
    # Run the demo if script is executed directly
    demo_display_utilities()