# Policy Intelligence Engine

An AI-powered backend system that reads, understands, and answers questions about complex insurance policy documents using advanced Natural Language Processing and Retrieval-Augmented Generation (RAG).

## 🎯 Features

- **Document Processing**: Extract text from PDFs and Word documents (including scanned PDFs with OCR)
- **Batch Processing**: Process multiple policy PDFs at once with comprehensive analysis
- **Semantic Search**: Find relevant policy sections using AI embeddings
- **Intelligent Q&A**: Answer questions with accurate citations (section, page numbers)
- **Policy Comparison**: Compare multiple policies side-by-side on coverage, limits, and exclusions
- **Country Eligibility**: Check which countries each policy covers and eligibility status
- **Local LLM**: Uses Ollama for local inference (no API costs, complete privacy)
- **Fast Retrieval**: Vector database enables instant semantic search across thousands of policy chunks

## 🏗️ Architecture

```
Policy Document (PDF/Word)
    ↓
[Document Ingestion] → Extract text, handle OCR
    ↓
[Text Chunking] → Split into semantic chunks with metadata
    ↓
[Vector Store] → Generate embeddings, store in ChromaDB
    ↓
[RAG Q&A] → Answer questions with citations
    ↓
[Policy Comparison] → Compare multiple policies
```

## 📦 Installation

### Prerequisites

- Python 3.8+
- Ollama installed and running (for local LLM)
- Tesseract OCR (optional, for scanned documents)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Install and Setup Ollama

**Download Ollama:**
- Windows/Mac/Linux: https://ollama.ai/download
- Or via command line: `curl -fsSL https://ollama.ai/install.sh | sh`

**Start Ollama:**
```bash
ollama serve
```

**Download a model:**
```bash
ollama pull llama3
```

Other model options: `mistral` (faster), `llama2`, `codellama`

### Step 3: Install Tesseract OCR (for scanned PDFs)

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH

**Mac:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### Step 4: Configure Environment

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and set your Ollama model:
```
OLLAMA_MODEL=llama3
```
(No API key needed - everything runs locally!)

### Step 5: Run the API Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 🚀 Usage

### API Endpoints

#### 1. Upload Policy Document

```bash
curl -X POST "http://localhost:8000/api/upload?policy_name=Gold%20Plan" \
  -F "file=@policy_document.pdf"
```

#### 2. Ask a Question

```bash
curl -X POST "http://localhost:8000/api/ask?question=Does%20this%20cover%20food%20poisoning?"
```

Response:
```json
{
  "question": "Does this cover food poisoning?",
  "answer": "Yes, this policy covers hospitalization due to illness, including food poisoning, up to SGD 100,000 (Section 2.1, Medical Expenses).",
  "citations": ["Section 2.1, page 15, Gold Plan Policy"],
  "sources_count": 3
}
```

#### 3. Compare Policies

```bash
curl -X POST "http://localhost:8000/api/compare?policy_names=Gold%20Plan&policy_names=Silver%20Plan"
```

#### 4. Upload Multiple Policies (Batch)

```bash
curl -X POST "http://localhost:8000/api/upload/batch?countries=Singapore&countries=Malaysia" \
  -F "files=@policy1.pdf" \
  -F "files=@policy2.pdf" \
  -F "files=@policy3.pdf"
```

#### 5. Check Country Eligibility

```bash
# Single country
curl -X POST "http://localhost:8000/api/country/check?policy_name=Gold%20Plan&country=Singapore"

# Multiple countries
curl -X POST "http://localhost:8000/api/country/check-multiple?policy_name=Gold%20Plan&countries=Singapore&countries=Malaysia"

# Get all covered countries
curl "http://localhost:8000/api/country/covered/Gold%20Plan"
```

#### 6. List All Policies

```bash
curl http://localhost:8000/api/policies
```

### Python Code Examples

#### Process a Document

