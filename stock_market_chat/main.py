from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
import httpx
import threading
import time
import finnhub
from rag_engine import retrieve_relevant_docs, generate_recommendation
from ingest_docs import ingest_news_articles
import re

app = FastAPI()

# Enable CORS for all origins (for local development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY", "demo")

# Finnhub client
finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

# --- Automated News Ingestion Background Task ---
def news_ingestion_worker():
    while True:
        print("[Ingestion] Fetching and indexing latest news...")
        try:
            ingest_news_articles()
        except Exception as e:
            print(f"[Ingestion] Error: {e}")
        time.sleep(3600)  # Run every hour

@app.on_event("startup")
def start_news_ingestion():
    threading.Thread(target=news_ingestion_worker, daemon=True).start()

@app.get("/health")
def health_check():
    return JSONResponse({"status": "ok"})

# --- WebSocket Multi-User Chat ---
chat_history = []  # In-memory chat history
active_connections = set()  # Set of active WebSocket connections

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    # Send chat history to the new client
    for msg in chat_history:
        await websocket.send_json(msg)
    try:
        while True:
            data = await websocket.receive_json()
            # data: {"user": ..., "message": ...}
            chat_msg = {"user": data.get("user", "User"), "message": data.get("message", "")}
            chat_history.append(chat_msg)
            # Broadcast to all clients
            for conn in list(active_connections):
                try:
                    await conn.send_json(chat_msg)
                except Exception:
                    active_connections.discard(conn)
    except WebSocketDisconnect:
        active_connections.discard(websocket)
    except Exception:
        active_connections.discard(websocket)

# --- SSE Real-Time Stock Price Streaming (Finnhub) ---
@app.get("/sse/stock/{symbol}")
async def sse_stock_price(symbol: str, interval: int = 5):
    async def event_generator():
        while True:
            try:
                quote = finnhub_client.quote(symbol)
                if not quote or quote.get("c") is None:
                    yield f"data: {{\"error\": \"No data or invalid symbol.\"}}\n\n"
                else:
                    price = quote["c"]
                    timestamp = int(time.time())
                    yield f"data: {{\"symbol\": \"{symbol}\", \"price\": {price}, \"timestamp\": {timestamp}}}\n\n"
            except finnhub.FinnhubAPIException as e:
                yield f"data: {{\"error\": \"Finnhub API error: {str(e)}\"}}\n\n"
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            await asyncio.sleep(interval)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- SSE Real-Time Chat Streaming ---
@app.get("/chat/stream")
async def chat_stream():
    async def event_generator():
        # Placeholder: In production, stream real chat messages here
        for i in range(5):
            yield f"data: Message {i}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- Stock Data Retrieval (Finnhub) ---
@app.get("/stock/{symbol}")
async def get_stock_data(symbol: str):
    try:
        quote = finnhub_client.quote(symbol)
        if not quote or quote.get("c") is None:
            raise HTTPException(status_code=404, detail="No data or invalid symbol.")
        price = quote["c"]
        timestamp = int(time.time())
        return {"symbol": symbol, "price": price, "timestamp": timestamp}
    except finnhub.FinnhubAPIException as e:
        raise HTTPException(status_code=429, detail=f"Finnhub API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stock data fetch error: {str(e)}")

# --- Trending News Retrieval (NewsAPI Integration) ---
@app.get("/news/trending")
async def get_trending_news():
    url = "https://newsapi.org/v2/top-headlines"
    params = {"category": "business", "apiKey": NEWSAPI_API_KEY}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            articles = [
                {"title": a["title"], "url": a["url"]}
                for a in data.get("articles", [])
            ]
            return {"articles": articles}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"News fetch error: {str(e)}")
    # TODO: Add caching to reduce API calls

def extract_symbol(user_query):
    # Simple regex for uppercase ticker, or use Finnhub symbol lookup for more robust
    match = re.search(r'\b[A-Z]{1,5}\b', user_query)
    return match.group(0) if match else None

# --- AI-Powered Stock Recommendations (RAG Integration, with live price) ---
@app.get("/recommendations")
async def get_recommendations(user_query: str = "What stocks should I buy today?"):
    symbol = extract_symbol(user_query)
    stock_data = None
    if symbol:
        try:
            stock_data = finnhub_client.quote(symbol)
        except Exception as e:
            stock_data = {"error": str(e)}
    relevant_docs = retrieve_relevant_docs(user_query, top_k=3)
    if not relevant_docs:
        raise HTTPException(status_code=500, detail="No relevant documents found or vector store not initialized.")
    # Compose context for LLM
    context = f"User Query: {user_query}\n"
    if stock_data and 'c' in stock_data:
        context += f"Latest {symbol} price: {stock_data['c']}, Open: {stock_data['o']}, High: {stock_data['h']}, Low: {stock_data['l']}, Prev Close: {stock_data['pc']}\n"
    elif stock_data and 'error' in stock_data:
        context += f"Error fetching {symbol} price: {stock_data['error']}\n"
    context += f"Relevant News: {relevant_docs}\n"
    try:
        recommendation = generate_recommendation(context, [])
        return {"recommendation": str(getattr(recommendation, 'content', recommendation))}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation generation error: {str(e)}") 