'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { queryAPI } from '@/lib/api';
import { Message, LanguageCode } from '@/lib/types';
import ChatInterface from '@/components/Chat/ChatInterface';
import Header from '@/components/Layout/Header';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('hi');

  const queryMutation = useMutation({
    mutationFn: queryAPI.ask,
    onSuccess: (data) => {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: data.answer,
        language: data.language,
        sources: data.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    },
  });

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

    // Send to API
    queryMutation.mutate({
      query,
      language: selectedLanguage,
    });
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header 
        selectedLanguage={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
      />
      
      <main className="flex-1 overflow-hidden">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={queryMutation.isPending}
        />
      </main>
    </div>
  );
}
