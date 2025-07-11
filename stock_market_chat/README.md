# Auto Email Responder

## Project Overview

This project is an **intelligent email response system** that retrieves company policies and generates appropriate responses using Gmail MCP. It is designed to streamline email handling by leveraging semantic search, caching, and batch processing, ensuring fast and relevant replies based on company policies, FAQs, and templates.

---

## Live Demo

- **Frontend:** [https://w5d2-qsif2qbzx-waglogy.vercel.app/](https://w5d2-qsif2qbzx-waglogy.vercel.app/)
- **Backend:** [https://w5d2.onrender.com](https://w5d2.onrender.com)

---

## Features

- **Store company policies, FAQs, and response templates**
- **Batch process emails** for efficient handling
- **Gmail integration** for receiving and sending emails
- **Semantic search** for relevant policies and templates
- **Prompt caching** for frequently accessed responses
- **Automated, context-aware email replies**

---

## Technical Stack

- **Frontend:** Static HTML/CSS/JS (deployed on Vercel)
- **Backend:** FastAPI, Pinecone, Nomic embeddings, LangChain RAG, Gmail MCP, and more (deployed on Render)

---

## Environment Variables

### Frontend
Set these in your Vercel project settings:
- `BACKEND_API_URL` — e.g. `https://w5d2.onrender.com`
- `BACKEND_WS_URL` — e.g. `wss://w5d2.onrender.com/ws/chat`

### Backend
Set these in your Render project settings as needed for:
- Gmail MCP credentials
- Pinecone API keys
- NewsAPI, Finnhub, etc.

---

## Local Development

### Backend
```bash
cd stock_market_chat
python -m venv .venv
source .venv/Scripts/activate  # or .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
Just open `index.html` in your browser, or use a static server:
```bash
cd stock_market_chat
python -m http.server 3000
```

---

## Usage
1. **Connect your Gmail MCP account** (see backend docs for setup).
2. **Store company policies, FAQs, and templates** in the backend.
3. **Batch process incoming emails** — the system will semantically search for relevant policies and generate responses.
4. **Send responses** via Gmail MCP integration.

---

## Deliverables
- Gmail-integrated response system
- Batch processing with prompt caching
- Semantic search for policies/templates
- FastAPI backend and static frontend

---

## Repository
- [GitHub Repo](https://github.com/ReesavGupta/w5d2)

---

## License
MIT 