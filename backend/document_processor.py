"""Document processing and metadata extraction"""

import os
import json
import uuid
from pathlib import Path
from typing import Dict, Tuple, Optional
from PyPDF2 import PdfReader
from docx import Document
import shutil
from backend.config import STORAGE_DIR, ALLOWED_EXTENSIONS

class DocumentProcessor:
    """Handle document uploads, storage, and metadata extraction"""
    
    def __init__(self):
        self.storage_dir = STORAGE_DIR
        self.metadata_file = self.storage_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load existing metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def upload_document(self, file_path: Path, metadata: Dict) -> Tuple[bool, str, str]:
        """
        Upload and store a document
        Returns: (success, doc_id, message)
        """
        try:
            # Validate file
            if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                return False, "", f"File type not allowed. Allowed: {ALLOWED_EXTENSIONS}"
            
            # Generate unique ID
            doc_id = str(uuid.uuid4())
            
            # Extract content and metadata
            content = self._extract_content(file_path)
            if not content:
                return False, "", "Could not extract content from file"
            
            # Save file with new name
            new_filename = f"{doc_id}_{file_path.name}"
            dest_path = self.storage_dir / new_filename
            shutil.copy2(file_path, dest_path)
            
            # Update metadata
            doc_metadata = {
                'id': doc_id,
                'original_name': file_path.name,
                'stored_name': new_filename,
                'file_type': file_path.suffix.lower(),
                'department': metadata.get('department', 'General'),
                'semester': metadata.get('semester', 'General'),
                'subject': metadata.get('subject', 'General'),
                'keywords': metadata.get('keywords', ''),
                'title': metadata.get('title', file_path.stem),
                'summary': metadata.get('summary', ''),
                'assignments': json.dumps(metadata.get('assignments', [])),  # Convert to JSON string
                'file_size_kb': dest_path.stat().st_size / 1024,
                'content_preview': content[:500]
            }
            
            self.metadata[doc_id] = doc_metadata
            self._save_metadata()
            
            return True, doc_id, f"Document '{file_path.name}' uploaded successfully"
        
        except Exception as e:
            return False, "", f"Upload error: {str(e)}"
    
    def _extract_content(self, file_path: Path) -> str:
        """Extract text content from document"""
        try:
            if file_path.suffix.lower() == ".pdf":
                return self._extract_pdf(file_path)
            elif file_path.suffix.lower() in [".docx", ".doc"]:
                return self._extract_docx(file_path)
            elif file_path.suffix.lower() == ".txt":
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
            else:
                return ""
        except Exception as e:
            print(f"Content extraction error: {e}")
            return ""
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"PDF extraction error: {e}")
        return text
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        text = ""
        try:
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"DOCX extraction error: {e}")
        return text
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get document metadata"""
        return self.metadata.get(doc_id)
    
    def get_document_path(self, doc_id: str) -> Optional[Path]:
        """Get full path to stored document"""
        doc = self.get_document(doc_id)
        if doc:
            return self.storage_dir / doc['stored_name']
        return None
    
    def delete_document(self, doc_id: str) -> Tuple[bool, str]:
        """Delete a document"""
        try:
            doc = self.get_document(doc_id)
            if not doc:
                return False, "Document not found"
            
            # Delete file
            file_path = self.storage_dir / doc['stored_name']
            if file_path.exists():
                file_path.unlink()
            
            # Remove metadata
            del self.metadata[doc_id]
            self._save_metadata()
            
            return True, f"Document deleted successfully"
        except Exception as e:
            return False, f"Delete error: {str(e)}"
    
    def search_by_metadata(self, **filters) -> list:
        """Search documents by metadata filters"""
        results = []
        for doc_id, doc_meta in self.metadata.items():
            match = True
            for key, value in filters.items():
                if key in doc_meta:
                    if isinstance(doc_meta[key], str):
                        if value.lower() not in doc_meta[key].lower():
                            match = False
                            break
                    else:
                        if doc_meta[key] != value:
                            match = False
                            break
            if match:
                results.append({'id': doc_id, **doc_meta})
        
        return results
    
    def update_metadata(self, doc_id: str, updates: Dict) -> Tuple[bool, str]:
        """Update document metadata"""
        try:
            if doc_id not in self.metadata:
                return False, "Document not found"
            
            self.metadata[doc_id].update(updates)
            self._save_metadata()
            return True, "Metadata updated successfully"
        except Exception as e:
            return False, f"Update error: {str(e)}"

# Global instance
doc_processor = DocumentProcessor()
