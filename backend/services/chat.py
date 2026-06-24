import json
import os
import requests


_state = {
    "context_files": [],
    "context_contents": [],
    "web_contexts": [],
    "history": [],
}


def get_context():
    files = _state["context_files"]
    web = _state["web_contexts"]
    total_size = sum(len(c) for c in _state["context_contents"])
    total_size += sum(len(w["content"]) for w in web)
    return {
        "files": files,
        "count": len(files),
        "web_contexts": web,
        "web_count": len(web),
        "total_chars": total_size,
    }


def load_context(file_paths: list[str]) -> dict:
    loaded = 0
    for fp in file_paths:
        if not os.path.isfile(fp):
            continue
        if fp in _state["context_files"]:
            continue
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            _state["context_files"].append(fp)
            _state["context_contents"].append(content)
            loaded += 1
        except Exception:
            continue
    return {"loaded": loaded, "total": len(_state["context_files"])}


def clear_context():
    _state["context_files"] = []
    _state["context_contents"] = []
    _state["web_contexts"] = []
    _state["history"] = []


def remove_context(file_path: str) -> dict:
    if file_path in _state["context_files"]:
        idx = _state["context_files"].index(file_path)
        _state["context_files"].pop(idx)
        _state["context_contents"].pop(idx)
    return {"total": len(_state["context_files"])}


def load_web_context(title: str, url: str, content: str) -> dict:
    for w in _state["web_contexts"]:
        if w["url"] == url:
            return {"loaded": 0, "total": len(_state["web_contexts"])}
    _state["web_contexts"].append({"title": title, "url": url, "content": content})
    return {"loaded": 1, "total": len(_state["web_contexts"])}


def remove_web_context(url: str) -> dict:
    _state["web_contexts"] = [w for w in _state["web_contexts"] if w["url"] != url]
    return {"total": len(_state["web_contexts"])}


def build_system_prompt() -> str:
    if not _state["context_contents"]:
        return "You are a helpful assistant. Answer questions based on your general knowledge."

    parts = [
        "Read the following articles and wait for further instructions. When you are done reading say \"I am ready\".",
        "",
        "[start of articles]",
    ]
    for fp, content in zip(_state["context_files"], _state["context_contents"]):
        parts.append("---")
        parts.append(f"File: {fp}")
        parts.append(content)

    parts.append("---")
    parts.append("[end of articles]")
    return "\n".join(parts)


def _build_web_injection(user_message: str) -> str:
    if not _state["web_contexts"]:
        return user_message

    parts = ["[Web context loaded]", ""]
    for w in _state["web_contexts"]:
        parts.append("---")
        parts.append(f"[Source: {w['title']} ({w['url']})]")
        parts.append(w["content"])
    parts.append("---")
    parts.append("")
    parts.append(f"User question: {user_message}")
    return "\n".join(parts)


def chat_stream(message: str, host: str, model: str):
    system_prompt = build_system_prompt()
    user_message = _build_web_injection(message)

    messages = [{"role": "system", "content": system_prompt}]
    for h in _state["history"]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    url = f"{host.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "stream": False,
    }

    full_response = ""
    try:
        resp = requests.post(url, json=payload, timeout=600)
        resp.raise_for_status()
        result = resp.json()
        full_response = result["choices"][0]["message"]["content"] or ""
    except Exception as e:
        full_response = f"Error connecting to Ollama: {e}"

    yield f"data: {json.dumps({'chunk': full_response})}\n\n"

    _state["history"].append({"role": "user", "content": message})
    _state["history"].append({"role": "assistant", "content": full_response})

    yield "data: [DONE]\n\n"


def clear_history():
    _state["history"] = []


def get_history():
    return _state["history"]
