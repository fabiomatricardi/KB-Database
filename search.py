import json
import os
import argparse
from rank_bm25 import BM25Okapi

def parse_arguments():
    parser = argparse.ArgumentParser(description="Search the article database using BM25.")
    parser.add_argument("-q", "--query", required=True, help="The search query.")
    parser.add_argument("-db", "--database", default="articles_db.json", help="Path to the JSON database.")
    parser.add_argument("-n", "--top_n", type=int, default=3, help="Number of results to return.")
    return parser.parse_args()

def tokenize(text: str) -> list[str]:
    return text.lower().split()

def main():
    args = parse_arguments()

    if not os.path.exists(args.database):
        print(f"Error: Database file '{args.database}' not found.")
        return

    with open(args.database, 'r', encoding='utf-8') as f:
        database = json.load(f)

    if not database:
        print("The database is empty.")
        return

    # Prepare corpus
    corpus = []
    for doc in database:
        searchable_text = f"{doc.get('title', '')} {doc.get('subheading', '')} {doc.get('summary', '')}"
        corpus.append(tokenize(searchable_text))

    bm25 = BM25Okapi(corpus)
    tokenized_query = tokenize(args.query)
    scores = bm25.get_scores(tokenized_query)
    
    results = sorted(zip(database, scores), key=lambda x: x[1], reverse=True)

    print(f"\n--- Top {args.top_n} Search Results for: '{args.query}' ---\n")
    
    count = 0
    for doc, score in results:
        if score == 0: 
            continue
        if count >= args.top_n:
            break
            
        print(f"Rank: {count + 1} | Score: {score:.4f}")
        print(f"Title:    {doc.get('title')}")
        print(f"Sub:      {doc.get('subheading')}")
        print(f"URL:      {doc.get('url')}")
        print(f"Source:   {doc.get('file_path')}")
        print(f"Summary:  {doc.get('summary')}")
        print("-" * 50)
        count += 1

    if count == 0:
        print("No matching articles found.")

if __name__ == "__main__":
    main()