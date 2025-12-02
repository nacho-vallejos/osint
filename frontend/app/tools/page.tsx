'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { Loader2, AlertCircle, ArrowLeft } from 'lucide-react';

// Dynamically import the browser to avoid SSR issues
const OsintToolBrowser = dynamic(
  () => import('../components/OsintToolBrowser'),
  { 
    ssr: false,
    loading: () => (
      <div className="h-screen flex items-center justify-center bg-slate-900">
        <Loader2 className="w-12 h-12 text-cyan-400 animate-spin" />
      </div>
    )
  }
);

interface ToolItem {
  id: string;
  name: string;
  description?: string;
  url?: string;
  is_internal: boolean;
  category_path?: string[];
}

interface Category {
  id: string;
  name: string;
  description?: string;
  parent_id?: string;
  children: Category[];
  tools: ToolItem[];
}

export default function ToolsPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/osint-framework/categories/tree');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success && data.data) {
        setCategories(data.data);
      } else {
        throw new Error(data.error || 'Failed to load categories');
      }
    } catch (err) {
      console.error('Error fetching categories:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-slate-900">
        <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mb-4" />
        <p className="text-gray-400">Loading OSINT Framework...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-slate-900 p-6">
        <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-6 max-w-md">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-red-300 mb-2 text-center">
            Failed to Load Tools
          </h2>
          <p className="text-red-200 text-center mb-4">{error}</p>
          <div className="flex gap-3">
            <button
              onClick={fetchCategories}
              className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
            >
              Retry
            </button>
            <Link
              href="/"
              className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors text-center"
            >
              Go Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Home
            </Link>
            <div className="w-px h-6 bg-slate-600"></div>
            <div>
              <h1 className="text-2xl font-bold text-white">OSINT Tools Explorer</h1>
              <p className="text-sm text-gray-400">
                Browse and execute {categories.reduce((acc, cat) => {
                  const countTools = (c: Category): number => {
                    return c.tools.length + c.children.reduce((sum, child) => sum + countTools(child), 0);
                  };
                  return acc + countTools(cat);
                }, 0)} OSINT tools across {categories.length} categories
              </p>
            </div>
          </div>
          
          <button
            onClick={fetchCategories}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <Loader2 className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Browser Component */}
      <div className="flex-1 overflow-hidden">
        <OsintToolBrowser categories={categories} />
      </div>
    </div>
  );
}
