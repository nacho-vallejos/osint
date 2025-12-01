'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { Node, Edge, MarkerType } from 'reactflow';

const OsintGraphViewer = dynamic(
  () => import('../components/OsintGraphViewer'),
  { ssr: false }
);

export default function GraphPage() {
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(false);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!domain.trim()) {
      setError('Ingresa un dominio o URL');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const dnsResponse = await fetch('http://localhost:8000/api/v1/collectors/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          collector_name: 'DNSCollector',
          target: domain.trim(),
        }),
      });

      const dnsResult = await dnsResponse.json();

      if (dnsResult.success && dnsResult.data) {
        const newNodes: Node[] = [];
        const newEdges: Edge[] = [];
        let nodeId = 0;

        newNodes.push({
          id: String(nodeId++),
          type: 'custom',
          position: { x: 0, y: 0 },
          data: { label: domain.trim(), type: 'dns', info: 'Target Domain' },
        });

        const mainNodeId = '0';

        if (dnsResult.data.a_records) {
          dnsResult.data.a_records.forEach((ip: string, idx: number) => {
            const id = String(nodeId++);
            newNodes.push({
              id,
              type: 'custom',
              position: { x: 300, y: idx * 80 },
              data: { label: ip, type: 'ip', info: 'A Record' },
            });
            newEdges.push({
              id: `e-${mainNodeId}-${id}`,
              source: mainNodeId,
              target: id,
              type: 'smoothstep',
              animated: true,
              label: 'A',
              markerEnd: { type: MarkerType.ArrowClosed },
            });
          });
        }

        if (dnsResult.data.mx_records) {
          dnsResult.data.mx_records.forEach((mx: string, idx: number) => {
            const id = String(nodeId++);
            newNodes.push({
              id,
              type: 'custom',
              position: { x: 300, y: -150 - idx * 80 },
              data: { label: mx, type: 'dns', info: 'MX Record' },
            });
            newEdges.push({
              id: `e-${mainNodeId}-${id}`,
              source: mainNodeId,
              target: id,
              type: 'smoothstep',
              animated: true,
              label: 'MX',
              markerEnd: { type: MarkerType.ArrowClosed },
            });
          });
        }

        if (dnsResult.data.ns_records) {
          dnsResult.data.ns_records.forEach((ns: string, idx: number) => {
            const id = String(nodeId++);
            newNodes.push({
              id,
              type: 'custom',
              position: { x: -300, y: idx * 80 },
              data: { label: ns, type: 'dns', info: 'NS Record' },
            });
            newEdges.push({
              id: `e-${mainNodeId}-${id}`,
              source: mainNodeId,
              target: id,
              type: 'smoothstep',
              animated: true,
              label: 'NS',
              markerEnd: { type: MarkerType.ArrowClosed },
            });
          });
        }

        if (dnsResult.data.txt_records) {
          dnsResult.data.txt_records.forEach((txt: string, idx: number) => {
            const id = String(nodeId++);
            const shortTxt = txt.length > 30 ? txt.substring(0, 30) + '...' : txt;
            newNodes.push({
              id,
              type: 'custom',
              position: { x: 600, y: idx * 80 },
              data: { label: shortTxt, type: 'dns', info: 'TXT Record' },
            });
            newEdges.push({
              id: `e-${mainNodeId}-${id}`,
              source: mainNodeId,
              target: id,
              type: 'smoothstep',
              animated: true,
              label: 'TXT',
              markerEnd: { type: MarkerType.ArrowClosed },
            });
          });
        }

        setNodes(newNodes);
        setEdges(newEdges);
      } else {
        setError(dnsResult.error || 'No se encontraron datos DNS');
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
    <div className="h-screen w-full flex flex-col">
      <div className="bg-slate-900/95 backdrop-blur-sm border-b border-slate-700 p-4 z-10">
        <div className="max-w-4xl mx-auto flex gap-4 items-center">
          <div className="flex-1">
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ingresa un dominio (ej: example.com)"
              className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              disabled={loading}
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            className="px-6 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors duration-200"
          >
            {loading ? 'Buscando...' : 'Analizar'}
          </button>
          <a
            href="/"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            Inicio
          </a>
        </div>
        
        {error && (
          <div className="max-w-4xl mx-auto mt-3">
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          </div>
        )}
      </div>

      <div className="flex-1">
        {nodes.length > 0 ? (
          <OsintGraphViewer 
            initialNodes={nodes} 
            initialEdges={edges}
            direction="LR"
          />
        ) : (
          <div className="h-full flex items-center justify-center bg-slate-900">
            <div className="text-center">
              <div className="text-6xl mb-4">🔍</div>
              <h2 className="text-2xl font-bold text-white mb-2">OSINT Graph Viewer</h2>
              <p className="text-gray-400">Ingresa un dominio para visualizar sus conexiones DNS</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
