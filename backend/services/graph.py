import json
import os
import shutil
import subprocess
import threading


_graph_state = {
    "running": False,
    "stage": "",
    "message": "",
    "progress": 0,
}


def get_graph_status() -> dict:
    return dict(_graph_state)


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


def _run_graph_build(articles_dir: str, database_path: str, host: str, model: str):
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

        _graph_state["stage"] = "extract"
        _graph_state["message"] = "Running graphify extract (entity extraction)..."
        _graph_state["progress"] = 40

        env = os.environ.copy()
        env["OLLAMA_BASE_URL"] = host
        env["OLLAMA_MODEL"] = model
        env["OLLAMA_API_KEY"] = "ollama"  # graphify requires non-empty value

        result = subprocess.run(
            ["graphify", "extract", wiki_dir, "--backend", "ollama", "--max-concurrency", "1"],
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
        _graph_state["stage"] = "label"
        _graph_state["message"] = "Running graphify label (community labeling)..."

        result = subprocess.run(
            ["graphify", "label", wiki_dir, "--backend", "ollama", "--model", model],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            _graph_state["message"] = f"Label failed: {result.stderr[:200]}"
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


def start_graph_build(articles_dir: str, database_path: str, host: str, model: str) -> dict:
    if _graph_state["running"]:
        return {"error": "A graph build is already in progress."}

    thread = threading.Thread(
        target=_run_graph_build,
        args=(articles_dir, database_path, host, model),
        daemon=True,
    )
    thread.start()
    return {"status": "Graph build started."}


def get_graph_html(articles_dir: str) -> str | None:
    wiki_dir = os.path.join(articles_dir, "..", "wiki")
    graph_path = os.path.join(os.path.normpath(wiki_dir), "graphify-out", "graph.html")
    if os.path.isfile(graph_path):
        with open(graph_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def graph_query(question: str, articles_dir: str) -> str:
    wiki_dir = os.path.join(articles_dir, "..", "wiki")
    graph_path = os.path.join(os.path.normpath(wiki_dir), "graphify-out", "graph.json")
    if not os.path.isfile(graph_path):
        return "No knowledge graph found. Build it first."

    try:
        result = subprocess.run(
            ["graphify", "query", question, "--graph", graph_path, "--budget", "2000"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout.strip() if result.returncode == 0 else f"Query failed: {result.stderr[:200]}"
    except FileNotFoundError:
        return "graphify CLI not found."
    except Exception as e:
        return f"Error: {str(e)}"
