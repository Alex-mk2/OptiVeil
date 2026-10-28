import { useEffect, useState } from 'react';
import { Server, CheckCircle, Radar, Activity, ChevronRight, AlertTriangle, ShieldAlert, LineChart, ShieldCheck, Loader2 } from 'lucide-react';
import ParetoVisualization from './ParetoVisualization';
import AttackRoadmap from './AttackRoadmap';
import { ValidationService } from '../services/api';

// Estilos del badge según el veredicto de validación (SPEC-0002).
const VALIDATION_STYLES = {
  confirmed:     { c: 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10', label: 'Confirmado' },
  likely:        { c: 'text-amber-400 border-amber-400/30 bg-amber-400/10',       label: 'Probable' },
  not_confirmed: { c: 'text-zinc-400 border-zinc-600/30 bg-zinc-600/10',          label: 'No confirmado' },
  not_tested:    { c: 'text-zinc-500 border-zinc-700/30 bg-zinc-700/10',          label: 'No probado' },
};

// Color del badge de severidad (SPEC-0007).
const SEVERITY_STYLES = {
  critical: 'text-red-400 border-red-400/30 bg-red-400/10',
  high:     'text-orange-400 border-orange-400/30 bg-orange-400/10',
  medium:   'text-amber-400 border-amber-400/30 bg-amber-400/10',
  low:      'text-sky-400 border-sky-400/30 bg-sky-400/10',
  info:     'text-zinc-400 border-zinc-600/30 bg-zinc-600/10',
  unknown:  'text-zinc-500 border-zinc-700/30 bg-zinc-700/10',
};
const SEVERITY_RANK = { critical: 5, high: 4, medium: 3, low: 2, info: 1, unknown: 0 };
const STATUS_RANK = { confirmed: 3, likely: 2, not_confirmed: 1, not_tested: 0 };

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

function IntelligenceResults({ result, loading, error, target }) {
  const [tacticalMessage, setTacticalMessage] = useState(TACTICAL_MESSAGES[0]);
  const [activeTab, setActiveTab] = useState('telemetry');
  // Validación no destructiva (opt-in). Lista plana de veredictos (null = no
  // ejecutada); de ella se derivan el badge por puerto y el veredicto ordenado.
  const [validationList, setValidationList] = useState(null);
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState('');

  const handleValidate = async () => {
    if (!result?.findings?.length) return;
    setValidating(true);
    setValidationError('');
    try {
      const findings = result.findings.map((f) => ({
        port: f.port, service: f.service, banner: f.banner || '',
      }));
      const data = await ValidationService.validate(target, findings);
      setValidationList(data.results || []);
    } catch (err) {
      setValidationError(
        err.response?.data?.detail || 'No se pudo validar. ¿El objetivo está en el scope autorizado?'
      );
    } finally {
      setValidating(false);
    }
  };

  // Veredicto más fuerte por puerto (para el badge de la tabla de servicios).
  const strongest = (a, b) => {
    const sa = STATUS_RANK[a.status] || 0, sb = STATUS_RANK[b.status] || 0;
    if (sa !== sb) return sa > sb ? a : b;
    return (SEVERITY_RANK[a.severity] || 0) >= (SEVERITY_RANK[b.severity] || 0) ? a : b;
  };
  const byPort = {};
  (validationList || []).forEach((r) => {
    byPort[r.port] = byPort[r.port] ? strongest(byPort[r.port], r) : r;
  });

  // Veredicto completo, ordenado por severidad y luego certeza (lo crítico arriba).
  const verdicts = [...(validationList || [])].sort((a, b) => {
    const d = (SEVERITY_RANK[b.severity] || 0) - (SEVERITY_RANK[a.severity] || 0);
    return d !== 0 ? d : (STATUS_RANK[b.status] || 0) - (STATUS_RANK[a.status] || 0);
  });

  const validationBadge = (port) => {
    const r = byPort[port];
    if (!r) return <span className="text-zinc-600 text-[10px]">—</span>;
    const s = VALIDATION_STYLES[r.status] || VALIDATION_STYLES.not_tested;
    const title = r.evidence?.reproduce ? `Reproducir: ${r.evidence.reproduce}` : '';
    return (
      <span title={title} className={`px-2 py-1 rounded text-[9px] uppercase font-bold border ${s.c}`}>
        {s.label}
      </span>
    );
  };

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
      <div className="bg-zinc-900/50 p-4 px-6 flex items-center justify-between">
        <h2 className="text-white font-semibold flex items-center gap-2 tracking-wide">
          <Server className="w-5 h-5 text-zinc-400" /> Inteligencia Recolectada
        </h2>
        {result && (
          <span className="flex items-center gap-2 text-xs text-green-400 bg-green-400/10 px-3 py-1.5 rounded-full border border-green-400/20 shadow-[0_0_10px_rgba(74,222,128,0.1)]">
            <CheckCircle className="w-3.5 h-3.5" /> Escaneo Exitoso
          </span>
        )}
      </div>

      {/* NUEVO: Barra de Navegación de Pestañas (Solo se muestra si hay resultados) */}
      {result && (
        <div className="flex border-b border-zinc-800/80 bg-zinc-900/30 px-6">
          <button 
            onClick={() => setActiveTab('telemetry')}
            className={`flex items-center gap-2 px-4 py-3 text-[11px] font-bold uppercase tracking-widest transition-all ${
              activeTab === 'telemetry' 
                ? 'text-cyan-400 border-b-2 border-cyan-400' 
                : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <LineChart className="w-4 h-4" /> Telemetría NSGA-II
          </button>
          
          {/* La pestaña de estrategia solo aparece si la IA logró generar la ruta */}
          {result.attack_roadmap && result.attack_roadmap.steps && (
            <button 
              onClick={() => setActiveTab('strategy')}
              className={`flex items-center gap-2 px-4 py-3 text-[11px] font-bold uppercase tracking-widest transition-all ${
                activeTab === 'strategy' 
                  ? 'text-fuchsia-400 border-b-2 border-fuchsia-400' 
                  : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              <ShieldAlert className="w-4 h-4" /> Estrategia Ofensiva (IA)
            </button>
          )}
        </div>
      )}

      <div className="p-6 flex-1 overflow-y-auto custom-scrollbar">
        {/* Estado: Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl flex items-start gap-3 mb-6">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Estado: Idle */}
        {!result && !loading && !error && (
          <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-4 py-20">
            <Radar className="w-16 h-16 opacity-20" />
            <p className="text-sm tracking-widest uppercase">Esperando telemetría de red...</p>
          </div>
        )}

        {/* Estado: Loading */}
        {loading && (
          <div className="h-full flex flex-col items-center justify-center text-cyan-500/70 space-y-6 py-20">
            <div className="relative">
              <Activity className="w-16 h-16 animate-pulse" />
              <div className="absolute inset-0 border-4 border-cyan-500/20 rounded-full animate-ping"></div>
            </div>
            <div className="text-center space-y-2">
              <p className="text-sm tracking-[0.2em] uppercase animate-pulse font-bold">Ejecutando Motor Evolutivo</p>
              <p className="text-[10px] text-zinc-500 font-mono italic">{"> "} {tacticalMessage}</p>
            </div>
          </div>
        )}

        {/* Estado: Data Ready */}
        {result && (
          <div className="animate-in fade-in duration-500">
            
            {/* VISTA 1: TELEMETRÍA (NSGA-II y Puertos) */}
            {activeTab === 'telemetry' && (
              <div className="space-y-10 animate-in slide-in-from-left-4 duration-500">
                <section>
                  <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-4">Parámetros de Auditoría Óptimos</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-[#0a0a0b] p-4 rounded border border-zinc-800">
                      <p className="text-xs text-zinc-500 mb-1">NOISE SCORE (f1)</p>
                      <p className="text-2xl text-red-400">{result.best_config.metrics.noise_score.toFixed(2)}</p>
                    </div>
                    <div className="bg-[#0a0a0b] p-4 rounded border border-zinc-800">
                      <p className="text-xs text-zinc-500 mb-1">ESPERA (Wait Time)</p>
                      <p className="text-2xl text-cyan-400">{result.best_config.wait_time_ms.toFixed(1)}<span className="text-sm text-zinc-600 ml-1">ms</span></p>
                    </div>
                    <div className="bg-[#0a0a0b] p-4 rounded border border-zinc-800">
                      <p className="text-xs text-zinc-500 mb-1">CONCURRENCIA (Hilos)</p>
                      <p className="text-2xl text-white">{result.best_config.threads}<span className="text-sm text-zinc-600 ml-1">hilos</span></p>
                    </div>
                  </div>
                </section>

                {result.pareto_front && (
                  <section>
                    <ParetoVisualization 
                      data={result.pareto_front} 
                      selectedPoint={{
                        noise: result.best_config.metrics.noise_score,
                        time: result.best_config.metrics.estimated_time_sec
                      }} 
                    />
                  </section>
                )}

                <section>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xs text-zinc-500 uppercase tracking-widest">Servicios Identificados</h3>
                    <button
                      onClick={handleValidate}
                      disabled={validating || !result.findings?.length}
                      title="Comprobación activa NO destructiva. Requiere que el objetivo esté en el scope autorizado."
                      className="flex items-center gap-2 px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-widest border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      {validating
                        ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Validando...</>
                        : <><ShieldCheck className="w-3.5 h-3.5" /> Validar explotabilidad</>}
                    </button>
                  </div>
                  {validationError && (
                    <div className="mb-4 bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded text-xs flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" /> {validationError}
                    </div>
                  )}
                  <div className="bg-[#0a0a0b] rounded border border-zinc-800 overflow-hidden shadow-lg">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-zinc-900/80 border-b border-zinc-800 text-zinc-400">
                        <tr>
                          <th className="p-4">PUERTO</th>
                          <th className="p-4">SERVICIO</th>
                          <th className="p-4">FINGERPRINT / BANNER</th>
                          <th className="p-4">OS GUESS</th>
                          <th className="p-4">VALIDACIÓN</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800/50">
                        {result.findings.map((finding, idx) => (
                          <tr key={idx} className="hover:bg-zinc-900/40 transition-colors group">
                            <td className="p-4 text-cyan-400 font-mono flex items-center gap-2">
                              <ChevronRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" /> 
                              {finding.port}
                            </td>
                            <td className="p-4 text-white font-semibold">{finding.service.toUpperCase()}</td>
                            <td className="p-4 text-zinc-400 font-mono text-xs truncate max-w-[250px]" title={finding.banner}>
                              {finding.banner || 'No Banner Detected'}
                            </td>
                            <td className="p-4">
                              <span className="px-2 py-1 rounded bg-fuchsia-500/10 text-fuchsia-400 text-[10px] border border-fuchsia-500/20 uppercase font-bold">
                                {finding.os_guess}
                              </span>
                            </td>
                            <td className="p-4">{validationBadge(finding.port)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>

                {verdicts.length > 0 && (
                  <section className="mt-6">
                    <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-4">
                      Veredicto de exposición ({verdicts.length})
                    </h3>
                    <div className="space-y-2">
                      {verdicts.map((v, i) => {
                        const st = VALIDATION_STYLES[v.status] || VALIDATION_STYLES.not_tested;
                        const sev = SEVERITY_STYLES[v.severity] || SEVERITY_STYLES.unknown;
                        return (
                          <div key={i} className="bg-[#0a0a0b] border border-zinc-800 rounded p-4">
                            <div className="flex items-center gap-2 flex-wrap mb-1">
                              <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold border ${sev}`}>{v.severity}</span>
                              <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold border ${st.c}`}>{st.label}</span>
                              <span className="text-white text-sm font-semibold">{v.vuln_class || v.name || 'hallazgo'}</span>
                              {v.port != null && <span className="text-zinc-500 text-xs">· puerto {v.port}</span>}
                            </div>
                            {v.location && (
                              <p className="text-cyan-400 font-mono text-xs break-all">{v.location}</p>
                            )}
                            {v.name && v.name !== v.vuln_class && (
                              <p className="text-zinc-400 text-xs mt-1">{v.name}</p>
                            )}
                            {v.evidence?.reproduce && (
                              <p className="text-zinc-500 font-mono text-[11px] mt-2">↳ {v.evidence.reproduce}</p>
                            )}
                            {v.evidence?.snippet && (
                              <pre className="text-zinc-500 text-[11px] mt-1 whitespace-pre-wrap break-all max-h-24 overflow-auto">{v.evidence.snippet}</pre>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </section>
                )}
              </div>
            )}

            {/* VISTA 2: ESTRATEGIA (Ruta de Ataque) */}
            {activeTab === 'strategy' && result.attack_roadmap && result.attack_roadmap.steps && (
              <div className="animate-in slide-in-from-right-4 duration-500">
                <AttackRoadmap steps={result.attack_roadmap.steps} />
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
}

export default IntelligenceResults;