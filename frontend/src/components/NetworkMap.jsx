import { useState, useEffect } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';
import { TopologyService } from '../services/api';
import TacticalNode from './NodeTypes'; 


const nodeTypes = { tactical: TacticalNode };


const defaultTopology = {
  nodes: [
    {
      id: 'attacker',
      type: 'tactical',
      position: { x: 250, y: 0 },
      data: { type: 'attacker', label_title: 'Terminal Ofensiva', label_value: 'OptiVeil Core' }
    },
    {
      id: 'target',
      type: 'tactical',
      position: { x: 250, y: 150 },
      data: { type: 'target', label_title: 'Objetivo', label_value: '186.64.114.50' }
    }
  ],
  edges: [
    { id: 'e-att-tar', source: 'attacker', target: 'target', animated: true, style: { stroke: '#d946ef', strokeWidth: 1.5, opacity: 0.6 } }
  ]
};

const NetworkMap = ({ target }) => {
  const [topology, setTopology] = useState(null);
  const [loadedTarget, setLoadedTarget] = useState(null);

  const loading = Boolean(target) && loadedTarget !== target;

  useEffect(() => {
    let isMounted = true;

    if (!target) {
      return () => { isMounted = false; };
    }

    TopologyService.getTopology(target)
      .then(data => {
        if (!isMounted) return;

        if (data && data.nodes && data.nodes.length > 0 && Array.isArray(data.edges)) {
          setTopology(data);
        } else {
          setTopology(defaultTopology);
        }
      })
      .catch(err => {
        if (!isMounted) return;
        console.warn("Usando topología base debido a error:", err);
        setTopology(defaultTopology);
      })
      .finally(() => {
        if (isMounted) setLoadedTarget(target);
      });

    return () => { isMounted = false; };
  }, [target]);

 
  if (loading) {
    return (
      <div style={{ width: '100%', height: '500px' }} className="bg-[#0a0a0c] rounded-lg border border-zinc-800/80 flex flex-col items-center justify-center opacity-70">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500 mb-4"></div>
        <span className="text-cyan-500 text-xs uppercase tracking-widest font-mono">Generando Matriz Lógica...</span>
      </div>
    );
  }

 
  const dynamicNodes = topology?.nodes.map(node => 
    node.id === 'target' && target 
      ? { ...node, data: { ...node.data, label_value: target } } 
      : node
  ) || [];

  return (
    <div style={{ width: '100%', height: '500px' }} className="bg-[#0a0a0c] rounded-lg border border-zinc-800/80 overflow-hidden relative shadow-inner">
      <ReactFlow
        nodes={dynamicNodes}
        edges={topology?.edges || []}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background color="#27272a" gap={24} size={1.5} variant="dots" />
        <Controls 
          showInteractive={false} 
          className="bg-[#121214] border-zinc-800 fill-zinc-400 shadow-xl" 
          style={{ button: { borderBottom: '1px solid #27272a' } }}
        />
      </ReactFlow>
    </div>
  );
};

export default NetworkMap;