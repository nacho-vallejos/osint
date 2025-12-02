'use client';

import React, { useState } from 'react';
import { 
  Search, 
  ExternalLink, 
  Play, 
  ChevronRight, 
  Folder, 
  Wrench, 
  Globe,
  Shield,
  Mail,
  User,
  Hash,
  MapPin,
  Phone,
  FileText,
  Image as ImageIcon,
  Video,
  Database,
  Clock
} from 'lucide-react';
import { useRouter } from 'next/navigation';

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

interface OsintToolBrowserProps {
  categories: Category[];
}

export default function OsintToolBrowser({ categories }: OsintToolBrowserProps) {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPath, setSelectedPath] = useState<Category[]>([]);
  const [hoveredWrench, setHoveredTool] = useState<string | null>(null);

  // Get icon for category name
  const getCategoryIcon = (name: string) => {
    const lowerName = name.toLowerCase();
    
    if (lowerName.includes('username') || lowerName.includes('user')) return User;
    if (lowerName.includes('email') || lowerName.includes('e-mail')) return Mail;
    if (lowerName.includes('ip') || lowerName.includes('network')) return Globe;
    if (lowerName.includes('domain')) return Globe;
    if (lowerName.includes('phone')) return Phone;
    if (lowerName.includes('location') || lowerName.includes('geo')) return MapPin;
    if (lowerName.includes('image') || lowerName.includes('photo')) return ImageIcon;
    if (lowerName.includes('video')) return Video;
    if (lowerName.includes('document') || lowerName.includes('file')) return FileText;
    if (lowerName.includes('database') || lowerName.includes('leak')) return Database;
    if (lowerName.includes('history') || lowerName.includes('archive')) return Clock;
    if (lowerName.includes('hash')) return Hash;
    if (lowerName.includes('security') || lowerName.includes('threat')) return Shield;
    
    return Folder;
  };

  // Filter categories and tools by search query
  const filterBySearch = (items: Category[]): Category[] => {
    if (!searchQuery.trim()) return items;

    const query = searchQuery.toLowerCase();
    
    return items
      .map(category => {
        const matchingTools = category.tools.filter(tool =>
          tool.name.toLowerCase().includes(query) ||
          tool.description?.toLowerCase().includes(query)
        );

        const matchingChildren = filterBySearch(category.children);

        const categoryMatches = category.name.toLowerCase().includes(query) ||
          category.description?.toLowerCase().includes(query);

        if (categoryMatches || matchingTools.length > 0 || matchingChildren.length > 0) {
          return {
            ...category,
            children: matchingChildren,
            tools: matchingTools
          };
        }

        return null;
      })
      .filter((cat): cat is Category => cat !== null);
  };

  // Get current column data based on selection path
  const getColumnData = (columnIndex: number): Category[] => {
    if (columnIndex === 0) {
      return filterBySearch(categories);
    }

    if (columnIndex <= selectedPath.length) {
      const parent = selectedPath[columnIndex - 1];
      return filterBySearch(parent?.children || []);
    }

    return [];
  };

  // Handle category selection
  const handleCategoryClick = (category: Category, columnIndex: number) => {
    const newPath = selectedPath.slice(0, columnIndex);
    newPath.push(category);
    setSelectedPath(newPath);
  };

  // Handle internal tool execution
  const handleExecuteInternal = (tool: ToolItem) => {
    const searchParams = new URLSearchParams({
      tool: tool.id,
      name: tool.name,
    });
    router.push(`/collectors?${searchParams.toString()}`);
  };

  // Handle external tool opening
  const handleOpenExternal = (url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const currentCategory = selectedPath.length > 0 ? selectedPath[selectedPath.length - 1] : null;
  const currentTools = currentCategory?.tools || [];

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* Search Bar */}
      <div className="p-4 bg-slate-800 border-b border-slate-700">
        <div className="relative">
          <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search OSINT tools and categories..."
            className="w-full pl-10 pr-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
          />
        </div>
        
        {/* Breadcrumb */}
        {selectedPath.length > 0 && (
          <div className="mt-3 flex items-center gap-2 text-sm text-gray-400">
            <button
              onClick={() => setSelectedPath([])}
              className="hover:text-cyan-400 transition-colors"
            >
              All Categories
            </button>
            {selectedPath.map((category, idx) => (
              <React.Fragment key={category.id}>
                <ChevronRight className="w-4 h-4" />
                <button
                  onClick={() => setSelectedPath(selectedPath.slice(0, idx + 1))}
                  className="hover:text-cyan-400 transition-colors"
                >
                  {category.name}
                </button>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Miller Columns Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Column 1: Root Categories */}
        <div className="w-80 border-r border-slate-700 overflow-y-auto bg-slate-900">
          <div className="p-2">
            <h3 className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Categories
            </h3>
            <div className="space-y-1">
              {getColumnData(0).map((category) => {
                const Icon = getCategoryIcon(category.name);
                const isSelected = selectedPath[0]?.id === category.id;
                
                return (
                  <button
                    key={category.id}
                    onClick={() => handleCategoryClick(category, 0)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                      isSelected
                        ? 'bg-cyan-600 text-white'
                        : 'text-gray-300 hover:bg-slate-800 hover:text-white'
                    }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <div className="flex-1 text-left">
                      <div className="font-medium">{category.name}</div>
                      {category.description && (
                        <div className="text-xs opacity-75 truncate">{category.description}</div>
                      )}
                    </div>
                    {(category.children.length > 0 || category.tools.length > 0) && (
                      <ChevronRight className="w-4 h-4 flex-shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Column 2: Subcategories (if any) */}
        {selectedPath.length > 0 && selectedPath[0].children.length > 0 && (
          <div className="w-80 border-r border-slate-700 overflow-y-auto bg-slate-850">
            <div className="p-2">
              <h3 className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Subcategories
              </h3>
              <div className="space-y-1">
                {getColumnData(1).map((category) => {
                  const Icon = getCategoryIcon(category.name);
                  const isSelected = selectedPath[1]?.id === category.id;
                  
                  return (
                    <button
                      key={category.id}
                      onClick={() => handleCategoryClick(category, 1)}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                        isSelected
                          ? 'bg-cyan-600 text-white'
                          : 'text-gray-300 hover:bg-slate-800 hover:text-white'
                      }`}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <div className="flex-1 text-left">
                        <div className="font-medium">{category.name}</div>
                        {category.description && (
                          <div className="text-xs opacity-75 truncate">{category.description}</div>
                        )}
                      </div>
                      {(category.children.length > 0 || category.tools.length > 0) && (
                        <ChevronRight className="w-4 h-4 flex-shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Column 3: Tools Panel */}
        <div className="flex-1 overflow-y-auto bg-slate-900">
          {currentTools.length > 0 ? (
            <div className="p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-white mb-2">
                  {currentCategory?.name} Tools
                </h2>
                <p className="text-gray-400">
                  {currentTools.length} tool{currentTools.length !== 1 ? 's' : ''} available
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {currentTools.map((tool) => (
                  <div
                    key={tool.id}
                    onMouseEnter={() => setHoveredTool(tool.id)}
                    onMouseLeave={() => setHoveredTool(null)}
                    className="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-cyan-500 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10"
                  >
                    <div className="flex items-start gap-3 mb-4">
                      <div className={`p-2.5 rounded-lg ${
                        tool.is_internal 
                          ? 'bg-cyan-600/20 text-cyan-400' 
                          : 'bg-purple-600/20 text-purple-400'
                      }`}>
                        {tool.is_internal ? (
                          <Wrench className="w-5 h-5" />
                        ) : (
                          <ExternalLink className="w-5 h-5" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-white mb-1 truncate">
                          {tool.name}
                        </h3>
                        {tool.is_internal && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-cyan-500/20 text-cyan-300 text-xs font-medium rounded-full">
                            Internal
                          </span>
                        )}
                      </div>
                    </div>

                    {tool.description && (
                      <p className="text-sm text-gray-400 mb-4 line-clamp-3">
                        {tool.description}
                      </p>
                    )}

                    {tool.is_internal ? (
                      <button
                        onClick={() => handleExecuteInternal(tool)}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-medium rounded-lg transition-colors"
                      >
                        <Play className="w-4 h-4" />
                        Execute Now
                      </button>
                    ) : tool.url ? (
                      <button
                        onClick={() => handleOpenExternal(tool.url!)}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Open External Site
                      </button>
                    ) : (
                      <div className="text-sm text-gray-500 italic">
                        No URL available
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : selectedPath.length > 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Wrench className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No Tools Found</h3>
                <p className="text-gray-400">
                  This category doesn't have any tools yet.
                </p>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center px-4">
                <Search className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Select a Category</h3>
                <p className="text-gray-400 max-w-md">
                  Choose a category from the left to explore available OSINT tools and resources.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stats Footer */}
      <div className="px-6 py-3 bg-slate-800 border-t border-slate-700 flex items-center justify-between text-sm">
        <div className="text-gray-400">
          {searchQuery ? (
            <span>Showing filtered results</span>
          ) : (
            <span>
              {categories.length} root categories • {
                categories.reduce((acc, cat) => {
                  const countTools = (c: Category): number => {
                    return c.tools.length + c.children.reduce((sum, child) => sum + countTools(child), 0);
                  };
                  return acc + countTools(cat);
                }, 0)
              } total tools
            </span>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-cyan-500 rounded-full"></div>
            <span className="text-gray-400">Internal Tools</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span className="text-gray-400">External Tools</span>
          </div>
        </div>
      </div>
    </div>
  );
}
