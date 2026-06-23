import json
import os
import subprocess
import sys
import threading

from openai import OpenAI

# Monkey-patch tiktoken to allow special tokens (e.g. <|im_start|>) in content.
# graphify's _estimate_file_tokens() calls encode() without allowed_special,
# which crashes when article content contains LLM chat template tokens.
try:
    import tiktoken as _tiktoken
    _original_get_encoding = _tiktoken.get_encoding
    def _patched_get_encoding(name: str = "cl100k_base"):
        enc = _original_get_encoding(name)
        _orig_encode = enc.encode
        def _safe_encode(text, *args, **kwargs):
            kwargs.setdefault("allowed_special", "all")
            return _orig_encode(text, *args, **kwargs)
        enc.encode = _safe_encode
        return enc
    _tiktoken.get_encoding = _patched_get_encoding
except ImportError:
    pass


_graph_state = {
    "running": False,
    "stage": "",
    "message": "",
    "progress": 0,
}

_PATCHER = os.path.join(
    sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__)),
    "backend", "services", "graphify_patcher.py"
) if getattr(sys, "frozen", False) else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "graphify_patcher.py"
)


def get_graph_status() -> dict:
    return dict(_graph_state)


def _build_graphify_env(backend: str, host: str, model: str, api_key: str, base_url: str,
                        max_output_tokens: int, max_concurrency: int) -> dict:
    env = os.environ.copy()
    env["GRAPHIFY_MAX_OUTPUT_TOKENS"] = str(max_output_tokens)
    env["GRAPHIFY_MAX_CONCURRENCY"] = str(max_concurrency)

    if backend == "ollama":
        env["OLLAMA_BASE_URL"] = host
        env["OLLAMA_MODEL"] = model
        env["OLLAMA_API_KEY"] = "ollama"
    elif backend == "gemini":
        env["GEMINI_API_KEY"] = api_key
        env["GRAPHIFY_MODEL"] = model
    elif backend == "openrouter":
        env["OPENROUTER_APIKEY"] = api_key
        env["OPENROUTER_BASE_URL"] = base_url or "https://openrouter.ai/api/v1"
        env["OLLAMA_BASE_URL"] = base_url or "https://openrouter.ai/api/v1"
        env["OLLAMA_API_KEY"] = api_key
        env["GRAPHIFY_MODEL"] = model
    elif backend == "openai":
        env["OPENAI_API_KEY"] = api_key
        env["OPENAI_BASE_URL"] = base_url or "https://api.openai.com/v1"
        env["OLLAMA_BASE_URL"] = base_url or "https://api.openai.com/v1"
        env["OLLAMA_API_KEY"] = api_key
        env["GRAPHIFY_MODEL"] = model

    return env


def _get_llm_client(backend: str, host: str, model: str, api_key: str, base_url: str) -> tuple[OpenAI, str]:
    if backend == "ollama":
        url = host.rstrip("/")
        if not url.endswith("/v1"):
            url += "/v1"
        return OpenAI(api_key="ollama", base_url=url, timeout=600), model
    elif backend == "gemini":
        return OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/", timeout=60), model
    elif backend == "openrouter":
        return OpenAI(api_key=api_key, base_url=base_url or "https://openrouter.ai/api/v1", timeout=60), model
    elif backend == "openai":
        return OpenAI(api_key=api_key, base_url=base_url or "https://api.openai.com/v1", timeout=60), model
    else:
        raise ValueError(f"Unknown backend: {backend}")


