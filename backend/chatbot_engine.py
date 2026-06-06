"""Chatbot search and retrieval engine"""

import time
import json
from typing import List, Dict
from backend.database import db
from backend.document_processor import doc_processor
from backend.config import SEARCH_RESULTS_LIMIT, SEARCH_TIMEOUT
from pathlib import Path

class ChatbotEngine:
    """Core chatbot search and response generation"""
    
    def __init__(self):
        self.vector_db = db
        self.doc_processor = doc_processor
        self.project_topics_file = Path(__file__).resolve().parent.parent / "data" / "storage" / "PROJECT_TOPICS.json"
    
    def get_related_projects(self, department: str, subject: str) -> List[Dict]:
        """Get related projects for a subject"""
        try:
            if self.project_topics_file.exists():
                with open(self.project_topics_file, 'r', encoding='utf-8') as f:
                    topics_data = json.load(f)
                
                dept_topics = topics_data.get("project_topics", {}).get(department, {})
                all_topics = dept_topics.get("topics", [])
                
                # Filter projects related to subject
                related = []
                subject_lower = subject.lower()
                for topic in all_topics:
                    title_match = subject_lower in topic.get('title', '').lower()
                    desc_match = subject_lower in topic.get('description', '').lower()
                    if title_match or desc_match or len(related) < 3:
                        related.append({
                            'id': topic.get('id'),
                            'title': topic.get('title'),
                            'difficulty': topic.get('difficulty')
                        })
                        if len(related) >= 3:
                            break
                
                return related[:3]
        except:
            pass
        return []
    
    def semantic_search(self, query: str, n_results: int = SEARCH_RESULTS_LIMIT,
                        department: str = None, semester: int = None) -> Dict:
        """
        Perform semantic search using embeddings with optional metadata filtering
        Returns top n relevant documents
        """
        start_time = time.time()
        
        try:
            # Build ChromaDB where filter
            where_filter = {}
            filters_list = []
            if department:
                filters_list.append({"department": department})
            if semester:
                filters_list.append({"semester": int(semester)})
                
            if len(filters_list) == 1:
                where_filter = filters_list[0]
            elif len(filters_list) > 1:
                where_filter = {"$and": filters_list}
            else:
                where_filter = None

            results = self.vector_db.search(query, n_results, where=where_filter)
            elapsed = time.time() - start_time
            
            formatted_results = []
            for result in results:
                doc_metadata = result.get('metadata', {})
                doc_dept = doc_metadata.get('department', 'General')
                doc_subject = doc_metadata.get('subject', 'General')
                
                formatted_results.append({
                    'doc_id': result['id'],
                    'title': doc_metadata.get('title', 'Unknown'),
                    'subject': doc_subject,
                    'department': doc_dept,
                    'semester': doc_metadata.get('semester', 'N/A'),
                    'file_type': doc_metadata.get('file_type', ''),
                    'relevance_score': 1 - result.get('distance', 0),
                    'snippet': result.get('document', '')[:200],
                    'assignments': json.loads(doc_metadata.get('assignments', '[]')) if doc_metadata.get('assignments') else [],
                    'downloadable': doc_metadata.get('file_type', '') in ['.pdf', '.docx', '.doc', '.pptx'],
                    'related_projects': self.get_related_projects(doc_dept, doc_subject)
                })
            
            return {
                'status': 'success',
                'query': query,
                'results': formatted_results,
                'count': len(formatted_results),
                'search_time_ms': round(elapsed * 1000, 2)
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Search failed: {str(e)}",
                'results': []
            }
    
    def keyword_search(self, query: str, department: str = None, semester: int = None) -> Dict:
        """
        Perform keyword-based search with filters
        """
        try:
            keywords = query.lower().split()
            filters = {}
            
            if department:
                filters['department'] = department
            if semester:
                filters['semester'] = semester
            
            # Search metadata
            results = self.doc_processor.search_by_metadata(**filters)
            
            # Score results based on keyword matches
            scored_results = []
            for doc in results:
                score = 0
                doc_text = (
                    str(doc.get('title', '')).lower() + ' ' +
                    str(doc.get('subject', '')).lower() + ' ' +
                    str(doc.get('keywords', '')).lower()
                )
                
                for keyword in keywords:
                    score += doc_text.count(keyword)
                
                if score > 0:
                    department = doc.get('department', '')
                    subject = doc.get('subject', '')
                    scored_results.append({
                        'doc_id': doc['id'],
                        'title': doc.get('title'),
                        'subject': doc.get('subject'),
                        'department': department,
                        'semester': doc.get('semester'),
                        'file_type': doc.get('file_type'),
                        'relevance_score': score,
                        'snippet': doc.get('content_preview', '')[:200],
                        'assignments': json.loads(doc.get('assignments', '[]')) if doc.get('assignments') else [],
                        'downloadable': doc.get('file_type', '') in ['.pdf', '.docx', '.doc', '.pptx'],
                        'related_projects': self.get_related_projects(department, subject)
                    })
            
            # Sort by relevance
            scored_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return {
                'status': 'success',
                'query': query,
                'results': scored_results[:SEARCH_RESULTS_LIMIT],
                'count': len(scored_results[:SEARCH_RESULTS_LIMIT])
            }
        
        except Exception as e:
            return {
                'status': 'error',
                'message': f"Keyword search failed: {str(e)}",
                'results': []
            }
    
    def combined_search(self, query: str, search_type: str = "hybrid", 
                       department: str = None, semester: int = None) -> Dict:
        """
        Perform combined search (semantic + keyword)
        search_type: 'semantic', 'keyword', or 'hybrid'
        """
        if search_type == "semantic":
            return self.semantic_search(query, department=department, semester=semester)
        elif search_type == "keyword":
            return self.keyword_search(query, department, semester)
        elif search_type == "hybrid":
            # Combine both searches
            semantic_results = self.semantic_search(query, n_results=3, department=department, semester=semester)
            keyword_results = self.keyword_search(query, department, semester)
            
            # Merge and deduplicate
            all_results = {}
            for result in semantic_results.get('results', []):
                all_results[result['doc_id']] = {**result, 'type': 'semantic'}
            
            for result in keyword_results.get('results', []):
                if result['doc_id'] in all_results:
                    all_results[result['doc_id']]['relevance_score'] += result['relevance_score']
                    all_results[result['doc_id']]['type'] = 'hybrid'
                else:
                    all_results[result['doc_id']] = {**result, 'type': 'keyword'}
            
            # Sort by relevance
            final_results = sorted(
                all_results.values(),
                key=lambda x: x['relevance_score'],
                reverse=True
            )[:SEARCH_RESULTS_LIMIT]
            
            return {
                'status': 'success',
                'query': query,
                'results': final_results,
                'count': len(final_results),
                'search_type': 'hybrid'
            }
        else:
            return {
                'status': 'error',
                'message': f"Unknown search type: {search_type}",
                'results': []
            }
    
    def get_subject_materials(self, department: str, semester: int, subject: str) -> Dict:
        """Get all materials for a specific subject"""
        results = self.doc_processor.search_by_metadata(
            department=department,
            semester=str(semester),
            subject=subject
        )
        
        # Categorize by type
        materials = {
            'notes': [],
            'lab_manuals': [],
            'question_papers': [],
            'others': []
        }
        
        for doc in results:
            item = {
                'id': doc['id'],
                'title': doc.get('title'),
                'file_type': doc.get('file_type'),
                'size_kb': doc.get('file_size_kb')
            }
            
            title_lower = doc.get('title', '').lower()
            if 'note' in title_lower or 'summary' in title_lower:
                materials['notes'].append(item)
            elif 'lab' in title_lower:
                materials['lab_manuals'].append(item)
            elif 'question' in title_lower or 'paper' in title_lower or 'exam' in title_lower:
                materials['question_papers'].append(item)
            else:
                materials['others'].append(item)
        
        return {
            'status': 'success',
            'department': department,
            'semester': semester,
            'subject': subject,
            'materials': materials,
            'total_count': sum(len(v) for v in materials.values())
        }

# Global instance
chatbot_engine = ChatbotEngine()
