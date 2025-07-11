import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_nomic import NomicEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic.types import SecretStr
import re

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
NOMIC_API_KEY = os.getenv("NOMIC_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

# 1. Initialize Nomic Embeddings
embeddings = NomicEmbeddings(nomic_api_key=NOMIC_API_KEY, model="nomic-embed-text-v1.5")

# 2. Initialize Pinecone
index_name = "gmail-policies-index"
vector_store = None
index = None

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    if not pc.has_index(index_name):
        try:
            created_index = pc.create_index(
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

# 3. Text splitter for policies/templates
splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=0)

# Simple in-memory caches
_semantic_search_cache = {}
_llm_response_cache = {}

def embed_and_index_policies(policies: list[dict]):
    """
    Embed and index policy/template data into Pinecone.
    :param policies: List of dicts (policies/templates)
    """
    if not vector_store:
        print("Pinecone vector store not initialized.")
        return
    texts = []
    metadatas = []
    for item in policies:
        # Use 'content', 'answer', or 'template' as text
        text = item.get("content") or item.get("answer") or item.get("template")
        if not text:
            continue
        for chunk in splitter.split_text(text):
            texts.append(chunk)
            metadatas.append({
                "id": item.get("id"),
                "type": item.get("type"),
                "title": item.get("title", item.get("question", "")),
                "tags": item.get("tags", [])
            })
    try:
        vector_store.add_texts(texts, metadatas=metadatas)
    except Exception as e:
        print(f"Error upserting to Pinecone: {e}")

def retrieve_relevant_policies(query: str, top_k: int = 3):
    """
    Retrieve top_k relevant policies/templates from Pinecone for a given query, with caching.
    :param query: Query string
    :param top_k: Number of docs to retrieve
    :return: List of dicts with 'page_content' and metadata
    """
    cache_key = (query, top_k)
    if cache_key in _semantic_search_cache:
        return _semantic_search_cache[cache_key]
    if not vector_store:
        print("Pinecone vector store not initialized.")
        return []
    try:
        results = vector_store.similarity_search(query, k=top_k)
        out = [
            {"page_content": doc.page_content, **(doc.metadata if hasattr(doc, 'metadata') else {})}
            for doc in results
        ]
        _semantic_search_cache[cache_key] = out
        return out
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []

def generate_draft_response(email_content: str, relevant_policies: list[str]) -> str:
    """
    Generate a draft response using Groq LLM and relevant policies/templates, with caching.
    :param email_content: The incoming email content
    :param relevant_policies: List of relevant policy/template texts
    :return: Draft response string
    """
    cache_key = (email_content, tuple(relevant_policies))
    if cache_key in _llm_response_cache:
        return _llm_response_cache[cache_key]
    if not groq_api_key:
        print("GROQ_API_KEY not set in environment.")
        return "[Error: LLM API key not configured.]"
    llm = ChatGroq(api_key=SecretStr(groq_api_key), model="meta-llama/llama-4-scout-17b-16e-instruct")
    prompt = f"""
        You are an automated support agent. Given the following customer email and relevant company policies/templates, draft a response that is accurate, helpful, and policy-compliant.

        Customer Email:
        {email_content}

        Relevant Policies/Templates:
        {relevant_policies}

        Draft Response:
    """
    result = llm.invoke(prompt)
    # Ensure result is always a string
    if hasattr(result, 'content'):
        response = result.content
    else:
        response = str(result)
    _llm_response_cache[cache_key] = response
    return response

def fill_template(template: str, variables: dict) -> str:
    """
    Substitute variables in the template string with values from the variables dict.
    """
    def replacer(match):
        key = match.group(1)
        return str(variables.get(key, f'{{{key}}}'))
    return re.sub(r'\{(\w+)\}', replacer, template)

def generate_response_with_template(email_content: str, relevant_policies: list[dict], variables: dict) -> str:
    """
    Try to use a template from relevant_policies. If found, fill variables. Otherwise, use LLM.
    :param email_content: The incoming email content
    :param relevant_policies: List of relevant policy/template dicts (with 'page_content' and metadata)
    :param variables: Dict of variables for substitution
    :return: Final response string
    """
    # Look for a template in relevant_policies
    for item in relevant_policies:
        if item.get('type') == 'template' and item.get('page_content'):
            return fill_template(item['page_content'], variables)
    # Fallback: use LLM
    texts = [str(item.get('page_content', '')) for item in relevant_policies]
    if not texts:
        return generate_draft_response(email_content, [''])
    return generate_draft_response(email_content, texts) 