import React, { useRef, useEffect } from 'react';
import MonacoEditor from '@monaco-editor/react';

interface EditorProps {
  language?: 'python' | 'javascript';
  value?: string;
  onChange?: (value: string | undefined) => void;
  height?: string;
  onMount?: (editor: any, monaco: any) => void;
}

const LANGUAGE_HINTS: Record<string, string> = {
  python: 'Hint: Use print() to output text. Example: print("Hello, World!")',
  javascript: 'Hint: Use console.log() to output text. Example: console.log("Hello, World!")',
};

const LANGUAGE_TEMPLATES: Record<string, string> = {
  python: 'print("Hello, World!")',
  javascript: 'console.log("Hello, World!");',
};

const Editor: React.FC<EditorProps> = ({ language = 'python', value = '', onChange, height = '400px', onMount }) => {
  const editorRef = useRef(null);
  const prevLanguage = useRef(language);

  // If language changes, update the code template if the editor is empty or default
  useEffect(() => {
    if (prevLanguage.current !== language && onChange) {
      if (!value || value === LANGUAGE_TEMPLATES[prevLanguage.current]) {
        onChange(LANGUAGE_TEMPLATES[language]);
      }
      prevLanguage.current = language;
    }
  }, [language, onChange, value]);

  return (
    <div className="h-full w-full border rounded overflow-hidden">
      <div className="text-xs text-gray-400 px-2 py-1 bg-gray-900 border-b border-gray-800">
        {LANGUAGE_HINTS[language]}
      </div>
      <MonacoEditor
        height={height}
        language={language}
        value={value}
        theme="vs-dark"
        onChange={onChange}
        onMount={onMount}
        options={{
          fontSize: 16,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: 'on',
        }}
      />
    </div>
  );
};

export default Editor; 