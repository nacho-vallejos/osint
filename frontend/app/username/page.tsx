'use client';

import { useState } from 'react';

interface PlatformResult {
  platform: string;
  url: string;
  exists: boolean;
  status_code: number | null;
  confidence: number;
  error?: string;
}

interface UsernameData {
  username: string;
  profiles: PlatformResult[];
  found: PlatformResult[];
  not_found: PlatformResult[];
  total_platforms: number;
  found_count: number;
}

export default function UsernamePage() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<UsernameData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!username.trim()) {
      setError('Por favor ingresa un username');
      return;
    }

    setLoading(true);
    setError(null);
    setData(null);

    try {
      const response = await fetch('http://localhost:8000/api/v1/collectors/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          collector_name: 'UsernameCollector',
          target: username.trim(),
        }),
      });

      const result = await response.json();

      if (result.success) {
        setData(result.data);
      } else {
        setError(result.error || 'Error al buscar el username');
      }
    } catch (err) {
      setError('Error de conexión con el servidor');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Username Search</h1>
          <p className="text-gray-300">Busca la presencia de un username en múltiples plataformas</p>
        </div>

        {/* Search Box */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 mb-8 border border-white/20">
          <div className="flex gap-4">
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ingresa un username (ej: octocat)"
              className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors duration-200"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Buscando...
                </span>
              ) : (
                'Buscar'
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-8">
            <p className="text-red-200">{error}</p>
          </div>
        )}

        {/* Results */}
        {data && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-4">
                Resultados para: <span className="text-blue-400">{data.username}</span>
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4">
                  <div className="text-3xl font-bold text-green-400">{data.found_count}</div>
                  <div className="text-gray-300">Perfiles encontrados</div>
                </div>
                <div className="bg-gray-500/20 border border-gray-500/50 rounded-lg p-4">
                  <div className="text-3xl font-bold text-gray-400">{data.not_found.length}</div>
                  <div className="text-gray-300">No encontrados</div>
                </div>
              </div>
            </div>

            {/* Found Profiles */}
            {data.found.length > 0 && (
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Perfiles Encontrados
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.found.map((profile) => (
                    <a
                      key={profile.platform}
                      href={profile.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 hover:bg-green-500/20 transition-colors duration-200 group"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-lg font-semibold text-white group-hover:text-green-400 transition-colors">
                            {profile.platform}
                          </div>
                          <div className="text-sm text-gray-400 truncate">{profile.url}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-green-400 font-mono">HTTP {profile.status_code}</span>
                          <svg className="w-5 h-5 text-gray-400 group-hover:text-green-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </div>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Not Found Profiles */}
            {data.not_found.length > 0 && (
              <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                  <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  No Encontrados
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {data.not_found.map((profile) => (
                    <div
                      key={profile.platform}
                      className="bg-gray-500/10 border border-gray-500/30 rounded-lg p-3"
                    >
                      <div className="text-gray-400 font-medium">{profile.platform}</div>
                      {profile.status_code && (
                        <div className="text-xs text-gray-500 font-mono">HTTP {profile.status_code}</div>
                      )}
                      {profile.error && (
                        <div className="text-xs text-red-400 mt-1">{profile.error}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Back to Home */}
        <div className="mt-8 text-center">
          <a
            href="/"
            className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Volver al inicio
          </a>
        </div>
      </div>
    </div>
  );
}
