import { useState } from 'react';
import { Terminal, Radar, Activity } from 'lucide-react';


function AuditForm({ onScan, loading }) {
  const [target, setTarget] = useState('186.64.114.50');
  const [stealth, setStealth] = useState(5);
  const [ports, setPorts] = useState(100);

  const handleSubmit = (e) => {
    e.preventDefault();
    onScan(target, stealth, ports);
  };

  
  return (
    <form onSubmit={handleSubmit} className="bg-[#121214] p-6 rounded-xl border border-zinc-800/80 shadow-2xl">
      <h2 className="flex items-center gap-2 mb-6 text-white font-semibold tracking-wide">
        <Terminal className="w-5 h-5 text-cyan-400" /> Parámetros de Inserción
      </h2>
      
      <div className="space-y-5">
        <div>
          <label className="block text-xs text-zinc-500 mb-2 uppercase tracking-wider">IPv4 Objetivo</label>
          <input 
            type="text"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="w-full bg-[#0a0a0b] border border-zinc-800 p-3 rounded text-cyan-400 focus:outline-none focus:border-cyan-500"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-zinc-500 mb-2 uppercase tracking-wider">Sigilo (1-10)</label>
            <input 
              type="number" min="1" max="10"
              value={stealth}
              onChange={(e) => setStealth(e.target.value)}
              className="w-full bg-[#0a0a0b] border border-zinc-800 p-3 rounded text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
          <div>
            <label className="block text-xs text-zinc-500 mb-2 uppercase tracking-wider">Puertos</label>
            <input 
              type="number" min="1" max="65535"
              value={ports}
              onChange={(e) => setPorts(e.target.value)}
              className="w-full bg-[#0a0a0b] border border-zinc-800 p-3 rounded text-white focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>
        
        <button 
          type="submit"
          disabled={loading}
          className="w-full bg-cyan-500 hover:bg-cyan-400 text-zinc-950 font-bold p-4 rounded flex items-center justify-center gap-3 mt-4 disabled:opacity-50"
        >
          {loading ? <Activity className="animate-spin w-5 h-5" /> : <Radar className="w-5 h-5" />}
          {loading ? "CALCULANDO NSGA-II..." : "INICIAR AUDITORÍA"}
        </button>
      </div>
    </form>
  );
}

export default AuditForm;