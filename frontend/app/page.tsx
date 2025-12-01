'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="max-w-4xl mx-auto p-8">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-4">
            OSINT Platform
          </h1>
          <p className="text-xl text-gray-400">
            Open Source Intelligence Collection & Visualization
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <Link 
            href="/collectors"
            className="block p-6 bg-slate-800 rounded-lg border border-slate-700 hover:border-green-500 transition-colors"
          >
            <h2 className="text-2xl font-bold text-green-400 mb-3">
              🎯 All Collectors
            </h2>
            <p className="text-gray-300">
              Execute all 10 OSINT collectors with interactive interface.
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

        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h3 className="text-xl font-bold text-white mb-4">Available Collectors</h3>
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
