'use client';

import { useState } from 'react';
import { Investor, InvestorDetailResponse } from '@/lib/types';
import { investorsAPI } from '@/lib/api';
import { 
  MapPin, 
  Target, 
  DollarSign, 
  Mail, 
  ExternalLink, 
  X, 
  Loader2,
  Building2,
  TrendingUp,
  Users,
  Calendar,
  Linkedin,
  Twitter,
  Newspaper,
  Sparkles,
  Link2
} from 'lucide-react';

interface Props {
  investor: Investor;
}

// Format ticket size to display in millions USD
const formatTicketSize = (min?: number, max?: number): string => {
  if (!min && !max) return 'Undisclosed';
  
  const formatNum = (n: number) => {
    if (n >= 1) return `$${n.toFixed(1)}M`;
    return `$${(n * 1000).toFixed(0)}K`;
  };
  
  if (min && max) {
    return `${formatNum(min)} - ${formatNum(max)}`;
  }
  return min ? `${formatNum(min)}+` : `Up to ${formatNum(max!)}`;
};

export default function InvestorCard({ investor }: Props) {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [details, setDetails] = useState<InvestorDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCardClick = async () => {
    setShowModal(true);
    if (!details && !loading) {
      setLoading(true);
      setError(null);
      try {
        const response = await investorsAPI.getDetails(investor.name);
        setDetails(response);
      } catch (err) {
        console.error('Error fetching investor details:', err);
        setError('Failed to load investor details');
      } finally {
        setLoading(false);
      }
    }
  };

  const closeModal = () => {
    setShowModal(false);
  };

  return (
    <>
      {/* Card */}
      <div 
        onClick={handleCardClick}
        className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all p-6 border border-gray-200 cursor-pointer hover:border-indigo-300 hover:scale-[1.02]"
      >
        <div className="mb-4">
          <h3 className="text-xl font-bold text-gray-900 mb-1">
            {investor.name}
          </h3>
          <p className="text-sm text-indigo-600 font-medium">
            {investor.type}
          </p>
        </div>

        <div className="space-y-3 mb-4">
          <div className="flex items-start gap-2">
            <Target className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-sm text-gray-600 mb-1">Focus Areas</p>
              <div className="flex flex-wrap gap-1">
                {investor.focus_areas.slice(0, 3).map((area, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-indigo-50 text-indigo-700 text-xs rounded-full"
                  >
                    {area}
                  </span>
                ))}
                {investor.focus_areas.length > 3 && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                    +{investor.focus_areas.length - 3} more
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-gray-400 flex-shrink-0" />
            <p className="text-sm text-gray-700">{investor.location}</p>
          </div>

          <div className="flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-gray-400 flex-shrink-0" />
            <p className="text-sm text-gray-700">
              {formatTicketSize(investor.ticket_size.min, investor.ticket_size.max)}
            </p>
          </div>
        </div>

        {investor.portfolio && investor.portfolio.length > 0 && (
          <div className="mb-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-2">Notable Portfolio</p>
            <div className="flex flex-wrap gap-1">
              {investor.portfolio.slice(0, 4).map((company, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                >
                  {company}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-2">
          {investor.contact?.email && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                window.location.href = `mailto:${investor.contact?.email}`;
              }}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors text-sm font-medium"
            >
              <Mail className="w-4 h-4" />
              Contact
            </button>
          )}
          {investor.contact?.website && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                window.open(investor.contact?.website, '_blank');
              }}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
            >
              <ExternalLink className="w-4 h-4" />
              Website
            </button>
          )}
        </div>
        
        <p className="text-xs text-center text-gray-400 mt-3">Click for more details</p>
      </div>

      {/* Modal */}
      {showModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={closeModal}
        >
          <div 
            className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 rounded-t-2xl">
              <button
                onClick={closeModal}
                className="absolute top-4 right-4 p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
              
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 bg-indigo-100 rounded-xl flex items-center justify-center">
                  <Building2 className="w-8 h-8 text-indigo-600" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{investor.name}</h2>
                  <p className="text-indigo-600 font-medium">{investor.type}</p>
                  <p className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                    <MapPin className="w-4 h-4" /> {investor.location}
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              {loading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-4" />
                  <p className="text-gray-600">Loading investor details...</p>
                </div>
              ) : error ? (
                <div className="text-center py-12">
                  <p className="text-red-600 mb-4">{error}</p>
                  <button
                    onClick={() => handleCardClick()}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                  >
                    Retry
                  </button>
                </div>
              ) : details ? (
                <div className="space-y-6">
                  {/* AI Summary */}
                  {details.ai_summary && (
                    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-5 border border-indigo-100">
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles className="w-5 h-5 text-indigo-600" />
                        <h3 className="font-semibold text-gray-900">AI Summary</h3>
                      </div>
                      <p className="text-gray-700 leading-relaxed">{details.ai_summary}</p>
                    </div>
                  )}

                  {/* Key Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <DollarSign className="w-6 h-6 text-green-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Ticket Size</p>
                      <p className="font-semibold text-gray-900">
                        {formatTicketSize(details.investor.ticket_size.min, details.investor.ticket_size.max)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <TrendingUp className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Investments</p>
                      <p className="font-semibold text-gray-900">{details.investor.number_of_investments || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <Users className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Exits</p>
                      <p className="font-semibold text-gray-900">{details.investor.number_of_exits || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <Calendar className="w-6 h-6 text-orange-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Founded</p>
                      <p className="font-semibold text-gray-900">{details.investor.founding_year || 'N/A'}</p>
                    </div>
                  </div>

                  {/* Description */}
                  {details.investor.description && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">About</h3>
                      <p className="text-gray-600 leading-relaxed">{details.investor.description}</p>
                    </div>
                  )}

                  {/* Focus Areas */}
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Focus Areas</h3>
                    <div className="flex flex-wrap gap-2">
                      {details.investor.focus_areas.map((area, index) => (
                        <span
                          key={index}
                          className="px-3 py-1.5 bg-indigo-50 text-indigo-700 text-sm rounded-full"
                        >
                          {area}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Investment Stages */}
                  {details.investor.investment_stages && details.investor.investment_stages.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3">Investment Stages</h3>
                      <div className="flex flex-wrap gap-2">
                        {details.investor.investment_stages.map((stage, index) => (
                          <span
                            key={index}
                            className="px-3 py-1.5 bg-green-50 text-green-700 text-sm rounded-full"
                          >
                            {stage}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Portfolio Companies */}
                  {details.investor.portfolio && details.investor.portfolio.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3">Portfolio Companies</h3>
                      <div className="flex flex-wrap gap-2">
                        {details.investor.portfolio.map((company, index) => (
                          <span
                            key={index}
                            className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg"
                          >
                            {company}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recent News */}
                  {details.recent_news && details.recent_news.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <Newspaper className="w-5 h-5" /> Recent News
                      </h3>
                      <div className="space-y-3">
                        {details.recent_news.map((news, index) => (
                          <a
                            key={index}
                            href={news.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                          >
                            <p className="font-medium text-gray-900 mb-1">{news.title}</p>
                            <p className="text-sm text-gray-600 line-clamp-2">{news.snippet}</p>
                            {news.date && (
                              <p className="text-xs text-gray-400 mt-2">{news.date}</p>
                            )}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Web Insights / Citations */}
                  {details.web_insights && details.web_insights.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <Link2 className="w-5 h-5" /> Sources & Citations
                      </h3>
                      <div className="space-y-2">
                        {details.web_insights.map((insight, index) => (
                          <a
                            key={index}
                            href={insight.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
                          >
                            <span className="text-xs text-gray-400 mt-1">[{index + 1}]</span>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 group-hover:text-indigo-600 truncate">
                                {insight.title}
                              </p>
                              <p className="text-xs text-gray-500 truncate">{insight.url}</p>
                            </div>
                            <ExternalLink className="w-4 h-4 text-gray-400 group-hover:text-indigo-600 flex-shrink-0" />
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Contact & Social Links */}
                  <div className="border-t border-gray-200 pt-6">
                    <h3 className="font-semibold text-gray-900 mb-4">Contact & Links</h3>
                    <div className="flex flex-wrap gap-3">
                      {details.investor.contact?.email && (
                        <a
                          href={`mailto:${details.investor.contact.email}`}
                          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                        >
                          <Mail className="w-4 h-4" />
                          Email
                        </a>
                      )}
                      {details.investor.contact?.website && (
                        <a
                          href={details.investor.contact.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                          Website
                        </a>
                      )}
                      {details.investor.linkedin && (
                        <a
                          href={details.investor.linkedin}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                        >
                          <Linkedin className="w-4 h-4" />
                          LinkedIn
                        </a>
                      )}
                      {details.investor.twitter && (
                        <a
                          href={details.investor.twitter}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-sky-100 text-sky-700 rounded-lg hover:bg-sky-200 transition-colors"
                        >
                          <Twitter className="w-4 h-4" />
                          Twitter
                        </a>
                      )}
                    </div>
                    {details.investor.partner_name && (
                      <p className="text-sm text-gray-600 mt-4">
                        <span className="font-medium">Key Contact:</span> {details.investor.partner_name}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                // Fallback content from basic investor data
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <DollarSign className="w-6 h-6 text-green-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Ticket Size</p>
                      <p className="font-semibold text-gray-900">
                        {formatTicketSize(investor.ticket_size.min, investor.ticket_size.max)}
                      </p>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Focus Areas</h3>
                    <div className="flex flex-wrap gap-2">
                      {investor.focus_areas.map((area, index) => (
                        <span
                          key={index}
                          className="px-3 py-1.5 bg-indigo-50 text-indigo-700 text-sm rounded-full"
                        >
                          {area}
                        </span>
                      ))}
                    </div>
                  </div>

                  {investor.portfolio && investor.portfolio.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3">Portfolio Companies</h3>
                      <div className="flex flex-wrap gap-2">
                        {investor.portfolio.map((company, index) => (
                          <span
                            key={index}
                            className="px-3 py-1.5 bg-gray-100 text-gray-700 text-sm rounded-lg"
                          >
                            {company}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
                    {investor.contact?.email && (
                      <a
                        href={`mailto:${investor.contact.email}`}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                      >
                        <Mail className="w-4 h-4" />
                        Email
                      </a>
                    )}
                    {investor.contact?.website && (
                      <a
                        href={investor.contact.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Website
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
