'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Server, Network, User, Fingerprint } from 'lucide-react';

type SearchMode = 'infra' | 'identity';

export default function Home() {
  const [searchMode, setSearchMode] = useState<SearchMode>('infra');
  const [target, setTarget] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSearch = async () => {
    if (!target.trim()) return;
    
    setLoading(true);
    setResult(null);

    try {
      const collectorName = searchMode === 'infra' ? 'DNSCollector' : 'IdentityCollector';
      const response = await fetch('http://localhost:8000/api/v1/collectors/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ collector_name: collectorName, target: target.trim() })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Search error:', error);
      setResult({ error: 'Failed to execute search' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900">
      <div className="max-w-6xl mx-auto p-8">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            OSINT Platform
          </h1>
          <p className="text-xl text-gray-400">
            Open Source Intelligence Collection & Visualization
          </p>
        </div>

        {/* Mode Selector */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-8 mb-12">
          <div className="flex flex-col gap-6">
            {/* Segmented Control */}
            <div className="flex gap-4 p-2 bg-slate-900 rounded-lg">
              <button
                onClick={() => setSearchMode('infra')}
                className={`flex-1 flex items-center justify-center gap-3 px-6 py-4 rounded-md font-semibold transition-all ${
                  searchMode === 'infra'
                    ? 'bg-green-600 text-white shadow-lg'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <Server className="w-5 h-5" />
                Infrastructure
              </button>
              <button
                onClick={() => setSearchMode('identity')}
                className={`flex-1 flex items-center justify-center gap-3 px-6 py-4 rounded-md font-semibold transition-all ${
                  searchMode === 'identity'
                    ? 'bg-purple-600 text-white shadow-lg'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <User className="w-5 h-5" />
                Identity & Signals
              </button>
            </div>

            {/* Search Input */}
            <div className="flex gap-4">
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder={searchMode === 'infra' ? 'domain.com' : 'username / email'}
                className="flex-1 px-6 py-4 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              />
              <button
                onClick={handleSearch}
                disabled={loading || !target.trim()}
                className="px-8 py-4 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 disabled:text-gray-500 text-white font-semibold rounded-lg transition-colors"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>

            {/* Mode Description */}
            <div className="text-sm text-gray-400 text-center">
              {searchMode === 'infra' ? (
                <span>🖥️ Search DNS records, subdomains, and infrastructure data</span>
              ) : (
                <span>👤 Discover digital footprint, Gravatar, and social media presence</span>
              )}
            </div>
          </div>

          {/* Results */}
          {result && (
            <div className="mt-6 p-6 bg-slate-900 rounded-lg border border-slate-700">
              <pre className="text-sm text-gray-300 overflow-auto max-h-96">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Quick Access Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <Link 
            href="/collectors"
            className="block p-6 bg-slate-800 rounded-lg border border-slate-700 hover:border-green-500 transition-colors"
          >
            <h2 className="text-2xl font-bold text-green-400 mb-3">
              🎯 All Collectors
            </h2>
            <p className="text-gray-300">
              Execute all 11 OSINT collectors with interactive interface.
            </p>
          </Link>

          <Link 
            href="/graph"
            className="block p-6 bg-slate-800 rounded-lg border border-slate-700 hover:border-cyan-500 transition-colors"
          >
            <h2 className="text-2xl font-bold text-cyan-400 mb-3">
              📊 Graph Viewer
            </h2>
            <p className="text-gray-300">
              Interactive DNS visualization with React Flow.
            </p>
          </Link>

          <Link 
            href="/username"
            className="block p-6 bg-slate-800 rounded-lg border border-slate-700 hover:border-blue-500 transition-colors"
          >
            <h2 className="text-2xl font-bold text-blue-400 mb-3">
              👤 Username Search
            </h2>
            <p className="text-gray-300">
              Search usernames across 6 social platforms.
            </p>
          </Link>

          <a 
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="block p-6 bg-slate-800 rounded-lg border border-slate-700 hover:border-cyan-500 transition-colors"
          >
            <h2 className="text-2xl font-bold text-cyan-400 mb-3">
              🔧 API Docs
            </h2>
            <p className="text-gray-300">
              FastAPI documentation with all endpoints.
            </p>
          </a>
        </div>

        {/* Available Collectors */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h3 className="text-xl font-bold text-white mb-4">Available Collectors (11)</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="text-gray-300 text-sm">✅ DNS Collector</div>
            <div className="text-gray-300 text-sm">✅ Shodan Collector</div>
            <div className="text-gray-300 text-sm">✅ Whois Collector</div>
            <div className="text-gray-300 text-sm">✅ VirusTotal Collector</div>
            <div className="text-gray-300 text-sm">✅ HaveIBeenPwned</div>
            <div className="text-gray-300 text-sm">✅ SecurityTrails</div>
            <div className="text-gray-300 text-sm">✅ Social Collector</div>
            <div className="text-gray-300 text-sm">✅ Crtsh Collector</div>
            <div className="text-gray-300 text-sm">✅ Username Collector</div>
            <div className="text-gray-300 text-sm">✅ Metadata Collector</div>
            <div className="text-purple-400 text-sm font-semibold">✨ Identity Collector</div>
          </div>
        </div>

        <div className="mt-8 text-center">
          <p className="text-gray-500 text-sm">
            Backend: <a href="http://localhost:8000/health" className="text-cyan-400 hover:underline">localhost:8000</a>
            {' • '}
            Frontend: <span className="text-cyan-400">localhost:3000</span>
          </p>
        </div>
      </div>
    </div>
  );
}
