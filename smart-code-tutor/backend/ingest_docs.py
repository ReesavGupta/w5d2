from langchain_community.document_loaders import PyPDFLoader
from rag_engine import embed_and_index_docs
import os

def main():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    docs = [
        (os.path.join(data_dir, 'Python Fundamentals Documentation.pdf'), 'python'),
        (os.path.join(data_dir, 'JavaScript Fundamentals Documentation.pdf'), 'javascript'),
    ]
    for pdf_path, language in docs:
        print(f"Extracting and ingesting {pdf_path} as {language}...")
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()  # This returns a list of Document objects, one per page
        # Optionally, you can concatenate or further split these
        page_texts = [doc.page_content for doc in pages]
        embed_and_index_docs(page_texts, language=language)
        print(f"Ingested {pdf_path}.")

if __name__ == "__main__":
    main() 