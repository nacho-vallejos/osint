'use client';

import React from 'react';
import { X, ExternalLink, Globe, Server, Mail, User } from 'lucide-react';
import { Node } from 'reactflow';

interface DorkLink {
  platform: string;
  url: string;
  description: string;
  icon: string;
}

interface EntityDetailsSidebarProps {
  selectedNode: Node | null;
  onClose: () => void;
}

/**
 * Generate passive dorking links for external intelligence pivots
 */
const generateDorks = (target: string, type: 'person' | 'domain'): DorkLink[] => {
  const safeTarget = encodeURIComponent(target);
  const quotedTarget = encodeURIComponent(`"${target}"`);

  if (type === 'person') {
    return [
      {
        platform: 'LinkedIn Profiles',
        url: `https://www.google.com/search?q=site:linkedin.com/in/+${quotedTarget}`,
        description: 'Professional profiles and career history',
        icon: '💼'
      },
      {
        platform: 'Pastebin Leaks',
        url: `https://www.google.com/search?q=site:pastebin.com+${quotedTarget}`,
        description: 'Text leaks and credential mentions',
        icon: '📋'
      },
      {
        platform: 'Trello Boards',
        url: `https://www.google.com/search?q=site:trello.com+${quotedTarget}`,
        description: 'Public project boards',
        icon: '📊'
      },
      {
        platform: 'Document Files',
        url: `https://www.google.com/search?q=filetype:pdf+OR+filetype:docx+${quotedTarget}`,
        description: 'PDF and DOCX documents',
        icon: '📄'
      },
      {
        platform: 'GitHub Code',
        url: `https://www.google.com/search?q=site:github.com+${quotedTarget}`,
        description: 'Source code and repositories',
        icon: '💻'
      },
      {
        platform: 'Social Media',
        url: `https://www.google.com/search?q=${quotedTarget}+site:twitter.com+OR+site:facebook.com+OR+site:instagram.com`,
        description: 'Major social platforms',
        icon: '👥'
      }
    ];
  } else {
    // Domain type
    return [
      {
        platform: 'Configuration Files',
        url: `https://www.google.com/search?q=site:${safeTarget}+ext:xml+OR+ext:conf+OR+ext:cnf+OR+ext:reg`,
        description: 'Exposed config and registry files',
        icon: '⚙️'
      },
      {
        platform: 'Login Pages',
        url: `https://www.google.com/search?q=site:${safeTarget}+inurl:login+OR+inurl:admin+OR+inurl:dashboard`,
        description: 'Administrative portals',
        icon: '🔐'
      },
      {
        platform: 'AWS S3 Buckets',
        url: `https://www.google.com/search?q=site:s3.amazonaws.com+${quotedTarget}`,
        description: 'Open S3 buckets',
        icon: '☁️'
      },
      {
        platform: 'Database Files',
        url: `https://www.google.com/search?q=site:${safeTarget}+ext:sql+OR+ext:db+OR+ext:mdb`,
        description: 'Database files and SQL dumps',
        icon: '🗄️'
      },
      {
        platform: 'Backup Files',
        url: `https://www.google.com/search?q=site:${safeTarget}+ext:bak+OR+ext:backup+OR+ext:old`,
        description: 'Backup and legacy resources',
        icon: '💾'
      },
      {
        platform: 'Directory Listings',
        url: `https://www.google.com/search?q=site:${safeTarget}+intitle:"index+of"`,
        description: 'Open directory browsers',
        icon: '📁'
      },
      {
        platform: 'Subdomain Enumeration',
        url: `https://www.google.com/search?q=site:*.${safeTarget}+-site:www.${safeTarget}`,
        description: 'Google-indexed subdomains',
        icon: '🌐'
      },
      {
        platform: 'API Documentation',
        url: `https://www.google.com/search?q=site:${safeTarget}+inurl:api+OR+inurl:swagger+OR+inurl:docs`,
        description: 'API endpoints and docs',
        icon: '🔌'
      }
    ];
  }
};

