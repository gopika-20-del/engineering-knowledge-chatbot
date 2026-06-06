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
</style>
""", unsafe_allow_html=True)

# API Base URL
API_BASE_URL = "http://localhost:8000"

# Session state
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

def perform_search(query: str, search_type: str, department: Optional[str] = None, semester: Optional[int] = None):
    try:
        params = {"query": query, "search_type": search_type}
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
    try:
        response = requests.get(f"{API_BASE_URL}/subject-materials", 
            params={"department": department, "semester": semester, "subject": subject}, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "error", "message": "Failed to fetch materials"}

def download_document(doc_id: str):
    try:
        response = requests.get(f"{API_BASE_URL}/download/{doc_id}", timeout=30)
        if response.status_code == 200:
            return response.content, response.headers.get("content-disposition")
    except Exception as e:
        st.error(f"Download failed: {str(e)}")
    return None, None

def upload_document(file, department: str, semester: int, subject: str, title: str, keywords: str, admin_key: str):
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {"department": department, "semester": semester, "subject": subject, 
                "title": title or file.name, "keywords": keywords, "admin_key": admin_key}
        response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "message": response.json().get("detail", "Upload failed")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== Main App ====================
def main():
    config = get_config()
    departments = config.get("departments", [])
    semesters = config.get("semesters", [])
    
    # Initialize session state for summary display
    if "last_search_results" not in st.session_state:
        st.session_state.last_search_results = None
    if "summaries" not in st.session_state:
        st.session_state.summaries = {}
    
    # HEADER
    st.markdown("""<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; color: white; margin-bottom: 20px;'>
        <h1 style='margin: 0; text-align: center;'>🎓 Engineering Chatbot Platform</h1>
        <p style='text-align: center; margin: 10px 0 0 0; font-size: 16px;'>Complete Academic Resource Hub</p>
        <p style='text-align: center; margin: 5px 0 0 0; font-size: 12px;'>Search Materials • Browse Projects • Download Resources • Manage Content</p>
    </div>""", unsafe_allow_html=True)
    
    # STATS
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
    
    # LAYOUT
    sidebar_col, main_col = st.columns([1, 3.5], gap="large")
    
    with sidebar_col:
        st.subheader("⚙️ Settings")
        
        selected_dept = st.selectbox("📚 Department", options=departments, key="selected_dept")
        selected_sem = st.selectbox("📖 Semester", options=semesters, key="selected_sem")
        search_type = st.radio("🔍 Search Type", options=["Hybrid", "Semantic", "Keyword"], key="search_type")
        
        st.divider()
        
        st.subheader("🔐 Admin")
        admin_password = st.text_input("Password", type="password", key="admin_pwd")
        
        if admin_password == "admin123":
            st.session_state.is_admin = True
            st.success("✅ Admin Mode")
        elif admin_password:
            st.error("❌ Invalid")
            st.session_state.is_admin = False
    
    with main_col:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔎 Search", "📁 Materials", "💡 Projects", "⬆️ Upload", "📊 Dashboard", "🤖 AI Help"])
        
        # TAB 1: SEARCH
        with tab1:
            st.subheader("🔎 Search Study Materials")
            col1, col2 = st.columns([4, 1])
            with col1:
                search_query = st.text_input("Enter search query", placeholder="e.g., 'Python', 'DBMS', 'lab manual'", key="search_query")
            with col2:
                search_button = st.button("🔍 Search", use_container_width=True)
            
            if search_button and search_query:
                with st.spinner("🔍 Searching..."):
                    result = perform_search(query=search_query, search_type=search_type.lower(), 
                                          department=selected_dept, semester=selected_sem)
                
                if result.get("status") == "success":
                    results = result.get("results", [])
                    st.session_state.last_search_results = results
                    st.session_state.summaries = {}
            
            # Display stored search results
            if st.session_state.last_search_results:
                results = st.session_state.last_search_results
                if results:
                    st.success(f"✅ Found {len(results)} result(s)")
                    for i, doc in enumerate(results, 1):
                        col1, col2, col3 = st.columns([3.5, 0.75, 0.75])
                        with col1:
                            st.markdown(f"### {i}. {doc['title']}")
                            st.caption(f"📍 {doc.get('department', 'N/A')} • Sem {doc.get('semester', 'N/A')} • {doc.get('subject', 'General')}")
                        with col2:
                            if doc.get('downloadable'):
                                try:
                                    response = requests.get(f"{API_BASE_URL}/download/{doc.get('doc_id')}", timeout=30)
                                    if response.status_code == 200:
                                        filename = doc.get('title', 'document').replace(" ", "_")
                                        file_ext = doc.get('file_type', '.txt')
                                        st.download_button(
                                            label="⬇️ Download",
                                            data=response.content,
                                            file_name=f"{filename}{file_ext}",
                                            mime="text/plain",
                                            key=f"download_{i}"
                                        )
                                    else:
                                        st.error("❌ File not found")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        with col3:
                            if st.button("📝 Summary", key=f"summary_{i}", use_container_width=True):
                                with st.spinner("🔄 Generating summary..."):
                                    try:
                                        summary_response = requests.get(f"{API_BASE_URL}/summarize/{doc.get('doc_id')}?num_sentences=5", timeout=30)
                                        if summary_response.status_code == 200:
                                            summary_data = summary_response.json()
                                            if summary_data.get("status") == "success":
                                                st.session_state.summaries[doc.get('doc_id')] = summary_data.get('summary')
                                                st.success("✅ Summary Generated! Scroll down to view →")
                                        else:
                                            st.error("❌ Could not generate summary")
                                    except Exception as e:
                                        st.error(f"❌ Error: {str(e)}")
                        
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("Type", doc.get('file_type', 'N/A'))
                        with m2:
                            st.metric("Relevance", f"{doc.get('relevance_score', 0):.0%}")
                        with m3:
                            st.metric("Status", "Available")
                            
                        st.write(f"**Preview:** {doc.get('snippet', 'N/A')}")
                        
                        # Display summary in prominent box if it exists
                        if doc.get('doc_id') in st.session_state.summaries:
                            st.markdown("---")
                            st.markdown("### 📄 Summary")
                            with st.container():
                                st.info(st.session_state.summaries[doc.get('doc_id')])
                            st.markdown("---")
                        
                        assignments = doc.get('assignments', [])
                        if assignments:
                            st.subheader("📋 Assignment Topics")
                            for j, assignment in enumerate(assignments, 1):
                                st.write(f"{j}. {assignment}")
                        
                        related_projects = doc.get('related_projects', [])
                        if related_projects:
                            st.subheader("📚 Related Projects")
                            for project in related_projects:
                                difficulty_emoji = "🟢" if project.get('difficulty') == 'Easy' else "🟡" if project.get('difficulty') == 'Medium' else "🔴"
                                st.write(f"{difficulty_emoji} **{project.get('title')}** ({project.get('difficulty')})")
                                st.caption(f"Project ID: {project.get('id')}")
                        
                        st.divider()
                    else:
                        st.warning("⚠️ No results found")
                else:
                    st.error(f"❌ {result.get('message')}")
        
        # TAB 2: MATERIALS
        with tab2:
            st.subheader("📁 Browse by Subject")
            subject = st.text_input("Subject Name", placeholder="e.g., 'Database Management Systems'", key="subject_input")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📚 Get Materials"):
                    if subject:
                        st.success(f"✅ Searching for: {subject}")
                    else:
                        st.warning("⚠️ Enter subject name")
            
            with col2:
                if st.button("🌐 Search Online"):
                    if subject:
                        # Open Google search for the subject
                        google_url = f"https://www.google.com/search?q={subject}+tutorial"
                        st.markdown(f"[🔗 Open Google Search in New Tab]({google_url})")
                    else:
                        st.warning("⚠️ Enter subject name")
            
            with col3:
                if st.button("📖 Learn More"):
                    if subject:
                        # Multiple resource options
                        st.markdown("### 📚 Learning Resources:")
                        col_res1, col_res2, col_res3 = st.columns(3)
                        
                        with col_res1:
                            youtube_url = f"https://www.youtube.com/results?search_query={subject}"
                            st.markdown(f"[📺 YouTube]({youtube_url})")
                        
                        with col_res2:
                            wiki_url = f"https://en.wikipedia.org/w/index.php?search={subject}"
                            st.markdown(f"[📖 Wikipedia]({wiki_url})")
                        
                        with col_res3:
                            udemy_url = f"https://www.udemy.com/courses/search/?q={subject}"
                            st.markdown(f"[🎓 Udemy]({udemy_url})")
                    else:
                        st.warning("⚠️ Enter subject name")
        
        # TAB 3: PROJECTS
        with tab3:
            st.subheader("💡 Project Topics")
            try:
                response = requests.get(f"{API_BASE_URL}/project-topics", timeout=5)
                if response.status_code == 200:
                    topics_data = response.json()
                    st.info(f"📚 Departments: {topics_data.get('total_departments')} | 💼 Projects: {topics_data.get('total_projects')}")
                    
                    dept_options = topics_data.get("departments", {})
                    selected_project_dept = st.selectbox("Select Department",
                        options=list(dept_options.keys()),
                        format_func=lambda x: f"{x}: {dept_options[x]['name']}",
                        key="project_dept")
                    
                    if st.button("📖 View Topics", key="view_topics"):
                        with st.spinner("Loading..."):
                            topic_response = requests.get(f"{API_BASE_URL}/project-topics/{selected_project_dept}", timeout=5)
                            if topic_response.status_code == 200:
                                dept_data = topic_response.json()
                                st.success(f"✅ {dept_data.get('department_name')}")
                                st.metric("Total Projects", dept_data.get("total_topics", 0))
                                st.divider()
                                
                                topics = dept_data.get("topics", [])
                                for idx, topic in enumerate(topics, 1):
                                    with st.expander(f"**{idx}. {topic['title']}** ({topic.get('difficulty')})"):
                                        st.write(f"**Description:** {topic['description']}")
                                        st.write("**Skills Required:**")
                                        for skill in topic.get('skills', []):
                                            st.write(f"🛠️ {skill}")
                                        
                                        # Implementation Roadmap
                                        if topic.get('roadmap'):
                                            st.divider()
                                            st.subheader("🗓️ Implementation Roadmap")
                                            
                                            roadmap = topic.get('roadmap', [])
                                            cols = st.columns(len(roadmap))
                                            
                                            for col_idx, (col, phase) in enumerate(zip(cols, roadmap)):
                                                with col:
                                                    # Phase Header
                                                    st.markdown(f"### 📍 Phase {phase['phase']}")
                                                    st.markdown(f"**{phase['title'].split('(')[0].strip()}**")
                                                    
                                                    # Tasks
                                                    st.markdown("**Tasks:**")
                                                    for task in phase.get('tasks', []):
                                                        st.markdown(f"• {task}")
                                                    
                                                    # Resources
                                                    st.markdown("**Resources:**")
                                                    resources = phase.get('resources', [])
                                                    if resources:
                                                        for idx, resource in enumerate(resources, 1):
                                                            st.markdown(f"[{idx}. {resource['name']}]({resource['url']})")
                                                    else:
                                                        st.info("No resources available")
                            else:
                                st.error("Failed to load topics")
                else:
                    st.error("Failed to fetch project topics")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # TAB 4: UPLOAD
        with tab4:
            if st.session_state.is_admin:
                st.subheader("📤 Upload Materials")
                col1, col2 = st.columns(2)
                
                with col1:
                    uploaded_file = st.file_uploader("Choose file", 
                        type=["pdf", "docx", "doc", "txt", "pptx"], key="file_uploader")
                    title = st.text_input("Title", key="doc_title")
                    keywords = st.text_area("Keywords", key="doc_keywords")
                
                with col2:
                    dept = st.selectbox("Department", departments, key="upload_dept")
                    sem = st.selectbox("Semester", semesters, key="upload_sem")
                    subject = st.text_input("Subject", key="upload_subject")
                
                if st.button("⬆️ Upload"):
                    if uploaded_file and title and subject:
                        with st.spinner("⏳ Uploading..."):
                            result = upload_document(file=uploaded_file, department=dept, semester=sem,
                                                    subject=subject, title=title, keywords=keywords, admin_key="admin123")
                        if result.get("status") == "success":
                            st.success(f"✅ {result.get('message')}")
                        else:
                            st.error(f"❌ {result.get('message')}")
                    else:
                        st.warning("⚠️ Fill all fields")
            else:
                st.warning("🔐 Admin access required")
        
        # TAB 5: DASHBOARD
        with tab5:
            st.subheader("📊 System Dashboard")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📈 Statistics")
                st.info("""**System Overview:**
                - 8 Departments
                - 8 Semesters (1-8)
                - 4 Documents
                - 95+ Projects
                - Hybrid Search""")
            
            with col2:
                st.markdown("### 🎯 Features")
                st.success("""**Active Features:**
                - ✅ Semantic Search
                - ✅ Document Download
                - ✅ Assignment Topics
                - ✅ Project Browse
                - ✅ Admin Upload""")
            
            st.divider()
            
            st.markdown("### 📚 Available Departments")
            dept_cols = st.columns(4)
            dept_list = ["CSE", "IT", "AI&DS", "CSBS", "ECE", "EEE", "Mechanical", "Civil"]
            
            for idx, dept in enumerate(dept_list):
                with dept_cols[idx % 4]:
                    st.info(f"### {dept}\n10+ Projects")
        
        # TAB 6: AI HELP
        with tab6:
            # Custom CSS for AI Help
            st.markdown("""
            <style>
            .ai-help-container {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 10px;
                color: white;
                margin-bottom: 20px;
            }
            .ai-help-title {
                font-size: 28px;
                font-weight: bold;
                margin: 0;
                padding: 0;
            }
            .ai-help-subtitle {
                font-size: 16px;
                opacity: 0.9;
                margin-top: 8px;
            }
            .question-box {
                background-color: #f0f4ff;
                border-left: 4px solid #667eea;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                color: #1a1a1a;
                font-size: 15px;
            }
            .answer-box {
                background-color: #fff9e6;
                border-left: 4px solid #ffc107;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
                line-height: 1.8;
                color: #1a1a1a;
                font-size: 15px;
                font-weight: 500;
            }
            .category-button {
                background-color: #667eea;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                border: none;
                margin: 5px;
                cursor: pointer;
                font-weight: 500;
            }
            .match-badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                margin: 5px 0;
            }
            .exact-match {
                background-color: #d4edda;
                color: #155724;
            }
            .keyword-match {
                background-color: #cfe2ff;
                color: #084298;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Header Section
            st.markdown("""
            <div class="ai-help-container">
                <div class="ai-help-title">🤖 AI Assistant</div>
                <div class="ai-help-subtitle">Ask me anything about the Engineering Chatbot. I'm here to help students and management!</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Search Section
            st.markdown("### 💬 Ask Your Question")
            col1, col2 = st.columns([4, 1])
            with col1:
                user_question = st.text_input(
                    "What would you like to know?",
                    placeholder="e.g., How do I download materials? What are the future plans?",
                    key="ai_question"
                )
            with col2:
                ask_button = st.button("🔍 Ask", use_container_width=True, key="ask_btn")
            
            # Handle Ask Button
            if ask_button and user_question:
                with st.spinner("🤔 Thinking..."):
                    try:
                        response = requests.post(f"{API_BASE_URL}/ai-help", params={"query": user_question}, timeout=10)
                        if response.status_code == 200:
                            result = response.json()
                            
                            # Question Display
                            st.markdown(f"""
                            <div class="question-box">
                                <strong>Your Question:</strong><br/>
                                {result.get('question', user_question)}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Match Type Badge
                            match_type = result.get('type', 'unknown')
                            if match_type == 'exact_match':
                                st.markdown('<span class="match-badge exact-match">✓ Exact Match</span>', unsafe_allow_html=True)
                            elif match_type == 'keyword_match':
                                confidence = result.get('confidence', '50%')
                                st.markdown(f'<span class="match-badge keyword-match">≈ Keyword Match ({confidence})</span>', unsafe_allow_html=True)
                            
                            # Answer Display
                            answer_text = result.get('answer', 'No answer found')
                            st.markdown(f"""
                            <div class="answer-box">
                                <strong>Answer:</strong><br/>
                                {answer_text}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Related Questions
                            if result.get('suggestions'):
                                st.markdown("---")
                                st.markdown("### 💡 Related Questions You Might Ask:")
                                suggestion_cols = st.columns(len(result.get('suggestions', [])[:3]))
                                for idx, (col, suggestion) in enumerate(zip(suggestion_cols, result.get('suggestions', [])[:3])):
                                    with col:
                                        if st.button(suggestion, key=f"suggestion_{idx}", use_container_width=True):
                                            st.session_state.ai_question = suggestion
                                            st.rerun()
                        else:
                            st.error("❌ Failed to get response from AI")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            # Divider
            st.divider()
            
            # Quick Questions Section
            st.markdown("### 📚 Quick Questions")
            st.markdown("**Click any question below to get instant answers:**")
            
            categories = {
                "Getting Started": [
                    "What is the Engineering Chatbot?",
                    "How do I use the Engineering Chatbot?"
                ],
                "Features & Usage": [
                    "What are the key features?",
                    "How do I download study materials?",
                    "What are the different search types?"
                ],
                "Content": [
                    "Tell me about the projects feature",
                    "What departments are supported?"
                ],
                "For Everyone": [
                    "What are the benefits for students?",
                    "What are the benefits for management?",
                    "What are the future plans for this chatbot?"
                ],
                "Admin & Support": [
                    "How does admin upload work?",
                    "How do I get support?"
                ]
            }
            
            for category, questions in categories.items():
                st.markdown(f"**{category}**")
                cols = st.columns(len(questions))
                for idx, (col, question) in enumerate(zip(cols, questions)):
                    with col:
                        if st.button(question, key=f"cat_q_{idx}_{category}", use_container_width=True):
                            with st.spinner("Fetching answer..."):
                                try:
                                    response = requests.post(f"{API_BASE_URL}/ai-help", params={"query": question}, timeout=10)
                                    if response.status_code == 200:
                                        result = response.json()
                                        st.markdown(f"""
                                        <div class="question-box">
                                            <strong>Question:</strong><br/>
                                            {result.get('question', question)}
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        if result.get('type') == 'exact_match':
                                            st.markdown('<span class="match-badge exact-match">✓ Exact Match</span>', unsafe_allow_html=True)
                                        
                                        st.markdown(f"""
                                        <div class="answer-box">
                                            {result.get('answer', 'No answer found')}
                                        </div>
                                        """, unsafe_allow_html=True)
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                st.markdown("")  # Spacing between categories
            
            # Info Box
            st.markdown("---")
            st.info("""
            📌 **Pro Tips:**
            - Ask natural questions, the AI will understand
            - Click any category button for instant answers
            - The AI provides detailed explanations for all features
            - Perfect for students and management to learn about the chatbot
            """)

if __name__ == "__main__":
    main()
