# Policy Intelligence Engine - Backend

Backend API server for the Conversational Insurance Assistant.

## Structure

See `../STRUCTURE.md` for detailed folder organization.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment:
   ```bash
   cp config/.env.example .env
   # Edit .env with your settings
   ```

3. Make sure Ollama is running:
   ```bash
   ollama serve
   ollama pull llama3
   ```

4. Run the server:
   ```bash
   cd app
   python main.py
   ```

Or use the script:
```bash
scripts\run_server.bat
```

## Documentation

- `docs/README.md` - Main backend documentation
- `docs/README_RUN.md` - How to run the backend
- `docs/BATCH_PROCESSING_GUIDE.md` - Batch processing guide
- `STRUCTURE.md` - Detailed folder structure

