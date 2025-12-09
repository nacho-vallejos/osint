'use client';

import Link from 'next/link';
import { FileText, Layers, Shield, Activity, ArrowRight, CheckCircle } from 'lucide-react';

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
            <div className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-950/50 border border-emerald-800/50 rounded-full">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-medium text-emerald-400">System Active</span>
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
              Professional OSINT
              <span className="block text-blue-500">Tools Directory</span>
            </h1>
            
            <p className="text-xl text-slate-400 mb-10 leading-relaxed max-w-2xl mx-auto">
              Comprehensive collection of 500+ OSINT tools organized by category for efficient intelligence gathering and analysis.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                href="/tools"
                className="inline-flex items-center justify-center px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-semibold shadow-lg shadow-blue-600/20 hover:shadow-xl"
              >
                Browse Tools Directory
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
              <Link 
                href="/video-analysis"
                className="inline-flex items-center justify-center px-8 py-4 bg-slate-800 text-slate-200 rounded-lg hover:bg-slate-700 transition-all font-semibold border border-slate-700 shadow-sm"
              >
                Video Facial Detection
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        {/* Featured Tool */}
        <div className="mb-16">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">Featured Capability</h2>
            <p className="text-slate-400">Access to comprehensive OSINT tools collection</p>
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
                  <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-medium rounded-md border border-slate-700">7 Categories</span>
                  <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-medium rounded-md border border-slate-700">External Links</span>
                  <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs font-medium rounded-md border border-slate-700">Quick Search</span>
                </div>
              </div>
              <ArrowRight className="w-6 h-6 text-slate-600 group-hover:text-blue-500 group-hover:translate-x-1 transition-all flex-shrink-0" />
            </div>
          </Link>
        </div>

        {/* Available Tools */}
        <div className="mb-16">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">Available Tools</h2>
            <p className="text-slate-400">Fully functional OSINT capabilities</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Tools Directory */}
            <Link 
              href="/tools"
              className="group bg-slate-900 rounded-xl border border-slate-800 hover:border-blue-700 transition-all p-6 shadow-sm hover:shadow-lg hover:shadow-blue-900/20"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-blue-950/50 border border-blue-800/50 rounded-lg flex items-center justify-center group-hover:bg-blue-600 group-hover:border-blue-600 transition-colors">
                  <Layers className="w-6 h-6 text-blue-400 group-hover:text-white transition-colors" />
                </div>
                <CheckCircle className="w-5 h-5 text-emerald-500" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">OSINT Tools Directory</h3>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                Browse 500+ categorized OSINT tools with direct links. Covers username lookup, email verification, domain analysis, IP investigation, phone number search, and social media intelligence.
              </p>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">500+ Tools</span>
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">7 Categories</span>
              </div>
            </Link>

            {/* Video Analysis */}
            <Link 
              href="/video-analysis"
              className="group bg-slate-900 rounded-xl border border-slate-800 hover:border-purple-700 transition-all p-6 shadow-sm hover:shadow-lg hover:shadow-purple-900/20"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-purple-950/50 border border-purple-800/50 rounded-lg flex items-center justify-center group-hover:bg-purple-600 group-hover:border-purple-600 transition-colors">
                  <FileText className="w-6 h-6 text-purple-400 group-hover:text-white transition-colors" />
                </div>
                <CheckCircle className="w-5 h-5 text-emerald-500" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Video Facial Detection</h3>
              <p className="text-slate-400 text-sm mb-4 leading-relaxed">
                Upload videos to detect faces frame-by-frame using OpenCV Haar Cascade. Real-time bounding box overlay during playback with timestamp synchronization.
              </p>
              <div className="flex gap-2 flex-wrap">
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">OpenCV</span>
                <span className="px-2 py-1 bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded">Real-time</span>
              </div>
            </Link>
          </div>
        </div>

        {/* Platform Statistics */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-sm overflow-hidden">
          <div className="p-8">
            <h2 className="text-2xl font-bold text-white mb-2">Platform Overview</h2>
            <p className="text-slate-400 mb-8">Current capabilities and coverage</p>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-500 mb-2">500+</div>
                <div className="text-sm text-slate-400 font-medium">OSINT Tools</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-indigo-500 mb-2">7</div>
                <div className="text-sm text-slate-400 font-medium">Tool Categories</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-purple-500 mb-2">1</div>
                <div className="text-sm text-slate-400 font-medium">Analysis Tool</div>
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
                <div className="text-xs text-slate-500">v2.5.0</div>
              </div>
            </div>
            
            <div className="flex items-center gap-6 text-sm text-slate-400">
              <span className="font-medium">localhost:3000</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
