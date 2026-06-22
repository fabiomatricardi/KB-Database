import os
import json
import argparse
import requests

def parse_arguments():
    parser = argparse.ArgumentParser(description="Scan folder and extract article metadata using Ollama.")
    parser.add_argument("-d", "--dir", required=True, help="Path to the folder containing articles.")
    parser.add_argument("-o", "--host", default="http://localhost:11434", help="Ollama host IP/URL (default: http://localhost:11434).")
    parser.add_argument("-m", "--model", default="llama3", help="Ollama model to use (default: llama3).")
    parser.add_argument("-db", "--database", default="articles_db.json", help="Path to the output JSON database.")
    return parser.parse_args()

def extract_metadata(host: str, model: str, file_content: str) -> dict:
    # Setup OpenAI structural instructions 
    system_prompt = "You are a precise data extractor. Your job is to extract metadata from articles and output ONLY raw valid JSON."
    
    user_prompt = f"""
    Analyze the following article text and extract:
    1. Title
    2. Subheading (if any, otherwise provide a brief hook)
    3. Original URL (look for links, source URLs, or metadata at the top/bottom. If not found, output "None")
    4. A short summary (2-3 sentences)

    Respond ONLY with a valid JSON object matching this schema. Do not include markdown formatting like ```json or any conversational text.
    {{
        "title": "string",
        "subheading": "string",
        "url": "string",
        "summary": "string"
    }}

    Article Content:
    {file_content}
    """
    
    # Notice the corrected OpenAI compatible path mapping
    url = f"{host.rstrip('/')}/v1/chat/completions"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.0, # Zero variance ensures structural accuracy
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        # Extract content out of the classic OpenAI schema response tree
        response_text = result['choices'][0]['message']['content'].strip()
        
        # Clean up code blocks if the local model ignored instructions
        response_text = response_text.strip("`").removeprefix("json\n").strip()
        return json.loads(response_text)
        
    except Exception as e:
        return {
            "title": "Extraction Failed",
            "subheading": "Error during LLM processing",
            "url": "None",
            "summary": f"Could not process file. Error: {str(e)}"
        }

def main():
    args = parse_arguments()
    
    # Load or initialize DB
    if os.path.exists(args.database):
        with open(args.database, 'r', encoding='utf-8') as f:
            database = json.load(f)
    else:
        database = []

    processed_files = {entry['filename'] for entry in database}

    print(f"Scanning directory: {args.dir} using Python 3.12 environment...")
    
    supported_extensions = ('.txt', '.md', '.html')
    for root, _, files in os.walk(args.dir):
        for file in files:
            if file.endswith(supported_extensions) and file not in processed_files:
                file_path = os.path.join(root, file)
                print(f"Processing: {file}...")
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    metadata = extract_metadata(args.host, args.model, content)
                    metadata['filename'] = file
                    metadata['file_path'] = file_path
                    
                    database.append(metadata)
                except Exception as e:
                    print(f"Error reading file {file}: {e}")

    with open(args.database, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=4, ensure_ascii=False)
        
    print(f"\nScanning complete. Database saved to '{args.database}' with {len(database)} entries.")

if __name__ == "__main__":
    main()