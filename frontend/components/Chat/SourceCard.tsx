'use client';

import { useState } from 'react';
import { Source } from '@/lib/types';
import { ChevronDown, ChevronUp, ExternalLink, FileText, Newspaper, Building, Database, CheckCircle, AlertCircle, Shield } from 'lucide-react';

interface Props {
  source: Source;
  index: number;
}

const typeIcons = {
  article: Newspaper,
  report: FileText,
  policy: Building,
  database: Database,
};

export default function SourceCard({ source, index }: Props) {
  const [isExpanded, setIsExpanded] = useState(index <= 2);

  const Icon = typeIcons[source.type] || FileText;

  // Verification badge component
  const VerificationBadge = () => {
    if (source.verified === undefined) return null;
    
    if (source.verified) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
          <CheckCircle className="w-3 h-3" />
          Verified ({Math.round((source.verification_confidence || 0) * 100)}%)
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full">
          <AlertCircle className="w-3 h-3" />
          Unverified
        </span>
      );
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            source.verified ? 'bg-green-100' : 'bg-indigo-100'
          }`}>
            <Icon className={`w-4 h-4 ${source.verified ? 'text-green-600' : 'text-indigo-600'}`} />
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <p className="font-medium text-gray-900">[{index}] {source.title}</p>
              <VerificationBadge />
            </div>
            {source.date && (
              <p className="text-xs text-gray-500">{source.date}</p>
            )}
          </div>
        </div>
        {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
      </button>

      {isExpanded && (
        <div className="px-4 pb-3 border-t border-gray-200">
          <p className="text-sm text-gray-600 mt-3 mb-2">{source.snippet}</p>
          
          {/* Supporting web sources */}
          {source.supporting_web_sources && source.supporting_web_sources.length > 0 && (
            <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-700">Web Verification Sources</span>
              </div>
              <div className="space-y-2">
                {source.supporting_web_sources.map((webSource, i) => (
                  <div key={i} className="text-xs">
                    <a
                      href={webSource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-green-600 hover:text-green-700 font-medium inline-flex items-center gap-1"
                    >
                      {webSource.title} <ExternalLink className="w-3 h-3" />
                    </a>
                    <p className="text-gray-500 mt-0.5">{webSource.snippet}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-700 mt-2"
            >
              View source <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      )}
    </div>
  );
}
