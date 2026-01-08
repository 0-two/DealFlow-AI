'use client';

import { useState, useEffect, useMemo, useRef } from 'react';
import { queryAPI } from '@/lib/api';
import { Message, LanguageCode } from '@/lib/types';
import Header from '@/components/Layout/Header';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';
import MessageBubble from '@/components/Chat/MessageBubble';
import InputBox from '@/components/Chat/InputBox';
import { Sparkles } from 'lucide-react';

function ChatPageContent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedLanguage] = useState<LanguageCode>('en');
  const { profile } = useAuth();
  const userRole = profile?.role;
  const storageKey = useMemo(() => `chatMessages_${userRole || 'default'}`, [userRole]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load from localStorage on mount per role
  useEffect(() => {
    if (!userRole) return;
    try {
      const cached = localStorage.getItem(storageKey);
      if (cached) {
        const parsed: Message[] = JSON.parse(cached);
        setMessages(parsed);
      }
    } catch {}
  }, [userRole, storageKey]);

  // Persist messages per role
  useEffect(() => {
    if (!userRole) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify(messages));
    } catch {}
  }, [messages, storageKey, userRole]);

  const [isStreaming, setIsStreaming] = useState(false);

  const handleSendMessage = async (query: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      language: 'auto', // Let backend detect language
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Placeholder assistant message to stream into
    const streamId = `stream-${Date.now()}`;
    const placeholder: Message = {
      id: streamId,
      role: 'assistant',
      content: '',
      language: 'auto', // Will be updated when final event arrives
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, placeholder]);
    setIsStreaming(true);

    await queryAPI.askStream(
      { query, language: 'auto' }, // Let backend detect and respond in same language
      (chunk) => {
        // Ensure proper spacing between chunks
        setMessages((prev) => prev.map(m => {
          if (m.id === streamId) {
            const currentContent = m.content;
            // Add space before chunk if needed (not at start, not after space, not before punctuation)
            const needsSpace = currentContent.length > 0 && 
                             !currentContent.endsWith(' ') && 
                             !currentContent.endsWith('\n') &&
                             !/^[.,!?;:]/.test(chunk);
            return { ...m, content: currentContent + (needsSpace ? ' ' : '') + chunk };
          }
          return m;
        }));
      },
      (final) => {
        setMessages((prev) => prev.map(m => m.id === streamId ? { ...m, language: final.language || m.language } : m));
        setIsStreaming(false);
      },
      (sources) => {
        // Sources now come after answer completes (no delay needed)
        setMessages((prev) => prev.map(m => m.id === streamId ? { ...m, sources } : m));
      }
    );
  };

  const roleBanner = userRole && (
    <div className={`${userRole === 'founder' ? 'bg-indigo-50 border-indigo-200' : 'bg-green-50 border-green-200'} border-b px-4 py-2`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <p className={`text-sm ${userRole === 'founder' ? 'text-indigo-700' : 'text-green-700'}`}>
          <span className="font-semibold">
            {userRole === 'founder' ? '🚀 Founder Mode' : '💼 Investor Mode'}
          </span>
          {' - '}
          {userRole === 'founder' 
            ? 'Get insights about investors, funding trends, and government schemes'
            : 'Discover startups, analyze trends, and find investment opportunities'}
        </p>
      </div>
    </div>
  );

  const displayName = profile?.full_name || (profile?.email ? profile.email.split('@')[0] : 'there');
  const greetingBanner = (
    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-indigo-100 px-4 py-3">
      <div className="max-w-5xl mx-auto">
        <p className="text-lg text-gray-800">
          <span className="font-semibold text-indigo-700">Hello, {displayName}!</span>
          {' '}
          {userRole === 'founder' 
            ? 'I\'m here to help you with funding insights, investor information, and government schemes.'
            : 'I\'m here to help you discover promising startups, analyze funding trends, and provide investment insights.'}
        </p>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      {roleBanner}
      {greetingBanner}
      
      <main className="flex-1 overflow-hidden">
        <div className="flex flex-col h-full max-w-5xl mx-auto px-4">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="text-center">
                <Sparkles className="w-16 h-16 mx-auto mb-4 text-indigo-600" />
                <h1 className="text-4xl font-bold text-gray-800 mb-2">
                  DealFlow AI
                </h1>
                <p className="text-gray-600 text-lg">
                  Ask me anything about investors, funding trends, or government schemes
                </p>
                <p className="text-gray-500 mt-2">
                  अपनी भाषा में पूछें | Ask in your language
                </p>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto py-6 space-y-6">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
              {isStreaming && (
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
            <InputBox onSend={handleSendMessage} isLoading={isStreaming} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatPageContent />
    </ProtectedRoute>
  );
}
