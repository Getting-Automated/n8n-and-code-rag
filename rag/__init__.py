#!/usr/bin/env python3
"""
N8N RAG Example Package

This package provides tools and utilities for implementing RAG patterns using LangChain
and Supabase with documents from Google Drive.
"""

__version__ = "0.1.0"

from .auth import GoogleDriveAuth
from .ingestion import LangChainIngestion
from .query import query_langchain
from .store import SupabaseStore

# For backwards compatibility
import sys
import os

# Add compat imports for old structure users
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))