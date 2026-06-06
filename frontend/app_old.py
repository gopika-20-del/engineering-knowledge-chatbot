"""Streamlit UI for Engineering Chatbot - Unified Dashboard"""

import streamlit as st
import requests
import json
from pathlib import Path
from typing import Optional
import time

# Page configuration
st.set_page_config(
    page_title="Engineering Chatbot - Unified Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styling
st.markdown("""
<style>
    .main {background-color: #f5f5f5;}
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 5px;
    }
    .header-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# API Base URL
API_BASE_URL = "http://localhost:8000"

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ==================== Helper Functions ====================
@st.cache_resource
def get_config():
    """Fetch chatbot configuration"""
    try:
        response = requests.get(f"{API_BASE_URL}/config", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    return {
        "departments": ["CSE", "IT", "AI&DS", "CSBS", "ECE", "EEE", "Mechanical", "Civil"],
        "semesters": list(range(1, 9)),
        "max_file_size_mb": 50
    }

def perform_search(query: str, search_type: str, department: Optional[str] = None, 
                  semester: Optional[int] = None):
    """Perform search via API"""
    try:
        params = {
            "query": query,
            "search_type": search_type
        }
        if department:
            params["department"] = department
        if semester:
            params["semester"] = semester
        
        response = requests.get(f"{API_BASE_URL}/search", params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e), "results": []}
    
    return {"status": "error", "message": "Search failed", "results": []}

def get_subject_materials(department: str, semester: int, subject: str):
    """Get all materials for a subject"""
    try:
        params = {
            "department": department,
            "semester": semester,
            "subject": subject
        }
        response = requests.get(f"{API_BASE_URL}/subject-materials", params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    return {"status": "error", "message": "Failed to fetch materials"}

def download_document(doc_id: str):
    """Download a document"""
    try:
        response = requests.get(f"{API_BASE_URL}/download/{doc_id}", timeout=30)
        if response.status_code == 200:
            return response.content, response.headers.get("content-disposition")
    except Exception as e:
        st.error(f"Download failed: {str(e)}")
    
    return None, None

def upload_document(file, department: str, semester: int, subject: str, 
                   title: str, keywords: str, admin_key: str):
    """Upload a document"""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {
            "department": department,
            "semester": semester,
            "subject": subject,
            "title": title or file.name,
            "keywords": keywords,
            "admin_key": admin_key
        }
        
        response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": response.json().get("detail", "Upload failed")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== Main App ====================
def main():
    """Main application - Unified Dashboard"""
    
    # Get configuration
    config = get_config()
    departments = config.get("departments", [])
    semesters = config.get("semesters", [])
    
    # ==================== HEADER ====================
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; margin-bottom: 20px;'>
        <h1 style='margin: 0; text-align: center;'>🎓 Engineering Chatbot Platform</h1>
        <p style='text-align: center; margin: 10px 0 0 0; font-size: 16px;'>Complete Academic Resource Hub</p>
        <p style='text-align: center; margin: 5px 0 0 0; font-size: 12px;'>Search Materials • Browse Projects • Download Resources • Manage Content</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== TOP STATS ====================
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📚 Departments", "8", "+95 Projects")
    with col2:
        st.metric("📖 Semesters", "1-8", "Configured")
    with col3:
        st.metric("📄 Documents", "4", "Indexed")
    with col4:
        st.metric("🎯 Projects", "95+", "Available")
    with col5:
        st.metric("🔍 Search", "Hybrid", "Mode")
    
    st.divider()
    
    # ==================== MAIN LAYOUT ====================
    # Left Sidebar with Settings
    sidebar_col, main_col = st.columns([1, 3.5], gap="large")
    
    with sidebar_col:
        st.subheader("⚙️ Settings")
        
        selected_dept = st.selectbox(
            "📚 Department",
            options=departments,
            key="selected_dept"
        )
        
        selected_sem = st.selectbox(
            "📖 Semester",
            options=semesters,
            key="selected_sem"
        )
        
        search_type = st.radio(
            "🔍 Search Type",
            options=["Hybrid", "Semantic", "Keyword"],
            key="search_type"
        )
        
        st.divider()
        
        # Admin Login
        st.subheader("🔐 Admin")
        admin_password = st.text_input("Password", type="password", key="admin_pwd")
        
        if admin_password == "admin123":
            st.session_state.is_admin = True
            st.success("✅ Admin Mode")
        elif admin_password:
            st.error("❌ Invalid")
            st.session_state.is_admin = False
        
        st.divider()
        
        # Quick Links
        st.subheader("📌 Quick Links")
        if st.button("📊 View All Documents"):
            try:
                response = requests.get(f"{API_BASE_URL}/documents")
                if response.status_code == 200:
                    docs = response.json()
                    st.info(f"Total Documents: {docs.get('count', 0)}")
            except:
                st.error("Failed to fetch")
    
    with main_col:
        # Create tabs for main content
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔎 Search",
            "📁 Materials",
            "💡 Projects",
            "⬆️ Upload",
            "📊 Dashboard"
        ])
        
        # ==================== TAB 1: SEARCH ====================
        with tab1:
            st.subheader("🔎 Search Study Materials")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                search_query = st.text_input(
                    "Enter search query",
                    placeholder="e.g., 'Python', 'DBMS', 'lab manual'",
                    key="search_query"
                )
            with col2:
                search_button = st.button("🔍 Search", use_container_width=True)
            
            if search_button and search_query:
                with st.spinner("🔍 Searching..."):
                    result = perform_search(
                        query=search_query,
                        search_type=search_type.lower(),
                        department=selected_dept,
                        semester=selected_sem
                    )
                
                if result.get("status") == "success":
                    results = result.get("results", [])
                    
                    if results:
                        st.success(f"✅ Found {len(results)} result(s) in {result.get('search_time_ms', 'N/A')}ms")
                        
                        for i, doc in enumerate(results, 1):
                            with st.container():
                                # Header
                                col1, col2 = st.columns([4, 1])
                                with col1:
                                    st.markdown(f"### {i}. {doc['title']}")
                                    st.caption(f"📍 {doc['department']} • Sem {doc['semester']} • {doc['subject']}")
                                with col2:
                                    if doc.get('downloadable'):
                                        if st.button(f"⬇️ Download", key=f"download_{i}", help="Download file"):
                                            content, _ = download_document(doc['doc_id'])
                                            if content:
                                                st.download_button(
                                                    "Save File",
                                                    data=content,
                                                    file_name=f"{doc['title']}{doc['file_type']}",
                                                    key=f"save_{i}"
                                                )
                                
                                # Metrics
                                m1, m2, m3 = st.columns(3)
                                with m1:
                                    st.metric("Type", doc.get('file_type', 'N/A'))
                                with m2:
                                    st.metric("Relevance", f"{doc.get('relevance_score', 0):.0%}")
                                with m3:
                                    st.metric("Content", "Preview")
                                
                                # Preview
                                st.write(f"**Preview:** {doc.get('snippet', 'N/A')}")
                                
                                # Assignments
                                assignments = doc.get('assignments', [])
                                if assignments:
                                    st.subheader("📋 Assignment Topics")
                                    for j, assignment in enumerate(assignments, 1):
                                        st.write(f"{j}. {assignment}")
                                
                                st.divider()
                    else:
                        st.warning("⚠️ No results found")
                else:
                    st.error(f"❌ {result.get('message')}")
        
        # ==================== TAB 2: MATERIALS ====================
        with tab2:
            st.subheader("📁 Browse by Subject")
            
            subject = st.text_input(
                "Subject Name",
                placeholder="e.g., 'Database Management Systems'",
                key="subject_input"
            )
            
            if st.button("📚 Get Materials"):
                if subject:
                    with st.spinner("Loading..."):
                        result = get_subject_materials(selected_dept, selected_sem, subject)
                    
                    if result.get("status") == "success":
                        materials = result.get("materials", {})
                        total = result.get("total_count", 0)
                        
                        st.success(f"✅ Found {total} material(s)")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("📝 Notes", len(materials.get('notes', [])))
                        with col2:
                            st.metric("🧪 Labs", len(materials.get('lab_manuals', [])))
                        with col3:
                            st.metric("📄 Papers", len(materials.get('question_papers', [])))
                        with col4:
                            st.metric("📌 Others", len(materials.get('others', [])))
                    else:
                        st.warning(f"⚠️ {result.get('message')}")
                else:
                    st.warning("⚠️ Enter subject name")
        
        # ==================== TAB 3: PROJECTS ====================
        with tab3:
            st.subheader("💡 Project Topics")
            
            try:
                response = requests.get(f"{API_BASE_URL}/project-topics", timeout=5)
                if response.status_code == 200:
                    topics_data = response.json()
                    
                    st.info(f"📚 Total Departments: {topics_data.get('total_departments')} | 💼 Total Projects: {topics_data.get('total_projects')}")
                    
                    dept_options = topics_data.get("departments", {})
                    selected_project_dept = st.selectbox(
                        "Select Department",
                        options=list(dept_options.keys()),
                        format_func=lambda x: f"{x}: {dept_options[x]['name']}",
                        key="project_dept"
                    )
                    
                    if st.button("📖 View Topics", key="view_topics"):
                        with st.spinner("Loading..."):
                            topic_response = requests.get(
                                f"{API_BASE_URL}/project-topics/{selected_project_dept}",
                                timeout=5
                            )
                            
                            if topic_response.status_code == 200:
                                dept_data = topic_response.json()
                                
                                st.success(f"✅ {dept_data.get('department_name')}")
                                st.metric("Total Projects", dept_data.get("total_topics", 0))
                                
                                st.divider()
                                
                                topics = dept_data.get("topics", [])
                                
                                if topics:
                                    difficulty_levels = sorted(list(set(t.get("difficulty", "Unknown") for t in topics)))
                                    
                                    if len(difficulty_levels) > 1:
                                        diff_tabs = st.tabs([f"📊 {d}" for d in difficulty_levels])
                                        
                                        for diff_idx, diff_level in enumerate(difficulty_levels):
                                            with diff_tabs[diff_idx]:
                                                diff_topics = [t for t in topics if t.get("difficulty") == diff_level]
                                                
                                                for topic in diff_topics:
                                                    with st.expander(f"**{topic['id']}: {topic['title']}**"):
                                                        st.write(f"**Description:** {topic['description']}")
                                                        
                                                        st.write("**Skills Required:**")
                                                        for skill in topic.get('skills', []):
                                                            st.write(f"🛠️ {skill}")
                                                        
                                                        st.markdown(f"**Difficulty:** `{topic['difficulty']}`")
                                    else:
                                        for idx, topic in enumerate(topics, 1):
                                            with st.expander(f"**{idx}. {topic['title']}** ({topic.get('difficulty')})", expanded=False):
                                                st.write(f"**Description:** {topic['description']}")
                                                
                                                st.write("**Skills Required:**")
                                                for skill in topic.get('skills', []):
                                                    st.write(f"🛠️ {skill}")
                                                
                                                st.markdown(f"**Difficulty:** `{topic['difficulty']}`")
                            else:
                                st.error("Failed to load topics")
                else:
                    st.error("Failed to fetch project topics")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # ==================== TAB 4: UPLOAD ====================
        with tab4:
            if st.session_state.is_admin:
                st.subheader("📤 Upload Materials")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    uploaded_file = st.file_uploader(
                        "Choose file",
                        type=["pdf", "docx", "doc", "txt", "pptx"],
                        key="file_uploader"
                    )
                    
                    title = st.text_input("Title", key="doc_title")
                    keywords = st.text_area("Keywords", key="doc_keywords")
                
                with col2:
                    dept = st.selectbox("Department", departments, key="upload_dept")
                    sem = st.selectbox("Semester", semesters, key="upload_sem")
                    subject = st.text_input("Subject", key="upload_subject")
                
                if st.button("⬆️ Upload"):
                    if uploaded_file and title and subject:
                        with st.spinner("⏳ Uploading..."):
                            result = upload_document(
                                file=uploaded_file,
                                department=dept,
                                semester=sem,
                                subject=subject,
                                title=title,
                                keywords=keywords,
                                admin_key="admin123"
                            )
                        
                        if result.get("status") == "success":
                            st.success(f"✅ {result.get('message')}")
                        else:
                            st.error(f"❌ {result.get('message')}")
                    else:
                        st.warning("⚠️ Fill all fields")
            else:
                st.warning("🔐 Admin access required")
        
        # ==================== TAB 5: DASHBOARD ====================
        with tab5:
            st.subheader("📊 System Dashboard")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 Statistics")
                st.info("""
                **System Overview:**
                - 8 Departments Configured
                - 8 Semesters (1-8)
                - 4 Documents Indexed
                - 95+ Projects Available
                - Hybrid Search Enabled
                """)
            
            with col2:
                st.markdown("### 🎯 Features")
                st.success("""
                **Active Features:**
                - ✅ Semantic Search
                - ✅ Document Download
                - ✅ Assignment Topics
                - ✅ Project Browse
                - ✅ Admin Upload
                - ✅ Material Filter
                """)
            
            st.divider()
            
            st.markdown("### 📚 Available Departments")
            dept_cols = st.columns(4)
            dept_list = ["CSE", "IT", "AI&DS", "CSBS", "ECE", "EEE", "Mechanical", "Civil"]
            
            for idx, dept in enumerate(dept_list):
                with dept_cols[idx % 4]:
                    st.info(f"### {dept}\n10+ Projects")
            
            st.divider()
            
            st.markdown("### 🔍 Quick Search Tips")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Semantic Search**")
                st.write("Find similar concepts")
            
            with col2:
                st.write("**Keyword Search**")
                st.write("Exact word matching")
            
            with col3:
                st.write("**Hybrid Search**")
                st.write("Combined approach")

if __name__ == "__main__":
    main()
