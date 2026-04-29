import { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Code, Database, Clock, Loader2, Activity, Download, ShieldAlert, Network, Terminal } from 'lucide-react';
import { reportService, auditService, PersistenceService, LatestAudit, DeltaAudit } from '../services/api';

import YaraViewer from '../components/YaraViewer';
import NetworkMap from '../components/NetworkMap';
import NmapTecnique from '../components/NmapTecnique';
import OffensiveStrategy from '../components/OffensiveStrategy';

function ReportsDashboard() {
  const [activeTab, setActiveTab] = useState('ia');
  const [reportMarkdown, setReportMarkdown] = useState('');
  const [reportYara, setReportYara] = useState('');
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [loadingContent, setLoadingContent] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [globalNmapFindings, setGlobalNmapFindings] = useState(null);
  const [globalTarget, setGlobalTarget] = useState("");
  const [globalStealth, setGlobalStealth] = useState(5);
  const [deltaData, setDeltaData] = useState(null);
  const [loadingDelta, setLoadingDelta] = useState(false);

  useEffect(() => {
    const recuperarMemoria = async () => {
      try {
        const data = await LatestAudit.getLatestScans();
        if (data && data.has_data) {
          setGlobalTarget(data.target);
          setGlobalStealth(data.stealth_level);
          setGlobalNmapFindings(data.findings);
        }
      } catch (error) {
        console.error(error);
      }
    };
    recuperarMemoria();
  }, []);

  const handleReportClick = useCallback(async (report) => {
    setLoadingContent(true);
    setSelectedReport(report);

    try {
      const [markdownRes, yaraRes, dbRes] = await Promise.all([
        reportService.getReportContent(report.filename),
        reportService.getYaraRule(report.target),
        fetch(`http://localhost:8000/api/persistence/latest?target=${report.target}`).then(res => res.json())
      ]);
      
      setReportMarkdown(markdownRes.content);
      setReportYara(yaraRes.content);
      setGlobalTarget(report.target);

      if (dbRes && dbRes.has_data) {
        setGlobalNmapFindings(dbRes.findings);
        setGlobalStealth(dbRes.stealth_level);
      } else {
        setGlobalNmapFindings([]);
      }
    } catch (error) {
      console.error(error);
      setReportMarkdown("## ⚠️ Error Crítico\nNo se pudo recuperar el análisis.");
      setReportYara("// Error de extracción");
    } finally {
      setLoadingContent(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    void auditService.getReports()
      .then((data) => {
        if (!isMounted) return;
        setReports(data);
        if (data.length > 0) {
          handleReportClick(data[0]); 
        }
      })
      .catch((error) => console.error(error))
      .finally(() => {
        if (isMounted) setLoadingList(false);
      });
    return () => { isMounted = false; };
  }, [handleReportClick]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-[75vh]">
      <section className="lg:col-span-3 bg-[#121214] rounded-xl border border-zinc-800/80 shadow-2xl flex flex-col overflow-hidden">
        <div className="p-4 border-b border-zinc-800/80 bg-zinc-900/50">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-white font-semibold flex items-center gap-2 text-sm uppercase tracking-widest">
              <Database className="w-4 h-4 text-cyan-400" /> Archivos Clasificados
            </h2>
            <button
              type="button"
              onClick={() => selectedReport && reportService.downloadPDF(selectedReport.filename)}
              disabled={!selectedReport}
              className="inline-flex items-center gap-2 px-3 py-2 rounded border border-zinc-800 bg-zinc-900 text-zinc-300 text-xs font-semibold uppercase tracking-widest disabled:opacity-40 disabled:cursor-not-allowed hover:bg-zinc-800"
            >
              <Download className="w-4 h-4" /> Exportar
            </button>
          </div>
        </div>
        
        <div className="p-4 flex-1 overflow-y-auto space-y-3 custom-scrollbar">
          {loadingList ? (
            <div className="flex justify-center items-center h-32">
              <Loader2 className="animate-spin text-zinc-700 w-8 h-8" />
            </div>
          ) : reports.length > 0 ? (
            reports.map((rep, index) => (
              <button
                key={index}
                onClick={() => handleReportClick(rep)}
                className={`w-full text-left p-3 rounded border transition-all cursor-pointer ${
                  selectedReport?.filename === rep.filename 
                  ? 'bg-cyan-500/10 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.1)]' 
                  : 'bg-zinc-900 border-zinc-800 hover:bg-zinc-800'
                }`}
              >
                <p className={`font-bold text-sm ${selectedReport?.filename === rep.filename ? 'text-cyan-400' : 'text-zinc-300'}`}>
                  Target: {rep.target}
                </p>
                <p className="text-zinc-500 text-[10px] mt-1 flex items-center gap-1">
                   <Clock className="w-3 h-3" /> MD: {rep.filename.split('_').pop()}
                </p>
              </button>
            ))
          ) : (
            <div className="text-zinc-600 text-xs italic text-center mt-10">
              No hay inteligencia almacenada.
            </div>
          )}
        </div>
      </section>

      <section className="lg:col-span-9 bg-[#121214] rounded-xl border border-zinc-800/80 shadow-2xl flex flex-col overflow-hidden">
        <div className="flex border-b border-zinc-800/80 bg-zinc-900/50 px-4 pt-4 gap-2 overflow-x-auto custom-scrollbar">
          <button 
            onClick={() => setActiveTab('ia')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'ia' ? 'bg-[#0a0a0b] text-cyan-400 border-t border-l border-r border-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <FileText className="w-4 h-4" /> ANÁLISIS IA
          </button>
          <button 
            onClick={() => setActiveTab('yara')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'yara' ? 'bg-[#0a0a0b] text-magenta-400 border-t border-l border-r border-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Code className="w-4 h-4" /> REGLAS YARA
          </button>
          <button 
            onClick={() => setActiveTab('strategy')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'strategy' ? 'bg-[#0a0a0b] text-fuchsia-400 border-t border-l border-r border-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <ShieldAlert className="w-4 h-4" /> ESTRATEGIA OFENSIVA
          </button>
          <button 
            onClick={() => setActiveTab('topology')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'topology' ? 'bg-[#0a0a0b] text-indigo-400 border-t border-l border-r border-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Network className="w-4 h-4" /> MAPA LÓGICO
          </button>
          <button 
            onClick={() => setActiveTab('nmap')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'nmap' ? 'bg-[#0a0a0b] text-cyan-500 border-t border-l border-r border-zinc-800 shadow-[0_-5px_10px_-5px_rgba(6,182,212,0.2)]' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Terminal className="w-4 h-4" /> NMAP
          </button>
          <button 
            onClick={async () => {
              setActiveTab('delta');
              setLoadingDelta(true);
              try {
                const data = await DeltaAudit.getDeltaAnalysis(globalTarget);
                setDeltaData(data);
              } catch (e) {
                console.error(e);
              } finally {
                setLoadingDelta(false);
              }
            }}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'delta' ? 'bg-[#0a0a0b] text-yellow-400 border-t border-l border-r border-zinc-800 shadow-[0_-5px_10px_-5px_rgba(250,204,21,0.2)]' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Activity className="w-4 h-4" /> ANÁLISIS DELTA
          </button>
        </div>

        <div className="p-8 flex-1 overflow-y-auto bg-[#0a0a0b] m-4 rounded border border-zinc-800/50 shadow-inner custom-scrollbar">
          {loadingContent ? (
            <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-50">
              <Activity className="animate-spin text-cyan-500 w-10 h-10" />
              <p className="text-cyan-500 text-xs tracking-widest uppercase">Descifrando Inteligencia...</p>
            </div>
          ) : (
            <div className="h-full">
              
              {activeTab === 'ia' && (
                <div className="animate-in fade-in duration-500 max-w-4xl mx-auto">
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => <h1 className="text-2xl font-bold text-white mb-6 pb-2 border-b border-zinc-800 tracking-tight">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-xl font-bold text-cyan-400 mt-8 mb-4 flex items-center gap-2">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-lg font-semibold text-zinc-200 mt-6 mb-3">{children}</h3>,
                      p:  ({ children }) => <p className="text-zinc-400 text-sm leading-relaxed mb-4">{children}</p>,
                      strong: ({ children }) => {
                        const text = String(children).toUpperCase();
                        if (text.includes('CRÍTICO') || text.includes('ALTO')) return <strong className="text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded font-bold">{children}</strong>;
                        if (text.includes('MEDIO')) return <strong className="text-amber-400 bg-amber-400/10 px-1.5 py-0.5 rounded font-bold">{children}</strong>;
                        if (text.includes('BAJO')) return <strong className="text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded font-bold">{children}</strong>;
                        return <strong className="text-zinc-200 font-bold">{children}</strong>;
                      },
                      ul: ({ children }) => <ul className="list-none space-y-2 mb-6">{children}</ul>,
                      li: ({ children }) => (
                        <li className="flex items-start text-zinc-400 text-sm">
                          <span className="text-cyan-500 mr-2 mt-0.5">▹</span>
                          <span>{children}</span>
                        </li>
                      ),
                    }}
                  >
                    {reportMarkdown}
                  </ReactMarkdown>
                </div>
              )}

              {activeTab === 'yara' && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <YaraViewer code={reportYara} />
                </div>
              )}

              {activeTab === 'strategy' && (
                <div className="animate-in fade-in duration-500 h-full">
                  <OffensiveStrategy
                    findings={globalNmapFindings} 
                    target={globalTarget} 
                    stealth={globalStealth} 
                  />
                </div>
              )}

              {activeTab === 'topology' && (
                <div className="animate-in fade-in zoom-in-95 duration-500 h-full min-h-[500px]">
                  <NetworkMap target={globalTarget} />
                </div>
              )}

              {activeTab === 'nmap' && (
                <div className="animate-in fade-in slide-in-from-right-8 duration-500 h-full min-h-[500px]">
                  <NmapTecnique 
                    defaultTarget={globalTarget}
                    onScanComplete={async (target, stealth, findings) => {
                      setGlobalTarget(target);
                      setGlobalStealth(stealth);
                      setGlobalNmapFindings(findings);

                      try {
                        await PersistenceService.syncData({
                          target: target,
                          stealth_level: stealth,
                          findings: findings
                        });
                      } catch (err) {
                        console.error(err);
                      }
                    }}
                  />
                </div>
              )}

              {activeTab === 'delta' && (
                <div className="animate-in fade-in zoom-in-95 duration-500 h-full">
                  <h2 className="text-xl font-bold text-yellow-400 mb-6 flex items-center gap-2">
                    <Activity className="w-5 h-5" /> Evolución Táctica (Delta)
                  </h2>
                  
                  {loadingDelta ? (
                     <div className="flex justify-center items-center h-32"><Loader2 className="animate-spin text-yellow-400 w-8 h-8" /></div>
                  ) : !deltaData || deltaData.status === "insufficient_data" ? (
                    <div className="bg-zinc-900/50 border border-zinc-800 p-6 rounded text-center text-zinc-400">
                      <p>Se necesitan al menos 2 escaneos históricos de la IP <b>{globalTarget}</b> para calcular la evolución.</p>
                      <p className="text-xs mt-2 text-zinc-500">Ejecuta un nuevo escaneo en la pestaña NMAP para generar un punto de comparación.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-lg flex items-center justify-between">
                        <span className="text-zinc-300 font-mono text-sm">Índice de Volatilidad:</span>
                        <span className="text-2xl font-bold text-white">{deltaData.delta_score}</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="border border-red-900/50 bg-red-900/10 rounded p-4">
                          <h3 className="text-red-400 font-bold mb-3 text-sm">🔴 Nuevos Riesgos ({deltaData.added.length})</h3>
                          {deltaData.added.map(p => (
                            <div key={p.port} className="text-xs text-zinc-300 mb-1 border-b border-red-900/30 pb-1">
                              Puerto {p.port} - {p.service}
                            </div>
                          ))}
                        </div>

                        <div className="border border-emerald-900/50 bg-emerald-900/10 rounded p-4">
                          <h3 className="text-emerald-400 font-bold mb-3 text-sm">🟢 Mitigados ({deltaData.removed.length})</h3>
                          {deltaData.removed.map(p => (
                            <div key={p.port} className="text-xs text-zinc-300 mb-1 border-b border-emerald-900/30 pb-1">
                              Puerto {p.port} - {p.service}
                            </div>
                          ))}
                        </div>

                        <div className="border border-yellow-900/50 bg-yellow-900/10 rounded p-4">
                          <h3 className="text-yellow-400 font-bold mb-3 text-sm">🟡 Modificados ({deltaData.changed.length})</h3>
                          {deltaData.changed.map(p => (
                            <div key={p.port} className="text-xs text-zinc-300 mb-1 border-b border-yellow-900/30 pb-1">
                              Puerto {p.port} ({p.old_service} ➔ {p.new_service})
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default ReportsDashboard;