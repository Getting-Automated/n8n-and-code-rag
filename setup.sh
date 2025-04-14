#!/bin/bash
# Simple setup script for n8n-rag-example

echo "Setting up n8n RAG example environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Please ensure Python 3.9+ is installed."
        exit 1
    fi
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows using Git Bash or similar
    source venv/Scripts/activate
else
    # Linux/macOS
    source venv/bin/activate
fi

# Install requirements
echo "Installing dependencies..."
pip install -U pip setuptools wheel
pip install -r requirements.txt

# Create config directory if it doesn't exist
if [ ! -d "config" ]; then
    mkdir -p config
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your API keys and credentials."
fi

echo "Setup complete! To run the example:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the example: python examples/langchain_examples_new.py" 