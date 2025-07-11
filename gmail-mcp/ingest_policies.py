import json
import os
from rag_engine import embed_and_index_policies

def main():
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'policies_templates.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        policies = json.load(f)
    print(f"Loaded {len(policies)} policies/templates. Ingesting into Pinecone...")
    embed_and_index_policies(policies)
    print("Ingestion complete.")

if __name__ == "__main__":
    main() 