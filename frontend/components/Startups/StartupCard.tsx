'use client';

import { useState } from 'react';
import { StartupDetailResponse } from '@/lib/types';
import { startupsAPI } from '@/lib/api';
import { 
  Building2, 
  MapPin, 
  DollarSign, 
  Users, 
  X, 
  Loader2,
  TrendingUp,
  Calendar,
  Linkedin,
  Twitter,
  Facebook,
  ExternalLink,
  Mail,
  Sparkles,
  Newspaper,
  Link2,
  Target,
  Briefcase,
  LineChart
} from 'lucide-react';

interface StartupCardProps {
  startup: {
    name?: string;
    startup_name?: string;
    sector?: string;
    stage?: string;
    location?: string;
    description?: string;
    funding_amount?: number;
    team_size?: number;
    contact_email?: string;
    website?: string;
    _investors_str?: string;
    _total_funding?: string;
  };
}

// Format funding amount for display
const formatFunding = (amount?: number, totalFunding?: string): string => {
  if (totalFunding && totalFunding !== '') return totalFunding;
  if (!amount || amount === 0) return 'Undisclosed';
  if (amount >= 100) return `$${(amount / 100).toFixed(1)}B`;
  if (amount >= 1) return `$${amount.toFixed(1)}M`;
  return `$${(amount * 1000).toFixed(0)}K`;
};

