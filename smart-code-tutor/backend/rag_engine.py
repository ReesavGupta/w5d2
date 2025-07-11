from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_nomic import NomicEmbeddings
from langchain_groq import ChatGroq
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from pydantic.types import SecretStr
from dotenv import load_dotenv

load_dotenv()
# Load environment variables for API keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
NOMIC_API_KEY = os.getenv("NOMIC_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 1. Initialize Nomic Embeddings
embeddings = NomicEmbeddings(nomic_api_key=NOMIC_API_KEY, model="nomic-embed-text-v1.5")

# 2. Initialize Pinecone with error handling
index_name = "code-docs-index"
vector_store = None
index = None

try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    # Check if index exists and has correct dimension
    if not pc.has_index(index_name):
        try:
            created_index = pc.create_index(
                name=index_name,
                dimension=768,
                spec=ServerlessSpec(cloud="aws", region="us-east-1")  # Adjust as needed
            )
        except Exception as e:
            print(f"Error creating Pinecone index: {e}")
    index = pc.Index(name=index_name)
    vector_store = PineconeVectorStore(embedding=embeddings, index=index)
except Exception as e:
    print(f"Error connecting to Pinecone: {e}")

# 3. Text splitters for docs
python_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.PYTHON, chunk_size=512, chunk_overlap=0)
javascript_splitter = RecursiveCharacterTextSplitter.from_language(language=Language.JS, chunk_size=256, chunk_overlap=0)

# 4. Embed and index documentation

def embed_and_index_docs(docs: list[str], language: str = "python"):
    """
    Embed and index documentation strings into Pinecone.
    :param docs: List of documentation strings
    :param language: 'python' or 'javascript'
    """
    if not vector_store:
        print("Pinecone vector store not initialized.")
        return
    if language == "python":
        splitter = python_splitter
    elif language == "javascript":
        splitter = javascript_splitter
    else:
        raise ValueError("Unsupported language for splitting.")
    texts = []
    metadatas = []
    for doc in docs:
        for chunk in splitter.split_text(doc):
            texts.append(chunk)
            metadatas.append({"source": "doc", "language": language})
    # Use vector_store.add_texts for upserting
    try:
        vector_store.add_texts(texts, metadatas=metadatas)
    except Exception as e:
        print(f"Error upserting to Pinecone: {e}")

# 5. Retrieve relevant docs

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

# 6. Generate explanation with Groq LLM

def generate_explanation(code: str, output: str, error: str, retrieved_docs: list[str]):
    """
    Generate an explanation using Groq LLM and retrieved docs.
    """
    if not GROQ_API_KEY:
        return
    llm = ChatGroq(api_key=SecretStr(GROQ_API_KEY), model="meta-llama/llama-4-scout-17b-16e-instruct")
    prompt = f"""
        You are a code tutor. Given the following code, output, error, and documentation, explain what happened and how to fix any issues.

        Code:
        {code}

        Output:
        {output}

        Error:
        {error}

        Relevant Documentation:
        {retrieved_docs}

        Step-by-step explanation:
    """
    return llm.invoke(prompt) 