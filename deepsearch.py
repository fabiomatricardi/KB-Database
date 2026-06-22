import os
import argparse
from rank_bm25 import BM25Okapi

def parse_arguments():
    parser = argparse.ArgumentParser(description="Deep search a folder and its subfolders using BM25.")
    parser.add_argument("-d", "--dir", required=True, help="Path to the folder to search over.")
    parser.add_argument("-q", "--query", required=True, help="The search query.")
    parser.add_argument("-n", "--top_n", type=int, default=3, help="Number of results to return.")
    return parser.parse_args()

def tokenize(text: str) -> list[str]:
    # Standard lowercase space-splitting to match search.py exactly
    return text.lower().split()

def main():
    args = parse_arguments()

    if not os.path.isdir(args.dir):
        print(f"Error: Directory '{args.dir}' does not exist.")
        return

    # 1. Scan directory and subfolders for text-based files
    supported_extensions = ('.txt', '.md', '.html')
    file_registry = [] # Keeps track of file paths and metadata
    corpus = []        # Holds tokenized contents for BM25

    print(f"Indexing files in '{args.dir}' and subfolders...")

    for root, _, files in os.walk(args.dir):
        for file in files:
            if file.endswith(supported_extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Store tracking info
                    file_registry.append({
                        "filename": file,
                        "file_path": file_path,
                        "preview": content[:150].replace('\n', ' ') + "..." # Snippet for display
                    })
                    
                    # Tokenize full text content for the index corpus
                    corpus.append(tokenize(content))
                    
                except Exception as e:
                    # Silently skip files that fail to read (e.g., permission issues)
                    continue

    if not corpus:
        print("No valid text, markdown, or HTML files found to index.")
        return

    print(f"Successfully indexed {len(corpus)} documents. Running BM25 search...")

    # 2. Initialize BM25 pipeline
    bm25 = BM25Okapi(corpus)
    tokenized_query = tokenize(args.query)
    scores = bm25.get_scores(tokenized_query)
    
    # 3. Pair documents with scores and sort by highest relevance
    results = sorted(zip(file_registry, scores), key=lambda x: x[1], reverse=True)

    print(f"\n--- Top {args.top_n} Deep Search Results for: '{args.query}' ---\n")
    
    count = 0
    for doc, score in results:
        if score == 0: 
            continue  # Skip files with absolutely no matching terms
        if count >= args.top_n:
            break
            
        print(f"Rank: {count + 1} | Score: {score:.4f}")
        print(f"File:    {doc['filename']}")
        print(f"Path:    {doc['file_path']}")
        print(f"Snippet: {doc['preview']}")
        print("-" * 50)
        count += 1

    if count == 0:
        print("No matches found in any local file contents.")

if __name__ == "__main__":
    main()