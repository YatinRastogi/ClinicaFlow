// src/ChatPanel.tsx
import React from 'react';
import { Send, Loader2 } from 'lucide-react';

interface Message {
  sender: 'ai' | 'user';
  text: string;
}

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage, isLoading }) => {
  const [input, setInput] = React.useState('');
  const bottomRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (trimmed && !isLoading) {
      onSendMessage(trimmed);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="fixed bottom-5 right-5 w-96 h-[520px] bg-white rounded-xl shadow-2xl flex flex-col border border-gray-200 z-50">
      {/* Header */}
      <div className="bg-indigo-600 text-white p-3 rounded-t-xl flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <h3 className="font-semibold text-sm">AI Follow-up Questions</h3>
        </div>
        <span className="text-indigo-200 text-xs">{messages.length} message{messages.length !== 1 ? 's' : ''}</span>
      </div>

      {/* Messages */}
      <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-2">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`max-w-[82%] px-3 py-2 rounded-lg text-sm leading-relaxed ${
              msg.sender === 'ai'
                ? 'bg-gray-100 text-gray-800 self-start rounded-tl-sm'
                : 'bg-indigo-600 text-white self-end rounded-tr-sm ml-auto'
            }`}
          >
            {msg.text}
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div className="self-start bg-gray-100 px-3 py-2 rounded-lg rounded-tl-sm flex items-center gap-1">
            <Loader2 size={12} className="animate-spin text-gray-500" />
            <span className="text-xs text-gray-500">AI is thinking…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-gray-100 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isLoading ? 'Waiting for AI…' : 'Type your answer…'}
          className="flex-1 p-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:bg-gray-50 disabled:text-gray-400 transition"
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className="bg-indigo-600 text-white px-3 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
          aria-label="Send"
        >
          {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </div>
    </div>
  );
};