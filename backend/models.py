from pydantic import BaseModel


class Article(BaseModel):
    title: str = ""
    subheading: str = ""
    url: str = ""
    summary: str = ""
    filename: str = ""
    file_path: str = ""


class SearchResult(BaseModel):
    rank: int
    score: float
    article: Article


class SearchResponse(BaseModel):
    query: str
    top_n: int
    results: list[SearchResult]
    total_found: int


class DeepSearchResult(BaseModel):
    rank: int
    score: float
    filename: str
    file_path: str
    snippet: str


class DeepSearchResponse(BaseModel):
    query: str
    top_n: int
    results: list[DeepSearchResult]
    total_indexed: int
    total_found: int


class ScanRequest(BaseModel):
    directory: str = ".\\articles\\"
    host: str = "http://localhost:11434"
    model: str = "llama3"
    database: str = "articles_db.json"


class ScanStatus(BaseModel):
    running: bool
    current_file: str = ""
    processed: int = 0
    total: int = 0
    message: str = ""


class AppConfig(BaseModel):
    host: str = "http://localhost:11434"
    model: str = "llama3"
    articles_dir: str = ".\\articles\\"
    database: str = "articles_db.json"
    server_port: int = 8000


class ChatMessage(BaseModel):
    message: str


class ChatContextRequest(BaseModel):
    file_paths: list[str]
