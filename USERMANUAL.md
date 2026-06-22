# ArticleDatabase - User Manual

## Overview

ArticleDatabase is a local article management system that combines BM25 full-text search with LLM-powered metadata extraction and chat. It runs as a standalone Windows application.

## Getting Started

### Running the Application

**Option 1: Standalone executable**
1. Double-click `ArticleDatabase.exe`
2. If Windows Smart App Control blocks the exe, run in PowerShell:
   ```powershell
   Unblock-File -Path "C:\path\to\ArticleDatabase.exe"
   ```
   Then right-click the exe > Properties > check "Unblock" > Apply.
3. Your browser will open automatically to `http://localhost:8000`
4. The application runs silently in the background

**Option 2: Development mode**
```batch
run-dev.bat
```
Or manually:
```batch
uv sync
uv run python -m backend.main
```

### Prerequisites (for full features)

- **Ollama** running locally (for Scan and Chat features)
  - Install from [ollama.ai](https://ollama.ai)
  - Pull a model: `ollama pull llama3`
  - Ensure it follows the OpenAI-compatible API at `http://localhost:11434`

---

## Features

### 1. Search Database

Search through article metadata (title, subheading, summary) that has been extracted by the Scan tool.

**How to use:**
1. Click **Search** in the sidebar
2. Type your query (e.g., "RAG", "OpenCode", "llama")
3. Set the number of results (Top N)
4. Click **Search** or press Enter

**Results show:**
- Article title and subheading
- BM25 relevance score
- Summary, clickable URL, and source file path
- Click a result card to expand/collapse details

---

### 2. Deep Search

Full-text BM25 search across all `.txt`, `.md`, and `.html` files in a directory (including subdirectories). This searches raw file content, not the database.

**How to use:**
1. Click **Deep Search** in the sidebar
2. Enter your search query
3. Optionally change the directory path (defaults to `.\\articles\\`)
4. Set the number of results
5. Click **Deep Search**

**Results show:**
- Filename and relevance score
- If the file exists in the database: title, summary, URL
- If not: a preview snippet of the raw content
- Source file path

**Load to Chat:**
- Click **Load All to Chat** to send all results to the Chat tab
- Or click **Load to Chat** on individual result cards

---

### 3. Chat

Have a conversation with an LLM about your loaded articles. The chat maintains conversation history across multiple turns and renders responses with full Markdown formatting.

**How to use:**
1. First, load articles from Deep Search (see above)
2. Click **Chat** in the sidebar
3. You'll see the loaded articles listed at the top
4. Type your question and press Enter or click Send
5. The response streams in real-time with Markdown rendering (code blocks, lists, tables, etc.)

**First message tip:** When articles are loaded, you'll see a hint. You can:
- Ask a direct question: "What are the main topics in these articles?"
- Request a summary: "Summarize these articles"
- Compare: "Compare the different approaches mentioned"

**Context bar:**
- Shows how many articles are loaded
- Click the X on any article chip to remove it
- Click **Clear All** to remove all context and start fresh

**Save Chat:**
- Click **Save Chat** to download the conversation as a Markdown file
- The saved file includes the date, loaded articles, and full conversation history

**Example workflow:**
1. Deep Search for "RAG"
2. Click **Load All to Chat**
3. Switch to Chat tab
4. Ask: "Compare the different approaches to RAG mentioned in these articles"
5. Follow up: "Which one is best for local deployment?"
6. Click **Save Chat** to keep a record

---

### 4. Scan & Extract

Scan article files and extract metadata (title, subheading, URL, summary) using an Ollama LLM. Results are saved to `articles_db.json`.

**How to use:**
1. Click **Scan & Extract** in the sidebar
2. Configure Ollama settings:
   - **Host**: Ollama server URL (default: `http://localhost:11434`)
   - **Model**: LLM model to use (e.g., `llama3`, `mistral`)
   - **Articles Directory**: folder containing your articles
   - **Database File**: output JSON file path
3. Click **Start Scan**
4. Watch the progress bar as files are processed

**Notes:**
- Only processes new files (skips already-scanned files)
- Supports `.txt`, `.md`, and `.html` files
- Requires Ollama running with a compatible model

---

### 5. Settings

Configure application defaults.

**Available settings:**
- **Ollama Host**: URL for your Ollama instance
- **Default Model**: model name used for Scan and Chat
- **Articles Directory**: default folder for scanning
- **Database File**: path to the JSON database
- **Server Port**: web server port (default: 8000)

**Fetch Models:**
- Click **Fetch Models** to query your Ollama instance for available models
- Check **Free only** to filter models containing "free" in the name
- Click a model chip to select it as the default

**Shutdown:**
- Click **Stop App** to terminate the application completely

---

## Architecture

```
ArticleDatabase/
├── articles/           # Your article files (.txt, .md, .html)
├── articles_db.json    # Extracted metadata database
├── backend/            # FastAPI server
│   ├── main.py         # App entry, routes, static mount
│   ├── models.py       # Pydantic models
│   ├── routers/        # API endpoints (search, deepsearch, scan, chat)
│   └── services/       # Business logic (bm25, scanner, chat, config)
├── frontend/           # Vue 3 + Vite UI
│   └── src/components/ # SearchView, DeepSearchView, ChatView, ScanView, SettingsPanel
├── dist/               # Built .exe
├── build.py            # PyInstaller build script
└── run-dev.bat         # Quick dev launcher
```

**Technology stack:**
- **Backend**: Python 3.12, FastAPI, uvicorn, rank-bm25, requests
- **Frontend**: Vue 3, Vite, marked (Markdown rendering)
- **Packaging**: PyInstaller (standalone .exe)
- **LLM**: Ollama (OpenAI-compatible API)

---

## Original CLI Tools

The original Python CLI scripts are still available for command-line use:

```batch
# Search the database
uv run search.py --query "RAG" --top_n 5

# Deep search files
uv run deepsearch.py --dir .\articles\ --query "llama.cpp" --top_n 5

# Scan articles with Ollama
uv run scan.py --dir .\articles\ --host http://localhost:11434 --model mistral
```

---

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
| `/api/chat/history` | GET | Get conversation history |
| `/api/chat/history` | DELETE | Clear history |
| `/api/settings` | GET/PUT | App configuration |
| `/api/shutdown` | POST | Stop application |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Browser doesn't open | Navigate manually to `http://localhost:8000` |
| Smart App Control blocks exe | Run `Unblock-File -Path "ArticleDatabase.exe"` in PowerShell, or right-click exe > Properties > Unblock |
| "Could not reach Ollama" | Ensure Ollama is running: `ollama serve` |
| No models listed | Pull a model: `ollama pull llama3` |
| App won't stop | Use Settings > Stop App, or Task Manager |
| Scan fails with JSON error | Try a different model (e.g., `mistral` instead of small models) |
| Port 8000 in use | Change port in Settings > Server Port |
| Chat shows raw Markdown | Reload the page (marked library should render formatting) |