/**
 * Detect entity type based on node data
 */
const detectEntityType = (node: Node): 'person' | 'domain' => {
  const label = node.data.label?.toLowerCase() || '';
  const nodeType = node.data.type;

  // Check if it's an email
  if (label.includes('@') || nodeType === 'email') {
    return 'person';
  }

  // Check if it's a username or person-related
  if (nodeType === 'user' || label.match(/^[a-z0-9_-]{3,20}$/i)) {
    return 'person';
  }

  // Default to domain for DNS/IP/domain types
  return 'domain';
};

/**
 * Get icon component based on node type
 */
const getEntityIcon = (nodeType: string) => {
  switch (nodeType) {
    case 'dns':
      return <Globe className="w-6 h-6 text-cyan-400" />;
    case 'ip':
      return <Server className="w-6 h-6 text-green-400" />;
    case 'email':
      return <Mail className="w-6 h-6 text-purple-400" />;
    case 'user':
      return <User className="w-6 h-6 text-blue-400" />;
    default:
      return <Globe className="w-6 h-6 text-gray-400" />;
  }
};

export default function EntityDetailsSidebar({ selectedNode, onClose }: EntityDetailsSidebarProps) {
  if (!selectedNode) return null;

  const entityType = detectEntityType(selectedNode);
  const dorks = generateDorks(selectedNode.data.label, entityType);

  return (
    <div className="absolute right-0 top-0 h-full w-96 bg-slate-800 border-l border-slate-700 shadow-2xl z-50 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-slate-900 border-b border-slate-700 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {getEntityIcon(selectedNode.data.type)}
          <div>
            <h3 className="text-lg font-bold text-white">Entity Details</h3>
            <p className="text-xs text-gray-400">{selectedNode.data.info || 'Selected Node'}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          aria-label="Close sidebar"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Basic Information */}
        <div>
          <h4 className="text-sm font-semibold text-gray-400 uppercase mb-3">Basic Information</h4>
          <div className="bg-slate-900 rounded-lg p-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Label:</span>
              <span className="text-white font-mono text-sm">{selectedNode.data.label}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Type:</span>
              <span className="text-cyan-400 text-sm capitalize">{selectedNode.data.type}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400 text-sm">Node ID:</span>
              <span className="text-gray-500 text-sm font-mono">{selectedNode.id}</span>
            </div>
            {selectedNode.data.info && (
              <div className="flex justify-between">
                <span className="text-gray-400 text-sm">Info:</span>
                <span className="text-white text-sm">{selectedNode.data.info}</span>
              </div>
            )}
          </div>
        </div>

        {/* External Intelligence Pivots */}
        <div>
          <h4 className="text-sm font-semibold text-gray-400 uppercase mb-3 flex items-center gap-2">
            <ExternalLink className="w-4 h-4" />
            External Intelligence Pivots
          </h4>
          <p className="text-xs text-gray-500 mb-4">
            Pre-optimized search queries for external OSINT gathering ({entityType === 'person' ? 'Person' : 'Domain'} mode)
          </p>

          {/* Dork Links Grid */}
          <div className="space-y-2">
            {dorks.map((dork, index) => (
              <a
                key={index}
                href={dork.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-slate-900 hover:bg-blue-600 border border-slate-700 hover:border-blue-500 rounded-lg p-3 transition-all group"
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{dork.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-white font-semibold text-sm">{dork.platform}</span>
                      <ExternalLink className="w-3 h-3 text-gray-400 group-hover:text-white" />
                    </div>
                    <p className="text-xs text-gray-400 group-hover:text-gray-200">
                      {dork.description}
                    </p>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>

        {/* Tips */}
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <span className="text-blue-400 text-xl">💡</span>
            <div>
              <h5 className="text-blue-300 font-semibold text-sm mb-1">Passive Dorking</h5>
              <p className="text-blue-200 text-xs">
                Click any link to open Google with pre-optimized search queries. 
                These dorks help discover {entityType === 'person' ? 'digital footprints' : 'exposed infrastructure'} without direct interaction.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
