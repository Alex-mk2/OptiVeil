import { ShieldAlert, Crosshair, Terminal, Activity} from 'lucide-react';

function AttackRoadmap({ steps }) {
  if (!steps || steps.length === 0) return null;

  
  const getRiskStyles = (risk) => {
    const r = (risk || '').toLowerCase();
    if (r.includes('alto') || r.includes('crítico')) {
      return { text: 'text-red-400', bg: 'bg-red-400/10', border: 'border-red-400/20' };
    }
    if (r.includes('medio')) {
      return { text: 'text-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20' };
    }
    return { text: 'text-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20' };
  };

  
  const getStepIcon = (id, totalSteps) => {
    if (id === 1) return <Crosshair className="w-5 h-5 text-cyan-400" />; // Entrada
    if (id === totalSteps) return <Terminal className="w-5 h-5 text-fuchsia-400" />; // Objetivo Final
    return <Activity className="w-5 h-5 text-zinc-400" />; // Movimiento Lateral
  };

  return (
    <div className="bg-[#121214] p-6 rounded-xl border border-zinc-800 shadow-inner mt-8">
      <h3 className="text-cyan-400 text-xs font-bold uppercase tracking-widest mb-6 flex items-center gap-2">
        <ShieldAlert className="w-4 h-4" /> 
        Ruta de Ataque Sugerida (IA Estratégica)
      </h3>

      {/* AQUÍ ESTÁ LA MAGIA: Contenedor con altura máxima y scroll interno */}
      <div className="pr-4">
        <div className="space-y-2 relative">
          {steps.map((step, index) => {
            const styles = getRiskStyles(step.risk);
            
            return (
              <div key={step.id} className="relative group">
                {/* Conector Vertical (Línea de tiempo) */}
                {/* Ajustamos el bottom para que la línea no se corte feo con el scroll */}
                {index !== steps.length - 1 && (
                  <div className="absolute left-6 top-12 bottom-[-1.5rem] w-px bg-zinc-800 group-hover:bg-cyan-900/50 transition-colors z-0" />
                )}
                
                {/* ... el resto de tu código de la tarjeta queda EXACTAMENTE IGUAL ... */}
                <div className="relative z-10 flex gap-6 items-start">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-zinc-950 border border-zinc-800 flex items-center justify-center shadow-lg mt-1 group-hover:border-cyan-500/50 transition-colors">
                    {getStepIcon(step.id, steps.length)}
                  </div>

                  <div className="flex-1 bg-[#0a0a0b] border border-zinc-800/80 p-5 rounded-lg hover:border-zinc-700 transition-all hover:bg-zinc-900/40">
                    <div className="flex flex-col md:flex-row md:items-center justify-between mb-3 gap-2">
                      <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">
                        Fase {step.id}: <span className="text-zinc-300">{step.phase}</span>
                      </span>
                      <span className={`px-2 py-1 rounded text-[9px] uppercase font-bold border ${styles.bg} ${styles.text} ${styles.border}`}>
                        Riesgo {step.risk}
                      </span>
                    </div>
                    
                    <h4 className="text-white font-medium text-sm mb-2">{step.action}</h4>
                    
                    <div className="bg-zinc-900/50 p-3 rounded border border-zinc-800/50">
                      <p className="text-zinc-400 text-xs italic leading-relaxed">
                        "{step.justification}"
                      </p>
                    </div>
                  </div>
                </div>
                
                {index !== steps.length - 1 && <div className="h-6" />}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default AttackRoadmap;