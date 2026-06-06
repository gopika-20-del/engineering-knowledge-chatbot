"""Configuration settings for the Engineering Chatbot"""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = DATA_DIR / "storage"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Create directories if they don't exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# Supported departments
DEPARTMENTS = [
    "CSE",
    "IT",
    "AI&DS",
    "CSBS",
    "ECE",
    "EEE",
    "Mechanical",
    "Civil"
]

# Semesters
SEMESTERS = list(range(1, 9))  # 1 to 8

# File upload settings
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".pptx"}

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # HuggingFace model

# ChromaDB settings
CHROMA_DB_PATH = str(CHROMA_DB_DIR)

# API settings
API_HOST = "127.0.0.1"
API_PORT = 8000

# Search settings
SEARCH_RESULTS_LIMIT = 5
SEARCH_TIMEOUT = 2  # seconds