def _call_llm(client: OpenAI, model: str, system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def build_wiki_from_articles(articles_dir: str, database_path: str, wiki_dir: str) -> int:
    if not os.path.exists(database_path):
        return 0

    with open(database_path, "r", encoding="utf-8") as f:
        database = json.load(f)

    notes_dir = os.path.join(wiki_dir, "notes")
    os.makedirs(notes_dir, exist_ok=True)

    count = 0
    for entry in database:
        file_path = entry.get("file_path", "")
        if not file_path or not os.path.isfile(file_path):
            continue

        title = entry.get("title", "Untitled")
        tags = entry.get("tags", [])
        toc = entry.get("toc", [])
        summary = entry.get("summary", "")
        url = entry.get("url", "")

        slug = title.lower().replace(" ", "-").replace("/", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")[:60]

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        frontmatter_lines = [
            "---",
            f'title: "{title}"',
            f'tags: {json.dumps(tags)}',
            f'source: "{entry.get("filename", "")}"',
        ]
        if url and url != "None":
            frontmatter_lines.append(f'url: "{url}"')
        frontmatter_lines.append("---")
        frontmatter_lines.append("")
        frontmatter_lines.append(f"# {title}")
        frontmatter_lines.append("")
        if summary:
            frontmatter_lines.append(summary)
            frontmatter_lines.append("")
        if toc:
            frontmatter_lines.append("## Table of Contents")
            frontmatter_lines.append("")
            for heading in toc:
                frontmatter_lines.append(f"- {heading}")
            frontmatter_lines.append("")
        frontmatter_lines.append(content)

        md_content = "\n".join(frontmatter_lines)
        md_path = os.path.join(notes_dir, f"{slug}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        count += 1

    index_lines = ["# Knowledge Base Index", ""]
    for entry in database:
        title = entry.get("title", "Untitled")
        slug = title.lower().replace(" ", "-").replace("/", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")[:60]
        index_lines.append(f"- [[notes/{slug}|{title}]]")
    with open(os.path.join(wiki_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines))

    return count


def _run_graph_build(articles_dir: str, database_path: str, host: str, model: str,
                     backend: str, api_key: str, base_url: str,
                     max_output_tokens: int, max_concurrency: int):
    global _graph_state
    _graph_state["running"] = True
    _graph_state["message"] = "Preparing wiki files..."
    _graph_state["stage"] = "convert"
    _graph_state["progress"] = 10

    wiki_dir = os.path.join(articles_dir, "..", "wiki")
    wiki_dir = os.path.normpath(wiki_dir)

    try:
        count = build_wiki_from_articles(articles_dir, database_path, wiki_dir)
        _graph_state["message"] = f"Converted {count} articles to wiki format"
        _graph_state["progress"] = 30

        if count == 0:
            _graph_state["message"] = "No articles found to build graph"
            _graph_state["running"] = False
            return

        env = _build_graphify_env(backend, host, model, api_key, base_url, max_output_tokens, max_concurrency)

        _graph_state["stage"] = "extract"
        _graph_state["message"] = f"Running graphify extract ({backend})..."
        _graph_state["progress"] = 40

        result = subprocess.run(
            ["python", _PATCHER, "extract", wiki_dir, "--backend", backend, "--max-concurrency", str(max_concurrency)],
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            _graph_state["message"] = f"Extract failed: {result.stderr[:200]}"
            _graph_state["running"] = False
            return

        _graph_state["progress"] = 70
        _graph_state["stage"] = "html"
        _graph_state["message"] = "Generating graph HTML visualization..."

        graph_json = os.path.join(wiki_dir, "graphify-out", "graph.json")
        result = subprocess.run(
            ["python", _PATCHER, "export", "html", "--graph", graph_json],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            _graph_state["message"] = f"HTML generation failed: {result.stderr[:200]}"
            _graph_state["running"] = False
            return

        _graph_state["progress"] = 100
        _graph_state["stage"] = "done"
        _graph_state["message"] = "Knowledge graph built successfully!"

    except subprocess.TimeoutExpired:
        _graph_state["message"] = "Graph build timed out (10 min limit)"
    except FileNotFoundError:
        _graph_state["message"] = "graphify CLI not found. Install it first."
    except Exception as e:
        _graph_state["message"] = f"Error: {str(e)}"
    finally:
        _graph_state["running"] = False


def start_graph_build(articles_dir: str, database_path: str, host: str, model: str,
                      backend: str = "ollama", api_key: str = "", base_url: str = "",
                      max_output_tokens: int = 8192, max_concurrency: int = 1) -> dict:
    if _graph_state["running"]:
        return {"error": "A graph build is already in progress."}

    thread = threading.Thread(
        target=_run_graph_build,
        args=(articles_dir, database_path, host, model, backend, api_key, base_url, max_output_tokens, max_concurrency),
        daemon=True,
    )
    thread.start()
    return {"status": "Graph build started.", "backend": backend}


def get_graph_html(articles_dir: str) -> str | None:
    wiki_dir = os.path.join(articles_dir, "..", "wiki")
    graph_path = os.path.join(os.path.normpath(wiki_dir), "graphify-out", "graph.html")
    if os.path.isfile(graph_path):
        with open(graph_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def _get_graph_path(articles_dir: str) -> str | None:
    wiki_dir = os.path.join(articles_dir, "..", "wiki")
    graph_path = os.path.join(os.path.normpath(wiki_dir), "graphify-out", "graph.json")
    return graph_path if os.path.isfile(graph_path) else None


def _run_graphify_cli(args: list[str], timeout: int = 60) -> str:
    cmd = ["python", _PATCHER] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[:300] or f"graphify exited with code {result.returncode}")
    return result.stdout.strip()


QUERY_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about a knowledge graph. "
    "Based on the graph traversal results below, provide a clear, concise answer "
    "to the user's question. Use the node names and edge relationships to form "
    "your answer. Be specific and reference the actual document names when relevant. "
    "Format your answer in plain text. Do not use markdown code blocks."
)

EXPLAIN_SYSTEM_PROMPT = (
    "You are a helpful assistant that explains concepts from a knowledge graph. "
    "Based on the graph data below, provide a clear explanation of the concept, "
    "what it connects to, and why it might be important. "
    "Be specific and reference actual document names."
)

PATH_SYSTEM_PROMPT = (
    "You are a helpful assistant that explains connections in a knowledge graph. "
    "Based on the path found between two concepts, explain how they are related "
    "and what the intermediate connections mean. Be specific."
)


def graph_query_llm(question: str, articles_dir: str, backend: str, model: str,
                    api_key: str, base_url: str) -> str:
    graph_path = _get_graph_path(articles_dir)
    if not graph_path:
        return "No knowledge graph found. Build it first."

    raw = _run_graphify_cli(["query", question, "--graph", graph_path, "--budget", "2000"])

    client, llm_model = _get_llm_client(backend, "", model, api_key, base_url)
    return _call_llm(client, llm_model, QUERY_SYSTEM_PROMPT, f"Question: {question}\n\nGraph traversal results:\n{raw}")


def graph_explain(concept: str, articles_dir: str, backend: str, model: str,
                  api_key: str, base_url: str) -> str:
    graph_path = _get_graph_path(articles_dir)
    if not graph_path:
        return "No knowledge graph found. Build it first."

    raw = _run_graphify_cli(["explain", concept, "--graph", graph_path])

    client, llm_model = _get_llm_client(backend, "", model, api_key, base_url)
    return _call_llm(client, llm_model, EXPLAIN_SYSTEM_PROMPT, f"Explain: {concept}\n\nGraph data:\n{raw}")


def graph_path(start: str, end: str, articles_dir: str, backend: str, model: str,
               api_key: str, base_url: str) -> str:
    graph_path = _get_graph_path(articles_dir)
    if not graph_path:
        return "No knowledge graph found. Build it first."

    raw = _run_graphify_cli(["path", start, end, "--graph", graph_path])

    client, llm_model = _get_llm_client(backend, "", model, api_key, base_url)
    return _call_llm(client, llm_model, PATH_SYSTEM_PROMPT, f"Find path from '{start}' to '{end}'\n\nPath results:\n{raw}")
