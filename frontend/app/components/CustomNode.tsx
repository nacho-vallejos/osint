import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Globe, Server, Mail } from 'lucide-react';

interface CustomNodeData {
  label: string;
  type: 'dns' | 'ip' | 'email' | 'default';
  info?: string;
}

const CustomNode = ({ data, selected }: NodeProps<CustomNodeData>) => {
  const getIcon = () => {
    switch (data.type) {
      case 'dns':
        return <Globe className="w-5 h-5" />;
      case 'ip':
        return <Server className="w-5 h-5" />;
      case 'email':
        return <Mail className="w-5 h-5" />;
      default:
        return <Globe className="w-5 h-5" />;
    }
  };

  const getColor = () => {
    switch (data.type) {
      case 'dns':
        return 'border-cyan-500 bg-slate-800';
      case 'ip':
        return 'border-green-500 bg-slate-800';
      case 'email':
        return 'border-purple-500 bg-slate-800';
      default:
        return 'border-gray-500 bg-slate-800';
    }
  };

  return (
    <div
      className={`px-4 py-2 shadow-lg rounded-lg border-2 ${getColor()} ${
        selected ? 'ring-2 ring-cyan-400' : ''
      } min-w-[180px] transition-all duration-200`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-cyan-500" />
      
      <div className="flex items-center gap-2">
        <div className="text-cyan-400">{getIcon()}</div>
        <div className="flex-1">
          <div className="text-sm font-bold text-white">{data.label}</div>
          {data.info && (
            <div className="text-xs text-gray-400 mt-1">{data.info}</div>
          )}
        </div>
      </div>
      
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-cyan-500" />
    </div>
  );
};

export default memo(CustomNode);
