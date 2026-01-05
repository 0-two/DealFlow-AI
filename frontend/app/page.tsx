'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { queryAPI } from '@/lib/api';
import { Message, LanguageCode } from '@/lib/types';
import ChatInterface from '@/components/Chat/ChatInterface';
import Header from '@/components/Layout/Header';

export default function Home() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('hi');
  const [isLoading, setIsLoading] = useState(true);

  // Check if user has selected a role
  useEffect(() => {
    const role = localStorage.getItem('userRole');
    if (!role) {
      // Redirect to role selection if no role is set
      router.push('/role-select');
    } else {
      setIsLoading(false);
    }
  }, [router]);

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
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      language: selectedLanguage,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    queryMutation.mutate({
      query,
      language: selectedLanguage,
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

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
