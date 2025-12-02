'use client';

import Link from 'next/link';
import { Search, Globe, Camera, FileText, Users, Database, Layers, ArrowRight, Activity, Shield, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Navigation Header */}
      <nav className="bg-slate-900/95 border-b border-slate-800 sticky top-0 z-50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="text-xl font-bold text-white">OSINT Platform</div>
                <div className="text-xs text-slate-400">Intelligence & Analysis</div>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" 
                 className="text-sm text-slate-400 hover:text-white transition-colors font-medium">
                API Docs
              </a>
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-950/50 border border-emerald-800/50 rounded-full">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-xs font-medium text-emerald-400">System Active</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-950/50 border border-blue-800/50 rounded-full mb-6">
              <Activity className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-semibold text-blue-300">Open Source Intelligence Platform</span>
            </div>
            
            <h1 className="text-5xl sm:text-6xl font-bold text-white mb-6 leading-tight">
              Professional Intelligence
              <span className="block text-blue-500">Collection & Analysis</span>
            </h1>
            
            <p className="text-xl text-slate-400 mb-10 leading-relaxed max-w-2xl mx-auto">
              Enterprise-grade toolkit for digital investigations, data collection, and security analysis with comprehensive visualization capabilities.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                href="/graph"
                className="inline-flex items-center justify-center px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-semibold shadow-lg shadow-blue-600/20 hover:shadow-xl"
              >
                Start Investigation
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
              <Link 
                href="/tools"
                className="inline-flex items-center justify-center px-8 py-4 bg-slate-800 text-slate-200 rounded-lg hover:bg-slate-700 transition-all font-semibold border border-slate-700 shadow-sm"
              >
                Browse Tools Directory
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Featured Tool */}
        <div className="mb-16">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-white">Featured Capability</h2>
              <p className="text-slate-400 mt-1">Comprehensive OSINT tools directory with 500+ resources</p>
            </div>
          </div>
          
          <Link 
            href="/tools"
            className="group relative bg-slate-900 rounded-xl border border-slate-800 hover:border-blue-700 transition-all overflow-hidden shadow-sm hover:shadow-lg hover:shadow-blue-900/20"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-950/30 to-indigo-950/30 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div className="relative p-8 flex items-center gap-6">
              <div className="flex-shrink-0 w-16 h-16 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <Layers className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-2xl font-bold text-white">OSINT Framework Directory</h3>
                  <span className="px-3 py-1 bg-blue-950 border border-blue-800 text-blue-400 text-xs font-bold rounded-full">500+ TOOLS</span>
                </div>
                <p className="text-slate-400 mb-3">
                  Organized catalog of OSINT tools across multiple categories: Username, Email, Domain, IP Address, Phone Numbers, Social Media, and more. Miller Columns interface for efficient navigation.
                </p>
                <div className="flex gap-2 flex-wrap">
                  <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-medium rounded-md border border-slate-700">Categorized</span>
                  <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-medium rounded-md border border-slate-700">External Links</span>
                  <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-medium rounded-md border border-slate-700">Quick Search</span>
                </div>
              </div>
              <ArrowRight className="w-6 h-6 text-slate-600 group-hover:text-blue-500 group-hover:translate-x-1 transition-all flex-shrink-0" />
            </div>
          </Link>
        </div>

        {/* Core Features */}
        <div className="mb-16">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">Core Capabilities</h2>
            <p className="text-slate-400">Integrated data collection and analysis modules</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Data Collection */}
            <Link 
              href="/graph"
              className="group bg-slate-900 rounded-xl border border-slate-800 hover:border-blue-700 transition-all p-6 shadow-sm hover:shadow-lg hover:shadow-blue-900/20"
            >
              <div className="w-12 h-12 bg-blue-950/50 border border-blue-800/50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 group-hover:border-blue-600 transition-colors">
                <Globe className="w-6 h-6 text-blue-400 group-hover:text-white transition-colors" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Data Collection & Graphs</h3>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                11 integrated collectors including DNS, Shodan, VirusTotal, WHOIS, and social media. Interactive network visualization with relationship mapping.
              </p>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">11 Collectors</span>
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">Network Graphs</span>
              </div>
            </Link>

            {/* Metadata Extraction */}
            <Link 
              href="/metadata"
              className="group bg-slate-900 rounded-xl border border-slate-800 hover:border-purple-700 transition-all p-6 shadow-sm hover:shadow-lg hover:shadow-purple-900/20"
            >
              <div className="w-12 h-12 bg-purple-950/50 border border-purple-800/50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-purple-600 group-hover:border-purple-600 transition-colors">
                <Camera className="w-6 h-6 text-purple-400 group-hover:text-white transition-colors" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Metadata Extraction</h3>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                Forensic metadata extraction from images and documents. GPS coordinates, EXIF data, and automatic geolocation with map integration.
              </p>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">GPS/EXIF</span>
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">Geolocation</span>
              </div>
            </Link>

            {/* Username Intelligence */}
            <Link 
              href="/username"
              className="group bg-slate-900 rounded-xl border border-slate-800 hover:border-orange-700 transition-all p-6 shadow-sm hover:shadow-lg hover:shadow-orange-900/20"
            >
              <div className="w-12 h-12 bg-orange-950/50 border border-orange-800/50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-orange-600 group-hover:border-orange-600 transition-colors">
                <Users className="w-6 h-6 text-orange-400 group-hover:text-white transition-colors" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Username Intelligence</h3>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                Cross-platform username enumeration across major social networks. Digital footprint analysis and account discovery.
              </p>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">6+ Platforms</span>
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">Social Media</span>
              </div>
            </Link>

            {/* Search Intelligence */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 shadow-sm">
              <div className="w-12 h-12 bg-yellow-950/50 border border-yellow-800/50 rounded-lg flex items-center justify-center mb-4">
                <Search className="w-6 h-6 text-yellow-400" />
              </div>
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-lg font-bold text-white">Search Intelligence</h3>
                <span className="px-2 py-0.5 bg-emerald-950/50 border border-emerald-800/50 text-emerald-400 text-xs font-semibold rounded">Integrated</span>
              </div>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                Pre-configured Google dorks for reconnaissance. Available in Graph Viewer - click any node for external intelligence pivots and advanced queries.
              </p>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">18+ Dorks</span>
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">Node Context</span>
              </div>
            </div>

            {/* Collectors Dashboard */}
            <Link 
              href="/collectors"
              className="group bg-slate-900 rounded-xl border border-slate-800 hover:border-indigo-700 transition-all p-6 shadow-sm hover:shadow-lg hover:shadow-indigo-900/20"
            >
              <div className="w-12 h-12 bg-indigo-950/50 border border-indigo-800/50 rounded-lg flex items-center justify-center mb-4 group-hover:bg-indigo-600 group-hover:border-indigo-600 transition-colors">
                <Database className="w-6 h-6 text-indigo-400 group-hover:text-white transition-colors" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Collectors Dashboard</h3>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                Direct access to individual data collection modules. Execute collectors independently without graph visualization.
              </p>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">Raw Data</span>
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">Direct Access</span>
              </div>
            </Link>

            {/* API Documentation */}
            <a 
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="group bg-slate-900 rounded-xl border border-slate-800 hover:border-slate-700 transition-all p-6 shadow-sm hover:shadow-lg"
            >
              <div className="w-12 h-12 bg-slate-800 border border-slate-700 rounded-lg flex items-center justify-center mb-4 group-hover:bg-slate-700 group-hover:border-slate-600 transition-colors">
                <FileText className="w-6 h-6 text-slate-400 group-hover:text-white transition-colors" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">API Documentation</h3>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                Interactive FastAPI documentation with endpoint reference, request/response schemas, and live testing interface.
              </p>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">REST API</span>
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">Swagger UI</span>
              </div>
            </a>
          </div>
        </div>

        {/* Platform Statistics */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-sm overflow-hidden">
          <div className="p-8">
            <h2 className="text-2xl font-bold text-white mb-2">Platform Overview</h2>
            <p className="text-slate-400 mb-8">Key capabilities and coverage metrics</p>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-500 mb-2">500+</div>
                <div className="text-sm text-slate-400 font-medium">OSINT Tools</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-indigo-500 mb-2">11</div>
                <div className="text-sm text-slate-400 font-medium">Data Collectors</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-purple-500 mb-2">7</div>
                <div className="text-sm text-slate-400 font-medium">Tool Categories</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-emerald-500 mb-2">∞</div>
                <div className="text-sm text-slate-400 font-medium">Investigations</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-sm font-semibold text-white">OSINT Platform</div>
                <div className="text-xs text-slate-500">v2.4.0</div>
              </div>
            </div>
            
            <div className="flex items-center gap-6 text-sm text-slate-400">
              <a href="http://localhost:8000/health" className="hover:text-white transition-colors font-medium">
                Backend: localhost:8000
              </a>
              <span className="text-slate-700">•</span>
              <span className="font-medium">Frontend: localhost:3000</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
