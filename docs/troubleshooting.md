# Troubleshooting Guide

This guide addresses common issues you might encounter when using the n8n RAG Example project.

## Installation Issues

### Python Environment Problems

**Issue**: `ModuleNotFoundError: No module named '<package_name>'`  
**Solution**: Ensure your virtual environment is activated and reinstall dependencies:
```bash
# Linux/macOS
source venv/bin/activate
pip install -r requirements.txt

# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

**Issue**: Python version compatibility errors  
**Solution**: Ensure you're using Python 3.9 or higher:
```bash
python --version
```

### Virtual Environment Problems

**Issue**: Virtual environment not working correctly  
**Solution**: Try recreating it:
```bash
# Linux/macOS
rm -rf venv
./setup.sh

# Windows
rmdir /s /q venv
setup.bat
```

### Missing Dependencies for Advanced Features

**Issue**: Errors related to OCR, table extraction, or computer vision features  
**Solution**: Install the required external dependencies:

For OCR (Tesseract):
```bash
# Linux
sudo apt-get install tesseract-ocr
# macOS
brew install tesseract
# Windows: Download and install from https://github.com/UB-Mannheim/tesseract/wiki
```

For PDF table extraction:
```bash
# Linux
sudo apt-get install default-jre ghostscript
# macOS
brew install openjdk ghostscript
# Windows: Install Java Runtime Environment and Ghostscript
```

## Authentication Issues

### Google Drive Authentication Problems

**Issue**: `google.auth.exceptions.DefaultCredentialsError`  
**Solution**: Ensure your service account credentials are correctly set up:
1. Verify the `service-account.json` file exists in the `config/` directory
2. Check that the Google Drive API is enabled in your Google Cloud project
3. Ensure your service account has the necessary permissions on the target folders

**Issue**: Permission denied errors when accessing Google Drive  
**Solution**: 
1. Ensure the service account has been granted access to the target folders/files
2. Share the folders explicitly with the service account email address
3. For shared drives, ensure the service account has been added to the shared drive

**Issue**: SSL connection errors with Google Drive API  
**Solution**:
1. These are handled gracefully by the system and shouldn't cause failures
2. If persistent, try updating your SSL certificates or temporarily disable SSL verification in your test environment

## Supabase Issues

**Issue**: Connection errors to Supabase  
**Solution**: 
1. Verify your Supabase URL and API key in the `.env` file
2. Check that your IP address is not restricted in Supabase dashboard settings
3. Test your connection with a simple query:
```python
from supabase import create_client
import os

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_API_KEY")
supabase = create_client(url, key)
response = supabase.table('langchain_docs').select('id').limit(1).execute()
print(response)
```

**Issue**: `relation "langchain_docs" does not exist`  
**Solution**: 
1. Run the Supabase setup script:
```bash
python -c "import setup_vector_store; setup_vector_store.setup()"
```
2. Or manually create the tables as described in [Supabase Setup Guide](supabase_setup.md)

**Issue**: pgvector extension errors  
**Solution**:
1. Ensure the pgvector extension is enabled:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
2. Verify your Supabase plan supports extensions

## Ingestion Issues

**Issue**: Memory errors when processing large files  
**Solution**: 
1. Decrease the chunk size in your code:
```python
ingestion = LangChainIngestion(chunk_size=300, chunk_overlap=30)
```
2. Process fewer files at a time
3. Increase your system's available memory

**Issue**: Slow ingestion speed  
**Solution**:
1. Enable parallel processing with a reasonable worker count:
```python
ingestion = LangChainIngestion(workers=4, use_parallel=True)
```
2. Use a simpler embedding model if available
3. Process only files that have changed since last ingestion

**Issue**: Timeout errors with large collections  
**Solution**:
1. Increase the timeout setting:
```python
ingestion = LangChainIngestion(timeout=180)  # 3 minutes timeout
```
2. Process in smaller batches

**Issue**: SSL connection errors during ingestion  
**Solution**: These are automatically handled by the robust SSL error handling in the system

## Query Issues

**Issue**: No results returned from queries  
**Solution**:
1. Verify documents were successfully ingested (check the Supabase tables)
2. Try simpler queries
3. Increase the number of results requested:
```python
results = query_langchain(query="your query", top_k=10)
```
4. Ensure your embedding model matches the one used during ingestion

**Issue**: Irrelevant results  
**Solution**:
1. Reformulate your query to be more specific
2. Try using metadata filters to narrow results:
```python
results = query_langchain(
    query="your query",
    filter_metadata={"source_type": "pdf"}
)
```
3. Adjust the similarity threshold if applicable

**Issue**: Slow query performance  
**Solution**:
1. Ensure you've created appropriate indexes in Supabase (see [Supabase Setup Guide](supabase_setup.md))
2. Use smaller result sets (lower `top_k` values)
3. Apply metadata filters to reduce the search space

## OpenAI API Issues

**Issue**: OpenAI API authentication errors  
**Solution**:
1. Ensure your OpenAI API key is correctly set in the `.env` file
2. Verify your key has not expired and has sufficient quota
3. Check network connectivity to the OpenAI API

**Issue**: `RateLimitError` from OpenAI  
**Solution**:
1. Implement exponential backoff:
```python
import time
import random
for attempt in range(5):
    try:
        # Your OpenAI API call
        break
    except RateLimitError:
        time.sleep((2 ** attempt) + random.random())
```
2. Reduce parallel requests
3. Upgrade your OpenAI API plan

## Specific Feature Issues

### OCR Issues

**Issue**: OCR not extracting text correctly  
**Solution**:
1. Ensure Tesseract is properly installed
2. Check image quality and resolution
3. Try preprocessing the image (the system does this automatically)
4. For languages other than English, install language packs for Tesseract

### PDF Table Extraction Issues

**Issue**: Tables not being extracted correctly  
**Solution**:
1. Ensure Java Runtime Environment and Ghostscript are properly installed
2. Try different extraction methods (the system attempts multiple methods automatically)
3. For complex tables, consider pre-processing the PDFs

## Getting Additional Help

If you're still experiencing issues:

1. Check for similar issues in the [GitHub repository](https://github.com/Getting-Automated/n8n-rag-example/issues)
2. Enable debug logging for more detailed information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
3. When reporting issues, include:
   - Complete error messages and stack traces
   - Steps to reproduce the problem
   - Your environment details (OS, Python version, etc.)
   - Specific file types and sizes causing issues 