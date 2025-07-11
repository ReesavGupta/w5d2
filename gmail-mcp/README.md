# Intelligent Gmail Auto Email Responder

Automatically process incoming emails, retrieve relevant company policies, and generate contextually appropriate responses using semantic search, a vector database, and a large language model (LLM).

## Features
- Gmail integration via FastMCP (fetch, send, mark processed)
- Store/search company policies, FAQs, and response templates
- Semantic search with Pinecone and Nomic embeddings
- LLM-based response generation (Groq via LangChain)
- Batch email processing with idempotency
- Caching, logging, and compliance review
- Admin CRUD for policies/templates

## Setup
1. **Clone the repo and enter the directory:**
   ```bash
   git clone <repo-url>
   cd gmail-mcp
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your API keys.
   - Download Gmail API `credentials.json` from Google Cloud Console and place in project root.
4. **Ingest policies/templates:**
   ```bash
   python ingest_policies.py
   ```
5. **Run batch email processing:**
   ```bash
   python process_email_batch.py
   ```

## Usage
- **Manage policies/templates:**
  ```bash
  python manage_policies.py [list|add|update|delete]
  ```
- **Test the pipeline:**
  ```bash
  python test_pipeline.py
  ```
- **Review compliance logs:**
  - See `logs/email_responder.jsonl` for a structured audit trail.

## Security Notes
- All credentials and tokens are loaded from `.env` or environment variables.
- `.env`, `token.json`, `credentials.json`, and logs are in `.gitignore`.
- Never commit sensitive files to version control.

## License
MIT 