# Supabase Vector Storage Setup Guide

This guide provides detailed instructions for setting up Supabase as your vector database for the n8n RAG Example project.

## Overview

Supabase provides a scalable, cloud-hosted PostgreSQL database with pgvector extension, making it perfect for production RAG applications. The setup involves:

1. Creating a Supabase project
2. Enabling the pgvector extension
3. Creating tables for document storage
4. Setting up similarity search functions

## Getting Started

### 1. Create a Supabase Project

1. Go to [Supabase.com](https://supabase.com/) and sign up/login
2. Create a new project and set a secure database password
3. Note your project URL and API key (found under Project Settings > API)
4. Add these credentials to your `.env` file:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_API_KEY=your-supabase-api-key
   ```

### 2. Setting Up pgvector

#### Automated Setup (Recommended)

The easiest way to set up your vector database is to use our provided SQL script:

1. Go to the SQL Editor in your Supabase dashboard
2. Upload the provided `setup_vector_store.sql` file or copy-paste its contents
3. Run the script to create all necessary tables and functions

Alternatively, you can run our Python setup utility:

```bash
# Run the included setup script
python -c "import setup_vector_store; setup_vector_store.setup()"
```

#### Manual Setup

If you prefer to set up your vector database manually, follow these steps:

1. Enable the pgvector extension in the SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. Create the basic vector tables:
   ```sql
   -- Main documents table
   CREATE TABLE langchain_docs (
     id TEXT PRIMARY KEY,
     content TEXT,
     metadata JSONB,
     embedding VECTOR(1536)
   );

   -- Example table for testing
   CREATE TABLE langchain_example (
     id TEXT PRIMARY KEY,
     content TEXT,
     metadata JSONB,
     embedding VECTOR(1536)
   );
   ```

3. Create vector similarity search indexes:
   ```sql
   -- IVF index (good balance of speed and accuracy)
   CREATE INDEX ON langchain_docs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
   
   -- HNSW index (faster for larger datasets)
   CREATE INDEX IF NOT EXISTS hnsw_index ON langchain_docs USING hnsw (embedding vector_cosine_ops);
   ```

## Table Structure

The Supabase setup creates the following tables:

| Table Name | Purpose |
|------------|---------|
| `langchain_docs` | Primary storage for your document embeddings |
| `langchain_example` | For testing and example purposes |

Each table has the following structure:

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Unique identifier for each document chunk |
| `content` | TEXT | The text content of the document chunk |
| `metadata` | JSONB | Metadata about the document (source, filename, etc.) |
| `embedding` | VECTOR(1536) | The OpenAI embedding vector (1536 dimensions) |

## Understanding Vector Indexes

The setup creates two types of indexes for efficient similarity search:

### 1. IVFFlat Index

```sql
CREATE INDEX ON langchain_docs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

- **Purpose**: General-purpose index with good balance of search speed and accuracy
- **How it works**: Partitions vectors into lists for faster search
- **Best for**: Medium-sized collections (thousands to tens of thousands of documents)

### 2. HNSW Index

```sql
CREATE INDEX IF NOT EXISTS hnsw_index ON langchain_docs USING hnsw (embedding vector_cosine_ops);
```

- **Purpose**: High-performance approximate nearest neighbor search
- **How it works**: Creates a hierarchical graph structure for efficient navigation
- **Best for**: Large collections and performance-critical applications

## Using with the RAG System

Once your Supabase vector database is set up, the n8n RAG Example will automatically use it for document storage and retrieval:

```python
from rag.auth import GoogleDriveAuth
from rag.ingestion import LangChainIngestion

# Authenticate with Google Drive
auth = GoogleDriveAuth()
drive = auth.authenticate()

# Process documents from Google Drive
ingestion = LangChainIngestion(drive_client=drive)

# Documents are automatically stored in Supabase
documents = ingestion.process_folder("your_folder_id")
```

## Performance Optimization

For production workloads with large document collections, consider these optimizations:

1. **Increase lists parameter** for IVFFlat index with larger datasets:
   ```sql
   CREATE INDEX ON langchain_docs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);
   ```

2. **Tune HNSW parameters** for better performance:
   ```sql
   CREATE INDEX hnsw_index ON langchain_docs 
   USING hnsw (embedding vector_cosine_ops) 
   WITH (m = 16, ef_construction = 128);
   ```

3. **Create a custom function** for filtered searches:
   ```sql
   CREATE OR REPLACE FUNCTION match_documents_filtered (
     query_embedding VECTOR(1536),
     filter_condition TEXT,
     match_count INT DEFAULT 5
   ) RETURNS TABLE (
     id TEXT,
     content TEXT,
     metadata JSONB,
     similarity FLOAT
   ) LANGUAGE plpgsql AS $$
   BEGIN
     RETURN QUERY EXECUTE 
     format('SELECT id, content, metadata, 1 - (embedding <=> %L::vector) AS similarity
             FROM langchain_docs
             WHERE %s
             ORDER BY similarity DESC
             LIMIT %s',
             query_embedding, filter_condition, match_count);
   END;
   $$;
   ```

## Troubleshooting

### Common Issues and Solutions

- **"Extension 'vector' does not exist"**: Ensure you've created the extension with `CREATE EXTENSION IF NOT EXISTS vector;`

- **"Relation does not exist"**: Tables weren't created properly. Check for errors in the SQL script execution.

- **Slow query performance**: Make sure you've created the proper indexes for your workload. For large collections, use the HNSW index.

- **Connection errors**: Verify your Supabase URL and API key in the `.env` file. Check that your IP is not restricted in Supabase settings.

- **Permission errors**: Ensure your service key has the necessary permissions. For testing, you can use the `anon` key, but for production, create a custom API key with appropriate permissions.

### Getting Additional Help

If you're experiencing issues with Supabase:

1. Check the [Supabase documentation](https://supabase.com/docs) for general guidance
2. Review the [pgvector documentation](https://github.com/pgvector/pgvector) for vector-specific issues
3. See our [Troubleshooting Guide](troubleshooting.md) for more project-specific help 