import { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { FileText, Code, Database, Clock, Loader2, Activity, Download, ShieldAlert, Network } from 'lucide-react';
import { reportService, auditService } from '../services/api';
import AttackRoadmap from '../components/AttackRoadmap';
import YaraViewer from '../components/YaraViewer';
import NetworkMap from '../components/NetworkMap';

function ReportsDashboard() {
  const [activeTab, setActiveTab] = useState('ia');
  const [reportMarkdown, setReportMarkdown] = useState('');
  const [reportYara, setReportYara] = useState('');
  const [reportStrategy, setReportStrategy] = useState(null); 
  
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  
  const [loadingContent, setLoadingContent] = useState(false);
  const [loadingList, setLoadingList] = useState(true);

  const handleReportClick = useCallback(async (report) => {
    setLoadingContent(true);
    setSelectedReport(report);

    try {
      const [markdownRes, yaraRes, strategyRes] = await Promise.all([
        reportService.getReportContent(report.filename),
        reportService.getYaraRule(report.target),
        reportService.getStrategy(report.target).catch(() => null) 
      ]);
      
      setReportMarkdown(markdownRes.content);
      setReportYara(yaraRes.content);
      setReportStrategy(strategyRes);

    } catch (error) {
      console.error("Error al cargar datos del reporte:", error);
      setReportMarkdown("## ⚠️ Error Crítico\nNo se pudo recuperar el análisis de inteligencia de la base de datos.");
      setReportYara("// Error de extracción de la regla YARA");
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
      .catch((error) => {
        console.error("Error al cargar la lista de reportes:", error);
      })
      .finally(() => {
        if (isMounted) setLoadingList(false);
      });

    return () => {
      isMounted = false;
    };
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
              <Download className="w-4 h-4" /> Exportar PDF
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
                   <Clock className="w-3 h-3" /> ARCHIVO MD: {rep.filename.split('_').pop()}
                </p>
              </button>
            ))
          ) : (
            <div className="text-zinc-600 text-xs italic text-center mt-10">
              No hay inteligencia almacenada en la base de datos.
            </div>
          )}
        </div>
      </section>

      
      <section className="lg:col-span-9 bg-[#121214] rounded-xl border border-zinc-800/80 shadow-2xl flex flex-col overflow-hidden">
        
        {/* NAVEGACIÓN */}
        <div className="flex border-b border-zinc-800/80 bg-zinc-900/50 px-4 pt-4 gap-2">
          <button 
            onClick={() => setActiveTab('ia')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all ${activeTab === 'ia' ? 'bg-[#0a0a0b] text-cyan-400 border-t border-l border-r border-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <FileText className="w-4 h-4" /> ANÁLISIS IA
          </button>
          <button 
            onClick={() => setActiveTab('yara')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all ${activeTab === 'yara' ? 'bg-[#0a0a0b] text-magenta-400 border-t border-l border-r border-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Code className="w-4 h-4" /> REGLAS YARA
          </button>
          <button 
            onClick={() => setActiveTab('strategy')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all ${activeTab === 'strategy' ? 'bg-[#0a0a0b] text-fuchsia-400 border-t border-l border-r border-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <ShieldAlert className="w-4 h-4" /> ESTRATEGIA OFENSIVA
          </button>

          {/* Topologia de red */}
          <button 
            onClick={() => setActiveTab('topology')}
            className={`px-4 py-2 rounded-t-lg flex items-center gap-2 text-xs font-bold transition-all ${activeTab === 'topology' ? 'bg-[#0a0a0b] text-indigo-400 border-t border-l border-r border-zinc-800' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            <Network className="w-4 h-4" /> MAPA LÓGICO
          </button>
        </div>

        {/* CONTENEDOR */}
        <div className="p-8 flex-1 overflow-y-auto bg-[#0a0a0b] m-4 rounded border border-zinc-800/50 shadow-inner custom-scrollbar">
          {loadingContent ? (
            <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-50">
              <Activity className="animate-spin text-cyan-500 w-10 h-10" />
              <p className="text-cyan-500 text-xs tracking-widest uppercase">Descifrando Inteligencia...</p>
            </div>
          ) : (
            <div className="animate-in fade-in duration-500">
              
              
              {activeTab === 'ia' && (
                <div className="max-w-4xl mx-auto">
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
                <div className="max-w-4xl mx-auto">
                  {reportStrategy && reportStrategy.steps ? (
                    <AttackRoadmap steps={reportStrategy.steps} />
                  ) : (
                    <div className="flex flex-col items-center justify-center py-20 opacity-50">
                      <ShieldAlert className="w-12 h-12 text-zinc-600 mb-4" />
                      <p className="text-zinc-500 text-sm uppercase tracking-widest">No hay ruta de ataque generada para este objetivo.</p>
                    </div>
                  )}
                </div>
              )}
              {activeTab === 'topology' && (
                <div className="animate-in fade-in zoom-in-95 duration-500 h-full min-h-[500px]">
                  {/* Le pasamos el target actual al componente para que sepa qué dibujar */}
                  <NetworkMap target={selectedReport?.target} />
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