```python
from pipeline import PolicyPipeline
from vector_store import VectorStore

# Initialize components
vector_store = VectorStore()
pipeline = PolicyPipeline(vector_store)

# Process a policy document
result = pipeline.process_document("travel_policy.pdf", "Travel Insurance Gold")
print(f"Created {result['chunks_count']} chunks")
```

#### Ask Questions

```python
from vector_store import VectorStore
from rag_qa import PolicyQASystem

# Initialize
store = VectorStore()
qa = PolicyQASystem(store)

# Ask a question
result = qa.answer_question("What is the baggage loss coverage?")
print(result['answer'])
```

#### Compare Policies

```python
from policy_comparison import PolicyComparator

comparator = PolicyComparator(store)
result = comparator.compare_policies(["Gold Plan", "Silver Plan", "Bronze Plan"])
print(result['summary'])
```

#### Batch Process Multiple PDFs

```python
from batch_processor import BatchPolicyProcessor

# Initialize processor
processor = BatchPolicyProcessor()

# Process all PDFs in a directory and check country eligibility
results = processor.process_batch(
    pdf_directory="./policy_pdfs",
    countries_to_check=["Singapore", "Malaysia", "Thailand"]
)

# Print summary
print(results['summary'])

# Export to JSON
processor.export_results(results, "batch_results.json")
```

#### Check Country Eligibility

```python
from country_eligibility import CountryEligibilityChecker
from vector_store import VectorStore
from rag_qa import PolicyQASystem

# Initialize
store = VectorStore()
qa = PolicyQASystem(store)
checker = CountryEligibilityChecker(store, qa)

# Check single country
result = checker.check_country_eligibility("Travel Insurance Gold", "Singapore")
print(f"Eligible: {result['eligibility_status']}")

# Check multiple countries
results = checker.check_multiple_countries(
    "Travel Insurance Gold",
    ["Singapore", "Malaysia", "Thailand"]
)
print(results['summary'])
```

## 📁 Project Structure

```
.
├── main.py                  # FastAPI server (main entry point)
├── pipeline.py              # Orchestrates document processing
├── document_ingestion.py    # PDF/Word text extraction
├── text_chunking.py         # Splits text into semantic chunks
├── vector_store.py          # Embeddings & ChromaDB storage
├── rag_qa.py               # Q&A system with citations
├── policy_comparison.py     # Policy comparison engine
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── README.md              # This file
```

## 🔧 How It Works

### 1. Document Ingestion (`document_ingestion.py`)

- **PDF Processing**: Uses PyMuPDF to extract text from PDFs
- **Word Processing**: Uses python-docx for .docx files
- **OCR Support**: Automatically uses Tesseract OCR for scanned PDFs

### 2. Text Chunking (`text_chunking.py`)

- Splits documents into ~500 token chunks
- Preserves document structure (sections, page numbers)
- Adds metadata for citations
- Uses overlap between chunks to prevent context loss

### 3. Vector Storage (`vector_store.py`)

- Converts text chunks into embeddings using `sentence-transformers` (local, no API)
- Uses `all-MiniLM-L6-v2` model (fast) or `all-mpnet-base-v2` (better quality)
- Stores embeddings in ChromaDB (vector database)
- Enables fast semantic search (finds similar meaning, not just exact words)
- Batch embedding generation for faster processing

### 4. RAG Q&A (`rag_qa.py`)

**Retrieval-Augmented Generation process:**

1. User asks a question
2. System converts question to embedding
3. Finds most similar policy chunks (semantic search)
4. Sends question + relevant chunks to Ollama LLM (local, no API)
5. LLM generates answer with citations

**Example:**
- Question: "Does it cover food poisoning?"
- System finds chunks about "medical expenses" and "illness coverage"
- Ollama LLM generates: "Yes, food poisoning is covered under medical expenses (Section 2.1, page 15)"

### 5. Country Eligibility (`country_eligibility.py`)

**Checks policy eligibility for countries:**

1. Searches policy documents for coverage areas
2. Asks structured questions about country coverage
3. Analyzes responses to determine eligibility
4. Extracts covered and excluded countries
5. Generates eligibility summaries

