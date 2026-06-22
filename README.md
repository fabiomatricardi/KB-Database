# KB Database

A local knowledge base application that combines BM25 full-text search with LLM-powered metadata extraction and chat. Runs as a standalone Windows executable or in development mode.

## Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12, FastAPI, uvicorn, rank-bm25, Pydantic, requests |
| **Frontend** | Vue 3 (Composition API), Vite, PrimeIcons, Axios, Marked |
| **Packaging** | PyInstaller (single .exe) |
| **LLM** | Ollama (OpenAI-compatible API) |
| **Package Manager** | uv (Python), npm (Node.js) |

## Features

- **Search** — BM25 search through article metadata (title, subheading, summary)
- **Deep Search** — Full-text BM25 search across `.txt`, `.md`, `.html` files
- **Chat** — Multi-turn conversation with an LLM about loaded articles, with Markdown rendering
- **Scan & Extract** — Use Ollama to extract metadata from article files and save to a JSON database
- **Settings** — Configure Ollama host, model, directories, and server port

## Prerequisites

- **Python 3.12** — pinned via `.python-version`
- **Node.js 18+** — for building the frontend
- **uv** — Python package manager ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Ollama** (optional) — for Chat and Scan features ([install](https://ollama.ai))

## Quick Start

### Development Mode

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies and build
cd frontend
npm install
npm run build
cd ..

# Start the dev server
uv run python -m backend.main
```

Or use the batch script:
```bash
run-dev.bat
```

Your browser opens automatically to `http://localhost:8000`.

### Standalone Executable

```bash
# Build the frontend
cd frontend && npm install && npm run build && cd ..

# Build the .exe
uv run python build.py
```

The executable is created at `dist/ArticleDatabase.exe`.

## Building the Executable

The `build.py` script:
1. Cleans previous build artifacts
2. Builds the Vue frontend (if not already built)
3. Runs PyInstaller with `--onefile --noconsole`
4. Automatically unblocks the exe for Windows Smart App Control

### Windows Smart App Control

Windows may block unsigned executables. The build script automatically unblocks the file, but if you still see a warning:

**Option 1: PowerShell (recommended)**
```powershell
Unblock-File -Path "dist\ArticleDatabase.exe"
```

**Option 2: File Properties**
1. Right-click `dist\ArticleDatabase.exe`
2. Select **Properties**
3. Check **Unblock** at the bottom
4. Click **Apply**

### Hidden Imports

If the exe crashes with import errors, add the missing module to `hidden_imports` in `build.py`:
```python
"--hidden-import", "your_module",
```

## Architecture

```
KB_database/
├── backend/
│   ├── main.py              # FastAPI app, CORS, static mount, shutdown endpoint
│   ├── models.py            # Pydantic models for request/response
│   ├── routers/             # API endpoints (search, deepsearch, scan, chat)
│   └── services/            # Business logic (bm25, scanner, chat, config)
├── frontend/
│   └── src/
│       ├── App.vue          # Root component with sidebar navigation
│       ├── composables/     # API client (useApi.js)
│       ├── components/      # View components (Search, DeepSearch, Chat, Scan, Settings)
│       └── styles/          # Global dark theme CSS
├── build.py                 # PyInstaller build script
├── run-dev.bat              # Development launcher
└── pyproject.toml           # Python dependencies
```

### How It Works

1. **FastAPI backend** serves the Vue SPA and provides REST + SSE endpoints
2. **Vue frontend** communicates via `/api/*` endpoints (proxied in dev, served statically in exe)
3. **PyInstaller** bundles Python, FastAPI, uvicorn, and the built frontend into a single `.exe`
4. **Ollama** provides LLM capabilities for metadata extraction and chat (optional)

## CLI Tools (Legacy)

Original Python CLI scripts are included for command-line use:

```bash
# Search the database
uv run search.py --query "RAG" --top_n 5

# Deep search files
uv run deepsearch.py --dir .\articles\ --query "llama.cpp" --top_n 5

# Scan articles with Ollama
uv run scan.py --dir .\articles\ --host http://localhost:11434 --model mistral
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search?q=&top_n=` | GET | Search article metadata |
| `/api/deepsearch?query=&dir=&top_n=` | GET | Full-text file search |
| `/api/scan` | POST | Start Ollama scan |
| `/api/scan/status` | GET | Scan progress |
| `/api/ollama/models?filter_free=` | GET | List Ollama models |
| `/api/chat/context` | GET/POST/DELETE | Manage chat context |
| `/api/chat/message` | POST | Send chat message (SSE stream) |
| `/api/chat/history` | GET/DELETE | Conversation history |
| `/api/settings` | GET/POST | App configuration |
| `/api/shutdown` | POST | Stop application |

## User Manual

See [USERMANUAL.md](USERMANUAL.md) for detailed usage instructions, feature guides, and troubleshooting.

## License

[MIT](LICENSE) — Fabio Matricardi (fabio.matricardi@gmail.com)
