'use client';

import { Message } from '@/lib/types';
import SourceCard from './SourceCard';
import { User, Bot } from 'lucide-react';

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex gap-3 max-w-3xl ${isUser ? 'flex-row-reverse' : ''}`}>
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-indigo-600' : 'bg-gray-700'
        }`}>
          {isUser ? <User className="w-5 h-5 text-white" /> : <Bot className="w-5 h-5 text-white" />}
        </div>

        <div className={`flex flex-col gap-2 ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`px-4 py-3 rounded-2xl ${
            isUser 
              ? 'bg-indigo-600 text-white' 
              : 'bg-white text-gray-800 shadow-md'
          }`}>
            <p className="whitespace-pre-wrap">{message.content}</p>
          </div>

          {message.sources && message.sources.length > 0 && (
            <div className="w-full space-y-2 mt-2">
              <p className="text-sm font-medium text-gray-600">Sources:</p>
              {message.sources.map((source, index) => (
                <SourceCard key={index} source={source} index={index + 1} />
              ))}
            </div>
          )}

          <span className="text-xs text-gray-500">
            {message.timestamp.toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
}
