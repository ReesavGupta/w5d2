import React, { useState, useRef } from 'react';
import Editor from './Editor';

function App() {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState<'python' | 'javascript'>('python');
  const [wsMessage, setWsMessage] = useState('');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const wsRef = useRef<WebSocket | null>(null);

  const connectWebSocket = () => {
    if (wsRef.current) return;
    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setOutput(data.output || '');
        setError(data.error || '');
        setWsMessage('');
      } catch {
        setOutput('');
        setError('');
        setWsMessage(event.data); // fallback for legacy string responses
      }
    };
    wsRef.current.onclose = () => {
      wsRef.current = null;
      console.log('WebSocket disconnected');
    };
    wsRef.current.onerror = (err) => {
      console.error('WebSocket error:', err);
    };
  };

  const sendCode = () => {
    if (!wsRef.current) connectWebSocket();
    setTimeout(() => {
      wsRef.current?.send(JSON.stringify({ code, language }));
    }, 100); // ensure connection is open
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold mb-4">Smart Code Tutor</h1>
      <div className="w-full max-w-3xl">
        <div className="mb-2 flex items-center gap-4">
          <label htmlFor="language" className="font-semibold">Language:</label>
          <select
            id="language"
            value={language}
            onChange={e => setLanguage(e.target.value as 'python' | 'javascript')}
            className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-700"
          >
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
          </select>
        </div>
        <Editor
          language={language}
          value={code}
          onChange={(value) => setCode(value ?? '')}
        />
        <button
          className="mt-4 px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
          onClick={sendCode}
        >
          Send to Backend
        </button>
        <div className="mt-4 p-2 bg-gray-800 rounded min-h-[40px]">
          {output && (
            <div><strong>Output:</strong><pre className="whitespace-pre-wrap text-white">{output}</pre></div>
          )}
          {error && (
            <div><strong className="text-red-400">Error:</strong> <pre className="whitespace-pre-wrap text-red-400">{error}</pre></div>
          )}
          {wsMessage && (
            <div><strong>Backend Response:</strong> {wsMessage}</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
