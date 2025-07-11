# Stock Market Chat Frontend (HTML/CSS/JS)

## Features
- Live stock price updates (SSE)
- Trending financial news
- AI-powered stock chat and recommendations

## How to Use
1. **Start the FastAPI backend:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
2. **Open `index.html` in your browser.**
   - No build step needed; just open the file directly.
   - For full CORS/SSE support, you may want to serve via a local web server:
     ```bash
     cd stock-market-chat
     python -m http.server 8080
     # Then visit http://localhost:8080/index.html
     ```
3. **Use the app:**
   - Enter a stock symbol and click Subscribe for live price updates.
   - View trending news.
   - Chat with the AI for recommendations.

## Requirements
- Modern browser (Chrome, Firefox, Edge, Safari)
- FastAPI backend running on localhost:8000

---

> For advanced features, consider integrating with a JS framework (React, Vue, etc.) 