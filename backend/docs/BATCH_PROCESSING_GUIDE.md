# Batch Processing Guide

## Overview

The Policy Intelligence Engine now supports:
- ✅ **Batch processing** of multiple policy PDFs
- ✅ **Ollama integration** for local LLM (no API costs)
- ✅ **Country eligibility checking** for policies

## Quick Start

### 1. Install Ollama

**Windows:**
- Download from: https://ollama.ai/download
- Install and run: `ollama serve`

**Mac/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

### 2. Download a Model

```bash
ollama pull llama3
```

Other options: `mistral`, `llama2`, `codellama`

### 3. Configure Environment

Copy `.env.example` to `.env` and set:
```
OLLAMA_MODEL=llama3
```

### 4. Process a Batch of PDFs

#### Option A: Using the Batch Processor Script

```bash
python batch_processor.py ./policy_pdfs Singapore Malaysia Thailand
```

This will:
1. Process all PDFs in `./policy_pdfs` directory
2. Check eligibility for Singapore, Malaysia, Thailand
3. Generate a comprehensive report

#### Option B: Using the API

```bash
# Start the API server
python main.py

# Upload multiple files via API
curl -X POST "http://localhost:8000/api/upload/batch?countries=Singapore&countries=Malaysia" \
  -F "files=@policy1.pdf" \
  -F "files=@policy2.pdf" \
  -F "files=@policy3.pdf"
```

#### Option C: Using Python Code

```python
from batch_processor import BatchPolicyProcessor

# Initialize processor
processor = BatchPolicyProcessor()

# Process all PDFs in a directory
results = processor.process_batch(
    pdf_directory="./policy_pdfs",
    countries_to_check=["Singapore", "Malaysia", "Thailand"]
)

# Print summary
print(results['summary'])

# Export to JSON
processor.export_results(results, "results.json")
```

## Batch Processing Workflow

```
PDF Files Directory
    ↓
[Batch Processor]
    ↓
For each PDF:
    1. Extract text
    2. Chunk text
    3. Generate embeddings
    4. Store in vector DB
    5. Extract policy summary
    6. Check country eligibility (if countries provided)
    ↓
Generate comprehensive report
```

## Country Eligibility Checking

The system can check if policies are eligible for specific countries by:

1. **Extracting coverage areas** from policy documents
2. **Asking structured questions** about country coverage
3. **Analyzing responses** to determine eligibility

### Example Usage

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
print(f"Details: {result['details']}")

# Check multiple countries
results = checker.check_multiple_countries(
    "Travel Insurance Gold",
    ["Singapore", "Malaysia", "Thailand", "Indonesia"]
)
print(results['summary'])
```

## API Endpoints for Batch Processing

### Upload Multiple Files
```bash
POST /api/upload/batch
- files: List of PDF files
- countries: Optional list of countries to check
- policy_name_prefix: Optional prefix for policy names
```

### Check Country Eligibility
```bash
POST /api/country/check
- policy_name: Name of policy
- country: Country to check

POST /api/country/check-multiple
- policy_name: Name of policy
- countries: List of countries to check

GET /api/country/covered/{policy_name}
- Returns all covered and excluded countries
```

## Output Format

Batch processing generates:

1. **Processing Results**:
   - Successfully processed files
   - Failed files with errors
   - Number of chunks created per policy

2. **Policy Summaries**:
   - Coverage type
   - Coverage area
   - Main benefits
   - Exclusions
   - Duration

3. **Country Eligibility** (if countries provided):
   - Eligibility status per country
   - Detailed answers
   - Summary report

## Example Output

```
============================================================
BATCH PROCESSING SUMMARY REPORT
============================================================

Total Files: 5
Successfully Processed: 5
Failed: 0

Processed Policies:
  • Travel Insurance Gold (policy1.pdf)
    - Chunks: 145, Pages: 25
  • Travel Insurance Silver (policy2.pdf)
    - Chunks: 132, Pages: 23
  ...

============================================================
COUNTRY ELIGIBILITY SUMMARY
============================================================

Travel Insurance Gold:
Eligibility Summary:
  ✓ Eligible: 3 countries - Singapore, Malaysia, Thailand
  ✗ Not Eligible: 1 countries - USA
```

## Tips

1. **Model Selection**: 
   - `llama3` - Best balance (recommended)
   - `mistral` - Faster, slightly less accurate
   - `llama2` - Older but still good

2. **Performance**:
   - Batch processing is faster than individual uploads (shared embeddings)
   - Country checking can be slow for many countries (consider running separately)

3. **Storage**:
   - ChromaDB stores all embeddings locally
   - Large batches may require significant disk space

4. **Error Handling**:
   - Failed files are logged and processing continues
   - Check `results['failed']` for errors

## Troubleshooting

**Ollama not found:**
- Ensure Ollama is running: `ollama serve`
- Check if model is downloaded: `ollama list`

**Slow processing:**
- Reduce number of countries checked
- Use smaller model (mistral instead of llama3)
- Process in smaller batches

**Out of memory:**
- Use smaller embedding model
- Process fewer files at once
- Close other applications

