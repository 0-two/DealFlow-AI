'use client';

import { useEffect, useMemo, useState } from 'react';
import Header from '@/components/Layout/Header';
import ProtectedRoute from '@/components/Auth/ProtectedRoute';
import { LanguageCode } from '@/lib/types';
import { ChevronDown, ChevronUp, ExternalLink, Globe2, Loader2, MessageCircle } from 'lucide-react';
import { queryAPI } from '@/lib/api';

type WebResult = {
  title: string;
  url: string;
  content: string;
  score?: number;
  published_date?: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function NewsPage() {
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<WebResult[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [aiInput, setAiInput] = useState<Record<string, string>>({});
  const [aiAnswer, setAiAnswer] = useState<Record<string, string>>({});
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});
  const [visibleCount, setVisibleCount] = useState(5);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const query = useMemo(
    () =>
      'Trending news on Indian startup ecosystem, funding, VC, policy, IPO, acquisitions',
    []
  );

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_URL}/api/query/web-search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, max_results: 10 }),
        });
        if (!res.ok) throw new Error('Failed to fetch news');
        const data = await res.json();
        const items = (data?.results || []).filter((r: WebResult) => r.title && r.url);
        setResults(items);
        setHasMore(items.length >= 5); // assume more may exist only if at least one page
      } catch (e: any) {
        setError(e?.message || 'Something went wrong');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [query]);

  const onAskAI = async (id: string, item: WebResult) => {
    const prompt = aiInput[id];
    if (!prompt) return;
    setAiLoading((s) => ({ ...s, [id]: true }));
    setAiAnswer((s) => ({ ...s, [id]: '' }));
    try {
      const snippet = (item.content || '').slice(0, 600);
      let userQuery = `About this news: ${item.title}\nURL: ${item.url}\nSnippet: ${snippet}\n\nQuestion: ${prompt}`;
      if (userQuery.length > 1800) userQuery = userQuery.slice(0, 1800);
      await queryAPI.askStream(
        {
          query: userQuery,
          language: selectedLanguage,
        },
        (chunk) => setAiAnswer((s) => ({ ...s, [id]: (s[id] || '') + chunk })),
        () => setAiLoading((s) => ({ ...s, [id]: false }))
      );
    } catch (e) {
      setAiLoading((s) => ({ ...s, [id]: false }));
    }
  };

  const visibleItems = results.slice(0, visibleCount);

  const loadMore = async () => {
    // If we already have hidden items, just reveal next 5
    if (visibleCount < results.length) {
      setVisibleCount((c) => c + 5);
      return;
    }
    // Otherwise fetch next batch excluding already seen URLs
    setLoadingMore(true);
    try {
      const res = await fetch(`${API_URL}/api/query/web-search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          max_results: 10,
          page: Math.floor(results.length / 5) + 1,
          page_size: 5,
          exclude_urls: results.map((r) => r.url),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        const newItems: WebResult[] = (data?.results || []).filter((r: WebResult) => r.title && r.url);
        if (newItems.length > 0) {
          setResults((prev) => [...prev, ...newItems]);
          setVisibleCount((c) => c + 5);
        } else {
          // No more items from backend, stop offering load more
          setHasMore(false);
        }
      }
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <Header selectedLanguage={selectedLanguage} onLanguageChange={setSelectedLanguage} />

        <main className="max-w-5xl mx-auto px-4 py-8">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-1">Startup Ecosystem News</h1>
            <p className="text-gray-600">Latest headlines across funding, deals, policy, and markets</p>
          </div>

          {loading && (
            <div className="flex items-center gap-2 text-gray-600"><Loader2 className="w-5 h-5 animate-spin"/> Loading news…</div>
          )}
          {error && (
            <div className="bg-red-50 text-red-700 border border-red-200 rounded-lg p-3 mb-4">{error}</div>
          )}

          <div className="flex flex-col gap-4">
            {visibleItems.map((item, idx) => {
              const id = `${idx}-${item.url}`;
              const isOpen = expanded === id;
              const hostname = (() => { try { return new URL(item.url).hostname; } catch { return ''; } })();
              return (
                <div key={id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                  <div className="p-5 flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-3">
                      <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-lg font-semibold text-indigo-700 hover:underline flex-1">
                        {item.title}
                      </a>
                      <button
                        onClick={() => setExpanded(isOpen ? null : id)}
                        className="px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50 flex items-center gap-1"
                      >
                        {isOpen ? <ChevronUp className="w-4 h-4"/> : <ChevronDown className="w-4 h-4"/>}
                        {isOpen ? 'Collapse' : 'Expand'}
                      </button>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Globe2 className="w-4 h-4"/>
                      <span>{hostname}</span>
                      {item.published_date && <span>• {new Date(item.published_date).toLocaleDateString()}</span>}
                    </div>
                    <p className="text-gray-700 line-clamp-2">{item.content}</p>
                  </div>

                  {isOpen && (
                    <div className="border-t border-gray-200 p-5 bg-gray-50">
                      <p className="text-gray-800 mb-3">{item.content}</p>
                      <div className="mt-4">
                        <label className="text-sm font-medium text-gray-700">Ask AI about this news</label>
                        <div className="mt-2 flex gap-2">
                          <input
                            value={aiInput[id] || ''}
                            onChange={(e) => setAiInput((s) => ({ ...s, [id]: e.target.value }))}
                            placeholder="e.g., Why is this important? Impact for founders?"
                            className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                          />
                          <button
                            onClick={() => onAskAI(id, item)}
                            disabled={aiLoading[id] || !(aiInput[id] || '').trim()}
                            className="px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                          >
                            <MessageCircle className="w-4 h-4"/>
                            Ask
                          </button>
                        </div>
                        {(aiAnswer[id] || aiLoading[id]) && (
                          <div className="mt-3 bg-white border rounded-lg p-3 text-sm text-gray-800 min-h-[48px]">
                            {aiLoading[id] && <span className="text-gray-500">Thinking…</span>}
                            <span>{aiAnswer[id]}</span>
                          </div>
                        )}
                      </div>

                      <div className="mt-4">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-700 font-medium"
                        >
                          <ExternalLink className="w-4 h-4"/>
                          Open full article
                        </a>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Load more */}
          {!loading && (
            <div className="mt-6 flex justify-center">
              <button
                onClick={loadMore}
                disabled={loadingMore || !hasMore}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {loadingMore ? 'Loading…' : hasMore ? 'Load more news' : 'No more news'}
              </button>
            </div>
          )}
        </main>
      </div>
    </ProtectedRoute>
  );
}
