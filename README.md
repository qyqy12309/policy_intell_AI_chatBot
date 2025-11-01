# Conversational Insurance Assistant

AI-powered conversational insurance assistant with a simple web chat interface.

## 🎯 Quick Start

### 1. Start Backend

```bash
cd backend
pip install -r requirements.txt

# Make sure Ollama is running
ollama serve
ollama pull llama3

# Start server
python app/main.py
```

Backend runs on `http://localhost:8000`

### 2. Open Web Chat

Simply open `frontend/index.html` in your browser!

**Option A: Double-click**
- Navigate to `frontend/index.html`
- Double-click to open

**Option B: Local server**
```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

## 📁 Project Structure

```
.
├── backend/
│   └── app/
│       ├── conversation_engine.py    # Chat & intent detection
│       ├── document_intelligence.py  # Extract trip info from docs
│       ├── commerce.py               # Quotes & payment
│       ├── predictive_intelligence.py # Risk & predictions
│       └── main.py                   # FastAPI server
│
├── frontend/
│   └── index.html                    # Single HTML file (everything included!)
│
└── README.md
```

## ✨ Features

### Web Chat Interface
- Simple HTML/CSS/JavaScript (no React, no build step!)
- Real-time chat with AI assistant
- Document upload button
- Persona switching (Travel Guru, Advisor, Companion)
- Responsive design

### Backend Capabilities
- **Conversation Engine** - Natural chat, intent detection
- **Document Intelligence** - Extract trip details from PDFs
- **Commerce** - Generate quotes, handle payments
- **Predictive Intelligence** - Risk assessment, smart nudges

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Web framework
- Ollama - Local LLM
- ChromaDB - Vector database

**Frontend:**
- Plain HTML/CSS/JavaScript
- No frameworks, no dependencies!

## 📚 Code Quality

- Every line of code is commented
- Easy to understand functions
- Clear variable names
- Step-by-step explanations

## 🚀 Usage

1. Start backend: `python backend/app/main.py`
2. Open `frontend/index.html` in browser
3. Start chatting! The AI will help with:
   - Getting insurance quotes
   - Comparing policies
   - Answering questions
   - Processing document uploads

## 📝 API Endpoints

- `POST /api/conversation/start` - Start chat
- `POST /api/conversation/message` - Send message
- `POST /api/document/extract` - Upload document
- `POST /api/commerce/quotes` - Get quotes
- `POST /api/predictive/risk-assessment` - Assess risk

See backend code for full API documentation.

## 🎓 Key Concepts

- **Intent Detection** - Understands what user wants
- **Entity Extraction** - Pulls out trip details from text
- **Document Intelligence** - Extracts info from uploaded files
- **RAG** - Retrieval-Augmented Generation for accurate answers

## 📄 License

Educational and development purposes.
