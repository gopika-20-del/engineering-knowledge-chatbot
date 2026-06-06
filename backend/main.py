"""FastAPI backend for Engineering Chatbot"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional, List
import asyncio
import re
from collections import Counter
from backend.config import DEPARTMENTS, SEMESTERS, MAX_FILE_SIZE_MB
from backend.database import db
from backend.document_processor import doc_processor
from backend.chatbot_engine import chatbot_engine
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Engineering Chatbot API starting...")
    print(f"Storage directory: {doc_processor.storage_dir}")
    print(f"Documents in system: {len(doc_processor.metadata)}")
    yield
    # Shutdown
    print("Shutting down Engineering Chatbot API...")
    db.close()

app = FastAPI(
    title="Engineering Chatbot API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Health Check ====================
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Engineering Chatbot"}

# ==================== Document Upload ====================
@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    department: str = Form(...),
    semester: int = Form(...),
    subject: str = Form(...),
    title: str = Form(None),
    keywords: str = Form(""),
    admin_key: str = Form(...),
):
    """
    Upload a new document (Admin only)
    Requires: file, department, semester, subject, admin_key
    """
    # Admin authentication (simple check)
    if admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Validate department and semester
    if department not in DEPARTMENTS:
        raise HTTPException(status_code=400, detail=f"Invalid department. Choose from: {DEPARTMENTS}")
    if semester not in SEMESTERS:
        raise HTTPException(status_code=400, detail=f"Invalid semester. Choose from 1-8")
    
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"./temp_{file.filename}")
        contents = await file.read()
        
        # Check file size
        if len(contents) / (1024 * 1024) > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {MAX_FILE_SIZE_MB}MB"
            )
        
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Upload to system
        metadata = {
            'department': department,
            'semester': semester,
            'subject': subject,
            'title': title or file.filename,
            'keywords': keywords
        }
        
        success, doc_id, message = doc_processor.upload_document(temp_path, metadata)
        
        # Clean up temp file
        temp_path.unlink()
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Add to vector database
        doc = doc_processor.get_document(doc_id)
        content = doc.get('content_preview', '')
        db.add_document(doc_id, content, doc)
        
        return {
            "status": "success",
            "message": message,
            "doc_id": doc_id,
            "document": {
                "title": doc['title'],
                "department": doc['department'],
                "semester": doc['semester'],
                "subject": doc['subject']
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Search ====================
@app.get("/search")
async def search(
    query: str,
    search_type: str = "hybrid",
    department: Optional[str] = None,
    semester: Optional[int] = None
):
    """
    Search for documents
    search_type: 'semantic', 'keyword', or 'hybrid'
    """
    if not query or len(query.strip()) < 2:
        return {"status": "error", "message": "Query too short", "results": []}
    
    return chatbot_engine.combined_search(
        query=query,
        search_type=search_type,
        department=department,
        semester=semester
    )

# ==================== Get Subject Materials ====================
@app.get("/subject-materials")
async def get_subject_materials(
    department: str,
    semester: int,
    subject: str
):
    """Get all materials for a specific subject"""
    if department not in DEPARTMENTS:
        raise HTTPException(status_code=400, detail="Invalid department")
    if semester not in SEMESTERS:
        raise HTTPException(status_code=400, detail="Invalid semester")
    
    return chatbot_engine.get_subject_materials(department, semester, subject)

# ==================== Document Download ====================
@app.get("/download/{doc_id}")
async def download_document(doc_id: str):
    """Download a document"""
    doc = doc_processor.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = doc_processor.get_document_path(doc_id)
    
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=doc['original_name'],
        media_type="application/octet-stream"
    )

# ==================== Document Management ====================
@app.get("/documents")
async def list_documents(department: Optional[str] = None, semester: Optional[int] = None):
    """List all documents with optional filters"""
    filters = {}
    if department:
        filters['department'] = department
    if semester:
        filters['semester'] = str(semester)
    
    results = doc_processor.search_by_metadata(**filters) if filters else list(doc_processor.metadata.values())
    
    return {
        "status": "success",
        "count": len(results),
        "documents": [
            {
                "id": doc['id'],
                "title": doc.get('title'),
                "department": doc.get('department'),
                "semester": doc.get('semester'),
                "subject": doc.get('subject'),
                "file_type": doc.get('file_type'),
                "size_kb": doc.get('file_size_kb')
            }
            for doc in results
        ]
    }

@app.get("/documents/{doc_id}")
async def get_document_info(doc_id: str):
    """Get detailed information about a document"""
    doc = doc_processor.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "status": "success",
        "document": doc
    }

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, admin_key: str):
    """Delete a document (Admin only)"""
    if admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    success, message = doc_processor.delete_document(doc_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Remove from vector DB
    db.delete_document(doc_id)
    
    return {"status": "success", "message": message}

@app.put("/documents/{doc_id}")
async def update_document_metadata(
    doc_id: str,
    updates: dict,
    admin_key: str
):
    """Update document metadata (Admin only)"""
    if admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    success, message = doc_processor.update_metadata(doc_id, updates)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Update vector DB
    doc = doc_processor.get_document(doc_id)
    db.add_document(doc_id, doc.get('content_preview', ''), doc)
    
    return {"status": "success", "message": message}

# ==================== Project Topics ====================
@app.get("/project-topics")
async def get_project_topics(department: Optional[str] = None):
    """Get project topics for departments"""
    import json
    from pathlib import Path
    
    try:
        project_file = Path(__file__).resolve().parent.parent / "data" / "storage" / "PROJECT_TOPICS.json"
        
        if not project_file.exists():
            raise HTTPException(status_code=404, detail="Project topics file not found")
        
        with open(project_file, 'r', encoding='utf-8') as f:
            topics_data = json.load(f)
        
        if department:
            if department not in topics_data.get("project_topics", {}):
                raise HTTPException(status_code=400, detail=f"Department '{department}' not found")
            
            dept_topics = topics_data["project_topics"][department]
            return {
                "status": "success",
                "department": department,
                "department_name": dept_topics.get("department_name"),
                "total_topics": dept_topics.get("total_topics"),
                "topics": dept_topics.get("topics", [])
            }
        
        # Return all departments
        return {
            "status": "success",
            "total_departments": topics_data.get("total_departments"),
            "total_projects": topics_data.get("total_projects"),
            "departments": {
                dept_code: {
                    "name": data.get("department_name"),
                    "total_topics": data.get("total_topics")
                }
                for dept_code, data in topics_data.get("project_topics", {}).items()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project-topics/{department}/{topic_id}")
async def get_project_topic_details(department: str, topic_id: str):
    """Get details of a specific project topic"""
    import json
    from pathlib import Path
    
    try:
        project_file = Path(__file__).resolve().parent.parent / "data" / "storage" / "PROJECT_TOPICS.json"
        
        if not project_file.exists():
            raise HTTPException(status_code=404, detail="Project topics file not found")
        
        with open(project_file, 'r', encoding='utf-8') as f:
            topics_data = json.load(f)
        
        if department not in topics_data.get("project_topics", {}):
            raise HTTPException(status_code=400, detail=f"Department '{department}' not found")
        
        dept_topics = topics_data["project_topics"][department]
        
        # Find the topic
        for topic in dept_topics.get("topics", []):
            if topic.get("id") == topic_id:
                return {
                    "status": "success",
                    "department": department,
                    "topic": topic
                }
                
        raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Configuration ====================
@app.get("/config")
async def get_config():
    """Get chatbot configuration"""
    return {
        "departments": DEPARTMENTS,
        "semesters": SEMESTERS,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "allowed_formats": [".pdf", ".docx", ".doc", ".txt", ".pptx"]
    }

# ==================== Summarization ====================
def summarize_text(text: str, num_sentences: int = 5) -> str:
    """Simple extractive summarization using sentence scoring"""
    # Clean and split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) <= num_sentences:
        return ' '.join(sentences)
    
    # Score sentences based on word frequency
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
    words = re.findall(r'\w+', text.lower())
    word_freq = Counter(word for word in words if word not in stop_words)
    
    # Score each sentence
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        for word in re.findall(r'\w+', sentence.lower()):
            if word in word_freq:
                sentence_scores[i] = sentence_scores.get(i, 0) + word_freq[word]
    
    # Get top sentences
    top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_sentences]
    top_sentences = sorted(top_sentences, key=lambda x: x[0])  # Restore original order
    
    summary = ' '.join([sentences[i] for i, _ in top_sentences])
    return summary

@app.get("/summarize/{doc_id}")
async def summarize_document(doc_id: str, num_sentences: int = 5):
    """Summarize a document by ID"""
    try:
        # For demo documents
        if doc_id == "demo_001" or doc_id.startswith("sample_doc_"):
            # Check if we can get it from metadata or default
            doc = doc_processor.get_document(doc_id)
            if doc:
                file_path = doc_processor.get_document_path(doc_id)
                if file_path and file_path.exists():
                    text = doc_processor._extract_content(file_path)
                else:
                    text = doc.get("content_preview", "")
            else:
                text = "Python is a high-level programming language. It is interpreted and dynamically typed. Easy to learn and widely used in industry."
            
            summary = summarize_text(text, num_sentences)
            return {
                "status": "success",
                "title": doc.get("title", "Python Lab Manual") if doc else "Python Lab Manual",
                "summary": summary
            }

        # For uploaded files
        doc = doc_processor.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = doc_processor.get_document_path(doc_id)
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        text = doc_processor._extract_content(file_path)
        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Document does not contain sufficient text for summarization")
        
        summary = summarize_text(text, num_sentences)
        return {
            "status": "success",
            "title": doc.get("title", "Document"),
            "summary": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== AI HELP ====================
AI_KNOWLEDGE_BASE = {
    "what_is_this": {
        "question": "What is the Engineering Chatbot?",
        "answer": "The Engineering Chatbot is an intelligent knowledge management system designed for engineering students and academic management. It helps students find study materials, project guidelines, and resources across 8 engineering departments (CSE, IT, AI&DS, CSBS, ECE, EEE, Mechanical, Civil). For management, it provides centralized control over academic content and student resource access."
    },
    "how_to_use": {
        "question": "How do I use the Engineering Chatbot?",
        "answer": "The chatbot has 5 main tabs:\n\n1. **Search**: Search for study materials using keyword, semantic, or hybrid search\n2. **Materials**: Browse materials by department and semester\n3. **Projects**: View implementation roadmaps for 24+ engineering projects with 4 phases each\n4. **Upload**: (Admin only) Upload documents with admin key 'admin123'\n5. **Dashboard**: View system statistics and activity\n\nTo download materials: Search → Click Download button → Save to your computer"
    },
    "features": {
        "question": "What are the key features?",
        "answer": "Key Features:\n✅ Smart Search (Keyword, Semantic, Hybrid)\n✅ Multi-department Support (8 departments)\n✅ 1000+ Study Materials\n✅ 24+ Project Roadmaps with 4 phases each\n✅ 95+ Resource Links\n✅ Online Search Integration (Google, YouTube, Wikipedia, Udemy)\n✅ File Download & Upload\n✅ Admin Dashboard\n✅ Real-time Statistics\n✅ Multi-semester Support (Semesters 1-8)"
    },
    "departments": {
        "question": "What departments are supported?",
        "answer": "The Engineering Chatbot supports 8 engineering departments:\n\n1. **CSE** - Computer Science & Engineering\n2. **IT** - Information Technology\n3. **AI&DS** - Artificial Intelligence & Data Science\n4. **CSBS** - Computer Science & Business Systems\n5. **ECE** - Electronics & Communication Engineering\n6. **EEE** - Electrical & Electronics Engineering\n7. **Mechanical** - Mechanical Engineering\n8. **Civil** - Civil Engineering\n\nEach department has organized materials for all 8 semesters."
    },
    "projects": {
        "question": "Tell me about the projects feature",
        "answer": "The Projects feature includes 24 implementation roadmaps (3 per department) with:\n\n📋 4-Phase Roadmap:\n- Phase 1: Research (research tasks & 4-5 resource links)\n- Phase 2: Design (design tasks & resources)\n- Phase 3: Implementation (coding tasks & resources)\n- Phase 4: Evaluation/Deployment (testing & launch tasks)\n\nEach project has detailed task breakdowns and links to learning resources. Perfect for capstone projects and skill development."
    },
    "download": {
        "question": "How do I download study materials?",
        "answer": "Downloading is simple:\n\n1. Go to **Search** tab\n2. Enter your search query (e.g., 'Python', 'DBMS')\n3. Click **🔍 Search**\n4. For any result, click the **⬇️ Download** button\n5. The file will download to your computer's Downloads folder\n\nSupported formats: TXT, PDF, and more. Files download with meaningful names."
    },
    "admin": {
        "question": "How does admin upload work?",
        "answer": "Admin Upload (Restricted):\n\n1. Go to **Upload** tab\n2. Enter **Admin Key**: admin123\n3. Select Department and Semester\n4. Enter Subject name\n5. Provide Document Title and Keywords\n6. Upload the file (max 50MB)\n7. Click **Upload Document**\n\nOnly authorized users with the correct admin key can upload. All uploads are stored and indexed automatically."
    },
    "search_types": {
        "question": "What are the different search types?",
        "answer": "Three powerful search methods:\n\n1. **Keyword Search**: Traditional text matching - fast and reliable\n   - Best for: Exact terms, specific topics\n\n2. **Semantic Search**: AI-powered meaning-based search\n   - Best for: Conceptual queries, finding related content\n   - Example: 'database concepts' finds DBMS, normalization, etc.\n\n3. **Hybrid Search**: Combines keyword + semantic\n   - Best for: Comprehensive results from both methods\n   - Most accurate and recommended"
    },
    "future": {
        "question": "What are the future plans for this chatbot?",
        "answer": "🎓 **What is the Engineering Chatbot?**\n\nThe Engineering Chatbot is an intelligent knowledge management system designed for engineering students and academic management. It centralizes study materials, project guidelines, and resources across 8 engineering departments.\n\n📊 **Current Status:**\n- 8 Engineering Departments supported\n- 24+ Project Implementation Roadmaps\n- 95+ Learning Resource Links\n- Multi-search capability (Keyword, Semantic, Hybrid)\n- Admin management system\n- Real-time file downloads\n\n🚀 **Future Roadmap:**\n\n**Phase 1 (Q1 2026)**:\n- Real LLM Integration (GPT-4/Claude)\n- Conversational AI for natural Q&A\n- Doubt resolution\n\n**Phase 2 (Q2 2026)**:\n- Video Tutorial Integration\n- Interactive Coding Exercises\n- Real-time Live Chat Support\n\n**Phase 3 (Q3 2026)**:\n- Mobile App (iOS/Android)\n- Offline Learning Mode\n- Peer Collaboration & Discussion Forums\n\n**Phase 4 (Q4 2026)**:\n- Advanced Analytics Dashboard\n- Adaptive Learning Paths\n- Certification & Achievement Badges\n\n✨ **Vision**: Transform engineering education through AI-powered personalized learning experiences"
    },
    "benefits_student": {
        "question": "What are the benefits for students?",
        "answer": "Benefits for Students:\n\n✅ **Centralized Learning Hub**: All materials in one place\n✅ **Smart Search**: Find exactly what you need quickly\n✅ **Project Roadmaps**: Clear guidance for capstone projects\n✅ **Resource Links**: Curated external learning materials\n✅ **Easy Downloads**: Save materials offline\n✅ **Multi-source Search**: Google/YouTube integration\n✅ **Semester-wise Organization**: Materials by difficulty level\n✅ **24/7 Availability**: Access anytime, anywhere\n✅ **AI-Powered Help**: Get instant answers about the system"
    },
    "benefits_management": {
        "question": "What are the benefits for management/faculty?",
        "answer": "Benefits for Management:\n\n✅ **Centralized Control**: Manage all academic content\n✅ **Admin Dashboard**: View system statistics and usage\n✅ **Easy Upload**: Add/update materials effortlessly\n✅ **Security**: Admin key protected uploads\n✅ **Analytics**: Track student access patterns\n✅ **Scalability**: Support 1000+ materials\n✅ **Multi-department Support**: Manage all 8 departments\n✅ **Curriculum Alignment**: Organize by semester and subject\n✅ **Cost-Effective**: Cloud-based, minimal infrastructure"
    },
    "contact": {
        "question": "How do I get support?",
        "answer": "Support & Contact:\n\n📧 **Email Support**: support@engineeringchatbot.edu\n🔧 **Technical Issues**: Check the DOWNLOAD_GUIDE.md for troubleshooting\n📚 **Documentation**: See API_DOCUMENTATION.md for developer details\n💡 **Feature Requests**: Submit via admin panel\n⚡ **Emergency Support**: Contact technical team\n\nThe system is designed to be user-friendly and self-explanatory with help features."
    }
}

@app.post("/ai-help")
def ai_help(query: str = None):
    """AI-powered help endpoint - answers questions about the chatbot"""
    try:
        if not query:
            return {
                "status": "success",
                "question": "How can I help you?",
                "answer": "I'm the Engineering Chatbot AI Assistant! I can help you with:\n\n- What is the Engineering Chatbot?\n- How do I use it?\n- What are the key features?\n- How do I download materials?\n- What are the projects?\n- What are the future plans?\n- How does admin upload work?\n- What are the search types?\n- Benefits for students\n- Benefits for management\n- How to get support\n\nTry asking any of these questions!",
                "type": "general",
                "all_questions": list(AI_KNOWLEDGE_BASE.keys())
            }
        
        query_lower = query.lower()
        
        # Try to find exact match first
        for key, item in AI_KNOWLEDGE_BASE.items():
            question_lower = item["question"].lower()
            if question_lower == query_lower or query_lower in question_lower or question_lower in query_lower:
                return {
                    "status": "success",
                    "question": item["question"],
                    "answer": item["answer"],
                    "type": "exact_match",
                    "key": key
                }
        
        # Try keyword matching for partial matches
        best_match = None
        best_score = 0
        
        for key, item in AI_KNOWLEDGE_BASE.items():
            question = item["question"].lower()
            score = 0
            for word in query_lower.split():
                if len(word) > 2:
                    if word in question:
                        score += 1
            
            if score > best_score:
                best_score = score
                best_match = (key, item)
        
        if best_match and best_score > 0:
            key, item = best_match
            return {
                "status": "success",
                "question": item["question"],
                "answer": item["answer"],
                "type": "keyword_match",
                "key": key,
                "confidence": f"{best_score * 20}%"
            }
        
        # If no match found, suggest questions
        return {
            "status": "success",
            "question": query,
            "answer": "I couldn't find a direct answer to your question. Here are some questions I can answer:\n\n" + "\n".join([f"- {item['question']}" for item in AI_KNOWLEDGE_BASE.values()]),
            "type": "no_match",
            "suggestions": [item["question"] for item in list(AI_KNOWLEDGE_BASE.values())[:5]]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
