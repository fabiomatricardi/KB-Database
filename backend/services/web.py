import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS


def web_search(query: str, max_results: int = 10) -> list[dict]:
    try:
        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")}
            for r in results
        ]
    except Exception as e:
        return [{"title": "Search error", "url": "", "snippet": str(e)}]


def web_fetch(url: str) -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else url

        body = soup.find("article") or soup.find("main") or soup.find("body")
        if body:
            text = body.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        content = "\n".join(lines)

        max_chars = 50000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[Content truncated...]"

        return {
            "title": title,
            "url": url,
            "content": content,
            "char_count": len(content),
        }
    except Exception as e:
        return {
            "title": "Fetch error",
            "url": url,
            "content": f"Failed to fetch URL: {e}",
            "char_count": 0,
        }
