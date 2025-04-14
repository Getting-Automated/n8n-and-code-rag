# Advanced Usage Guide

This guide covers advanced patterns and techniques for using the n8n RAG Example to its full potential.

## Advanced Ingestion Patterns

### Custom Ingestion Parameters

The `LangChainIngestion` class accepts various parameters to customize the ingestion process:

```python
from rag.auth import GoogleDriveAuth
from rag.ingestion import LangChainIngestion

# Authenticate with Google Drive
auth = GoogleDriveAuth()
drive = auth.authenticate()

# Create ingestion with custom parameters
ingestion = LangChainIngestion(
    drive_client=drive,
    chunk_size=500,                 # Size of text chunks
    chunk_overlap=50,               # Overlap between chunks
    table_name="custom_collection", # Supabase table name
    workers=4,                      # Number of parallel workers
    use_parallel=True,              # Enable parallel processing
    timeout=120,                    # Timeout for processing each file (seconds)
    skip_unchanged=True             # Skip unchanged documents
)

# Process documents
docs = ingestion.process_folder("your_folder_id")
```

### Selective Document Processing

Process only specific file types or matching certain criteria:

```python
# Process only PDF and Word documents
docs = ingestion.process_folder(
    "your_folder_id",
    mime_types=["application/pdf", "application/vnd.google-apps.document"]
)

# Process files with specific names
docs = ingestion.process_folder(
    "your_folder_id",
    query="name contains 'report'"
)

# Process only files modified after a certain date
docs = ingestion.process_folder(
    "your_folder_id",
    query="modifiedTime > '2023-10-01T00:00:00'"
)
```

### Processing Individual Files

Process specific files directly:

```python
# Process a specific file by ID
doc = ingestion.process_file("your_file_id")

# Process multiple specific files
docs = ingestion.process_files(["file_id_1", "file_id_2", "file_id_3"])
```

### Metadata Filtering

Apply metadata filters during querying:

```python
from rag.query import query_langchain

# Query documents with metadata filtering
results = query_langchain(
    query="renewable energy",
    table_name="langchain_docs",
    filter_metadata={
        "source_type": "pdf", 
        "department": "research"
    }
)
```

## Advanced Media Processing

### OCR and Image Processing

The system includes advanced image processing for extracting text from images:

```python
from rag.ingestion import LangChainIngestion

# Create ingestion with enhanced image processing
ingestion = LangChainIngestion(
    enable_ocr=True,                # Enable OCR for images
    ocr_min_confidence=70,          # Minimum confidence score (0-100)
    preprocess_images=True,         # Apply preprocessing to images
    extract_image_features=True     # Extract visual features
)

# Process documents with images
docs = ingestion.process_folder("your_folder_id")
```

### PDF Table Extraction

Extract and preserve table structures from PDFs:

```python
from rag.ingestion import LangChainIngestion

# Create ingestion with table extraction enabled
ingestion = LangChainIngestion(
    extract_tables=True,               # Enable table extraction
    table_extraction_engines=["all"],  # Use all available engines
    preserve_table_structure=True      # Keep table structure in output
)

# Process PDF documents
docs = ingestion.process_folder("your_folder_id")
```

## Document Versioning

The system tracks document versions to optimize processing and avoid redundant work:

```python
from rag.ingestion import LangChainIngestion

# Create ingestion with versioning options
ingestion = LangChainIngestion(
    skip_unchanged=True,              # Skip unchanged documents
    force_refresh=False,              # Don't force refresh if unchanged
    track_content_changes=True        # Track if content actually changed
)

# Process documents with versioning
docs = ingestion.process_folder("your_folder_id")

# Force refresh of all documents regardless of changes
docs_refreshed = ingestion.process_folder(
    "your_folder_id",
    force_refresh=True
)
```

## Parallel Processing

Speed up ingestion with parallel processing:

```python
from rag.ingestion import LangChainIngestion

# Set up parallel processing
ingestion = LangChainIngestion(
    use_parallel=True,        # Enable parallel processing
    workers=8,                # Number of worker processes
    batch_size=10,            # Number of documents per batch
    timeout=180               # Processing timeout per document (seconds)
)

# Process a large folder with parallel workers
docs = ingestion.process_folder("your_large_folder_id")
```

## Advanced Querying

### Similarity Search with Metadata Filtering

Combine vector similarity with metadata filtering:

```python
from rag.query import query_langchain

# Basic query with metadata filtering
results = query_langchain(
    query="climate change impact",
    table_name="langchain_docs",
    top_k=5,
    filter_metadata={"document_type": "research_paper"}
)

# More complex metadata filtering
results = query_langchain(
    query="renewable energy technology",
    table_name="langchain_docs", 
    top_k=10,
    filter_metadata={
        "year": "2023",
        "department": "research",
        "status": "published"
    }
)
```

