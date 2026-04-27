import { Handle, Position } from 'reactflow';
import { Laptop, Server, Network, Skull } from 'lucide-react'; 

const TacticalNode = ({ data }) => {
  const getIcon = () => {
    switch (data.type) {
      case 'attacker': return <Laptop className="w-5 h-5 text-fuchsia-400 drop-shadow-[0_0_8px_rgba(217,70,239,0.8)]" />;
      case 'target': return <Server className="w-5 h-5 text-cyan-400 drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]" />;
      case 'critical': return <Skull className="w-5 h-5 text-red-500 animate-pulse drop-shadow-[0_0_8px_rgba(239,68,68,0.8)]" />;
      default: return <Network className="w-5 h-5 text-zinc-400" />; 
    }
  };

  
  const getStyles = () => {
    if (data.type === 'attacker') {
      return 'border-fuchsia-500/50 bg-[#1a0b1a] shadow-[0_0_15px_rgba(217,70,239,0.15)] ring-1 ring-fuchsia-500/30';
    }
    if (data.type === 'target') {
      return 'border-cyan-500/50 bg-[#0b1a1f] shadow-[0_0_15px_rgba(6,182,212,0.15)] ring-1 ring-cyan-500/30';
    }
    if (data.type === 'critical') {
      return 'border-red-500/50 bg-[#1f0b0b] shadow-[0_0_15px_rgba(239,68,68,0.2)] ring-1 ring-red-500/30';
    }
    
    return 'border-zinc-800 bg-[#121214] hover:bg-[#18181b] hover:border-zinc-700'; 
  };

  return (
    <div className={`min-w-[160px] px-4 py-3 rounded-lg border backdrop-blur-sm flex items-center gap-3 transition-all duration-300 group ${getStyles()}`}>
      
      
      <Handle 
        type="target" 
        position={Position.Top} 
        className="opacity-0 w-2 h-2 rounded-none border-none bg-transparent" 
      />
      
      
      <div className="flex-shrink-0 bg-black/40 p-1.5 rounded-md border border-white/5">
        {getIcon()}
      </div>

      
      <div className="flex flex-col">
        <span className="text-[9px] text-zinc-500 uppercase tracking-widest font-mono font-bold">
          {data.label_title || 'Unknown Entity'}
        </span>
        <span className={`text-sm font-bold tracking-wide ${data.type === 'attacker' ? 'text-fuchsia-100' : (data.type === 'target' ? 'text-cyan-100' : 'text-zinc-200')}`}>
          {data.label_value || 'N/A'}
        </span>
      </div>

      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="opacity-0 w-2 h-2 rounded-none border-none bg-transparent" 
      />
    </div>
  );
};

export default TacticalNode;