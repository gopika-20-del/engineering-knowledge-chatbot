# Engineering Chatbot - Installation & Setup Guide

## 📋 Overview

This is a comprehensive AI-powered chatbot system for engineering students, supporting multiple departments and semesters. It provides intelligent search, document management, and easy access to study materials.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize System

```bash
python initialize.py
```

This will:
- Create necessary directories
- Initialize ChromaDB vector database
- Load sample documents
- Setup metadata storage

### 3. Start Backend API

```bash
python backend/main.py
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 4. Start Frontend (in another terminal)

```bash
streamlit run frontend/app.py
```

The chatbot UI will open at: `http://localhost:8501`

## 📁 Project Structure

```
knowledge chatbot/
├── backend/
│   ├── config.py              # Configuration settings
│   ├── database.py            # ChromaDB vector database
│   ├── document_processor.py  # Document upload & metadata
│   ├── chatbot_engine.py      # Search & retrieval engine
│   └── main.py                # FastAPI backend
├── frontend/
│   └── app.py                 # Streamlit web UI
├── data/
│   ├── storage/               # Uploaded documents
│   └── chroma_db/             # Vector database
├── initialize.py              # System initialization
└── requirements.txt           # Python dependencies
```

## 🔧 Configuration

Edit `backend/config.py` to customize:

- **Supported Departments**: CSE, IT, AI&DS, CSBS, ECE, EEE, Mechanical, Civil
- **Semesters**: 1-8
- **Max File Size**: 50 MB
- **Embedding Model**: all-MiniLM-L6-v2 (HuggingFace)
- **Database Path**: data/chroma_db/

## 👨‍💼 Admin Features

Login to admin panel with password: **`admin123`**

### Admin Capabilities:
- ✅ Upload new documents
- ✅ Update document metadata
- ✅ Delete documents
- ✅ View all documents in system

## 🔍 Search Features

### 1. **Semantic Search**
   - Uses AI embeddings to find contextually relevant documents
   - Best for: Natural language queries, conceptual questions
   - Example: "Explain TCP layers" → Network notes PDF

### 2. **Keyword Search**
   - Matches exact keywords in titles, subjects, and tags
   - Best for: Specific topics, precise queries
   - Example: "DBMS unit 2 notes"

### 3. **Hybrid Search** (Recommended)
   - Combines semantic and keyword search
   - Provides most accurate results
   - Ranked by relevance score

### Filters
- Department selection
- Semester filtering
- Subject-specific materials

## 📚 Supported Document Types

- PDF (.pdf)
- Word Documents (.docx, .doc)
- PowerPoint (.pptx)
- Text Files (.txt)

## 🎯 Key Features

### For Students
✅ Fast semantic search across all materials  
✅ Keyword-based filtering  
✅ Browse materials by department/semester  
✅ Download study materials directly  
✅ Search results ranked by relevance  
✅ Subject-wise material organization  

### For Admin
✅ Upload new documents with metadata  
✅ Automatic content extraction  
✅ Metadata extraction from PDFs & docs  
✅ Update or delete documents  
✅ View document statistics  

## 🔌 API Endpoints

### Search
```
GET /search?query=<query>&search_type=hybrid&department=<dept>&semester=<sem>
```

### Documents
```
GET /documents                      # List all documents
GET /documents/{doc_id}            # Get document info
GET /download/{doc_id}             # Download document
POST /upload                       # Upload document (admin)
DELETE /documents/{doc_id}         # Delete document (admin)
PUT /documents/{doc_id}            # Update metadata (admin)
```

### Subject Materials
```
GET /subject-materials?department=<dept>&semester=<sem>&subject=<subject>
```

### Configuration
```
GET /config                        # Get system configuration
GET /health                        # Health check
```

## 📊 Performance Targets

- Search results: < 2 seconds
- Metadata extraction: < 10 seconds/file
- System availability: 99% uptime
- Support: 1000+ files, 5000+ queries/day

## 🚨 Troubleshooting

### Issue: Port already in use
```bash
# Change port in backend/config.py
API_PORT = 8001
```

### Issue: ChromaDB not initializing
```bash
# Clear and reinitialize
rm -rf data/chroma_db
python initialize.py
```

### Issue: File upload fails
- Check file size (max 50MB)
- Verify file format is supported
- Ensure write permissions on data/storage/

### Issue: Search returns no results
- Try different keywords
- Use semantic search instead of keyword
- Check if documents are uploaded via Admin panel

## 📈 Future Enhancements

- [ ] User authentication system
- [ ] Student behavior analytics
- [ ] Advanced NLP question answering
- [ ] Multi-language support
- [ ] Offline mode
- [ ] Mobile app
- [ ] Video content indexing
- [ ] Plagiarism detection

## 📝 License

Internal use only - Engineering Education Platform

## 👨‍💻 Support

For issues or features, contact: gopika.arasi@example.com

---

**Happy Learning! 🎓**