### Custom Embedding Options

Use different embedding models or parameters:

```python
from rag.query import query_langchain
from langchain_openai import OpenAIEmbeddings

# Create custom embeddings
custom_embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    dimensions=1536
)

# Query with custom embeddings
results = query_langchain(
    query="future of renewable energy",
    table_name="langchain_docs",
    embedding_function=custom_embeddings
)
```

## Performance Optimization

### Optimizing Chunk Size

Finding the right chunk size is essential for good retrieval performance:

```python
from rag.ingestion import LangChainIngestion

# Smaller chunks for precise retrieval (better for Q&A)
ingestion_precise = LangChainIngestion(
    chunk_size=300,
    chunk_overlap=30
)

# Larger chunks for more context (better for summarization)
ingestion_context = LangChainIngestion(
    chunk_size=1000,
    chunk_overlap=100
)
```

### Batch Processing for Large Collections

Process large document collections in batches:

```python
from rag.auth import GoogleDriveAuth
from rag.ingestion import LangChainIngestion

# Authenticate with Google Drive
auth = GoogleDriveAuth()
drive = auth.authenticate()

# Create ingestion instance
ingestion = LangChainIngestion(drive_client=drive)

# Get all files in the folder
folder_id = "your_folder_id"
files = ingestion.list_files_in_folder(folder_id, recursive=True)

# Process in batches
batch_size = 50
for i in range(0, len(files), batch_size):
    batch = files[i:i+batch_size]
    print(f"Processing batch {i//batch_size + 1}/{(len(files) + batch_size - 1)//batch_size}")
    ingestion.process_files([file['id'] for file in batch])
```

## Robust Error Handling

The system includes built-in error handling for various scenarios:

```python
from rag.ingestion import LangChainIngestion

# Configure error handling
ingestion = LangChainIngestion(
    continue_on_error=True,        # Continue processing despite errors
    error_log_file="errors.log",   # Log errors to a file
    retry_count=3,                 # Number of retries for failed operations
    retry_delay=2                  # Delay between retries (seconds)
)

# Process folder with error handling
try:
    docs = ingestion.process_folder("your_folder_id")
except Exception as e:
    print(f"Ingestion failed with error: {e}")
    # Handle error gracefully
```

## Integration with Custom Applications

### Building a Custom RAG Solution

Integrate the n8n RAG Example into your own applications:

```python
from rag.auth import GoogleDriveAuth
from rag.ingestion import LangChainIngestion
from rag.query import query_langchain
from langchain_openai import ChatOpenAI

# 1. Set up authentication
auth = GoogleDriveAuth()
drive = auth.authenticate()

# 2. Create ingestion
ingestion = LangChainIngestion(drive_client=drive)

# 3. Process documents
docs = ingestion.process_folder("your_folder_id")

# 4. Set up query function
def answer_question(question):
    # Retrieve relevant documents
    relevant_docs = query_langchain(
        query=question,
        table_name="langchain_docs",
        top_k=5
    )
    
    # Format context from retrieved documents
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    
    # Create LLM
    llm = ChatOpenAI(model="gpt-4")
    
    # Generate response
    prompt = f"""
    Answer the following question based on the provided context:
    
    Context:
    {context}
    
    Question: {question}
    """
    
    response = llm.invoke(prompt)
    return response.content

# 5. Use in your application
answer = answer_question("What are the key benefits of renewable energy?")
print(answer)
```

### Web API Integration

Example of creating a simple FastAPI endpoint:

```python
from fastapi import FastAPI, Query
from pydantic import BaseModel
from rag.query import query_langchain

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_metadata: dict = None

class Document(BaseModel):
    content: str
    metadata: dict

class QueryResponse(BaseModel):
    documents: list[Document]

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    results = query_langchain(
        query=request.query,
        table_name="langchain_docs",
        top_k=request.top_k,
        filter_metadata=request.filter_metadata
    )
    
    return {
        "documents": [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in results
        ]
    }
```

## Best Practices

### Document Organization

- Organize your Google Drive folders logically by topic or department
- Use consistent naming conventions for files
- Consider creating separate vector stores for different document collections
- Process related documents together to maintain proper context

### Optimizing Retrieval Quality

- Use appropriate chunk sizes for your use case:
  - Smaller chunks (300-500 tokens) for precise Q&A
  - Larger chunks (1000+ tokens) for summarization and broader context
- Maintain reasonable chunk overlap (10-20% of chunk size)
- Experiment with different metadata filters to improve relevance
- Periodically refresh your document embeddings to keep them current

### Security Considerations

- Use service accounts with minimal necessary permissions
- Store all credentials securely in environment variables
- Implement proper authentication for any web APIs you create
- Consider implementing document-level access control based on metadata
- Regularly rotate API keys and credentials 