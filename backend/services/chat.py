import json
import os
import requests


_state = {
    "context_files": [],
    "context_contents": [],
    "history": [],
}


def get_context():
    files = _state["context_files"]
    total_size = sum(len(c) for c in _state["context_contents"])
    return {
        "files": files,
        "count": len(files),
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
    _state["history"] = []


def remove_context(file_path: str) -> dict:
    if file_path in _state["context_files"]:
        idx = _state["context_files"].index(file_path)
        _state["context_files"].pop(idx)
        _state["context_contents"].pop(idx)
    return {"total": len(_state["context_files"])}


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


def chat_stream(message: str, host: str, model: str):
    system_prompt = build_system_prompt()

    messages = [{"role": "system", "content": system_prompt}]
    for h in _state["history"]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    url = f"{host.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "stream": True,
    }

    full_response = ""
    try:
        with requests.post(url, json=payload, timeout=120, stream=True) as resp:
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_response += content
                        yield f"data: {json.dumps({'chunk': content})}\n\n"
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        error_msg = f"Error connecting to Ollama: {e}"
        full_response = error_msg
        yield f"data: {json.dumps({'chunk': error_msg})}\n\n"

    _state["history"].append({"role": "user", "content": message})
    _state["history"].append({"role": "assistant", "content": full_response})

    yield "data: [DONE]\n\n"


def clear_history():
    _state["history"] = []


def get_history():
    return _state["history"]
