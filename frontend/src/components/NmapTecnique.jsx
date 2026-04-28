import { useState } from 'react';
import { Terminal, ShieldAlert, Cpu, Globe, Crosshair, Loader2, Search } from 'lucide-react';
import { NmapTecniqueService, CVEService } from '../services/api';

const NmapTecnique = ({ defaultTarget = "186.64.114.50", onScanComplete }) => {
  const [target, setTarget] = useState(defaultTarget);
  const [stealth, setStealth] = useState(5);
  const [ports, setPorts] = useState(100);
  
  
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);


  const [cveLoading, setCveLoading] = useState(null);
  const [cveResults, setCveResults] = useState({});
  const [cveError, setCveError] = useState({});

  const handleLaunch = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await NmapTecniqueService.runActiveScan(target, stealth, ports);
      setResults(data);
      
      
      if (onScanComplete) {
        onScanComplete(target, stealth, data.findings);
      }
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchCVE = async (finding, idx) => {
    setCveLoading(idx);
    setCveError(prev => ({ ...prev, [idx]: null }));
    setCveResults(prev => ({ ...prev, [idx]: null }));
    try {
      const data = await CVEService.getCVEs(finding.banner || `${finding.service} ${finding.port}`);
      setCveResults(prev => ({ ...prev, [idx]: data }));
    } catch (err) {
      setCveError(prev => ({ ...prev, [idx]: err.message || 'Error buscando CVEs' }));
    } finally {
      setCveLoading(null);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 w-full h-full text-zinc-300">
      
      
      <div className="w-full lg:w-1/3 bg-[#0a0a0c] border border-zinc-800/80 rounded-xl p-6 shadow-xl flex flex-col gap-6">
        <div>
          <h2 className="text-cyan-400 font-mono tracking-widest text-sm font-bold flex items-center gap-2 mb-1">
            <Crosshair className="w-4 h-4" /> Nmap
          </h2>
          <h3 className="text-white text-xl font-bold">Orquestación Activa</h3>
          <p className="text-zinc-500 text-xs mt-2">Ejecución de Nmap orquestado con evasión de firmas IDS/IPS.</p>
        </div>

        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs font-mono text-zinc-400 uppercase">IP Objetivo</label>
            <input 
              type="text" 
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="bg-[#121214] border border-zinc-700 rounded p-2 text-white font-mono focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 transition-all"
            />
          </div>

          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-end">
              <label className="text-xs font-mono text-zinc-400 uppercase">Nivel de Sigilo (IA)</label>
              <span className={`text-xs font-bold font-mono ${stealth >= 8 ? 'text-green-400' : stealth <= 3 ? 'text-red-400' : 'text-fuchsia-400'}`}>
                NIVEL {stealth}
              </span>
            </div>
            <input 
              type="range" min="1" max="10" step="1"
              value={stealth} onChange={(e) => setStealth(parseInt(e.target.value))}
              className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
            <div className="flex justify-between text-[10px] text-zinc-600 font-mono mt-1">
              <span>Rápido/Ruidoso</span>
              <span>Paranoico/Lento</span>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-xs font-mono text-zinc-400 uppercase">Límite de Puertos</label>
            <input 
              type="number" min="1" max="65535"
              value={ports} onChange={(e) => setPorts(parseInt(e.target.value))}
              className="bg-[#121214] border border-zinc-700 rounded p-2 text-white font-mono focus:border-cyan-500 focus:outline-none"
            />
          </div>
        </div>

        <button 
          onClick={handleLaunch}
          disabled={loading}
          className={`mt-8 w-full py-3 rounded uppercase tracking-widest font-bold text-sm transition-all flex justify-center items-center gap-2
            ${loading 
              ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' 
              : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-[0_0_15px_rgba(6,182,212,0.4)]'
            }`}
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Terminal className="w-5 h-5" />}
          {loading ? 'Orquestando...' : 'Iniciar Escaneo Táctico'}
        </button>
      </div>

      
      <div className="w-full lg:w-2/3 bg-[#0a0a0c] border border-zinc-800/80 rounded-xl p-6 shadow-xl flex flex-col relative overflow-hidden">
        
        <h3 className="text-zinc-400 font-mono uppercase tracking-widest text-xs mb-4 border-b border-zinc-800 pb-2">
          Telemetría de Extracción
        </h3>

        {!loading && !results && !error && (
          <div className="flex flex-col items-center justify-center flex-1 opacity-30">
            <ShieldAlert className="w-16 h-16 mb-4 text-zinc-500" />
            <p className="font-mono text-sm uppercase">Motor en espera de parámetros</p>
          </div>
        )}

        {loading && (
          <div className="flex flex-col justify-center flex-1 font-mono text-xs text-green-500/80 space-y-2 p-4 bg-[#050505] rounded border border-zinc-900">
            <p className="animate-pulse"> Inicializando módulo OptiVeil Core...</p>
            <p className="animate-pulse" style={{ animationDelay: '0.5s' }}> Aplicando heurística de evasión (Nivel {stealth})...</p>
            <p className="animate-pulse" style={{ animationDelay: '1s' }}> Inyectando sondas Nmap hacia {target}...</p>
            <p className="animate-pulse text-cyan-500" style={{ animationDelay: '1.5s' }}> Extrayendo banners de servicios. Por favor espere...</p>
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center flex-1 text-red-400 font-mono text-center p-4 bg-red-950/20 rounded border border-red-900/50">
            <ShieldAlert className="w-10 h-10 mb-2" />
            <p>CRITICAL ERROR: {error}</p>
          </div>
        )}

        {!loading && results && (
          <div className="flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar">
            {results.findings.length === 0 ? (
              <p className="text-zinc-500 font-mono text-center py-10">No se encontraron puertos abiertos.</p>
            ) : (
              results.findings.map((finding, idx) => (
                <div key={idx} className="bg-[#121214] border border-zinc-800 p-4 rounded-lg flex flex-col gap-4 group hover:border-zinc-600 transition-colors">
                  
                  
                  <div className="flex items-start justify-between w-full">
                    <div className="flex items-center gap-4">
                      <div className="bg-[#1a1a1f] p-3 rounded-md border border-zinc-700/50">
                        {finding.port === 80 || finding.port === 443 ? <Globe className="w-5 h-5 text-cyan-400" /> : <Cpu className="w-5 h-5 text-fuchsia-400" />}
                      </div>
                      <div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-white font-bold text-lg whitespace-nowrap">PUERTO {finding.port}</span>
                          <span className="text-zinc-500 font-mono text-xs uppercase whitespace-nowrap">{finding.service}</span>
                        </div>
                        <p className="text-cyan-400/80 font-mono text-xs mt-1 bg-cyan-950/30 inline-block px-2 py-0.5 rounded border border-cyan-900/50">
                          {finding.banner}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex flex-col items-end">
                      <button
                        onClick={() => handleSearchCVE(finding, idx)}
                        disabled={cveLoading !== null}
                        className={`opacity-0 group-hover:opacity-100 transition-opacity bg-zinc-800 hover:bg-zinc-700 text-xs font-mono px-3 py-1.5 rounded text-white flex items-center gap-2 ${cveLoading === idx ? 'opacity-100' : ''}`}
                      >
                        <Search className="w-3 h-3" /> {cveLoading === idx ? 'Buscando...' : 'Buscar CVE'}
                      </button>
                      {cveLoading === idx && (
                        <div className="text-[10px] text-zinc-500 font-mono mt-2">Consultando NIST...</div>
                      )}
                      {cveError[idx] && (
                        <div className="text-[10px] text-red-400 font-mono mt-2">{cveError[idx]}</div>
                      )}
                    </div>
                  </div>

                  
                  {cveResults[idx] && (
                    <div className="mt-2 w-full bg-[#0b0b0d] border border-zinc-800/60 rounded p-3 text-xs font-mono shadow-inner">
                      {Array.isArray(cveResults[idx].cves) ? (
                        cveResults[idx].cves.length === 0 ? (
                          <div className="text-zinc-500 text-center py-2">No se encontraron vulnerabilidades conocidas (CVE) para esta versión.</div>
                        ) : (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {cveResults[idx].cves.map((cve, i) => (
                              <a 
                                key={i} 
                                href={`https://nvd.nist.gov/vuln/detail/${cve.id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                title="Ver documentación en el NIST"
                                className="flex flex-col gap-1.5 border border-zinc-800/50 bg-[#121214] p-2.5 group hover:bg-[#1a1a1f] hover:border-zinc-700 transition-all rounded"
                              >
                                <div className="flex items-start justify-between gap-2">
                                  <span className="font-bold text-zinc-300 group-hover:text-cyan-400 transition-colors text-xs flex items-center gap-1">
                                    {cve.id}
                                  </span>
                                  {(cve.severity || cve.score) && (
                                    <span className={`text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded font-bold whitespace-nowrap
                                      ${cve.severity === 'CRITICAL' || cve.severity === 'HIGH' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                                        cve.severity === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 
                                        'bg-zinc-700/30 text-zinc-400 border border-zinc-600/50'}`}
                                    >
                                      {cve.score !== "N/A" ? `CVSS: ${cve.score}` : cve.severity}
                                    </span>
                                  )}
                                </div>
                                {(cve.description || cve.summary) && (
                                  <p className="text-zinc-500 group-hover:text-zinc-400 text-[10px] line-clamp-2 leading-relaxed transition-colors">
                                    {cve.description || cve.summary}
                                  </p>
                                )}
                              </a>
                            ))}
                          </div>
                        )
                      ) : (
                        <pre className="whitespace-pre-wrap text-zinc-400">{JSON.stringify(cveResults[idx], null, 2)}</pre>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default NmapTecnique;