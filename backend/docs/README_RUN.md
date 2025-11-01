# How to Run the Backend

## Prerequisites
1. Python 3.8+ installed
2. Ollama installed and running (`ollama serve`)
3. Ollama model downloaded (e.g., `ollama pull llama3`)

## Quick Start

### Option 1: Using Python directly
```bash
cd C:\Users\User\Desktop\backend\app
python main.py
```

### Option 2: Using uvicorn directly
```bash
cd C:\Users\User\Desktop\backend\app
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Option 3: Using the batch file (Windows)
Double-click `run_server.bat` or run:
```bash
cd C:\Users\User\Desktop\backend
run_server.bat
```

## What Should Happen

You should see output like:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Verify It's Working

1. Open your browser and go to: `http://localhost:8000/api/health`
2. You should see a JSON response like:
   ```json
   {
     "status": "healthy",
     "components": {...}
   }
   ```

## Troubleshooting

### ModuleNotFoundError
If you see `ModuleNotFoundError`, install missing packages:
```bash
pip install fastapi uvicorn python-multipart python-dotenv ollama sentence-transformers chromadb python-docx
```

### Ollama Connection Error
Make sure Ollama is running:
```bash
ollama serve
```

In a separate terminal, verify the model is available:
```bash
ollama list
```

If the model isn't there, pull it:
```bash
ollama pull llama3
```

### Port Already in Use
If port 8000 is already in use, change it:
```bash
# Set environment variable
set PORT=8001
python main.py
```

Or edit `main.py` line 404 to change the default port.

## Notes

- The server runs on `http://0.0.0.0:8000` by default
- All API endpoints are under `/api/*`
- The frontend expects the backend at `http://localhost:8000`
- Make sure CORS is enabled (it is by default in `main.py`)

