import { useEffect, useState } from 'react';
import { Server, CheckCircle, Radar, Activity, ChevronRight, AlertTriangle } from 'lucide-react';
import ParetoVisualization from './ParetoVisualization';

const TACTICAL_MESSAGES = [
  "Inicializando población aleatoria de configuraciones...",
  "Calculando frentes de Pareto no dominados...",
  "Evaluando Noise Score vs Eficiencia de escaneo...",
  "Aplicando distancias de apiñamiento (Crowding Distance)...",
  "Ejecutando operadores genéticos de cruce y mutación...",
  "Optimizando vectores de sigilo para evitar IDS...",
  "Filtrando soluciones óptimas en el frente de Pareto...",
  "Sincronizando con el motor de Fingerprinting..."
];

function IntelligenceResults({ result, loading, error }) {
  const [tacticalMessage, setTacticalMessage] = useState(TACTICAL_MESSAGES[0]);

  
  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => {
        const randomIndex = Math.floor(Math.random() * TACTICAL_MESSAGES.length);
        setTacticalMessage(TACTICAL_MESSAGES[randomIndex]);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [loading]);


  return (
    <div className="bg-[#121214] border border-zinc-800/80 rounded-xl shadow-2xl min-h-[600px] flex flex-col overflow-hidden">
      {/* Header del Panel */}
      <div className="bg-zinc-900/50 border-b border-zinc-800/80 p-4 px-6 flex items-center justify-between">
        <h2 className="text-white font-semibold flex items-center gap-2 tracking-wide">
          <Server className="w-5 h-5 text-zinc-400" /> Inteligencia Recolectada
        </h2>
        {result && (
          <span className="flex items-center gap-2 text-xs text-green-400 bg-green-400/10 px-3 py-1.5 rounded-full border border-green-400/20">
            <CheckCircle className="w-3.5 h-3.5" /> Escaneo Exitoso
          </span>
        )}
      </div>

      <div className="p-6 flex-1 overflow-y-auto custom-scrollbar">
        {/* Estado: Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl flex items-start gap-3 mb-6">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Estado: Idle (Esperando) */}
        {!result && !loading && !error && (
          <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-4 py-20">
            <Radar className="w-16 h-16 opacity-20" />
            <p className="text-sm tracking-widest uppercase">Esperando telemetría de red...</p>
          </div>
        )}

        {/* Estado: Loading (Motor Evolutivo) */}
        {loading && (
          <div className="h-full flex flex-col items-center justify-center text-cyan-500/70 space-y-6 py-20">
            <div className="relative">
              <Activity className="w-16 h-16 animate-pulse" />
              <div className="absolute inset-0 border-4 border-cyan-500/20 rounded-full animate-ping"></div>
            </div>
            <div className="text-center space-y-2">
              <p className="text-sm tracking-[0.2em] uppercase animate-pulse font-bold">
                Ejecutando Motor Evolutivo
              </p>
              <p className="text-[10px] text-zinc-500 font-mono italic">
                {"> "} {tacticalMessage}
              </p>
            </div>
          </div>
        )}

        {/* Estado: Resultado (Data Ready) */}
        {result && (
          <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
            
            {/* 1. Métricas de la Configuración Seleccionada */}
            <section>
              <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-4">Parámetros de Auditoría Óptimos</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-[#0a0a0b] p-4 rounded border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">NOISE SCORE (f1)</p>
                  <p className="text-2xl text-red-400">{result.best_config.metrics.noise_score.toFixed(2)}</p>
                </div>
                <div className="bg-[#0a0a0b] p-4 rounded border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">ESPERA (Wait Time)</p>
                  <p className="text-2xl text-cyan-400">
                    {result.best_config.wait_time_ms.toFixed(1)}
                    <span className="text-sm text-zinc-600 ml-1">ms</span>
                  </p>
                </div>
                <div className="bg-[#0a0a0b] p-4 rounded border border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-1">CONCURRENCIA (Hilos)</p>
                  <p className="text-2xl text-white">
                    {result.best_config.threads} 
                    <span className="text-sm text-zinc-600 ml-1">hilos</span>
                  </p>
                </div>
              </div>
            </section>

            {/* 2. Visualización Matemática del Frente de Pareto */}
            {result.pareto_front && (
              <section className="animate-in fade-in zoom-in duration-1000 delay-200">
                <ParetoVisualization 
                  data={result.pareto_front} 
                  selectedPoint={{
                    noise: result.best_config.metrics.noise_score,
                    time: result.best_config.metrics.estimated_time_sec
                  }} 
                />
              </section>
            )}

            {/* 3. Vectores de Ataque Identificados */}
            <section>
              <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-4">Servicios Identificados</h3>
              <div className="bg-[#0a0a0b] rounded border border-zinc-800 overflow-hidden shadow-lg">
                <table className="w-full text-left text-sm">
                  <thead className="bg-zinc-900/80 border-b border-zinc-800 text-zinc-400">
                    <tr>
                      <th className="p-4">PUERTO</th>
                      <th className="p-4">SERVICIO</th>
                      <th className="p-4">FINGERPRINT / BANNER</th>
                      <th className="p-4">OS GUESS</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/50">
                    {result.findings.map((finding, idx) => (
                      <tr key={idx} className="hover:bg-zinc-900/40 transition-colors group">
                        <td className="p-4 text-cyan-400 font-mono flex items-center gap-2">
                          <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" /> 
                          {finding.port}
                        </td>
                        <td className="p-4 text-white font-semibold">
                          {finding.service.toUpperCase()}
                        </td>
                        <td className="p-4 text-zinc-400 font-mono text-xs truncate max-w-[250px]" title={finding.banner}>
                          {finding.banner || 'No Banner Detected'}
                        </td>
                        <td className="p-4">
                          <span className="px-2 py-1 rounded bg-fuchsia-500/10 text-fuchsia-400 text-[10px] border border-fuchsia-500/20 uppercase font-bold">
                            {finding.os_guess}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

          </div>
        )}
      </div>
    </div>
  );
}

export default IntelligenceResults;