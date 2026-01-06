'use client';

import { Building2, MapPin, DollarSign, Users } from 'lucide-react';

interface StartupCardProps {
  startup: {
    name?: string;
    sector?: string;
    stage?: string;
    location?: string;
    description?: string;
    funding_amount?: number;
    team_size?: number;
    contact_email?: string;
    website?: string;
  };
}

export default function StartupCard({ startup }: StartupCardProps) {
  const name = startup.name || 'Unnamed Startup';
  const sector = startup.sector || 'N/A';
  const stage = startup.stage || 'N/A';
  const location = startup.location || 'N/A';
  const description = startup.description || 'No description available';
  const fundingAmount = startup.funding_amount || 0;
  const teamSize = startup.team_size || 0;

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow p-6">
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

        {fundingAmount > 0 && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <DollarSign className="w-4 h-4 text-green-600" />
            <span>Seeking ₹{fundingAmount} Cr</span>
          </div>
        )}

        {teamSize > 0 && (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Users className="w-4 h-4 text-blue-600" />
            <span>{teamSize} team members</span>
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-gray-100 flex gap-2">
        {startup.website && (
          <a
            href={startup.website}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 text-center px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
          >
            Visit Website
          </a>
        )}
        {startup.contact_email && (
          <a
            href={`mailto:${startup.contact_email}`}
            className="flex-1 text-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Contact
          </a>
        )}
      </div>
    </div>
  );
}
