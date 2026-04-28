import { useState } from 'react';
import { BrainCircuit, Loader2, Target, ShieldAlert } from 'lucide-react';
import { StrategyService } from '../services/api';

const OffensiveStrategy = ({ findings, target = "186.64.114.50", stealth = 5 }) => {
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState(null);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await StrategyService.getStrategy(target, stealth, findings);
      setStrategy(data);
    } catch (err) {
      setError(err.message || "Error al conectar con el motor de IA");
    } finally {
      setLoading(false);
    }
  };

  
  if (!findings || findings.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-zinc-500 opacity-60 p-10">
        <ShieldAlert className="w-16 h-16 mb-4 text-zinc-600" />
        <h3 className="text-lg font-bold uppercase tracking-widest text-zinc-400">Telemetría Faltante</h3>
        <p className="font-mono text-sm mt-2 text-center max-w-md">
          El motor de IA requiere datos empíricos. Por favor, ejecuta un escaneo en la pestaña <span className="text-cyan-500 font-bold">NMAP</span> primero para alimentar la estrategia ofensiva.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 border-b border-zinc-800/80 pb-6 gap-4">
        <div>
          <h2 className="text-fuchsia-400 font-mono tracking-widest text-sm font-bold flex items-center gap-2 mb-1">
            <BrainCircuit className="w-4 h-4" /> Inteligencia Ofensiva
          </h2>
          <h3 className="text-white text-xl font-bold">Attack Roadmap Dinámico</h3>
          <p className="text-zinc-500 text-xs mt-2 font-mono">
            Objetivo: <span className="text-cyan-400">{target}</span> | Puertos vivos detectados: <span className="text-cyan-400">{findings.length}</span>
          </p>
        </div>
        
        <button
          onClick={handleGenerate}
          disabled={loading}
          className={`px-6 py-3 rounded-lg uppercase tracking-widest font-bold text-xs transition-all flex items-center gap-3 whitespace-nowrap
            ${loading
              ? 'bg-fuchsia-900/20 text-fuchsia-500/50 cursor-not-allowed border border-fuchsia-900/30'
              : 'bg-fuchsia-600/10 hover:bg-fuchsia-600/20 text-fuchsia-400 border border-fuchsia-500/30 shadow-[0_0_15px_rgba(217,70,239,0.15)]'
            }`}
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
          {loading ? 'Procesando Red Team Plan...' : 'Generar Ruta de Ataque'}
        </button>
      </div>

      {error && (
        <div className="mb-6 text-sm text-red-400 font-mono p-4 bg-red-950/20 rounded border border-red-900/50 flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      
      {strategy && strategy.steps && (
        <div className="flex flex-col gap-6 relative px-2 md:px-6 max-w-5xl mx-auto w-full pb-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
          
          
          <div className="absolute left-[34px] md:left-[50px] top-2 bottom-2 w-[2px] bg-zinc-800 z-0"></div>
          
          {strategy.steps.map((step, idx) => (
            <div key={idx} className="relative z-10 flex gap-4 md:gap-6">
              
              
              <div className="flex-shrink-0 mt-1">
                <div className="w-12 h-12 rounded-full bg-[#0a0a0c] border-2 border-zinc-700 flex items-center justify-center shadow-lg shadow-black/50">
                  <span className="text-zinc-300 font-mono font-bold">{idx + 1}</span>
                </div>
              </div>
              
              
              <div className="flex-1 bg-[#121214] border border-zinc-800/80 rounded-xl p-5 hover:border-zinc-600 transition-colors shadow-lg shadow-black/20 group">
                <div className="flex flex-col sm:flex-row justify-between sm:items-start mb-4 gap-3">
                  <span className="font-bold text-white text-lg uppercase tracking-wide group-hover:text-fuchsia-400 transition-colors">
                    {step.phase}
                  </span>
                  <span className={`text-[10px] uppercase tracking-wider font-bold px-3 py-1 rounded border whitespace-nowrap self-start
                    ${step.risk?.toLowerCase() === 'alto' || step.risk?.toLowerCase() === 'high' 
                      ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                      step.risk?.toLowerCase() === 'medio' || step.risk?.toLowerCase() === 'medium' 
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                      'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    }`}
                  >
                    Riesgo {step.risk}
                  </span>
                </div>
                
                <p className="text-zinc-300 text-sm mb-4 leading-relaxed">
                  {step.action}
                </p>
                
                <div className="bg-[#0a0a0c] rounded-lg p-4 border border-zinc-800/50">
                  <p className="text-zinc-500 text-xs italic font-mono leading-relaxed">
                    "{step.justification}"
                  </p>
                </div>
              </div>

            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default OffensiveStrategy;