**Example:**
- Check: "Is this policy eligible for Singapore?"
- System searches for country coverage information
- Returns: Eligibility status, details, and citations

### 6. Batch Processing (`batch_processor.py`)

**Processes multiple PDFs at once:**

1. Loads all PDFs from a directory
2. Processes each PDF (extract, chunk, embed, store)
3. Extracts policy summaries
4. Checks country eligibility (if countries provided)
5. Generates comprehensive report

### 7. Policy Comparison (`policy_comparison.py`)

- Extracts structured coverage details from each policy
- Normalizes categories (Medical, Baggage, Trip Delay, etc.)
- Creates side-by-side comparison tables
- Generates conversational summaries

## 🎓 Key Concepts Explained

### Embeddings

Text is converted into a list of numbers (vector) that represents its meaning. Similar texts have similar embeddings, allowing the system to find relevant content even with different wording.

**Example:**
- "medical expenses" → embedding: [0.1, -0.3, 0.7, ...]
- "hospitalization costs" → embedding: [0.12, -0.28, 0.69, ...]
- These are similar, so semantic search finds both!

### RAG (Retrieval-Augmented Generation)

Instead of training a model on all policies (expensive, slow), RAG:
1. Stores policy chunks in a searchable database
2. Retrieves relevant chunks when asked a question
3. Uses LLM to generate answer from retrieved chunks

**Benefits:**
- Up-to-date (just add new documents)
- Accurate (grounded in actual policy text)
- Citations included (know which section says what)

### Vector Database (ChromaDB)

A specialized database for storing and searching embeddings. Much faster than searching through raw text files.

## 🔐 Environment Variables

```env
OLLAMA_MODEL=llama3                  # Ollama model to use (llama3, mistral, llama2, etc.)
CHROMA_DB_PATH=./chroma_db           # Where to store vector database
MAX_CHUNK_SIZE=500                   # Tokens per chunk
CHUNK_OVERLAP=50                     # Overlap between chunks
HOST=0.0.0.0                         # API host
PORT=8000                            # API port
```

**No API keys needed!** Everything runs locally with Ollama.

## 📝 Notes

- **No API Costs**: Uses local Ollama and sentence-transformers (completely free!)
- **Processing Time**: Large PDFs may take 1-2 minutes to process (embedding generation).
- **Storage**: ChromaDB stores data locally. Ensure sufficient disk space.
- **OCR**: Scanned PDFs require Tesseract OCR installation.
- **Ollama**: Ensure Ollama is running (`ollama serve`) and model is downloaded (`ollama pull llama3`).
- **Batch Processing**: Much faster than individual uploads (shared embedding model).

## 🐛 Troubleshooting

**Error: "Ollama not found" or "Connection refused"**
- Ensure Ollama is running: `ollama serve`
- Check if model is downloaded: `ollama list`
- Download model: `ollama pull llama3`

**Error: "Tesseract not found"**
- Install Tesseract OCR and ensure it's in PATH
- Or set `use_ocr=False` in DocumentIngester

**Slow processing**
- Large documents take time to embed
- Consider reducing `chunk_size` for faster processing
- Use smaller Ollama model (mistral instead of llama3)

**Out of memory**
- Use smaller embedding model
- Process fewer files at once
- Close other applications

**API not responding**
- Check if port 8000 is available
- Try a different port in `.env`

## 📄 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Feel free to extend this system with:
- Additional document formats (Excel, images)
- Fine-tuned embeddings for insurance terminology
- User feedback loop for improving answers
- Claims data integration for real-world validation

## 📚 Additional Resources

- **Batch Processing Guide**: See `BATCH_PROCESSING_GUIDE.md` for detailed batch processing instructions
- **Ollama Models**: https://ollama.ai/library
- **ChromaDB Docs**: https://www.trychroma.com/

---

**Built with:** FastAPI, Ollama, ChromaDB, PyMuPDF, Sentence-Transformers

