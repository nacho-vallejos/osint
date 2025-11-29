'use client';

import React, { useCallback, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  MarkerType,
  MiniMap,
  Panel,
} from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';

const nodeTypes = {
  custom: CustomNode,
};

interface GraphLayout {
  direction: 'TB' | 'LR';
  nodeWidth: number;
  nodeHeight: number;
}

const getLayoutedElements = (nodes: Node[], edges: Edge[], layout: GraphLayout) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: layout.direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: layout.nodeWidth, height: layout.nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - layout.nodeWidth / 2,
        y: nodeWithPosition.y - layout.nodeHeight / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
};

interface OsintGraphViewerProps {
  initialNodes?: Node[];
  initialEdges?: Edge[];
  direction?: 'TB' | 'LR';
}

export default function OsintGraphViewer({
  initialNodes = [],
  initialEdges = [],
  direction = 'LR',
}: OsintGraphViewerProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [layout, setLayout] = useState<GraphLayout>({
    direction,
    nodeWidth: 200,
    nodeHeight: 80,
  });

  React.useEffect(() => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      initialNodes,
      initialEdges,
      layout
    );
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [initialNodes, initialEdges, layout, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: 'smoothstep',
            animated: true,
            markerEnd: { type: MarkerType.ArrowClosed },
          },
          eds
        )
      ),
    [setEdges]
  );

  const onLayout = useCallback(
    (newDirection: 'TB' | 'LR') => {
      const newLayout = { ...layout, direction: newDirection };
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        nodes,
        edges,
        newLayout
      );
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      setLayout(newLayout);
    },
    [nodes, edges, layout, setNodes, setEdges]
  );

  return (
    <div className="w-full h-screen bg-slate-900">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-slate-900"
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#06b6d4', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#06b6d4' },
        }}
      >
        <Background color="#1e293b" gap={16} />
        <Controls className="bg-slate-800 border border-slate-700" />
        <MiniMap
          className="bg-slate-800 border border-slate-700"
          nodeColor={(node) => {
            switch (node.data.type) {
              case 'dns':
                return '#06b6d4';
              case 'ip':
                return '#10b981';
              case 'email':
                return '#a855f7';
              default:
                return '#6b7280';
            }
          }}
        />
        <Panel position="top-right" className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <div className="flex flex-col gap-2">
            <h3 className="text-white font-bold mb-2">Layout</h3>
            <button
              onClick={() => onLayout('LR')}
              className="px-3 py-1 bg-cyan-600 text-white rounded hover:bg-cyan-700 text-sm"
            >
              Horizontal
            </button>
            <button
              onClick={() => onLayout('TB')}
              className="px-3 py-1 bg-cyan-600 text-white rounded hover:bg-cyan-700 text-sm"
            >
              Vertical
            </button>
          </div>
        </Panel>
        <Panel position="top-left" className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <h3 className="text-white font-bold mb-2">Legend</h3>
          <div className="flex flex-col gap-2 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-cyan-500 rounded"></div>
              <span className="text-gray-300">DNS Record</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span className="text-gray-300">IP Address</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-purple-500 rounded"></div>
              <span className="text-gray-300">Email</span>
            </div>
          </div>
        </Panel>
        <Panel position="bottom-left" className="bg-slate-800 p-4 rounded-lg border border-slate-700">
          <div className="text-white text-sm">
            <p className="font-bold mb-1">Stats:</p>
            <p className="text-gray-300">Nodes: {nodes.length}</p>
            <p className="text-gray-300">Edges: {edges.length}</p>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}
