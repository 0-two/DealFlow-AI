'use client';

import { useRef, useEffect } from 'react';
import { Message } from '@/lib/types';
import MessageBubble from './MessageBubble';
import InputBox from './InputBox';
import { Sparkles } from 'lucide-react';

interface Props {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

export default function ChatInterface({ messages, onSendMessage, isLoading }: Props) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const exampleQueries = [
    { text: 'मुझे एडटेक के लिए निवेशक चाहिए', lang: 'hi' },
    { text: '2024 में सबसे ज्यादा funding किस sector में हुई?', lang: 'hi' },
    { text: 'Startup India scheme की जानकारी दो', lang: 'hi' },
    { text: 'Who are the top fintech investors in Bangalore?', lang: 'en' },
  ];

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto px-4">
      {messages.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="text-center mb-8">
            <Sparkles className="w-16 h-16 mx-auto mb-4 text-indigo-600" />
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              Startup Funding Intelligence
            </h1>
            <p className="text-gray-600 text-lg">
              Ask me anything about investors, funding trends, or government schemes
            </p>
            <p className="text-gray-500 mt-2">
              अपनी भाषा में पूछें | Ask in your language
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-3xl mb-8">
            {exampleQueries.map((query, index) => (
              <button
                key={index}
                onClick={() => onSendMessage(query.text)}
                className="p-4 text-left bg-white rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200 hover:border-indigo-300"
              >
                <p className="text-sm text-gray-700">{query.text}</p>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto py-6 space-y-6">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="flex items-center space-x-2 text-gray-500">
              <div className="animate-bounce">●</div>
              <div className="animate-bounce delay-100">●</div>
              <div className="animate-bounce delay-200">●</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      <div className="pb-6">
        <InputBox onSend={onSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}
