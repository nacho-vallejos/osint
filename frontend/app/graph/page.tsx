'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { Node, Edge, MarkerType } from 'reactflow';

// Dynamically import OsintGraphViewer to avoid SSR issues
const OsintGraphViewer = dynamic(
  () => import('../components/OsintGraphViewer'),
  { ssr: false }
);

const sampleNodes: Node[] = [
  {
    id: '1',
    type: 'custom',
    position: { x: 0, y: 0 },
    data: { label: 'example.com', type: 'dns', info: 'Target Domain' },
  },
  {
    id: '2',
    type: 'custom',
    position: { x: 250, y: 0 },
    data: { label: '192.168.1.1', type: 'ip', info: 'A Record' },
  },
  {
    id: '3',
    type: 'custom',
    position: { x: 250, y: 100 },
    data: { label: 'mail.example.com', type: 'dns', info: 'MX Record' },
  },
  {
    id: '4',
    type: 'custom',
    position: { x: 500, y: 100 },
    data: { label: '10.0.0.1', type: 'ip', info: 'Mail Server IP' },
  },
  {
    id: '5',
    type: 'custom',
    position: { x: 250, y: 200 },
    data: { label: 'admin@example.com', type: 'email', info: 'Contact Email' },
  },
  {
    id: '6',
    type: 'custom',
    position: { x: 250, y: -100 },
    data: { label: 'ns1.example.com', type: 'dns', info: 'NS Record' },
  },
  {
    id: '7',
    type: 'custom',
    position: { x: 500, y: -100 },
    data: { label: '8.8.8.8', type: 'ip', info: 'Nameserver IP' },
  },
  {
    id: '8',
    type: 'custom',
    position: { x: 750, y: 0 },
    data: { label: 'cdn.example.com', type: 'dns', info: 'CNAME Record' },
  },
];

const sampleEdges: Edge[] = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    type: 'smoothstep',
    animated: true,
    label: 'A Record',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e1-3',
    source: '1',
    target: '3',
    type: 'smoothstep',
    animated: true,
    label: 'MX',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e3-4',
    source: '3',
    target: '4',
    type: 'smoothstep',
    animated: true,
    label: 'Resolves to',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e1-5',
    source: '1',
    target: '5',
    type: 'smoothstep',
    animated: true,
    label: 'Contact',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e1-6',
    source: '1',
    target: '6',
    type: 'smoothstep',
    animated: true,
    label: 'NS',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e6-7',
    source: '6',
    target: '7',
    type: 'smoothstep',
    animated: true,
    label: 'Resolves to',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
  {
    id: 'e2-8',
    source: '2',
    target: '8',
    type: 'smoothstep',
    animated: true,
    label: 'CDN',
    markerEnd: { type: MarkerType.ArrowClosed },
  },
];

export default function GraphPage() {
  return (
    <div className="h-screen w-full">
      <OsintGraphViewer 
        initialNodes={sampleNodes} 
        initialEdges={sampleEdges}
        direction="LR"
      />
    </div>
  );
}
