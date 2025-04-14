# Quick Start Guide

This guide will help you get started with the n8n RAG Example project quickly.

## Prerequisites

- Python 3.9+
- OpenAI API key
- Supabase account (for vector storage)
- Google Drive access with service account (recommended) or OAuth2

## Five-Minute Setup

1. **Clone the repository:**

```bash
git clone https://github.com/Getting-Automated/n8n-rag-example.git
cd n8n-rag-example
```

2. **Run the setup script:**

For Mac/Linux:
```bash
chmod +x setup.sh
./setup.sh
```

For Windows:
```bash
setup.bat
```

3. **Configure your environment:**

Copy the example file and fill in your credentials:
```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:
```
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_API_KEY=your_supabase_api_key_here

# Google Drive Configuration - Service Account (recommended)
GOOGLE_SERVICE_ACCOUNT_PATH=config/service-account.json

# Alternatively, for OAuth2 (personal account access)
# GOOGLE_CLIENT_ID=your_client_id_here
# GOOGLE_CLIENT_SECRET=your_client_secret_here
# GOOGLE_REFRESH_TOKEN=your_refresh_token_here
```

4. **Set up Google Drive access:**

#### Service Account Method (Recommended)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Library" and enable "Google Drive API"
4. Go to "APIs & Services" > "Credentials"
5. Click "Create Credentials" > "Service Account"
6. Fill in service account details and click "Create"
7. On the service account page, go to "Keys" tab
8. Add a new JSON key and download it
9. Save the JSON file to `config/service-account.json`
10. Share your Google Drive folders with the service account email

5. **Set up Supabase vector database:**

1. Create a Supabase account at [supabase.com](https://supabase.com/) if you don't have one
2. Create a new project in the Supabase dashboard
3. Copy your project URL and API key to the `.env` file
4. Run our setup script to create the necessary tables and indexes:

```bash
python -c "import setup_vector_store; setup_vector_store.setup()"
```

## Run Your First RAG Example

```bash
# Activate your virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Run the examples script
python examples/langchain_examples.py
```

You'll see a menu of options:
1. Basic ingestion - Process all folders with standard settings
2. Advanced ingestion - Process with optimized parameters and enhanced features
3. Specific files - Target individual documents with precision processing
4. Enhanced media - Process images and PDFs with OCR, table extraction, and image analysis

## Basic Usage

### 1. Ingest documents from Google Drive

```python
from rag.auth import GoogleDriveAuth
from rag.ingestion import LangChainIngestion

# Authenticate with Google Drive
auth = GoogleDriveAuth()
drive = auth.authenticate()

# Create an ingestion instance
ingestion = LangChainIngestion(drive_client=drive)

# Process documents from a Google Drive folder
folder_id = "your_google_drive_folder_id"
documents = ingestion.process_folder(folder_id)
```

### 2. Query your documents

```python
from rag.query import query_langchain

# Perform a similarity search
results = query_langchain(
    query="What is RAG?",
    table_name="langchain_docs",
    top_k=5
)

# Display results
for doc in results:
    print(f"Content: {doc.page_content}")
    print(f"Metadata: {doc.metadata}")
    print("---")
```

## Next Steps

After completing this quickstart guide, you can:

- Try advanced ingestion with custom parameters (see [Advanced Usage](advanced_usage.md))
- Explore the different processing options for various document types
- Set up custom embedding models and vector storage configurations
- Implement your own RAG application using our query engine

For detailed information on system architecture, refer to the [Architecture Overview](architecture.md).

## Directory Structure

The repository is organized as follows:

```
.
├── docs/                   # Documentation
│   ├── architecture.md     # System architecture documentation
│   ├── advanced_usage.md   # Advanced usage patterns
│   ├── quickstart.md       # Quickstart guide (this file)
│   ├── supabase_setup.md   # Supabase setup instructions
│   └── troubleshooting.md  # Common issues and solutions
├── examples/               # Example code
│   ├── langchain_examples.py
│   ├── llamaindex_examples.py
│   └── query_examples.py
├── setup/                  # Setup scripts
│   ├── database/           # Database setup scripts
│   │   ├── setup_supabase.py
│   │   ├── setup_supabase.sh
│   │   └── setup_supabase.bat
│   └── environment/        # Environment setup scripts
│       ├── setup.sh
│       └── setup.bat
├── src/                    # Source code
│   ├── auth/               # Authentication modules
│   ├── ingestion/          # Ingestion modules
│   ├── query/              # Query modules
│   └── utils/              # Utility modules
```

## Common Issues

- **Authentication errors**: Ensure your Google credentials are correct and have the necessary permissions
- **Import errors**: Make sure you've activated the virtual environment
- **Missing packages**: Run pip install -r requirements.txt 