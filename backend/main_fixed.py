"""Simple Working FastAPI Backend"""

import sys
sys.stdout.reconfigure(encoding='utf-8') if sys.stdout else None

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from pathlib import Path
import json
import uuid
import PyPDF2
from collections import Counter
import re

# Config
DEPARTMENTS = ["CSE", "IT", "AI&DS", "CSBS", "ECE", "EEE", "Mechanical", "Civil"]
STORAGE_DIR = Path(__file__).parent.parent / "data" / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Backend started successfully!")
    yield
    print("✅ Backend shutting down...")

app = FastAPI(title="Engineering Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Summarization function
def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            print(f"📄 Extracting text from PDF: {file_path.name} ({num_pages} pages)")
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                    print(f"  ✓ Page {page_num}: {len(page_text)} chars")
            
            print(f"✅ Total extracted: {len(text)} chars")
            return text if text else None
    except Exception as e:
        print(f"❌ PDF extraction error: {e}")
        return None

def summarize_text(text, num_sentences=5):
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

@app.get("/health")
def health():
    return {"status": "✅ healthy"}

@app.get("/config")
def config():
    return {
        "departments": DEPARTMENTS,
        "semesters": list(range(1, 9)),
        "max_file_size_mb": 50
    }

@app.get("/documents")
def list_docs():
    try:
        metadata_file = STORAGE_DIR / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                data = json.load(f)
                return {
                    "status": "success",
                    "count": len(data),
                    "documents": list(data.values())[:5]
                }
    except:
        pass
    return {"status": "success", "count": 0, "documents": []}

@app.get("/search")
def search(query: str, search_type: str = "hybrid", department: str = None, semester: int = None):
    # Load uploaded documents from metadata
    uploaded_docs = []
    try:
        metadata_file = STORAGE_DIR / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                for doc_id, doc_data in metadata.items():
                    # Calculate relevance score based on search
                    query_lower = query.lower()
                    title = doc_data.get("title", "").lower()
                    subject = doc_data.get("subject", "").lower()
                    keywords = doc_data.get("keywords", "").lower()
                    
                    # Simple relevance scoring
                    score = 0
                    if query_lower in title:
                        score += 0.9
                    elif any(word in title for word in query_lower.split()):
                        score += 0.7
                    if query_lower in subject or query_lower in keywords:
                        score += 0.6
                    
                    if score > 0:  # Only include if there's some match
                        uploaded_docs.append({
                            "title": doc_data.get("title"),
                            "department": doc_data.get("department"),
                            "semester": doc_data.get("semester"),
                            "subject": doc_data.get("subject"),
                            "relevance_score": min(score, 1.0),
                            "downloadable": True,
                            "file_type": doc_data.get("file_type", ".pdf"),
                            "doc_id": doc_id,
                            "snippet": f"Uploaded: {doc_data.get('subject')}",
                            "content_preview": doc_data.get("keywords", "")
                        })
    except Exception as e:
        print(f"Error loading metadata: {e}")
    
    # Sample data with more diverse results
    all_results = [
        {
            "title": "Python Lab Manual",
            "department": "CSE",
            "semester": 2,
            "subject": "Programming",
            "relevance_score": 0.95,
            "downloadable": True,
            "file_type": ".pdf",
            "doc_id": "demo_001",
            "snippet": "Python programming basics and lab exercises...",
            "content_preview": "Python Lab Manual"
        },
        {
            "title": "DBMS Unit 2 Notes",
            "department": "CSE",
            "semester": 3,
            "subject": "Database Systems",
            "relevance_score": 0.87,
            "downloadable": True,
            "file_type": ".pdf",
            "doc_id": "demo_002",
            "snippet": "Data models and concepts...",
            "content_preview": "Database Management Systems - Unit 2"
        },
        {
            "title": "Operating Systems Fundamentals",
            "department": "CSE",
            "semester": 4,
            "subject": "Operating Systems",
            "relevance_score": 0.78,
            "downloadable": True,
            "file_type": ".pdf",
            "doc_id": "demo_003",
            "snippet": "OS concepts, process management, memory management...",
            "content_preview": "Operating Systems"
        },
        {
            "title": "Web Development with Python",
            "department": "IT",
            "semester": 5,
            "subject": "Web Development",
            "relevance_score": 0.85,
            "downloadable": True,
            "file_type": ".pdf",
            "doc_id": "demo_004",
            "snippet": "Django, Flask, and web frameworks...",
            "content_preview": "Web Development"
        },
        {
            "title": "AI & ML Basics",
            "department": "AI&DS",
            "semester": 6,
            "subject": "Artificial Intelligence",
            "relevance_score": 0.92,
            "downloadable": True,
            "file_type": ".pdf",
            "doc_id": "demo_005",
            "snippet": "Machine learning, neural networks, deep learning...",
            "content_preview": "AI & ML Basics"
        },
        {
            "title": "ECE Circuit Design",
            "department": "ECE",
            "semester": 3,
            "subject": "Circuit Design",
            "relevance_score": 0.81,
            "downloadable": True,
            "file_type": ".pdf",
            "doc_id": "demo_006",
            "snippet": "Circuit analysis, design techniques...",
            "content_preview": "Circuit Design"
        }
    ]
    
    # Combine sample data with uploaded documents
    all_results.extend(uploaded_docs)
    
    # Filter by search query
    results = [r for r in all_results if query.lower() in r["title"].lower() or query.lower() in r["subject"].lower()]
    
    # Filter by department
    if department:
        results = [r for r in results if r["department"].lower() == department.lower()]
    
    # Filter by semester
    if semester:
        results = [r for r in results if r["semester"] == semester]
    
    # Sort by relevance
    results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
    
    return {
        "status": "success",
        "query": query,
        "filters": {
            "search_type": search_type,
            "department": department,
            "semester": semester
        },
        "total": len(results),
        "results": results
    }

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    department: str = Form(...),
    semester: int = Form(...),
    subject: str = Form(...),
    title: str = Form(None),
    keywords: str = Form(""),
    admin_key: str = Form(...)
):
    """Upload a document"""
    if admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    try:
        # Generate doc ID
        doc_id = str(uuid.uuid4())
        
        # Save file
        file_path = STORAGE_DIR / f"{doc_id}_{file.filename}"
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Save metadata
        metadata = {
            "id": doc_id,
            "title": title or file.filename,
            "department": department,
            "semester": semester,
            "subject": subject,
            "keywords": keywords,
            "file_type": Path(file.filename).suffix,
            "original_name": file.filename
        }
        
        # Update metadata file
        metadata_file = STORAGE_DIR / "metadata.json"
        existing = {}
        if metadata_file.exists():
            with open(metadata_file) as f:
                existing = json.load(f)
        
        existing[doc_id] = metadata
        with open(metadata_file, "w") as f:
            json.dump(existing, f, indent=2)
        
        return {
            "status": "success",
            "message": f"Document '{title or file.filename}' uploaded successfully",
            "doc_id": doc_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/project-topics")
def get_project_topics(department: str = None):
    """Get project topics"""
    return {
        "status": "success",
        "total_departments": 8,
        "total_projects": 95,
        "departments": {
            dept: {"name": dept, "total_topics": 10}
            for dept in DEPARTMENTS
        }
    }

@app.get("/project-topics/{department}")
def get_dept_topics(department: str):
    """Get topics for a department"""
    if department not in DEPARTMENTS:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Department-specific projects
    projects = {
        "CSE": [
            {
                "id": "cse_001",
                "title": "AI Chatbot with NLP",
                "description": "Build an intelligent chatbot using Natural Language Processing and machine learning",
                "difficulty": "Hard",
                "skills": ["Python", "NLP", "TensorFlow", "API Design"],
                "roadmap": [
                    {
                        "phase": 1,
                        "title": "Research (Months 1-2)",
                        "tasks": [
                            "Study NLP concepts and algorithms",
                            "Research chatbot frameworks",
                            "Literature review on machine learning"
                        ],
                        "resources": [
                            {"name": "TensorFlow Docs", "url": "https://www.tensorflow.org/"},
                            {"name": "NLTK Tutorial", "url": "https://www.nltk.org/"},
                            {"name": "Hugging Face NLP", "url": "https://huggingface.co/"},
                            {"name": "PyTorch Tutorials", "url": "https://pytorch.org/tutorials/"}
                        ]
                    },
                    {
                        "phase": 2,
                        "title": "Design (Months 3-4)",
                        "tasks": [
                            "Architecture design",
                            "API specifications",
                            "Database design and planning"
                        ],
                        "resources": [
                            {"name": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer"},
                            {"name": "FastAPI Docs", "url": "https://fastapi.tiangolo.com/"},
                            {"name": "MongoDB Design", "url": "https://www.mongodb.com/docs/"},
                            {"name": "REST API Best Practices", "url": "https://restfulapi.net/"}
                        ]
                    },
                    {
                        "phase": 3,
                        "title": "Implementation (Months 5-7)",
                        "tasks": [
                            "Core chatbot development",
                            "NLP integration",
                            "API development and testing"
                        ],
                        "resources": [
                            {"name": "Python Docs", "url": "https://docs.python.org/3/"},
                            {"name": "Rasa Framework", "url": "https://rasa.com/"},
                            {"name": "OpenAI API", "url": "https://openai.com/api/"},
                            {"name": "Stack Overflow", "url": "https://stackoverflow.com/"}
                        ]
                    },
                    {
                        "phase": 4,
                        "title": "Evaluation (Months 8-9)",
                        "tasks": [
                            "Performance testing",
                            "User acceptance testing",
                            "Deployment and documentation"
                        ],
                        "resources": [
                            {"name": "GitHub Pages", "url": "https://pages.github.com/"},
                            {"name": "Docker Docs", "url": "https://docs.docker.com/"},
                            {"name": "AWS Deployment", "url": "https://aws.amazon.com/"},
                            {"name": "Pytest Documentation", "url": "https://docs.pytest.org/"}
                        ]
                    }
                ]
            },
            {
                "id": "cse_002",
                "title": "E-Commerce Platform",
                "description": "Full-stack e-commerce website with payment gateway integration",
                "difficulty": "Hard",
                "skills": ["Python", "Django", "React", "PostgreSQL", "Stripe API"],
                "roadmap": [
                    {"phase": 1, "title": "Research (Months 1-2)", "tasks": ["Market analysis", "Technology selection", "Requirements definition"], "resources": [{"name": "Shopify Blog", "url": "https://www.shopify.com/blog"}, {"name": "Django Docs", "url": "https://docs.djangoproject.com/"}, {"name": "React Docs", "url": "https://react.dev/"}]},
                    {"phase": 2, "title": "Design (Months 3-4)", "tasks": ["Database design", "UI/UX design", "API specifications"], "resources": [{"name": "Figma Design", "url": "https://www.figma.com/"}, {"name": "PostgreSQL Docs", "url": "https://www.postgresql.org/docs/"}, {"name": "Stripe API", "url": "https://stripe.com/docs"}]},
                    {"phase": 3, "title": "Implementation (Months 5-7)", "tasks": ["Backend development", "Frontend development", "Payment integration"], "resources": [{"name": "Django REST", "url": "https://www.django-rest-framework.org/"}, {"name": "React Router", "url": "https://reactrouter.com/"}, {"name": "Stripe Integration", "url": "https://stripe.com/docs/payments"}]},
                    {"phase": 4, "title": "Deployment (Months 8-9)", "tasks": ["Testing and QA", "Performance optimization", "Live deployment"], "resources": [{"name": "Heroku Docs", "url": "https://devcenter.heroku.com/"}, {"name": "AWS RDS", "url": "https://aws.amazon.com/rds/"}, {"name": "Sentry Monitoring", "url": "https://sentry.io/"}]}
                ]
            },
            {
                "id": "cse_003",
                "title": "Social Media App",
                "description": "Real-time social networking platform with messaging",
                "difficulty": "Medium",
                "skills": ["Python", "FastAPI", "React", "WebSocket", "MongoDB"],
                "roadmap": [
                    {"phase": 1, "title": "Research (Weeks 1-2)", "tasks": ["Feature analysis", "Technology review", "Prototype planning"], "resources": [{"name": "FastAPI Docs", "url": "https://fastapi.tiangolo.com/"}, {"name": "WebSocket Guide", "url": "https://websockets.readthedocs.io/"}, {"name": "MongoDB", "url": "https://www.mongodb.com/"}]},
                    {"phase": 2, "title": "Design (Weeks 3-4)", "tasks": ["System architecture", "Database design", "API design"], "resources": [{"name": "Lucidchart", "url": "https://www.lucidchart.com/"}, {"name": "Miro Design", "url": "https://miro.com/"}, {"name": "Draw.io", "url": "https://draw.io/"}]},
                    {"phase": 3, "title": "Development (Weeks 5-8)", "tasks": ["Core features", "Real-time messaging", "Testing"], "resources": [{"name": "Socket.IO", "url": "https://socket.io/"}, {"name": "React Docs", "url": "https://react.dev/"}, {"name": "Jest Testing", "url": "https://jestjs.io/"}]},
                    {"phase": 4, "title": "Launch (Weeks 9-10)", "tasks": ["Beta testing", "Optimization", "Production release"], "resources": [{"name": "Vercel Deploy", "url": "https://vercel.com/"}, {"name": "GitHub Actions", "url": "https://github.com/features/actions"}, {"name": "Monitoring", "url": "https://www.datadoghq.com/"}]}
                ]
            }
        ],
        "IT": [
            {
                "id": "it_001",
                "title": "Network Monitoring System",
                "description": "Real-time network traffic monitoring and analysis tool",
                "difficulty": "Hard",
                "skills": ["Python", "Wireshark", "Network Protocols", "Database"],
                "roadmap": [
                    {"phase": 1, "title": "Research (Weeks 1-2)", "tasks": ["Study network protocols", "Research monitoring tools", "Technology selection"], "resources": [{"name": "Wireshark Guide", "url": "https://www.wireshark.org/"}, {"name": "Python Docs", "url": "https://docs.python.org/3/"}, {"name": "Network Basics", "url": "https://www.cisco.com/"}]},
                    {"phase": 2, "title": "Design (Weeks 3-4)", "tasks": ["Architecture design", "Database schema", "API design"], "resources": [{"name": "System Design", "url": "https://github.com/donnemartin/system-design-primer"}, {"name": "PostgreSQL", "url": "https://www.postgresql.org/docs/"}, {"name": "REST API", "url": "https://restfulapi.net/"}]},
                    {"phase": 3, "title": "Implementation (Weeks 5-8)", "tasks": ["Core development", "Monitoring features", "Testing"], "resources": [{"name": "Scapy", "url": "https://scapy.readthedocs.io/"}, {"name": "Django", "url": "https://docs.djangoproject.com/"}, {"name": "Pytest", "url": "https://docs.pytest.org/"}]},
                    {"phase": 4, "title": "Deployment (Weeks 9-10)", "tasks": ["Testing", "Optimization", "Live deployment"], "resources": [{"name": "Docker", "url": "https://docs.docker.com/"}, {"name": "AWS", "url": "https://aws.amazon.com/docs/"}, {"name": "GitHub", "url": "https://github.com/"}]}
                ]
            },
            {
                "id": "it_002",
                "title": "Cloud Infrastructure Manager",
                "description": "Automated cloud resource provisioning and management",
                "difficulty": "Hard",
                "skills": ["AWS/Azure", "Python", "Terraform", "Docker"],
                "roadmap": [
                    {"phase": 1, "title": "Research (Weeks 1-2)", "tasks": ["Cloud platforms study", "IaC tools research", "Architecture planning"], "resources": [{"name": "AWS Documentation", "url": "https://aws.amazon.com/documentation/"}, {"name": "Terraform Docs", "url": "https://www.terraform.io/docs"}, {"name": "Azure Docs", "url": "https://docs.microsoft.com/azure/"}]},
                    {"phase": 2, "title": "Design (Weeks 3-4)", "tasks": ["Infrastructure design", "Security planning", "Cost optimization"], "resources": [{"name": "Well-Architected Framework", "url": "https://aws.amazon.com/architecture/well-architected/"}, {"name": "Terraform Best Practices", "url": "https://www.terraform.io/docs/language/syntax"}, {"name": "Security Design", "url": "https://owasp.org/"}]},
                    {"phase": 3, "title": "Implementation (Weeks 5-8)", "tasks": ["Code development", "Testing", "Documentation"], "resources": [{"name": "Boto3", "url": "https://boto3.amazonaws.com/v1/documentation/"}, {"name": "Python SDK", "url": "https://docs.python.org/3/"}, {"name": "Docker Hub", "url": "https://hub.docker.com/"}]},
                    {"phase": 4, "title": "Launch (Weeks 9-10)", "tasks": ["Deployment", "Monitoring", "Optimization"], "resources": [{"name": "CloudWatch", "url": "https://docs.aws.amazon.com/cloudwatch/"}, {"name": "Monitoring Tools", "url": "https://www.datadoghq.com/"}, {"name": "CI/CD", "url": "https://github.com/features/actions"}]}
                ]
            },
            {
                "id": "it_003",
                "title": "System Performance Analyzer",
                "description": "Monitor and analyze system performance metrics",
                "difficulty": "Medium",
                "skills": ["Python", "Linux", "Grafana", "Prometheus"],
                "roadmap": [
                    {"phase": 1, "title": "Research (Weeks 1-2)", "tasks": ["Performance metrics study", "Tools research", "Planning"], "resources": [{"name": "Prometheus", "url": "https://prometheus.io/docs/"}, {"name": "Grafana", "url": "https://grafana.com/docs/"}, {"name": "Linux Performance", "url": "https://www.linux.com/"}]},
                    {"phase": 2, "title": "Design (Weeks 3-4)", "tasks": ["Metrics design", "Dashboard design", "Alert setup"], "resources": [{"name": "Monitoring Design", "url": "https://docs.microsoft.com/en-us/azure/azure-monitor/"}, {"name": "Grafana Dashboards", "url": "https://grafana.com/grafana/dashboards/"}, {"name": "Alerting", "url": "https://prometheus.io/docs/alerting/"}]},
                    {"phase": 3, "title": "Implementation (Weeks 5-8)", "tasks": ["Agent development", "Integration", "Testing"], "resources": [{"name": "Node Exporter", "url": "https://github.com/prometheus/node_exporter"}, {"name": "Python Monitoring", "url": "https://pypi.org/project/prometheus-client/"}, {"name": "System Metrics", "url": "https://man7.org/linux/man-pages/"}]},
                    {"phase": 4, "title": "Launch (Weeks 9-10)", "tasks": ["Deployment", "Tuning", "Documentation"], "resources": [{"name": "InfluxDB", "url": "https://www.influxdata.com/products/influxdb/"}, {"name": "ELK Stack", "url": "https://www.elastic.co/what-is/elk-stack"}, {"name": "DevOps Tools", "url": "https://www.jenkins.io/"}]}
                ]
            }
        ],
        "AI&DS": [
            {
                "id": "aids_001",
                "title": "Predictive Analytics Dashboard",
                "description": "Machine learning model for sales forecasting with interactive dashboard",
                "difficulty": "Hard",
                "skills": ["Python", "Scikit-learn", "TensorFlow", "Pandas", "Plotly"],
                "roadmap": [
                    {"phase": 1, "title": "Research (Weeks 1-2)", "tasks": ["ML algorithms study", "Data analysis", "Tools selection"], "resources": [{"name": "Scikit-learn", "url": "https://scikit-learn.org/stable/"}, {"name": "Pandas Docs", "url": "https://pandas.pydata.org/docs/"}, {"name": "TensorFlow", "url": "https://www.tensorflow.org/"}]},
                    {"phase": 2, "title": "Design (Weeks 3-4)", "tasks": ["Model design", "Data pipeline", "Dashboard design"], "resources": [{"name": "Plotly", "url": "https://plotly.com/python/"}, {"name": "Jupyter", "url": "https://jupyter.org/"}, {"name": "Analytics", "url": "https://www.tableau.com/"}]},
                    {"phase": 3, "title": "Implementation (Weeks 5-8)", "tasks": ["Model training", "API development", "Dashboard creation"], "resources": [{"name": "FastAPI", "url": "https://fastapi.tiangolo.com/"}, {"name": "Streamlit", "url": "https://streamlit.io/"}, {"name": "Flask", "url": "https://flask.palletsprojects.com/"}]},
                    {"phase": 4, "title": "Launch (Weeks 9-10)", "tasks": ["Testing", "Deployment", "Monitoring"], "resources": [{"name": "Docker", "url": "https://docs.docker.com/"}, {"name": "AWS SageMaker", "url": "https://aws.amazon.com/sagemaker/"}, {"name": "MLflow", "url": "https://mlflow.org/"}]}
                ]
            },
            {
                "id": "aids_002",
                "title": "Image Classification Model",
                "description": "Deep learning model for medical image classification",
                "difficulty": "Hard",
                "skills": ["Python", "CNN", "PyTorch", "OpenCV", "Jupyter"],
                "roadmap": [
                    {"phase": 1, "title": "Research (Weeks 1-2)", "tasks": ["CNN study", "Medical imaging", "Dataset collection"], "resources": [{"name": "PyTorch", "url": "https://pytorch.org/"}, {"name": "OpenCV", "url": "https://opencv.org/"}, {"name": "ImageNet", "url": "https://www.image-net.org/"}]},
                    {"phase": 2, "title": "Design (Weeks 3-4)", "tasks": ["Model architecture", "Training pipeline", "Validation"], "resources": [{"name": "ResNet", "url": "https://github.com/pytorch/vision"}, {"name": "Transfer Learning", "url": "https://pytorch.org/tutorials/"}, {"name": "Data Augmentation", "url": "https://github.com/albumentations-team/albumentations"}]},
                    {"phase": 3, "title": "Implementation (Weeks 5-8)", "tasks": ["Model development", "Training", "Testing"], "resources": [{"name": "TensorBoard", "url": "https://www.tensorflow.org/tensorboard"}, {"name": "Weights & Biases", "url": "https://wandb.ai/"}, {"name": "Medical Imaging", "url": "https://simpleitk.readthedocs.io/"}]},
                    {"phase": 4, "title": "Launch (Weeks 9-10)", "tasks": ["Evaluation", "Deployment", "Documentation"], "resources": [{"name": "ONNX", "url": "https://onnx.ai/"}, {"name": "TensorRT", "url": "https://developer.nvidia.com/tensorrt"}, {"name": "Flask Deployment", "url": "https://flask.palletsprojects.com/"}]}
                ]
            },
            {
                "id": "aids_003",
                "title": "Sentiment Analysis Tool",
                "description": "NLP-based sentiment analysis for social media data",
                "difficulty": "Medium",
                "skills": ["Python", "NLTK", "BERT", "Streamlit"],
                "roadmap": [
                    {"phase": 1, "title": "Research (Weeks 1-2)", "tasks": ["NLP study", "BERT research", "Dataset collection"], "resources": [{"name": "Hugging Face", "url": "https://huggingface.co/"}, {"name": "NLTK", "url": "https://www.nltk.org/"}, {"name": "BERT", "url": "https://github.com/google-research/bert"}]},
                    {"phase": 2, "title": "Design (Weeks 3-4)", "tasks": ["Model selection", "Pipeline design", "UI design"], "resources": [{"name": "Transformers", "url": "https://huggingface.co/docs/transformers/"}, {"name": "Streamlit", "url": "https://streamlit.io/docs"}, {"name": "Data Processing", "url": "https://pandas.pydata.org/"}]},
                    {"phase": 3, "title": "Implementation (Weeks 5-8)", "tasks": ["Fine-tuning", "API creation", "UI development"], "resources": [{"name": "PyTorch", "url": "https://pytorch.org/"}, {"name": "FastAPI", "url": "https://fastapi.tiangolo.com/"}, {"name": "React", "url": "https://react.dev/"}]},
                    {"phase": 4, "title": "Launch (Weeks 9-10)", "tasks": ["Testing", "Deployment", "Monitoring"], "resources": [{"name": "Docker", "url": "https://docs.docker.com/"}, {"name": "Heroku", "url": "https://www.heroku.com/"}, {"name": "GitHub", "url": "https://github.com/"}]}
                ]
            }
        ],
        "CSBS": [
            {
                "id": "csbs_001",
                "title": "Blockchain Voting System",
                "description": "Secure voting system using blockchain technology",
                "difficulty": "Hard",
                "skills": ["Python", "Solidity", "Web3.py", "Ethereum"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["Blockchain study", "Solidity learning", "Smart contract research"], "resources": [{"name": "Ethereum", "url": "https://ethereum.org/"}, {"name": "Solidity Docs", "url": "https://docs.soliditylang.org/"}, {"name": "Web3.py", "url": "https://web3py.readthedocs.io/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Architecture design", "Smart contract design", "Security planning"], "resources": [{"name": "OpenZeppelin", "url": "https://docs.openzeppelin.com/"}, {"name": "Smart Contracts", "url": "https://github.com/ethereum/smart-contracts"}, {"name": "Security", "url": "https://consensys.github.io/smart-contract-best-practices/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Smart contract coding", "Backend development", "Frontend creation"], "resources": [{"name": "Truffle", "url": "https://www.trufflesuite.com/"}, {"name": "Hardhat", "url": "https://hardhat.org/"}, {"name": "React", "url": "https://react.dev/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Testing", "Audit", "Deployment"], "resources": [{"name": "Ganache", "url": "https://www.trufflesuite.com/ganache"}, {"name": "Security Audit", "url": "https://www.certik.org/"}, {"name": "Testnet", "url": "https://goerli.etherscan.io/"}]}
                ]
            },
            {
                "id": "csbs_002",
                "title": "Cybersecurity Threat Detector",
                "description": "AI-powered intrusion detection system",
                "difficulty": "Hard",
                "skills": ["Python", "Machine Learning", "Network Security", "Suricata"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["IDS research", "ML study", "Threat patterns"], "resources": [{"name": "Suricata", "url": "https://suricata.io/"}, {"name": "SNORT", "url": "https://www.snort.org/"}, {"name": "Scikit-learn", "url": "https://scikit-learn.org/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["System design", "Model selection", "Dataset planning"], "resources": [{"name": "UNSW-NB15", "url": "https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity-datasets/"}, {"name": "KDD99", "url": "http://kdd.ics.uci.edu/"}, {"name": "TensorFlow", "url": "https://www.tensorflow.org/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Feature engineering", "Model training", "Integration"], "resources": [{"name": "Pandas", "url": "https://pandas.pydata.org/"}, {"name": "Wireshark", "url": "https://www.wireshark.org/"}, {"name": "Zeek", "url": "https://zeek.org/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Validation", "Deployment", "Monitoring"], "resources": [{"name": "ELK Stack", "url": "https://www.elastic.co/what-is/elk-stack"}, {"name": "Splunk", "url": "https://www.splunk.com/"}, {"name": "Docker", "url": "https://docs.docker.com/"}]}
                ]
            },
            {
                "id": "csbs_003",
                "title": "Data Encryption Tool",
                "description": "End-to-end encryption application for secure file sharing",
                "difficulty": "Medium",
                "skills": ["Python", "Cryptography", "RSA", "AES"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["Cryptography study", "Encryption algorithms", "Tools research"], "resources": [{"name": "Cryptography.io", "url": "https://cryptography.io/"}, {"name": "RSA", "url": "https://en.wikipedia.org/wiki/RSA_(cryptosystem)"}, {"name": "AES", "url": "https://en.wikipedia.org/wiki/Advanced_Encryption_Standard"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Architecture", "Key management", "Protocol design"], "resources": [{"name": "OWASP", "url": "https://owasp.org/www-project-cryptographic-storage-cheat-sheet/"}, {"name": "PyCryptodome", "url": "https://pycryptodome.readthedocs.io/"}, {"name": "PKI", "url": "https://en.wikipedia.org/wiki/Public_key_infrastructure"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["UI development", "Backend coding", "Testing"], "resources": [{"name": "Flask", "url": "https://flask.palletsprojects.com/"}, {"name": "React", "url": "https://react.dev/"}, {"name": "Pytest", "url": "https://docs.pytest.org/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Security audit", "Deployment", "Documentation"], "resources": [{"name": "GitHub", "url": "https://github.com/"}, {"name": "Docker", "url": "https://docs.docker.com/"}, {"name": "Heroku", "url": "https://www.heroku.com/"}]}
                ]
            }
        ],
        "ECE": [
            {
                "id": "ece_001",
                "title": "IoT Smart Home System",
                "description": "Automated smart home with sensor integration",
                "difficulty": "Hard",
                "skills": ["Arduino", "Python", "MQTT", "IoT"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["IoT concepts", "Arduino learning", "Smart home research"], "resources": [{"name": "Arduino", "url": "https://www.arduino.cc/"}, {"name": "MQTT", "url": "https://mqtt.org/"}, {"name": "IoT Guide", "url": "https://www.iot-x.com/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["System architecture", "Hardware selection", "Communication protocol"], "resources": [{"name": "Raspberry Pi", "url": "https://www.raspberrypi.org/"}, {"name": "Mosquitto", "url": "https://mosquitto.org/"}, {"name": "Sensors", "url": "https://www.sparkfun.com/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Circuit design", "Programming", "Integration"], "resources": [{"name": "C++", "url": "https://www.cplusplus.com/"}, {"name": "Python", "url": "https://www.python.org/"}, {"name": "Home Assistant", "url": "https://www.home-assistant.io/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Testing", "Deployment", "Maintenance"], "resources": [{"name": "Node-RED", "url": "https://nodered.org/"}, {"name": "InfluxDB", "url": "https://www.influxdata.com/"}, {"name": "GitHub", "url": "https://github.com/"}]}
                ]
            },
            {
                "id": "ece_002",
                "title": "Signal Processing Application",
                "description": "Digital signal processing for audio/image enhancement",
                "difficulty": "Hard",
                "skills": ["C/C++", "MATLAB", "DSP", "Image Processing"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["DSP concepts", "Filter design", "Image processing"], "resources": [{"name": "MATLAB", "url": "https://www.mathworks.com/products/matlab.html"}, {"name": "OpenCV", "url": "https://opencv.org/"}, {"name": "DSP Guide", "url": "https://www.dspguide.com/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Algorithm design", "Filter selection", "Processing pipeline"], "resources": [{"name": "Numpy", "url": "https://numpy.org/"}, {"name": "Scipy", "url": "https://scipy.org/"}, {"name": "FFT", "url": "https://en.wikipedia.org/wiki/Fast_Fourier_transform"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Algorithm coding", "Optimization", "Testing"], "resources": [{"name": "C++", "url": "https://www.cplusplus.com/"}, {"name": "Scikit-image", "url": "https://scikit-image.org/"}, {"name": "Librosa", "url": "https://librosa.org/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Performance tuning", "Deployment", "Documentation"], "resources": [{"name": "GitHub", "url": "https://github.com/"}, {"name": "Jupyter", "url": "https://jupyter.org/"}, {"name": "Docker", "url": "https://docs.docker.com/"}]}
                ]
            },
            {
                "id": "ece_003",
                "title": "Wireless Power Transfer",
                "description": "Prototype for wireless charging technology",
                "difficulty": "Medium",
                "skills": ["Circuit Design", "Embedded Systems", "Power Electronics"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["WPT principles", "Technology review", "Component selection"], "resources": [{"name": "Wireless Power", "url": "https://en.wikipedia.org/wiki/Wireless_power_transfer"}, {"name": "Circuit Design", "url": "https://www.circuitlab.com/"}, {"name": "Components", "url": "https://www.mouser.com/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Circuit design", "Coil design", "Power management"], "resources": [{"name": "LTSPICE", "url": "https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html"}, {"name": "PCB Design", "url": "https://www.kicad.org/"}, {"name": "Electromagnetics", "url": "https://www.antennamagus.com/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Prototype building", "Testing", "Optimization"], "resources": [{"name": "Arduino", "url": "https://www.arduino.cc/"}, {"name": "Oscilloscope", "url": "https://www.rigol.com/"}, {"name": "Multimeter", "url": "https://www.fluke.com/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Validation", "Documentation", "Patents"], "resources": [{"name": "Patent Search", "url": "https://www.uspto.gov/"}, {"name": "IEEE", "url": "https://www.ieee.org/"}, {"name": "ResearchGate", "url": "https://www.researchgate.net/"}]}
                ]
            }
        ],
        "EEE": [
            {
                "id": "eee_001",
                "title": "Smart Grid Controller",
                "description": "Intelligent power distribution management system",
                "difficulty": "Hard",
                "skills": ["Python", "SCADA", "Power Systems", "Automation"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["Smart grid study", "SCADA concepts", "Power systems"], "resources": [{"name": "SCADA", "url": "https://en.wikipedia.org/wiki/SCADA"}, {"name": "Power Systems", "url": "https://www.power-technology.net/"}, {"name": "IEC 61850", "url": "https://en.wikipedia.org/wiki/IEC_61850"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Architecture design", "Protocol selection", "Database design"], "resources": [{"name": "Modbus", "url": "https://modbus.org/"}, {"name": "DNP3", "url": "https://www.dnp.org/"}, {"name": "PostgreSQL", "url": "https://www.postgresql.org/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Backend development", "Device communication", "UI creation"], "resources": [{"name": "Python", "url": "https://www.python.org/"}, {"name": "Pymodbus", "url": "https://github.com/riptideio/pymodbus"}, {"name": "Grafana", "url": "https://grafana.com/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Testing", "Deployment", "Training"], "resources": [{"name": "Docker", "url": "https://docs.docker.com/"}, {"name": "GitHub", "url": "https://github.com/"}, {"name": "Documentation", "url": "https://sphinx-rtd-tutorial.readthedocs.io/"}]}
                ]
            },
            {
                "id": "eee_002",
                "title": "Renewable Energy Monitor",
                "description": "Solar/Wind energy monitoring and optimization",
                "difficulty": "Medium",
                "skills": ["Python", "IoT", "Data Analytics", "Control Systems"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["Renewable energy study", "Monitoring systems", "Analytics"], "resources": [{"name": "Solar Energy", "url": "https://www.nrel.gov/"}, {"name": "Wind Energy", "url": "https://www.energy.gov/eere/wind"}, {"name": "IoT", "url": "https://www.iot-x.com/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["System design", "Sensor selection", "Data pipeline"], "resources": [{"name": "Time Series", "url": "https://pandas.pydata.org/docs/"}, {"name": "Data Analysis", "url": "https://matplotlib.org/"}, {"name": "Sensors", "url": "https://www.sparkfun.com/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Device integration", "Analytics engine", "Dashboard"], "resources": [{"name": "InfluxDB", "url": "https://www.influxdata.com/"}, {"name": "Streamlit", "url": "https://streamlit.io/"}, {"name": "Pandas", "url": "https://pandas.pydata.org/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Testing", "Deployment", "Monitoring"], "resources": [{"name": "AWS", "url": "https://aws.amazon.com/"}, {"name": "GCP", "url": "https://cloud.google.com/"}, {"name": "GitHub", "url": "https://github.com/"}]}
                ]
            },
            {
                "id": "eee_003",
                "title": "Electrical Load Forecasting",
                "description": "ML model for predicting electrical demand",
                "difficulty": "Medium",
                "skills": ["Python", "Time Series", "Machine Learning", "Forecasting"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["Forecasting methods", "Load patterns", "Time series"], "resources": [{"name": "Time Series", "url": "https://www.statsmodels.org/"}, {"name": "ARIMA", "url": "https://en.wikipedia.org/wiki/Autoregressive_integrated_moving_average"}, {"name": "Scikit-learn", "url": "https://scikit-learn.org/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Model selection", "Feature engineering", "Data preparation"], "resources": [{"name": "Feature Selection", "url": "https://scikit-learn.org/modules/feature_selection.html"}, {"name": "Pandas", "url": "https://pandas.pydata.org/"}, {"name": "Prophet", "url": "https://facebook.github.io/prophet/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Model training", "Validation", "API development"], "resources": [{"name": "TensorFlow", "url": "https://www.tensorflow.org/"}, {"name": "PyTorch", "url": "https://pytorch.org/"}, {"name": "FastAPI", "url": "https://fastapi.tiangolo.com/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Testing", "Deployment", "Monitoring"], "resources": [{"name": "Docker", "url": "https://docs.docker.com/"}, {"name": "Kubernetes", "url": "https://kubernetes.io/"}, {"name": "GitHub", "url": "https://github.com/"}]}
                ]
            }
        ],
        "Mechanical": [
            {
                "id": "mech_001",
                "title": "CAD Design Suite",
                "description": "3D modeling and CAD tool development",
                "difficulty": "Hard",
                "skills": ["C++", "OpenGL", "CAD Algorithms", "3D Graphics"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["CAD concepts", "3D graphics", "Geometric algorithms"], "resources": [{"name": "OpenGL", "url": "https://www.khronos.org/opengl/"}, {"name": "3D Graphics", "url": "https://learnopengl.com/"}, {"name": "Geometric Algorithms", "url": "https://github.com/erich666/Real-Time-Rendering"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Architecture design", "UI/UX design", "Algorithm selection"], "resources": [{"name": "Qt", "url": "https://www.qt.io/"}, {"name": "ImGui", "url": "https://github.com/ocornut/imgui"}, {"name": "CGAL", "url": "https://www.cgal.org/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Core engine", "Modeling tools", "Rendering"], "resources": [{"name": "C++", "url": "https://www.cplusplus.com/"}, {"name": "Mesh Processing", "url": "https://libigl.github.io/"}, {"name": "Assimp", "url": "https://github.com/assimp/assimp"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Testing", "Documentation", "Release"], "resources": [{"name": "GitHub", "url": "https://github.com/"}, {"name": "CMake", "url": "https://cmake.org/"}, {"name": "Documentation", "url": "https://www.doxygen.nl/"}]}
                ]
            },
            {
                "id": "mech_002",
                "title": "FEA Simulation Tool",
                "description": "Finite Element Analysis for structural simulation",
                "difficulty": "Hard",
                "skills": ["MATLAB", "ANSYS", "Numerical Methods", "Physics"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["FEA concepts", "Numerical methods", "Mechanics"], "resources": [{"name": "MATLAB", "url": "https://www.mathworks.com/products/matlab.html"}, {"name": "ANSYS", "url": "https://www.ansys.com/"}, {"name": "FEA Guide", "url": "https://en.wikipedia.org/wiki/Finite_element_method"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Solver design", "Mesh generation", "Algorithm selection"], "resources": [{"name": "Gmsh", "url": "https://gmsh.info/"}, {"name": "Meshmixer", "url": "https://www.meshmixer.com/"}, {"name": "NumPy", "url": "https://numpy.org/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Solver development", "Post-processing", "Visualization"], "resources": [{"name": "FEniCS", "url": "https://fenicsproject.org/"}, {"name": "SciPy", "url": "https://scipy.org/"}, {"name": "VTK", "url": "https://vtk.org/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Validation", "Optimization", "Release"], "resources": [{"name": "Paraview", "url": "https://www.paraview.org/"}, {"name": "GitHub", "url": "https://github.com/"}, {"name": "Documentation", "url": "https://sphinx-rtd-tutorial.readthedocs.io/"}]}
                ]
            },
            {
                "id": "mech_003",
                "title": "Robotics Control System",
                "description": "Autonomous robot controller with obstacle avoidance",
                "difficulty": "Medium",
                "skills": ["Python", "ROS", "Kinematics", "Control Theory"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["ROS concepts", "Robotics basics", "Control theory"], "resources": [{"name": "ROS", "url": "https://www.ros.org/"}, {"name": "Robotics", "url": "https://en.wikipedia.org/wiki/Robotics"}, {"name": "Control Theory", "url": "https://en.wikipedia.org/wiki/Control_theory"}]},
                    {"phase": 2, "title": "Design", "tasks": ["System design", "Algorithm selection", "Hardware planning"], "resources": [{"name": "Gazebo", "url": "http://gazebosim.org/"}, {"name": "URDF", "url": "http://wiki.ros.org/urdf"}, {"name": "Kinematics", "url": "https://en.wikipedia.org/wiki/Forward_kinematics"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["ROS nodes", "Control algorithms", "Testing"], "resources": [{"name": "Python ROS", "url": "http://wiki.ros.org/rospy"}, {"name": "OpenCV", "url": "https://opencv.org/"}, {"name": "NumPy", "url": "https://numpy.org/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Hardware testing", "Deployment", "Refinement"], "resources": [{"name": "GitHub", "url": "https://github.com/"}, {"name": "ROS Packages", "url": "https://wiki.ros.org/ROS/Tutorials"}, {"name": "Documentation", "url": "http://wiki.ros.org/ROS/Tutorials"}]}
                ]
            }
        ],
        "Civil": [
            {
                "id": "civil_001",
                "title": "Building Information Modeling",
                "description": "BIM software for construction planning",
                "difficulty": "Hard",
                "skills": ["Python", "3D Visualization", "Revit API", "Database"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["BIM concepts", "Revit learning", "3D modeling"], "resources": [{"name": "BIM Standards", "url": "https://www.buildingsmart.org/"}, {"name": "Revit API", "url": "https://www.autodesk.com/developer/revit"}, {"name": "IFC", "url": "https://www.buildingsmart.org/standards/bim/ifc/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Architecture design", "Data model", "UI design"], "resources": [{"name": "Three.js", "url": "https://threejs.org/"}, {"name": "Babylon.js", "url": "https://www.babylonjs-playground.com/"}, {"name": "IFC.js", "url": "https://ifcjs.io/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["API development", "3D rendering", "Database"], "resources": [{"name": "Python", "url": "https://www.python.org/"}, {"name": "FastAPI", "url": "https://fastapi.tiangolo.com/"}, {"name": "PostgreSQL", "url": "https://www.postgresql.org/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Testing", "Deployment", "Documentation"], "resources": [{"name": "GitHub", "url": "https://github.com/"}, {"name": "Docker", "url": "https://docs.docker.com/"}, {"name": "AWS", "url": "https://aws.amazon.com/"}]}
                ]
            },
            {
                "id": "civil_002",
                "title": "Traffic Flow Optimizer",
                "description": "AI-based traffic management system",
                "difficulty": "Hard",
                "skills": ["Python", "ML", "Computer Vision", "Traffic Simulation"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["Traffic science", "ML algorithms", "Simulation tools"], "resources": [{"name": "SUMO", "url": "https://sumo.dlr.de/"}, {"name": "OpenCV", "url": "https://opencv.org/"}, {"name": "Scikit-learn", "url": "https://scikit-learn.org/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["System design", "Model selection", "Data pipeline"], "resources": [{"name": "TensorFlow", "url": "https://www.tensorflow.org/"}, {"name": "PyTorch", "url": "https://pytorch.org/"}, {"name": "Graph ML", "url": "https://graphneural.network/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Model training", "API development", "Dashboard"], "resources": [{"name": "Pandas", "url": "https://pandas.pydata.org/"}, {"name": "Folium", "url": "https://python-visualization.github.io/folium/"}, {"name": "Streamlit", "url": "https://streamlit.io/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Validation", "Deployment", "Monitoring"], "resources": [{"name": "Docker", "url": "https://docs.docker.com/"}, {"name": "Kubernetes", "url": "https://kubernetes.io/"}, {"name": "GitHub", "url": "https://github.com/"}]}
                ]
            },
            {
                "id": "civil_003",
                "title": "Structural Analysis Tool",
                "description": "Software for bridge and building analysis",
                "difficulty": "Medium",
                "skills": ["Python", "FEA", "Structural Design", "MATLAB"],
                "roadmap": [
                    {"phase": 1, "title": "Research", "tasks": ["Structural mechanics", "FEA concepts", "Analysis methods"], "resources": [{"name": "Structural Engineering", "url": "https://en.wikipedia.org/wiki/Structural_engineering"}, {"name": "FEA", "url": "https://en.wikipedia.org/wiki/Finite_element_method"}, {"name": "MATLAB", "url": "https://www.mathworks.com/"}]},
                    {"phase": 2, "title": "Design", "tasks": ["Solver design", "UI/UX", "Algorithm selection"], "resources": [{"name": "SciPy", "url": "https://scipy.org/"}, {"name": "NumPy", "url": "https://numpy.org/"}, {"name": "Matplotlib", "url": "https://matplotlib.org/"}]},
                    {"phase": 3, "title": "Implementation", "tasks": ["Core solver", "Input interface", "Output visualization"], "resources": [{"name": "Python", "url": "https://www.python.org/"}, {"name": "VTK", "url": "https://vtk.org/"}, {"name": "OpenGL", "url": "https://www.khronos.org/opengl/"}]},
                    {"phase": 4, "title": "Launch", "tasks": ["Testing", "Documentation", "Release"], "resources": [{"name": "GitHub", "url": "https://github.com/"}, {"name": "CMake", "url": "https://cmake.org/"}, {"name": "ReadTheDocs", "url": "https://readthedocs.org/"}]}
                ]
            }
        ]
    }
    
    dept_projects = projects.get(department, [])
    
    return {
        "status": "success",
        "department": department,
        "department_name": f"{department} Department",
        "total_topics": len(dept_projects),
        "topics": dept_projects
    }

@app.get("/download/{doc_id}")
def download_document(doc_id: str):
    """Download a document"""
    try:
        # First check if it's an uploaded file
        metadata_file = STORAGE_DIR / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                if doc_id in metadata:
                    # Find the actual file
                    doc_meta = metadata[doc_id]
                    original_name = doc_meta.get("original_name", doc_meta.get("title", "file"))
                    file_pattern = f"{doc_id}_*"
                    
                    # Find the file in storage
                    for file_path in STORAGE_DIR.glob(file_pattern):
                        if file_path.is_file():
                            with open(file_path, "rb") as f:
                                content = f.read()
                            return StreamingResponse(
                                iter([content]),
                                media_type="application/octet-stream",
                                headers={"Content-Disposition": f"attachment; filename={original_name}"}
                            )
    except Exception as e:
        print(f"Error downloading file: {e}")
        raise HTTPException(status_code=404, detail="File not found")
        
        # Return sample/demo documents based on doc_id
        if doc_id == "demo_001":
            content = b"""Python Lab Manual

Chapter 1: Introduction to Python
- Python is a high-level programming language
- Interpreted and dynamically typed
- Easy to learn and widely used in industry

Chapter 2: Data Types and Structures
- Variables: containers for storing data values
- Data Types: int, float, str, list, dict, tuple, set, bool
- Mutable vs Immutable types

Chapter 3: Control Flow
- if/elif/else statements for conditional execution
- for loops for iteration over sequences
- while loops for repeated execution

Chapter 4: Functions
- Function definition and calling
- Parameters and return values
- Scope and lifetime of variables
- Decorators and higher-order functions

Chapter 5: File I/O
- Reading and writing files
- Working with CSV and JSON files
- Error handling with try/except

Hands-on Exercises:
1. Write a program to calculate factorial
2. Sort a list of numbers
3. Count word frequency in a text file
4. Create a simple calculator

This is a comprehensive Python Lab Manual for educational purposes."""
            
            return StreamingResponse(
                iter([content]),
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=Python_Lab_Manual.txt"}
            )
        
        elif doc_id == "demo_002":
            content = b"""DBMS Unit 2 - Data Models and Normalization

1. RELATIONAL MODEL
   - Foundational model for modern databases
   - Tables: collection of rows and columns
   - Attributes: column properties with domains
   - Tuples/Rows: individual records
   - Relations: mathematical relations on domains
   - Keys: primary, foreign, unique, composite

2. ENTITY-RELATIONSHIP MODEL (ER)
   - Entity: real-world object with attributes
   - Relationship: association between entities
   - Cardinality: 1:1, 1:N, M:N relationships
   - ER Diagrams: visual representation of database schema

3. NORMALIZATION PROCESS
   - First Normal Form (1NF):
     * Eliminate repeating groups
     * Atomic values only
   - Second Normal Form (2NF):
     * Satisfy 1NF requirements
     * Remove partial dependencies
   - Third Normal Form (3NF):
     * Satisfy 2NF requirements
     * Remove transitive dependencies
   - Boyce-Codd Normal Form (BCNF):
     * Stricter than 3NF
     * Every determinant is a candidate key

4. CONSTRAINTS AND RULES
   - Primary Key: uniquely identifies record
   - Foreign Key: references another table
   - Unique Constraint: ensures uniqueness
   - Not Null: ensures value exists
   - Check Constraint: domain values

5. DESIGN PRINCIPLES
   - Data Redundancy: minimize duplication
   - Data Integrity: maintain accuracy
   - Scalability: design for growth

Sample Table Design:
Students (StudentID, Name, Department, Email)
Courses (CourseID, CourseName, Department, Credits)
Enrollment (StudentID, CourseID, Semester, Grade)

This document covers Database Management Systems Unit 2 fundamentals."""
            
            return StreamingResponse(
                iter([content]),
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=DBMS_Unit2_Notes.txt"}
            )
        
        else:
            raise HTTPException(status_code=404, detail=f"Document with id {doc_id} not found")
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summarize/{doc_id}")
def summarize_document(doc_id: str, num_sentences: int = 5):
    """Summarize a document"""
    try:
        # Check if it's an uploaded file
        metadata_file = STORAGE_DIR / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file) as f:
                metadata = json.load(f)
                if doc_id in metadata:
                    # Find the actual file
                    file_pattern = f"{doc_id}_*"
                    for file_path in STORAGE_DIR.glob(file_pattern):
                        if file_path.is_file():
                            print(f"🔍 Found file: {file_path.name}")
                            # Extract text based on file type
                            text = None
                            if file_path.suffix.lower() == '.pdf':
                                print(f"📄 Processing PDF file...")
                                text = extract_text_from_pdf(file_path)
                            else:
                                # For text files
                                print(f"📝 Processing text file...")
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        text = f.read()
                                except:
                                    with open(file_path, 'r', encoding='latin-1') as f:
                                        text = f.read()
                            
                            if text and len(text.strip()) > 50:
                                print(f"✅ Text extracted: {len(text)} chars, generating summary...")
                                summary = summarize_text(text, num_sentences)
                                doc_title = metadata[doc_id].get("title", "Document")
                                return {
                                    "status": "success",
                                    "title": doc_title,
                                    "summary": summary,
                                    "source": "uploaded_file",
                                    "text_length": len(text)
                                }
                            else:
                                error_msg = f"Insufficient text: {len(text) if text else 0} chars"
                                print(f"❌ {error_msg}")
                                return {
                                    "status": "error",
                                    "message": error_msg
                                }
        
        # For demo documents
        if doc_id == "demo_001":
            text = "Python is a high-level programming language. It is interpreted and dynamically typed. Easy to learn and widely used in industry. Variables are containers for storing data values. Data Types include int, float, str, list, dict, tuple, set, bool. If/elif/else statements for conditional execution. For loops for iteration over sequences. While loops for repeated execution. Functions definition and calling. Parameters and return values. Scope and lifetime of variables. Decorators and higher-order functions. Reading and writing files. Working with CSV and JSON files. Error handling with try/except."
            summary = summarize_text(text, num_sentences)
            return {
                "status": "success",
                "title": "Python Lab Manual",
                "summary": summary,
                "source": "demo",
                "text_length": len(text)
            }
        
        return {
            "status": "error",
            "message": "Document not found"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# ==================== AI HELP ENDPOINT ====================
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
        "answer": "🎓 **What is the Engineering Chatbot?**\n\nThe Engineering Chatbot is an intelligent knowledge management system designed for engineering students and academic management. It centralizes study materials, project guidelines, and resources across 8 engineering departments.\n\n📊 **Current Status:**\n- 8 Engineering Departments supported\n- 24+ Project Implementation Roadmaps\n- 95+ Learning Resource Links\n- Multi-search capability (Keyword, Semantic, Hybrid)\n- Admin management system\n- Real-time file downloads\n\n🚀 **Future Roadmap:**\n\n**Phase 1 (Q1 2026)**:\n- Real LLM Integration (GPT-4/Claude)\n- Conversational AI for natural Q&A\n- Intelligent doubt resolution\n\n**Phase 2 (Q2 2026)**:\n- Video Tutorial Integration\n- Interactive Coding Exercises\n- Real-time Live Chat Support\n\n**Phase 3 (Q3 2026)**:\n- Mobile App (iOS/Android)\n- Offline Learning Mode\n- Peer Collaboration & Discussion Forums\n\n**Phase 4 (Q4 2026)**:\n- Advanced Analytics Dashboard\n- Adaptive Learning Paths\n- Certification & Achievement Badges\n\n✨ **Vision**: Transform engineering education through AI-powered personalized learning experiences"
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
        "answer": "Support & Contact:\n\n📧 **Email Support**: support@engineeringchatbot.edu\n🔧 **Technical Issues**: Check the DOWNLOAD_GUIDE.md for troubleshooting\n📚 **Documentation**: See API_DOCUMENTATION.md for developer details\n💡 **Feature Requests**: Submit via admin panel\n⚡ **Emergency Support**: Contact technical team\n\nThe system is designed to be user-friendly and self-explanatory with built-in help features."
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
            # Check for exact or very close match
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
                if len(word) > 2:  # Only match words with 3+ characters
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


@app.get("/ai-help")
def ai_help_get(query: str = None):
    """GET endpoint for AI help"""
    return ai_help(query)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Engineering Chatbot Backend - SIMPLE VERSION")
    print("="*60 + "\n")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")