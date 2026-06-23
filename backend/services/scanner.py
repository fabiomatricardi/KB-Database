import json
import os
import threading
import requests


_scan_state = {
    "running": False,
    "current_file": "",
    "processed": 0,
    "total": 0,
    "message": "",
}


def get_scan_status() -> dict:
    return dict(_scan_state)


def extract_metadata(host: str, model: str, file_content: str) -> dict:
    system_prompt = "You are a precise data extractor. Your job is to extract metadata from articles and output ONLY raw valid JSON."

    user_prompt = f"""
    Analyze the following article text and extract:
    1. Title
    2. Subheading (if any, otherwise provide a brief hook)
    3. Original URL (look for links, source URLs, or metadata at the top/bottom. If not found, output "None")
    4. A short summary (2-3 sentences)
    5. Table of Contents (list of section headings found in the article, or empty list if none)
    6. Tags (3-5 relevant topic tags/hashtags for categorization, lowercase, no # prefix)

    Respond ONLY with a valid JSON object matching this schema. Do not include markdown formatting like ```json or any conversational text.
    {{
        "title": "string",
        "subheading": "string",
        "url": "string",
        "summary": "string",
        "toc": ["string"],
        "tags": ["string"]
    }}

    Article Content:
    {file_content}
    """

    url = f"{host.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        response_text = result["choices"][0]["message"]["content"].strip()
        response_text = response_text.strip("`").removeprefix("json\n").strip()
        return json.loads(response_text)
    except Exception as e:
        return {
            "title": "Extraction Failed",
            "subheading": "Error during LLM processing",
            "url": "None",
            "summary": f"Could not process file. Error: {str(e)}",
        }


def _run_scan_thread(host: str, model: str, directory: str, database_path: str):
    global _scan_state
    _scan_state["running"] = True
    _scan_state["message"] = "Starting scan..."

    if os.path.exists(database_path):
        with open(database_path, "r", encoding="utf-8") as f:
            database = json.load(f)
    else:
        database = []

    processed_files = {entry.get("filename") for entry in database}

    supported_extensions = (".txt", ".md", ".html")
    files_to_process = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(supported_extensions) and file not in processed_files:
                files_to_process.append(os.path.join(root, file))

    _scan_state["total"] = len(files_to_process)
    _scan_state["processed"] = 0

    for file_path in files_to_process:
        file = os.path.basename(file_path)
        _scan_state["current_file"] = file
        _scan_state["message"] = f"Processing: {file}..."

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            metadata = extract_metadata(host, model, content)
            metadata["filename"] = file
            metadata["file_path"] = file_path
            database.append(metadata)
        except Exception as e:
            print(f"Error reading file {file}: {e}")

        _scan_state["processed"] += 1

    with open(database_path, "w", encoding="utf-8") as f:
        json.dump(database, f, indent=4, ensure_ascii=False)

    _scan_state["running"] = False
    _scan_state["message"] = f"Scan complete. {len(database)} entries in database."
    _scan_state["current_file"] = ""


def start_scan(host: str, model: str, directory: str, database_path: str) -> dict:
    if _scan_state["running"]:
        return {"error": "A scan is already in progress."}

    thread = threading.Thread(
        target=_run_scan_thread,
        args=(host, model, directory, database_path),
        daemon=True,
    )
    thread.start()
    return {"status": "Scan started."}
