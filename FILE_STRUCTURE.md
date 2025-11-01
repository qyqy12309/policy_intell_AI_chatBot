# File Structure & Dependencies

## ✅ Required Files (Keep These)

### Backend (`backend/app/`)

1. **main.py** ⭐ CRITICAL
   - Main FastAPI server
   - Imports all other modules
   - Defines all API endpoints

2. **conversation_engine.py** ⭐ REQUIRED
   - Stage 0-2: Chat, intent detection, entity extraction
   - Imported by: main.py

3. **document_intelligence.py** ⭐ REQUIRED
   - Stage 3: Extract trip info from uploaded documents
   - Imported by: main.py

4. **commerce.py** ⭐ REQUIRED
   - Stage 4: Quote generation and payment
   - Imported by: main.py

5. **predictive_intelligence.py** ⭐ REQUIRED
   - Stage 5: Risk assessment and smart nudges
   - Imported by: main.py

6. **__init__.py** ✅ HELPFUL
   - Makes `app` a Python package
   - Not strictly required but recommended

### Frontend (`frontend/`)

1. **index.html** ⭐ CRITICAL
   - Complete web chat interface
   - Everything in one file (HTML, CSS, JavaScript)
   - This is what users open in browser

2. **README.md** ✅ HELPFUL
   - Documentation for frontend
   - Explains how to use the HTML file

### Root Level

1. **README.md** ✅ HELPFUL
   - Main project documentation
   - Quick start guide

2. **FILE_STRUCTURE.md** ✅ HELPFUL (this file)
   - Explains file dependencies

### Backend Root (`backend/`)

1. **requirements.txt** ✅ REQUIRED
   - Python dependencies
   - Needed for: `pip install -r requirements.txt`

2. **.env.example** ✅ HELPFUL
   - Environment variable template
   - Shows what config is needed


## 📊 Dependency Graph

```
main.py (server entry point)
  ├── conversation_engine.py
  ├── document_intelligence.py
  │     └── (tries to import document_ingestion.py, but has fallback)
  ├── commerce.py
  └── predictive_intelligence.py

frontend/index.html (web interface)
  └── connects to → main.py API endpoints
```

## 🔍 How to Verify Files Are Needed

1. **Check imports in main.py** - If a file is imported there, it's required
2. **Check imports in other modules** - If imported by a required file, it's required
3. **Check if file has fallback** - Some files have try/except imports with fallbacks

## ✅ Current Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              ⭐ Main server
│   │   ├── conversation_engine.py
│   │   ├── document_intelligence.py
│   │   ├── commerce.py
│   │   └── predictive_intelligence.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html               ⭐ Web interface
│   └── README.md
│
├── README.md
└── FILE_STRUCTURE.md (this file)
```

