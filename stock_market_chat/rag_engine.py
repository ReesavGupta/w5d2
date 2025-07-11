import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_nomic import NomicEmbeddings
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.schema import Document
from pydantic.types import SecretStr
from dotenv import load_dotenv

load_dotenv()

# Load environment variables for API keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
NOMIC_API_KEY = os.getenv("NOMIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 1. Initialize Nomic Embeddings
embeddings = NomicEmbeddings(nomic_api_key=NOMIC_API_KEY, model="nomic-embed-text-v1.5")

# 2. Initialize Pinecone
index_name = "stock-market-index"
vector_store = None
index = None
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if not pc.has_index(index_name):
        try:
            pc.create_index(
                name=index_name,
                dimension=768,
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        except Exception as e:
            print(f"Error creating Pinecone index: {e}")
    index = pc.Index(name=index_name)
    vector_store = PineconeVectorStore(embedding=embeddings, index=index)
except Exception as e:
    print(f"Error connecting to Pinecone: {e}")

# 3. Retrieve relevant docs for a query
def retrieve_relevant_docs(query: str, top_k: int = 3):
    """
    Retrieve top_k relevant docs from Pinecone for a given query.
    :param query: Query string
    :param top_k: Number of docs to retrieve
    :return: List of matched document texts
    """
    if not vector_store:
        print("Pinecone vector store not initialized.")
        return []
    try:
        results = vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []

# 4. Generate stock recommendation using Groq LLM and retrieved docs
def generate_recommendation(user_query: str, retrieved_docs: list[str]):
    """
    Generate a stock recommendation using Groq LLM and relevant docs.
    """
    if not GROQ_API_KEY:
        return "Groq API key not set."
    llm = ChatGroq(api_key=SecretStr(GROQ_API_KEY), model="meta-llama/llama-4-scout-17b-16e-instruct")
    prompt = f"""
You are a financial assistant. Given the following user query and relevant market/news data, provide a personalized stock recommendation with reasoning.

User Query:
{user_query}

Relevant Data:
{retrieved_docs}

Recommendation:
"""
    return llm.invoke(prompt)

# TODO: Add document ingestion and indexing for news, analyst reports, and market data 