export default function StartupCard({ startup }: StartupCardProps) {
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [details, setDetails] = useState<StartupDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const name = startup.name || startup.startup_name || 'Unnamed Startup';
  const sector = startup.sector || 'N/A';
  const stage = startup.stage || 'N/A';
  const location = startup.location || 'N/A';
  const description = startup.description || 'No description available';
  const fundingAmount = startup.funding_amount || 0;
  const teamSize = startup.team_size || 0;

  const handleCardClick = async () => {
    setShowModal(true);
    if (!details && !loading) {
      setLoading(true);
      setError(null);
      try {
        const response = await startupsAPI.getDetails(name);
        setDetails(response);
      } catch (err) {
        console.error('Error fetching startup details:', err);
        setError('Failed to load startup details');
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
        className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all p-6 cursor-pointer hover:border-indigo-300 border border-transparent hover:scale-[1.02]"
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900 mb-2">{name}</h3>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Building2 className="w-4 h-4" />
              <span>{sector}</span>
              <span className="text-gray-400">•</span>
              <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium">
                {stage}
              </span>
            </div>
          </div>
        </div>

        <p className="text-gray-700 text-sm mb-4 line-clamp-3">
          {description}
        </p>

        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <MapPin className="w-4 h-4 text-gray-400" />
            <span>{location}</span>
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-600">
            <DollarSign className="w-4 h-4 text-green-600" />
            <span>{formatFunding(fundingAmount, startup._total_funding)}</span>
          </div>

          {teamSize > 0 && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Users className="w-4 h-4 text-blue-600" />
              <span>{teamSize} team members</span>
            </div>
          )}
        </div>

        {startup._investors_str && (
          <div className="mb-4 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-1">Investors</p>
            <p className="text-sm text-gray-700 line-clamp-1">{startup._investors_str}</p>
          </div>
        )}

        <div className="pt-4 border-t border-gray-100 flex gap-2">
          {startup.website && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                window.open(startup.website, '_blank');
              }}
              className="flex-1 text-center px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
            >
              Visit Website
            </button>
          )}
          {startup.contact_email && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                window.location.href = `mailto:${startup.contact_email}`;
              }}
              className="flex-1 text-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Contact
            </button>
          )}
        </div>
        
        <p className="text-xs text-center text-gray-400 mt-3">Click for detailed analysis</p>
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
                <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Building2 className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{name}</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                      {sector}
                    </span>
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                      {stage}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1 flex items-center gap-1">
                    <MapPin className="w-4 h-4" /> {location}
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              {loading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mb-4" />
                  <p className="text-gray-600">Analyzing startup data...</p>
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
                  {/* AI Investment Summary */}
                  {details.ai_summary && (
                    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-5 border border-indigo-100">
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles className="w-5 h-5 text-indigo-600" />
                        <h3 className="font-semibold text-gray-900">Investment Summary</h3>
                      </div>
                      <p className="text-gray-700 leading-relaxed">{details.ai_summary}</p>
                    </div>
                  )}

                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <DollarSign className="w-6 h-6 text-green-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Total Funding</p>
                      <p className="font-semibold text-gray-900">
                        {details.startup.total_funding || formatFunding(details.startup.funding_amount)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <TrendingUp className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Stage</p>
                      <p className="font-semibold text-gray-900">{details.startup.stage || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <Users className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Team Size</p>
                      <p className="font-semibold text-gray-900">{details.startup.team_size || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <Calendar className="w-6 h-6 text-orange-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Founded</p>
                      <p className="font-semibold text-gray-900">{details.startup.year_founded || 'N/A'}</p>
                    </div>
                  </div>

                  {/* Description */}
                  {details.startup.description && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">About</h3>
                      <p className="text-gray-600 leading-relaxed">{details.startup.description}</p>
                    </div>
                  )}

                  {/* Problem & Solution */}
                  {(details.startup.problem_statement || details.startup.solution) && (
                    <div className="grid md:grid-cols-2 gap-4">
                      {details.startup.problem_statement && (
                        <div className="bg-red-50 rounded-lg p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Target className="w-5 h-5 text-red-600" />
                            <h4 className="font-medium text-gray-900">Problem</h4>
                          </div>
                          <p className="text-sm text-gray-700">{details.startup.problem_statement}</p>
                        </div>
                      )}
                      {details.startup.solution && (
                        <div className="bg-green-50 rounded-lg p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Briefcase className="w-5 h-5 text-green-600" />
                            <h4 className="font-medium text-gray-900">Solution</h4>
                          </div>
                          <p className="text-sm text-gray-700">{details.startup.solution}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Business Model & Market */}
                  {(details.startup.business_model || details.startup.market_size) && (
                    <div className="grid md:grid-cols-2 gap-4">
                      {details.startup.business_model && (
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Business Model</h4>
                          <p className="text-sm text-gray-600">{details.startup.business_model}</p>
                        </div>
                      )}
                      {details.startup.market_size && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <LineChart className="w-5 h-5 text-indigo-600" />
                            <h4 className="font-medium text-gray-900">Market Size</h4>
                          </div>
                          <p className="text-sm text-gray-600">{details.startup.market_size}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Traction */}
                  {details.startup.traction && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">Traction</h3>
                      <p className="text-gray-600">{details.startup.traction}</p>
                    </div>
                  )}

                  {/* Investors */}
                  {details.startup.investors && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3">Investors</h3>
                      <div className="flex flex-wrap gap-2">
                        {details.startup.investors.split(',').map((investor, index) => (
                          <span
                            key={index}
                            className="px-3 py-1.5 bg-indigo-50 text-indigo-700 text-sm rounded-full"
                          >
                            {investor.trim()}
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

                  {/* Funding History */}
                  {details.funding_history && details.funding_history.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <DollarSign className="w-5 h-5" /> Funding Intelligence
                      </h3>
                      <div className="space-y-2">
                        {details.funding_history.map((item, index) => (
                          <a
                            key={index}
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-3 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                          >
                            <p className="font-medium text-gray-900 text-sm">{item.title}</p>
                            <p className="text-xs text-gray-600 mt-1 line-clamp-2">{item.snippet}</p>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Web Sources / Citations */}
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
                      {details.startup.contact?.email && (
                        <a
                          href={`mailto:${details.startup.contact.email}`}
                          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                        >
                          <Mail className="w-4 h-4" />
                          Contact Startup
                        </a>
                      )}
                      {details.startup.contact?.website && (
                        <a
                          href={details.startup.contact.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                          Website
                        </a>
                      )}
                      {details.startup.linkedin && (
                        <a
                          href={details.startup.linkedin}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                        >
                          <Linkedin className="w-4 h-4" />
                          LinkedIn
                        </a>
                      )}
                      {details.startup.twitter && (
                        <a
                          href={details.startup.twitter}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-sky-100 text-sky-700 rounded-lg hover:bg-sky-200 transition-colors"
                        >
                          <Twitter className="w-4 h-4" />
                          Twitter
                        </a>
                      )}
                      {details.startup.facebook && (
                        <a
                          href={details.startup.facebook}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors"
                        >
                          <Facebook className="w-4 h-4" />
                          Facebook
                        </a>
                      )}
                    </div>
                    {details.startup.founder_name && (
                      <p className="text-sm text-gray-600 mt-4">
                        <span className="font-medium">Founder:</span> {details.startup.founder_name}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                // Fallback content from basic startup data
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <DollarSign className="w-6 h-6 text-green-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Funding</p>
                      <p className="font-semibold text-gray-900">
                        {formatFunding(fundingAmount, startup._total_funding)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <TrendingUp className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Stage</p>
                      <p className="font-semibold text-gray-900">{stage}</p>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Description</h3>
                    <p className="text-gray-600">{description}</p>
                  </div>

                  <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
                    {startup.contact_email && (
                      <a
                        href={`mailto:${startup.contact_email}`}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                      >
                        <Mail className="w-4 h-4" />
                        Contact
                      </a>
                    )}
                    {startup.website && (
                      <a
                        href={startup.website}
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
