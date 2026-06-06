"""Initialize the chatbot system with sample data"""

import sys
from pathlib import Path
import json

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from document_processor import doc_processor
from database import db
from config import STORAGE_DIR, DEPARTMENTS

def create_sample_documents():
    """Create sample documents for testing"""
    
    print("🚀 Initializing Engineering Chatbot System...\n")
    
    # Sample document data
    sample_docs = [
        {
            "content": """
            DATABASE MANAGEMENT SYSTEMS (DBMS) - UNIT 2: DATA MODELS
            
            1. Introduction to Data Models
            - Hierarchical Data Model
            - Network Data Model
            - Relational Data Model
            
            2. Entity-Relationship Model
            - Entity sets and relationship sets
            - Attributes and keys
            - Constraints on relationships
            
            3. Relational Model
            - Structure of relational databases
            - Database schema
            - Keys and integrity constraints
            """,
            "metadata": {
                "department": "CSE",
                "semester": 3,
                "subject": "Database Management Systems",
                "title": "DBMS Unit 2 Notes - Data Models",
                "keywords": "database, data model, entity, relationship",
                "file_type": ".pdf"
            }
        },
        {
            "content": """
            PYTHON PROGRAMMING - LAB MANUAL
            
            Lab 1: Introduction to Python
            Lab 2: Data Types and Variables
            Lab 3: Control Flow Statements
            Lab 4: Functions and Modules
            Lab 5: File Handling
            Lab 6: Object-Oriented Programming
            
            Experiments include:
            - Writing simple programs
            - Using built-in functions
            - Creating classes and objects
            - Working with files
            """,
            "metadata": {
                "department": "CSE",
                "semester": 2,
                "subject": "Python Programming",
                "title": "Python Lab Manual",
                "keywords": "python, programming, lab, experiments",
                "file_type": ".pdf",
                "assignments": [
                    "Assignment 1: Write a Python program to calculate factorial",
                    "Assignment 2: Create a student management system using classes",
                    "Assignment 3: File I/O operations - Read and process CSV files",
                    "Assignment 4: List comprehensions and lambda functions",
                    "Assignment 5: Build a simple database application",
                    "Assignment 6: Exception handling in Python",
                    "Assignment 7: Working with dictionaries and sets",
                    "Assignment 8: String manipulation and regular expressions"
                ]
            }
        },
        {
            "content": """
            PREVIOUS YEAR QUESTION PAPER - OPERATING SYSTEMS
            
            Time: 3 Hours | Max Marks: 100
            
            Part A (2 marks each)
            1. Define an operating system
            2. What are the functions of an operating system?
            3. Explain process scheduling
            4. What is deadlock?
            5. Define virtual memory
            
            Part B (5 marks each)
            1. Explain the different states of a process
            2. Compare preemptive and non-preemptive scheduling
            3. Discuss synchronization mechanisms
            
            Part C (10 marks each)
            1. Explain page replacement algorithms
            2. Discuss file management in operating systems
            """,
            "metadata": {
                "department": "CSE",
                "semester": 5,
                "subject": "Operating Systems",
                "title": "Operating Systems - Previous Year Question Paper",
                "keywords": "question paper, exam, operating systems, processes",
                "file_type": ".pdf"
            }
        },
        {
            "content": """
            ARTIFICIAL INTELLIGENCE & DATA SCIENCE - PROJECT IDEAS
            
            1. Sentiment Analysis on Social Media
            - Collect tweets and analyze sentiment
            - Use NLP techniques
            - Deploy using Flask/Streamlit
            
            2. Customer Churn Prediction
            - Dataset: Customer transaction data
            - Models: Logistic Regression, Random Forest, SVM
            - Evaluation: Accuracy, Precision, Recall
            
            3. Recommendation System
            - Collaborative filtering
            - Content-based filtering
            - Hybrid approach
            
            4. Time Series Forecasting
            - Stock price prediction
            - Weather forecasting
            - Sales forecasting
            """,
            "metadata": {
                "department": "AI&DS",
                "semester": 6,
                "subject": "Machine Learning Project",
                "title": "AI&DS Project Ideas and Guidelines",
                "keywords": "project, machine learning, ai, data science, ideas",
                "file_type": ".pdf"
            }
        }
    ]
    
    print("Creating sample documents...\n")
    
    for i, doc_data in enumerate(sample_docs, 1):
        doc_id = f"sample_doc_{i}"
        
        # Create file content
        file_name = f"{doc_id}_{doc_data['metadata']['title']}.txt"
        file_path = STORAGE_DIR / file_name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(doc_data['content'])
        
        # Add to metadata
        metadata = doc_data['metadata'].copy()
        # Convert assignments list to JSON string for ChromaDB
        if 'assignments' in metadata and isinstance(metadata['assignments'], list):
            metadata['assignments'] = json.dumps(metadata['assignments'])
        metadata.update({
            'id': doc_id,
            'original_name': file_name,
            'stored_name': file_name,
            'file_type': '.txt',
            'file_size_kb': len(doc_data['content']) / 1024,
            'content_preview': doc_data['content'][:500]
        })
        
        doc_processor.metadata[doc_id] = metadata
        
        # Add to vector database
        db.add_document(doc_id, doc_data['content'], metadata)
        
        print(f"✅ Document {i}: {metadata['title']}")
        print(f"   Department: {metadata['department']}, Semester: {metadata['semester']}\n")
    
    # Save metadata
    doc_processor._save_metadata()
    
    print("\n" + "="*60)
    print("✨ Initialization Complete!")
    print("="*60)
    print(f"\n📊 System Status:")
    print(f"   - Total documents: {len(doc_processor.metadata)}")
    print(f"   - Storage directory: {STORAGE_DIR}")
    print(f"   - Vector database initialized: ✅")
    print(f"\n🚀 Next Steps:")
    print(f"   1. Start backend: python backend/main.py")
    print(f"   2. Start frontend: streamlit run frontend/app.py")
    print(f"   3. Access chatbot at: http://localhost:8501")
    print(f"\n📝 Admin credentials:")
    print(f"   - Password: admin123")

if __name__ == "__main__":
    create_sample_documents()
