'use client';

import { Investor } from '@/lib/types';
import { MapPin, Target, DollarSign, Mail, ExternalLink } from 'lucide-react';

interface Props {
  investor: Investor;
}

export default function InvestorCard({ investor }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200">
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
            ₹{investor.ticket_size.min} - ₹{investor.ticket_size.max} Cr
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
          <a
            href={`mailto:${investor.contact.email}`}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors text-sm font-medium"
          >
            <Mail className="w-4 h-4" />
            Contact
          </a>
        )}
        {investor.contact?.website && (
          <a
            href={investor.contact.website}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
          >
            <ExternalLink className="w-4 h-4" />
            Website
          </a>
        )}
      </div>
    </div>
  );
}
