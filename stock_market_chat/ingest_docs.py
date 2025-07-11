import os
import requests
from rag_engine import embeddings, vector_store
from langchain.text_splitter import RecursiveCharacterTextSplitter

def fetch_trending_news():
    """Fetch trending news articles directly from NewsAPI."""
    NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")
    if not NEWSAPI_API_KEY or NEWSAPI_API_KEY == "demo":
        print("NEWSAPI_API_KEY not set in environment.")
        return []
    url = "https://newsapi.org/v2/top-headlines"
    params = {"category": "business", "apiKey": NEWSAPI_API_KEY}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [article["title"] + ". " + article.get("description", "") for article in data.get("articles", [])]
    except Exception as e:
        print(f"Error fetching news from NewsAPI: {e}")
        return []

def ingest_news_articles():
    news_texts = fetch_trending_news()
    if not news_texts:
        print("No news articles to ingest.")
        return
    splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=0)
    texts = []
    metadatas = []
    for article in news_texts:
        for chunk in splitter.split_text(article):
            texts.append(chunk)
            metadatas.append({"source": "news"})
    if vector_store:
        try:
            vector_store.add_texts(texts, metadatas=metadatas)
            print(f"Ingested {len(texts)} news chunks into Pinecone.")
        except Exception as e:
            print(f"Error upserting news to Pinecone: {e}")
    else:
        print("Vector store not initialized.")

def ingest_analyst_reports():
    # Placeholder: Ingest analyst reports from files, APIs, or other sources
    print("Analyst report ingestion not implemented yet.")

def main():
    print("Ingesting news articles...")
    ingest_news_articles()
    print("Ingesting analyst reports...")
    ingest_analyst_reports()
    print("Done.")

if __name__ == "__main__":
    main() 