'use client';

import { useState, useEffect } from 'react';
import { queryAPI } from '@/lib/api';
import { Message, LanguageCode } from '@/lib/types';
import ChatInterface from '@/components/Chat/ChatInterface';
import Header from '@/components/Layout/Header';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import { useAuth } from '@/contexts/AuthContext';

function ChatPageContent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('hi');
  const { profile } = useAuth();
  const userRole = profile?.role;

  useEffect(() => {
    if (userRole) {
      // Add welcome message based on role
      const welcomeMessage: Message = {
        id: 'welcome',
        role: 'assistant',
        content: userRole === 'founder' 
          ? 'Hello! I\'m here to help you with funding insights, investor information, and government schemes. Ask me anything about your startup journey!'
          : 'Hello! I\'m here to help you discover promising startups, analyze funding trends, and provide investment insights. How can I assist you today?',
        language: 'en',
        timestamp: new Date(),
      };
      setMessages([welcomeMessage]);
    }
  }, [userRole]);

  const [isStreaming, setIsStreaming] = useState(false);

  const handleSendMessage = async (query: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      language: selectedLanguage,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Placeholder assistant message to stream into
    const streamId = `stream-${Date.now()}`;
    const placeholder: Message = {
      id: streamId,
      role: 'assistant',
      content: '',
      language: selectedLanguage,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, placeholder]);
    setIsStreaming(true);

    await queryAPI.askStream(
      { query, language: selectedLanguage },
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
        // Update sources immediately when they arrive
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

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header 
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
      />
      {roleBanner}
      
      <main className="flex-1 overflow-hidden">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isStreaming}
        />
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
