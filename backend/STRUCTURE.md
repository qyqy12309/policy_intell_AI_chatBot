# Backend Folder Structure

This document explains the organization of the backend folder.

## 📁 Folder Structure

```
backend/
├── app/                          # Main application code
│   ├── main.py                   # FastAPI server entry point (v2.0 - Conversational Assistant)
│   ├── conversation_engine.py   # Stage 2: Conversational AI logic
│   ├── document_intelligence.py # Stage 3: Document extraction
│   ├── commerce.py               # Stage 4: Quote & payment handling
│   ├── predictive_intelligence.py # Stage 5: Risk assessment
│   ├── __init__.py               # Makes app a Python package
│   └── core/                     # Core engine modules
│       ├── __init__.py           # Makes core a Python package
│       ├── vector_store.py        # Embedding & vector database
│       ├── rag_qa.py              # RAG question-answering system
│       ├── document_ingestion.py  # PDF/Word text extraction
│       ├── text_chunking.py       # Document chunking logic
│       ├── policy_comparison.py   # Policy comparison tool
│       ├── batch_processor.py    # Batch document processing
│       ├── country_eligibility.py # Country eligibility checker
│       └── pipeline.py            # Document processing pipeline
│
├── config/                       # Configuration files
│   └── .env.example              # Environment variable template
│
├── docs/                         # Documentation
│   ├── README.md                 # Main documentation
│   ├── README_RUN.md             # How to run the backend
│   └── BATCH_PROCESSING_GUIDE.md # Batch processing guide
│
├── scripts/                      # Utility scripts
│   ├── run_server.bat            # Windows server startup script
│   └── example_usage.py          # Example usage scripts (if any)
│
├── archive/                      # Old/legacy files
│   └── main_old.py               # Old main.py (v1.0 - Policy Engine)
│
└── requirements.txt              # Python dependencies

```

## 📂 Category Breakdown

### **app/** - Main Application
**Purpose**: Contains the active application code (v2.0 Conversational Insurance Assistant)

- **`main.py`**: FastAPI server with all API endpoints
- **`conversation_engine.py`**: Handles chat interactions, intent detection
- **`document_intelligence.py`**: Extracts data from user-uploaded documents
- **`commerce.py`**: Handles quotes, payments, policy issuance
- **`predictive_intelligence.py`**: Risk assessment and smart nudges

### **app/core/** - Core Engine Modules
**Purpose**: Core policy analysis engine (used by v1.0 and v2.0)

- **`vector_store.py`**: Manages embeddings and ChromaDB
- **`rag_qa.py`**: RAG system for Q&A with citations
- **`document_ingestion.py`**: Extracts text from PDFs/Word files
- **`text_chunking.py`**: Splits documents into chunks
- **`policy_comparison.py`**: Compares multiple policies
- **`batch_processor.py`**: Processes multiple documents
- **`country_eligibility.py`**: Checks country coverage
- **`pipeline.py`**: Orchestrates document processing

### **config/** - Configuration
**Purpose**: Configuration files and environment templates

### **docs/** - Documentation
**Purpose**: All documentation and guides

### **scripts/** - Utilities
**Purpose**: Helper scripts for running and testing

### **archive/** - Legacy Files
**Purpose**: Old versions that are no longer active

## 🔄 Import Structure

### From `app/main.py`:
```python
from conversation_engine import ConversationEngine
from document_intelligence import DocumentIntelligence
from commerce import QuoteService
from predictive_intelligence import PredictiveIntelligence
from core.vector_store import VectorStore
from core.rag_qa import PolicyQASystem
```

### Within `app/core/`:
Files use relative imports:
```python
from .vector_store import VectorStore
from .rag_qa import PolicyQASystem
```

## ✅ What's Active vs Old

**ACTIVE (v2.0 - Current)**:
- ✅ `app/main.py` - Main server
- ✅ `app/conversation_engine.py`
- ✅ `app/document_intelligence.py`
- ✅ `app/commerce.py`
- ✅ `app/predictive_intelligence.py`
- ✅ `app/core/*` - All core modules

**ARCHIVED (v1.0 - Old)**:
- ⚠️ `archive/main_old.py` - Old Policy Intelligence Engine API

## 🚀 Running the Backend

**From `backend/app/` directory:**
```bash
python main.py
```

**Or use the script:**
```bash
cd backend
scripts\run_server.bat
```

## 📝 Notes

- The `app/` folder structure is **essential** - this is where the main application lives
- The `core/` folder contains reusable engine components used by both old and new versions
- All imports have been updated to use the new structure
- Old files are archived, not deleted, in case you need to reference them

