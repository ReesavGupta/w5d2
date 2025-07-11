// --- Configurable Backend URLs ---
// Set these in a <script> tag before main.js is loaded, e.g.:
// <script>window.BACKEND_API_URL = 'https://your-backend.onrender.com'; window.BACKEND_WS_URL = 'wss://your-backend.onrender.com';</script>
const API_URL = window.BACKEND_API_URL || 'http://localhost:8000';
const WS_URL = window.BACKEND_WS_URL || 'ws://localhost:8000';

// --- Live Stock Price (SSE) ---
let stockEventSource = null;
const stockSymbolInput = document.getElementById('stock-symbol');
const subscribeBtn = document.getElementById('subscribe-stock');
const stockPriceDiv = document.getElementById('stock-price');

function subscribeStock() {
  const symbol = stockSymbolInput.value.trim().toUpperCase();
  if (!symbol) return;
  if (stockEventSource) stockEventSource.close();
  stockPriceDiv.textContent = 'Connecting...';
  stockEventSource = new EventSource(`${API_URL}/sse/stock/${symbol}`);
  stockEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.price) {
        stockPriceDiv.textContent = `${data.symbol}: $${data.price.toFixed(2)} (as of ${data.timestamp})`;
        stockPriceDiv.style.color = '#34d399';
      } else if (data.error) {
        stockPriceDiv.textContent = data.error;
        stockPriceDiv.style.color = '#f87171';
      }
    } catch (e) {
      stockPriceDiv.textContent = 'Error parsing data.';
      stockPriceDiv.style.color = '#f87171';
    }
  };
  stockEventSource.onerror = () => {
    stockPriceDiv.textContent = 'Connection error or API limit reached.';
    stockPriceDiv.style.color = '#f87171';
  };
}

subscribeBtn.addEventListener('click', subscribeStock);
window.addEventListener('DOMContentLoaded', subscribeStock);

// --- Trending News Feed ---
const newsList = document.getElementById('news-list');
function fetchNews() {
  fetch(`${API_URL}/news/trending`)
    .then(res => res.json())
    .then(data => {
      newsList.innerHTML = '';
      (data.articles || []).forEach(article => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = article.url;
        a.textContent = article.title;
        a.target = '_blank';
        li.appendChild(a);
        newsList.appendChild(li);
      });
    })
    .catch(() => {
      newsList.innerHTML = '<li>Failed to fetch news.</li>';
    });
}
window.addEventListener('DOMContentLoaded', fetchNews);

// --- Real-Time Multi-User Chat (WebSocket) ---
const chatHistoryDiv = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');
const sendChatBtn = document.getElementById('send-chat');

let userName = localStorage.getItem('stockchat-username');
if (!userName) {
  userName = prompt('Enter your name for chat:') || 'User';
  localStorage.setItem('stockchat-username', userName);
}

let ws = null;
function connectChatWS() {
  ws = new WebSocket(`${WS_URL.replace('http', 'ws')}/ws/chat`);
  ws.onopen = () => {
    appendChat('system', 'Connected to chat.');
  };
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      appendChat(msg.user, msg.message);
    } catch {}
  };
  ws.onclose = () => {
    appendChat('system', 'Disconnected. Reconnecting in 2s...');
    setTimeout(connectChatWS, 2000);
  };
}
connectChatWS();

function appendChat(user, content) {
  const div = document.createElement('div');
  if (user === userName) {
    div.className = 'user-msg';
    div.textContent = `You: ${content}`;
  } else if (user === 'AI') {
    div.className = 'ai-msg';
    div.textContent = `AI: ${content}`;
  } else if (user === 'system') {
    div.className = 'ai-msg';
    div.textContent = content;
  } else {
    div.className = 'ai-msg';
    div.textContent = `${user}: ${content}`;
  }
  chatHistoryDiv.appendChild(div);
  chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
}

sendChatBtn.addEventListener('click', () => {
  const msg = chatInput.value.trim();
  if (!msg || !ws || ws.readyState !== 1) return;
  ws.send(JSON.stringify({ user: userName, message: msg }));
  chatInput.value = '';
});

chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    sendChatBtn.click();
  }
});

// --- AI Recommendation Button (separate from real-time chat) ---
const aiBtn = document.createElement('button');
aiBtn.textContent = 'Ask AI';
aiBtn.style.marginLeft = '0.5rem';
document.querySelector('.chat-input-row').appendChild(aiBtn);
aiBtn.addEventListener('click', () => {
  const msg = chatInput.value.trim();
  if (!msg) return;
  appendChat(userName, msg);
  chatInput.value = '';
  fetch(`${API_URL}/recommendations?user_query=${encodeURIComponent(msg)}`)
    .then(res => res.json())
    .then(data => {
      appendChat('AI', data.recommendation || 'No answer.');
    })
    .catch(() => {
      appendChat('AI', 'Error getting recommendation.');
    });
}); 