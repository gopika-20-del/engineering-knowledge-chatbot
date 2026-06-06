"""Backend initialization module"""

import sys
from pathlib import Path

# Ensure backend modules can be imported
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

__all__ = ['config', 'database', 'document_processor', 'chatbot_engine', 'main']
