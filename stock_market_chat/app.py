import streamlit as st
import requests
import time
import json

st.set_page_config(page_title="Stock Market Chat", layout="wide")
st.title("📈 Real-Time Stock Market Chat")

# --- Stock Symbol Input and Real-Time Price Display ---
st.header("Live Stock Price")
stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL)", value="AAPL")
price_placeholder = st.empty()

# Polling for real-time price updates (avoid background thread issues)
def poll_stock_price(symbol, placeholder):
    url = f"http://localhost:8000/stock/{symbol}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "price" in data:
            placeholder.metric(label=f"{symbol} Price", value=f"${data['price']:.2f}", delta=data["timestamp"])
        elif "error" in data:
            placeholder.warning(data["error"])
    except Exception as e:
        placeholder.error(f"Error: {e}")

if stock_symbol:
    poll_stock_price(stock_symbol, price_placeholder)
    st.button("Refresh Price", on_click=lambda: poll_stock_price(stock_symbol, price_placeholder))

# --- Trending News Feed ---
st.header("Trending Financial News")
news_area = st.empty()
def fetch_news():
    try:
        resp = requests.get("http://localhost:8000/news/trending", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        news_area.write("\n".join([f"- [{a['title']}]({a['url']})" for a in articles]))
    except Exception as e:
        news_area.error(f"Failed to fetch news: {e}")
fetch_news()

# --- Chat and Recommendations ---
st.header("AI-Powered Stock Chat")
chat_history = st.session_state.setdefault("chat_history", [])

def clear_input():
    st.session_state["chat_input"] = ""

user_input = st.text_input("Ask a question or request a recommendation:", key="chat_input")
if st.button("Send", on_click=clear_input) and user_input:
    chat_history.append({"role": "user", "content": user_input})
    # Call recommendations endpoint
    try:
        resp = requests.get("http://localhost:8000/recommendations", params={"user_query": user_input}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("recommendation", "No answer.")
        chat_history.append({"role": "ai", "content": answer})
    except Exception as e:
        chat_history.append({"role": "ai", "content": f"Error: {e}"})

for msg in chat_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")

# TODO: Add multi-user session, streaming chat, and better UI/UX 