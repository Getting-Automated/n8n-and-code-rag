#!/bin/bash

# Install required Python dependencies if needed
pip install pyfiglet humanize rich tabulate colorama
pip install --upgrade langchain langchain-community langchain-openai langchain-google-community langchain-text-splitters

# Set the PYTHONPATH to include only the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=$SCRIPT_DIR

# Run the examples
cd $SCRIPT_DIR
python examples/langchain_examples_new.py
