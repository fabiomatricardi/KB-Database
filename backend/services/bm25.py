import json
import os
from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return text.lower().split()


def search_database(query: str, database_path: str, top_n: int = 5) -> dict:
    if not os.path.exists(database_path):
        return {"error": f"Database file '{database_path}' not found."}

    with open(database_path, "r", encoding="utf-8") as f:
        database = json.load(f)

    if not database:
        return {"error": "The database is empty."}

    corpus = []
    for doc in database:
        searchable_text = f"{doc.get('title', '')} {doc.get('subheading', '')} {doc.get('summary', '')}"
        corpus.append(tokenize(searchable_text))

    bm25 = BM25Okapi(corpus)
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    results = sorted(zip(database, scores), key=lambda x: x[1], reverse=True)

    matched = []
    for doc, score in results:
        if score == 0:
            continue
        matched.append({"rank": len(matched) + 1, "score": round(float(score), 4), "article": doc})

    return {
        "query": query,
        "top_n": top_n,
        "results": matched[:top_n],
        "total_found": len(matched),
    }


def deepsearch_directory(query: str, directory: str, top_n: int = 5, database_path: str | None = None) -> dict:
    if not os.path.isdir(directory):
        return {"error": f"Directory '{directory}' does not exist."}

    db_lookup = {}
    if database_path and os.path.exists(database_path):
        with open(database_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        for entry in db:
            fname = entry.get("filename", "")
            if fname:
                db_lookup[fname] = entry

    supported_extensions = (".txt", ".md", ".html")
    file_registry = []
    corpus = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(supported_extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    file_registry.append({
                        "filename": file,
                        "file_path": file_path,
                        "preview": content[:150].replace("\n", " ") + "...",
                    })
                    corpus.append(tokenize(content))
                except Exception:
                    continue

    if not corpus:
        return {"query": query, "top_n": top_n, "results": [], "total_indexed": 0, "total_found": 0}

    bm25 = BM25Okapi(corpus)
    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    results = sorted(zip(file_registry, scores), key=lambda x: x[1], reverse=True)

    matched = []
    for doc, score in results:
        if score == 0:
            continue
        meta = db_lookup.get(doc["filename"], {})
        matched.append({
            "rank": len(matched) + 1,
            "score": round(float(score), 4),
            "filename": doc["filename"],
            "file_path": doc["file_path"],
            "snippet": doc["preview"],
            "title": meta.get("title", ""),
            "subheading": meta.get("subheading", ""),
            "url": meta.get("url", ""),
            "summary": meta.get("summary", ""),
        })

    return {
        "query": query,
        "top_n": top_n,
        "results": matched[:top_n],
        "total_indexed": len(corpus),
        "total_found": len(matched),
    }
