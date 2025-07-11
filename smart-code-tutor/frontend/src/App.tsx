import React, { useState, useRef, useEffect } from 'react';
import Editor from './Editor';
import ReactMarkdown from 'react-markdown';
import { editor as monacoEditor } from 'monaco-editor';
import {  diff_match_patch, DIFF_INSERT, DIFF_DELETE } from 'diff-match-patch';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

function App() {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState<'python' | 'javascript'>('python');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [explanation, setExplanation] = useState('');
  const [chat, setChat] = useState<Array<{ role: string; content: string }>>([]);
  const [chatInput, setChatInput] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const [llmCodeBlocks, setLlmCodeBlocks] = useState<string[]>([]);
  const [selectedCodeBlockIdx, setSelectedCodeBlockIdx] = useState<number | null>(null);
  const [showDiff, setShowDiff] = useState(false);
  const [pendingDiff, setPendingDiff] = useState<{ newCode: string; addedLines: number[]; removedLines: number[] } | null>(null);
  const editorRef = useRef<monacoEditor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<any>(null);

  const connectWebSocket = () => {
    if (wsRef.current) return;
    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
    };
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // For RUN action
        if ('output' in data || 'error' in data) {
          setOutput(data.output || '');
          setError(data.error || '');
        }
        // For EXPLAIN action
        if ('explanation' in data) {
          setExplanation(data.explanation || '');
          const blocks = extractAllCodeBlocks(data.explanation || '');
          setLlmCodeBlocks(blocks);
          setChat((prev) => [
            ...prev,
            { role: 'explanation', content: data.explanation || '' }
          ]);
        }
        // For error fallback
        if (data.error && !('output' in data)) {
          setChat((prev) => [
            ...prev,
            { role: 'error', content: data.error }
          ]);
        }
      } catch {
        // fallback: do nothing
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
      setOutput('');
      setError('');
      setExplanation('');
      wsRef.current?.send(JSON.stringify({ action: 'run', code, language }));
    }, 100); // ensure connection is open
  };

  const sendChat = () => {
    if (!chatInput.trim()) return;
    if (!wsRef.current) connectWebSocket();
    setTimeout(() => {
      setChat((prev) => [
        ...prev,
        { role: 'user', content: chatInput }
      ]);
      wsRef.current?.send(
        JSON.stringify({
          action: 'explain',
          code,
          language,
          output,
          error,
          user_message: chatInput
        })
      );
      setChatInput('');
    }, 100);
  };

  // Utility: Generate merged diff string and line highlights
  function generateMergedDiff(oldCode: string, newCode: string) {
    const dmp = new diff_match_patch();
    const diffs = dmp.diff_main(oldCode, newCode);
    dmp.diff_cleanupSemantic(diffs);
    let mergedLines: string[] = [];
    let addedLines: number[] = [];
    let removedLines: number[] = [];
    let lineNum = 1;
    diffs.forEach(([op, text]) => {
      const lines = text.split('\n');
      if (op === DIFF_DELETE) {
        lines.forEach((line) => {
          mergedLines.push('// - ' + line);
          removedLines.push(lineNum);
          lineNum++;
        });
      } else if (op === DIFF_INSERT) {
        lines.forEach((line) => {
          mergedLines.push(line);
          addedLines.push(lineNum);
          lineNum++;
        });
      } else {
        lines.forEach((line) => {
          mergedLines.push(line);
          lineNum++;
        });
      }
    });
    return { merged: mergedLines.join('\n'), addedLines, removedLines };
  }

  // When a new explanation is received, extract the first code block and generate merged diff
  useEffect(() => {
    if (explanation) {
      if (/^\s*code breakdown[:：]/i.test(explanation)) {
        setPendingDiff(null); // Do not show diffs for explanations
        return;
      }
      const newCode = extractFirstCodeBlock(explanation);
      if (newCode && newCode !== code) {
        const { merged, addedLines, removedLines } = generateMergedDiff(code, newCode);
        setPendingDiff({ newCode: merged, addedLines, removedLines });
      } else {
        setPendingDiff(null);
      }
    } else {
      setPendingDiff(null);
    }
  }, [explanation]);

  // Apply decorations for merged diff
  useEffect(() => {
    if (!editorRef.current || !pendingDiff) return;
    const editor = editorRef.current;
    const model = editor.getModel();
    if (!model) return;
    let decorations: string[] = [];
    let newDecorations: monacoEditor.IModelDeltaDecoration[] = [];
    pendingDiff.addedLines.forEach((line) => {
      newDecorations.push({
        range: new monacoRef.current.Range(line, 1, line, 1),
        options: {
          isWholeLine: true,
          className: 'monaco-diff-bg-green',
        },
      });
    });
    pendingDiff.removedLines.forEach((line) => {
      newDecorations.push({
        range: new monacoRef.current.Range(line, 1, line, 1),
        options: {
          isWholeLine: true,
          className: 'monaco-diff-bg-red',
        },
      });
    });
    decorations = editor.deltaDecorations([], newDecorations);
    return () => {
      editor.deltaDecorations(decorations, []);
    };
  }, [pendingDiff]);

  // Accept/Discard handlers
  const handleAcceptDiff = () => {
    if (pendingDiff) {
      // Accept only the added and unchanged lines (skip removed lines)
      const finalLines = pendingDiff.newCode
        .split('\n')
        .filter((line, idx) => !pendingDiff.removedLines.includes(idx + 1))
        .map((line) => (line.startsWith('// - ') ? '' : line));
      setCode(finalLines.join('\n'));
      setPendingDiff(null);
      setExplanation('');
    }
  };
  const handleDiscardDiff = () => {
    setPendingDiff(null);
    setExplanation('');
  };

  // When user selects a code block, show the diff modal
  React.useEffect(() => {
    if (selectedCodeBlockIdx !== null) {
      setShowDiff(true);
    }
  }, [selectedCodeBlockIdx]);

  // Editor onMount to get ref
  const handleEditorMount = (editor: monacoEditor.IStandaloneCodeEditor, monaco: any) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
  };

  return (
    <div className="min-h-screen bg-[#23222b] text-white flex flex-row w-full h-screen">
      {/* Editor Area */}
      <div className="flex flex-col w-4/5 h-full justify-start p-8">
        <h1 className="text-3xl font-bold mb-4">Blursor</h1>
        <div className='flex justify-between items-center'>
          <div className="mb-2 flex items-center gap-4">
            <label htmlFor="language" className="font-semibold">Language:</label>
            <select
              id="language"
              value={language}
              onChange={e => setLanguage(e.target.value as 'python' | 'javascript')}
              className="bg-[#23222b] text-white px-2 py-1 rounded border border-gray-700"
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
            </select>
          </div>
          <button
            className="mt-4 px-4 py-2 bg-purple-600 rounded hover:bg-purple-700 w-fit"
            onClick={sendCode}
          >
            RUN
          </button>
        </div>
        <div className="flex-1 min-h-0">
          <Editor
            language={language}
            value={pendingDiff ? pendingDiff.newCode : code}
            onChange={(value) => setCode(value ?? '')}
            height="100%"
            onMount={handleEditorMount}
          />
        </div>
        {pendingDiff && (
          <div className="flex gap-4 mt-4 justify-end">
            <button
              className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 text-white font-semibold"
              onClick={handleAcceptDiff}
            >
              Accept
            </button>
            <button
              className="px-4 py-2 rounded bg-red-600 hover:bg-red-700 text-white font-semibold"
              onClick={handleDiscardDiff}
            >
              Discard
            </button>
          </div>
        )}
        {/* Mock Terminal */}
        <div className="mt-4 bg-black text-green-400 rounded p-4 min-h-[150px] max-h-60 overflow-y-auto font-mono text-sm">
          {output && <div><span className="text-green-400">$ </span>{output}</div>}
          {error && <div className="text-red-400"><span className="text-red-400">$ </span>{error}</div>}
          {!output && !error && <span className="text-gray-500">No output yet.</span>}
        </div>
      </div>
      {/* Chat Area */}
      <div className="flex flex-col w-2/5 h-full bg-[#23222b] p-0 border-l border-gray-700 relative">
        <div className="flex flex-col h-full">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {chat.map((msg, idx) => (
              <div
                key={idx}
                className={
                  msg.role === 'user'
                    ? 'flex justify-end'
                    : 'flex justify-start'
                }
              >
                <div
                  className={
                    'max-w-[75%] bg-gradient-to-br from-[#2d2c3a] to-[#23222b] text-gray-100 rounded-2xl px-4 py-3 shadow-md border border-[#35344a]'
                  }
                >
                  {msg.role === 'user' ? (
                    <span className="font-semibold">You: </span>
                  ) : (
                    <span className="font-semibold text-purple-400">AI Tutor: </span>
                  )}
                  {msg.role === 'explanation' ? (
                    <ReactMarkdown
                      components={{
                        code({ node, inline, className, children, ...props }) {
                          return !inline ? (
                            <SyntaxHighlighter
                              style={vscDarkPlus}
                              language={className?.replace('language-', '') || 'python'}
                              PreTag="div"
                              className="rounded-lg my-2"
                              customStyle={{ padding: '1em', background: '#181825', fontSize: '0.95em' }}
                            >
                              {String(children).replace(/\n$/, '')}
                            </SyntaxHighlighter>
                          ) : (
                            <code className="bg-[#23222b] px-1 rounded text-purple-300" {...props}>{children}</code>
                          );
                        },
                        pre({ node, children, ...props }) {
                          return <pre className="my-2" {...props}>{children}</pre>;
                        },
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    <span>{msg.content}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
          {/* Chat input fixed at the bottom */}
          <div className="w-full bg-[#23222b] border-t border-gray-700 p-4 flex gap-2 sticky bottom-0 z-10">
            <input
              className="flex-1 rounded-full bg-[#181825] px-4 py-2 text-white border border-gray-600 focus:outline-none shadow focus:ring-2 focus:ring-blue-500"
              type="text"
              placeholder="Ask about your code or error..."
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') sendChat(); }}
            />
            <button
              className="bg-purple-600 px-5 py-2 rounded-full text-white font-semibold shadow hover:bg-purple-700 transition"
              onClick={sendChat}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Utility: Extract first code block from markdown string
function extractFirstCodeBlock(markdown: string): string | null {
  const codeBlockRegex = /```[a-zA-Z]*\n([\s\S]*?)```/m;
  const match = codeBlockRegex.exec(markdown);
  if (match && match[1]) {
    return match[1].trim();
  }
  return null;
}

// Utility: Extract all code blocks from markdown string
function extractAllCodeBlocks(markdown: string): string[] {
  const codeBlockRegex = /```[a-zA-Z]*\n([\s\S]*?)```/gm;
  const matches = [];
  let match;
  while ((match = codeBlockRegex.exec(markdown)) !== null) {
    if (match[1]) {
      matches.push(match[1].trim());
    }
  }
  return matches;
}

export default App;
// Optionally export extractFirstCodeBlock for use in other components
export { extractFirstCodeBlock, extractAllCodeBlocks };
