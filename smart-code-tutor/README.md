# Smart Code Tutor

## 🚀 Overview

**Smart Code Tutor** is a full-stack AI-powered code assistant web app that lets users write, execute, and get intelligent explanations for Python and JavaScript code in real time. It combines a modern web-based code editor, secure sandboxed execution, and Retrieval-Augmented Generation (RAG) to provide step-by-step, context-aware explanations using relevant documentation.

---

## 🎥 Demo Video

<div align="center">
  <video src="./backend/public/recording.mp4" controls width="600">
    Your browser does not support the video tag.
  </video>
</div>

---

## 🧩 Problem Statement

> Build a full-stack code interpreter with a web-based code editor that can execute Python & JavaScript code and provide intelligent explanations using RAG-retrieved documentation with real-time streaming.

---

## 🛠️ Technical Requirements

- Interactive UI with Monaco code editor and syntax highlighting
- FastAPI backend with WebSocket support for streaming responses
- Embed and store docs, coding best practices, and error solutions in Pinecone (vector DB)
- E2B sandbox integration for secure, isolated code execution (Python, JS, TS)
- Real-time streaming of code execution results and RAG explanations to the client
- Asynchronous processing to handle multiple concurrent code executions
- Retrieve relevant docs based on code context and execution results, providing step-by-step explanations

---

## 🎯 Achievements & Features

- **Modern UI:**
  - Monaco Editor with language selection (Python/JavaScript)
  - Syntax highlighting, code templates, and language-specific hints
  - Chat-like interface for explanations, code generation, and debugging
  - Inline diffing for AI-suggested code changes (accept/discard with visual highlights)
  - Beautiful markdown and code block rendering
  - Unified color scheme and responsive design

- **Real-Time Streaming:**
  - WebSocket connection between frontend and backend for live code execution and output
  - Output and error streaming to a mock terminal in the frontend
  - Streaming of RAG-powered explanations and code suggestions

- **Secure & Scalable Execution:**
  - E2B sandboxed execution for Python, JavaScript, and TypeScript
  - Handles multiple concurrent users and executions using FastAPI async processing
  - All blocking operations (code execution, LLM, RAG) are offloaded for true concurrency

- **AI-Powered Assistance:**
  - RAG pipeline: Documentation PDFs are ingested, embedded (Nomic), and indexed in Pinecone
  - Backend retrieves relevant docs for every LLM query (generate, explain, modify, debug)
  - Groq LLM via LangChain for intent detection and specialized prompting
  - Step-by-step, context-aware explanations and error solutions

- **Robust UX:**
  - Suppresses diff UI for pure explanations ("Code breakdown" detection)
  - Sticky, rounded chat input and role-based chat bubbles
  - Output, error, and explanations are clearly separated and visually appealing

- **Performance & Reliability:**
  - Asynchronous backend ensures low-latency, high-concurrency handling
  - Secure sandboxing prevents code escape and abuse

---

## 🏗️ Architecture

- **Frontend:** React, TypeScript, Vite, Monaco Editor, Tailwind CSS, react-markdown, react-syntax-highlighter
- **Backend:** FastAPI (Python), E2B for sandboxed code execution, Pinecone (vector DB), Nomic embeddings, Groq LLM via LangChain
- **RAG Pipeline:** Documentation PDFs (Python, JS) are ingested, embedded, and indexed in Pinecone for retrieval

---

## 📦 Deliverables

- Full-stack application with code editor UI and chat assistant
- Streaming WebSocket implementation for real-time code execution and explanations
- E2B tool calling integration for secure sandboxed execution
- Performance analysis and robust handling of concurrent executions

---

## 📝 Setup & Usage

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd smart-code-tutor
   ```
2. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. **Install frontend dependencies:**
   ```bash
   cd ../frontend
   npm install
   ```
4. **Set up environment variables:**
   - Create a `.env` file in `backend/` with your API keys for E2B, Pinecone, Nomic, and Groq.
5. **Run the backend:**
   ```bash
   uvicorn main:app --reload
   ```
6. **Run the frontend:**
   ```bash
   npm run dev
   ```
7. **Open the app:**
   - Visit `http://localhost:5173` in your browser.

---

## 📊 Performance & Concurrency

- All blocking operations (code execution, LLM, RAG retrieval) are offloaded to threads, ensuring the backend can handle many concurrent users and executions without blocking.
- Real-time streaming ensures users see outputs and explanations as soon as they are available.

---

## 🏆 Why Smart Code Tutor?

- **Instant feedback:** Write, run, and debug code with live output and AI explanations.
- **Context-aware help:** Explanations are grounded in real documentation, not just LLM guesses.
- **Safe & scalable:** Secure sandboxing and async backend for robust, multi-user support.
- **Modern UX:** Clean, beautiful, and intuitive interface for both beginners and advanced users.

---

## 🙌 Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [E2B](https://e2b.dev/)
- [Pinecone](https://www.pinecone.io/)
- [Nomic](https://nomic.ai/)
- [Groq](https://groq.com/)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/)

---

**All changes saved.** 