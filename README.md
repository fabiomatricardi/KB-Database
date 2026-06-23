# KB Database

A local knowledge base application that combines BM25 full-text search with LLM-powered metadata extraction, chat, web search, tag/TOC extraction, and knowledge graph visualization. Runs as a standalone Windows executable or in development mode.

## Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12, FastAPI, uvicorn, rank-bm25, Pydantic, requests |
| **Frontend** | Vue 3 (Composition API), Vite, PrimeIcons, Axios, Marked |
| **Web Search/Fetch** | DuckDuckGo (`ddgs`), Tavily (keyless optional), httpx, BeautifulSoup4, lxml |
| **Packaging** | PyInstaller (single .exe) |
| **LLM** | Ollama (OpenAI-compatible API) |
| **Knowledge Graph** | graphify CLI (Wiki conversion + community detection) |
| **Package Manager** | uv (Python), npm (Node.js) |

## Features

- **Search** — BM25 search through article metadata (title, subheading, summary), with tag filtering
- **Deep Search** — Full-text BM25 search across `.txt`, `.md`, `.html` files, with tag filtering
- **Chat** — Multi-turn conversation with an LLM about loaded articles, with Markdown rendering
- **Web Search & Fetch** — Search the web via DuckDuckGo or Tavily and fetch/parse web pages, loaded as context into Chat
- **Scan & Extract** — Use Ollama to extract metadata, tags, and table of contents from article files
- **Knowledge Graph** — Build interactive knowledge graphs from articles using graphify (Wiki conversion + community detection)
- **Tag Filtering** — Filter search results by tags extracted from articles
- **Settings** — Configure Ollama host, model, web search provider, directories, and server port

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
# Build everything (frontend + .exe)
build-exe.bat
```

Or manually:
```bash
cd frontend && npm install && npm run build && cd ..
uv run python build.py
```

The executable is created at `dist/ArticleDatabase-v0.3.0.exe`.

## Building the Executable

The `build.py` script:
1. Validates that the frontend is built
2. Runs PyInstaller with `--onefile --noconsole`
3. Automatically unblocks the exe for Windows Smart App Control

### Windows Smart App Control

Windows may block unsigned executables. The build script automatically unblocks the file, but if you still see a warning:

**Option 1: PowerShell (recommended)**
```powershell
Unblock-File -Path "dist\ArticleDatabase-v0.3.0.exe"
```

**Option 2: File Properties**
1. Right-click `dist\ArticleDatabase-v0.2.2.exe`
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
│   ├── routers/
│   │   ├── search.py        # BM25 search over article metadata (tags filter)
│   │   ├── deepsearch.py    # Full-text BM25 search over files (tags filter)
│   │   ├── scan.py          # Ollama metadata extraction
│   │   ├── chat.py          # Chat context, history, SSE streaming
│   │   ├── web.py           # Web search & fetch endpoints
│   │   └── graph.py         # Knowledge graph build/query endpoints
│   └── services/
│       ├── bm25.py          # BM25 search implementations + tag filtering
│       ├── scanner.py       # Threaded Ollama scanning (tags + TOC extraction)
│       ├── chat.py          # Chat context management, LLM streaming
│       ├── config.py        # JSON config persistence
│       ├── web.py           # DuckDuckGo + Tavily search + httpx fetch
│       └── graph.py         # Wiki conversion + graphify CLI wrapper
├── frontend/
│   └── src/
│       ├── App.vue          # Root component with sidebar navigation
│       ├── composables/     # API client (useApi.js)
│       ├── components/      # View components (Search, DeepSearch, Chat, Scan, Settings, Graph)
│       └── styles/          # Global dark theme CSS
├── build.py                 # PyInstaller build script
├── build-exe.bat            # One-click build script
├── run-dev.bat              # Development launcher
└── pyproject.toml           # Python dependencies
```

### How It Works

1. **FastAPI backend** serves the Vue SPA and provides REST + SSE endpoints
2. **Vue frontend** communicates via `/api/*` endpoints (proxied in dev, served statically in exe)
3. **PyInstaller** bundles Python, FastAPI, uvicorn, and the built frontend into a single `.exe`
4. **Ollama** provides LLM capabilities for metadata extraction, tag/TOC extraction, and chat (optional)
5. **Web search/fetch** uses DuckDuckGo or Tavily to search the web and parse pages into chat context
6. **Knowledge graph** converts articles to a Wiki format, runs graphify for community detection, and renders an interactive HTML graph

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
| `/api/search?q=&top_n=&tags=` | GET | Search article metadata with tag filtering |
| `/api/deepsearch?query=&dir=&top_n=&tags=` | GET | Full-text file search with tag filtering |
| `/api/scan` | POST | Start Ollama scan |
| `/api/scan/status` | GET | Scan progress |
| `/api/ollama/models?filter_free=` | GET | List Ollama models |
| `/api/chat/context` | GET/POST/DELETE | Manage file-based chat context |
| `/api/chat/context/web` | POST/DELETE | Manage web-based chat context |
| `/api/chat/message` | POST | Send chat message (SSE stream) |
| `/api/chat/history` | GET/DELETE | Conversation history |
| `/api/web/search?q=&max_results=` | GET | Search the web via DuckDuckGo or Tavily |
| `/api/web/fetch` | POST | Fetch and parse a URL |
| `/api/graph/build` | POST | Build knowledge graph from articles |
| `/api/graph/status` | GET | Graph build progress |
| `/api/graph/html` | GET | Serve graph.html |
| `/api/graph/query` | POST | Query the knowledge graph |
| `/api/settings` | GET/PUT | App configuration |
| `/api/shutdown` | POST | Stop application |

## User Manual

See [USERMANUAL.md](USERMANUAL.md) for detailed usage instructions, feature guides, and troubleshooting.

## License

[MIT](LICENSE) — Fabio Matricardi (fabio.matricardi@gmail.com)
