'use client';

import { useState } from 'react';
import { Source } from '@/lib/types';
import { ChevronDown, ChevronUp, ExternalLink, FileText, Newspaper, Building, Database } from 'lucide-react';

interface Props {
  source: Source;
  index: number;
}

const typeIcons = {
  article: Newspaper,
  report: FileText,
  policy: Building,
  database: Database,
  web: ExternalLink,
};

export default function SourceCard({ source, index }: Props) {
  const [isExpanded, setIsExpanded] = useState(index <= 2);

  const Icon = typeIcons[source.type || 'web'] || ExternalLink;

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-indigo-100">
            <Icon className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="text-left flex-1">
            <p className="font-medium text-gray-900 line-clamp-1">{source.title}</p>
            {source.url && (
              <p className="text-xs text-gray-500 line-clamp-1">{new URL(source.url).hostname}</p>
            )}
          </div>
        </div>
        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
      </button>

      {isExpanded && (
        <div className="px-4 pb-3 border-t border-gray-200">
          <p className="text-sm text-gray-600 mt-3 mb-2">{source.snippet}</p>
          
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700 mt-2 font-medium"
            >
              Read full article <ExternalLink className="w-3 h-3" />
            </a>
          )}
          
          {source.published_date && (
            <p className="text-xs text-gray-500 mt-2">Published: {source.published_date}</p>
          )}
        </div>
      )}
    </div>
  );
}
