'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface CollectorResult {
  id: string;
  collector_name: string;
  target: string;
  success: boolean;
  data: any;
  error: string | null;
  timestamp: string;
  metadata?: any;
}

const COLLECTORS = [
  { 
    name: 'DNSCollector', 
    description: 'DNS records lookup (A, AAAA, MX, NS, TXT, CNAME)',
    icon: '🌐',
    placeholder: 'example.com'
  },
  { 
    name: 'WhoisCollector', 
    description: 'Domain registration and ownership information',
    icon: '📋',
    placeholder: 'example.com'
  },
  { 
    name: 'ShodanCollector', 
    description: 'Internet-facing devices and services (requires API key)',
    icon: '🔍',
    placeholder: 'IP address or domain'
  },
  { 
    name: 'VirusTotalCollector', 
    description: 'Malware and threat intelligence (requires API key)',
    icon: '🛡️',
    placeholder: 'domain or IP'
  },
  { 
    name: 'HaveIBeenPwnedCollector', 
    description: 'Check if email appears in data breaches',
    icon: '💀',
    placeholder: 'email@example.com'
  },
  { 
    name: 'SecurityTrailsCollector', 
    description: 'Historical DNS data (requires API key)',
    icon: '🕵️',
    placeholder: 'example.com'
  },
  { 
    name: 'SocialCollector', 
    description: 'Social media profile discovery (15 platforms)',
    icon: '👥',
    placeholder: 'username'
  },
  { 
    name: 'CrtshCollector', 
    description: 'Subdomain discovery via Certificate Transparency logs',
    icon: '🔐',
    placeholder: 'example.com'
  },
  { 
    name: 'UsernameCollector', 
    description: 'Username presence across 6 social platforms',
    icon: '👤',
    placeholder: 'username'
  },
  { 
    name: 'MetadataCollector', 
    description: 'Document metadata extraction (PDF, DOCX, XLSX)',
    icon: '📄',
    placeholder: 'example.com'
  },
];

export default function CollectorsPage() {
  const [selectedCollector, setSelectedCollector] = useState(COLLECTORS[0]);
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CollectorResult | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  const handleExecute = async () => {
    if (!target.trim()) {
      alert('Por favor ingresa un target');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/collectors/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          collector_name: selectedCollector.name,
          target: target.trim(),
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setResult({
        id: '',
        collector_name: selectedCollector.name,
        target: target.trim(),
        success: false,
        data: null,
        error: 'Error de conexión con el servidor',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleExecute();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">OSINT Collectors</h1>
          <p className="text-gray-300">Execute intelligence collectors and view results</p>
          <a href="/" className="text-cyan-400 hover:text-cyan-300 text-sm">← Back to Home</a>
        </div>

        {/* Control Panel */}
        <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-6 mb-8 border border-slate-700">
          <div className="space-y-4">
            {/* Collector Selector */}
            <div className="relative">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Select Collector
              </label>
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white text-left flex items-center justify-between hover:bg-slate-600 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{selectedCollector.icon}</span>
                  <div>
                    <div className="font-semibold">{selectedCollector.name}</div>
                    <div className="text-sm text-gray-400">{selectedCollector.description}</div>
                  </div>
                </div>
                <ChevronDown className="w-5 h-5 text-gray-400" />
              </button>

              {showDropdown && (
                <div className="absolute z-10 w-full mt-2 bg-slate-700 border border-slate-600 rounded-lg shadow-xl max-h-96 overflow-y-auto">
                  {COLLECTORS.map((collector) => (
                    <button
                      key={collector.name}
                      onClick={() => {
                        setSelectedCollector(collector);
                        setShowDropdown(false);
                        setResult(null);
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-slate-600 transition-colors border-b border-slate-600 last:border-b-0"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{collector.icon}</span>
                        <div>
                          <div className="font-semibold text-white">{collector.name}</div>
                          <div className="text-sm text-gray-400">{collector.description}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Target Input */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Target
              </label>
              <div className="flex gap-4">
                <input
                  type="text"
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={selectedCollector.placeholder}
                  className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  disabled={loading}
                />
                <button
                  onClick={handleExecute}
                  disabled={loading}
                  className="px-8 py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors duration-200"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Executing...
                    </span>
                  ) : (
                    'Execute'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Result Header */}
            <div className={`bg-slate-800/50 backdrop-blur-md rounded-xl p-6 border ${result.success ? 'border-green-500/50' : 'border-red-500/50'}`}>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                    {selectedCollector.icon} {result.collector_name}
                    {result.success ? (
                      <span className="text-green-400 text-lg">✓</span>
                    ) : (
                      <span className="text-red-400 text-lg">✗</span>
                    )}
                  </h2>
                  <p className="text-gray-400">Target: <span className="text-cyan-400">{result.target}</span></p>
                </div>
                <div className="text-right text-sm text-gray-400">
                  <div>ID: {result.id.substring(0, 8)}...</div>
                  <div>{new Date(result.timestamp).toLocaleString()}</div>
                </div>
              </div>

              {result.error && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                  <p className="text-red-200">{result.error}</p>
                </div>
              )}
            </div>

            {/* Result Data */}
            {result.success && result.data && (
              <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-6 border border-slate-700">
                <h3 className="text-xl font-bold text-white mb-4">Result Data</h3>
                <pre className="bg-slate-900 rounded-lg p-4 overflow-x-auto text-sm text-gray-300 max-h-[600px] overflow-y-auto">
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              </div>
            )}

            {/* Metadata */}
            {result.metadata && Object.keys(result.metadata).length > 0 && (
              <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-6 border border-slate-700">
                <h3 className="text-xl font-bold text-white mb-4">Metadata</h3>
                <pre className="bg-slate-900 rounded-lg p-4 overflow-x-auto text-sm text-gray-300">
                  {JSON.stringify(result.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Help Text */}
        {!result && !loading && (
          <div className="bg-slate-800/30 backdrop-blur-md rounded-xl p-6 border border-slate-700/50">
            <h3 className="text-lg font-semibold text-white mb-3">ℹ️ Quick Start</h3>
            <ul className="space-y-2 text-gray-300 text-sm">
              <li>• Select a collector from the dropdown</li>
              <li>• Enter your target (domain, IP, email, or username)</li>
              <li>• Click Execute or press Enter</li>
              <li>• Some collectors require API keys configured in backend/.env</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
