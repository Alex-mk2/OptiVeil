import { useState, useEffect } from 'react';
import { Activity, Loader2 } from 'lucide-react';
import { DeltaService } from '../services/api';

const Delta = ({ target }) => {
    const [deltaData, setDeltaData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;
        const fetchDelta = async () => {
            setLoading(true);
            try {
                const data = await DeltaService.getDelta(target);
                if (isMounted) setDeltaData(data);
            } catch (error) {
                console.error("Error al obtener Delta:", error);
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        if (target) {
            fetchDelta();
        }

        return () => { isMounted = false; };
    }, [target]);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-full min-h-[400px]">
                <Loader2 className="animate-spin text-yellow-400 w-10 h-10" />
            </div>
        );
    }

    if (!deltaData || deltaData.status === "insufficient_data") {
        return (
            <div className="bg-[#121214] border border-zinc-800/80 p-10 rounded-xl text-center shadow-lg max-w-2xl mx-auto mt-10">
                <Activity className="w-12 h-12 mx-auto mb-4 text-zinc-600 opacity-50" />
                <h3 className="text-lg font-bold text-zinc-300 mb-2">Telemetría Histórica Insuficiente</h3>
                <p className="text-zinc-500 text-sm">
                    Se necesitan al menos 2 escaneos en la bóveda para la IP <strong className="text-cyan-500">{target}</strong>.
                </p>
                <p className="text-[10px] mt-4 text-zinc-600 uppercase tracking-widest font-mono">
                    Ejecuta un nuevo escaneo en NMAP para generar un punto de comparación
                </p>
            </div>
        );
    }

    return (
        <div className="animate-in fade-in zoom-in-95 duration-500 h-full">
            <h2 className="text-xl font-bold text-yellow-400 mb-6 flex items-center gap-2">
                <Activity className="w-5 h-5" /> Evolución Táctica (Delta)
            </h2>

            <div className="space-y-6">
                <div className="bg-[#121214] border border-zinc-800 p-5 rounded-lg flex items-center justify-between shadow-inner">
                    <span className="text-zinc-400 font-mono text-sm uppercase tracking-wider">Índice de Volatilidad Táctica:</span>
                    <span className={`text-4xl font-black ${deltaData.delta_score > 0 ? 'text-yellow-400 drop-shadow-[0_0_10px_rgba(250,204,21,0.3)]' : 'text-zinc-500'}`}>
                        {deltaData.delta_score}
                    </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="border border-red-900/40 bg-[#1a0f14] rounded-lg p-5 shadow-lg">
                        <h3 className="text-red-400 font-bold mb-4 text-sm flex items-center gap-2 border-b border-red-900/30 pb-2">
                            🔴 Nuevos Riesgos ({deltaData.added.length})
                        </h3>
                        <div className="space-y-2">
                            {deltaData.added.length === 0 && <p className="text-zinc-700 text-xs italic font-mono">Sin nuevos puertos.</p>}
                            {deltaData.added.map(p => (
                                <div key={p.port} className="text-xs text-zinc-300 bg-red-950/30 p-2 rounded border border-red-900/50 font-mono shadow-inner">
                                    PORT: <span className="text-white font-bold">{p.port}</span> | SVC: {p.service}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="border border-emerald-900/40 bg-[#0f1a14] rounded-lg p-5 shadow-lg">
                        <h3 className="text-emerald-400 font-bold mb-4 text-sm flex items-center gap-2 border-b border-emerald-900/30 pb-2">
                            🟢 Mitigados ({deltaData.removed.length})
                        </h3>
                        <div className="space-y-2">
                            {deltaData.removed.length === 0 && <p className="text-zinc-700 text-xs italic font-mono">Sin mitigaciones.</p>}
                            {deltaData.removed.map(p => (
                                <div key={p.port} className="text-xs text-zinc-500 bg-emerald-950/30 p-2 rounded border border-emerald-900/30 font-mono line-through">
                                    PORT: {p.port} | SVC: {p.service}
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="border border-yellow-900/40 bg-[#1a180f] rounded-lg p-5 shadow-lg">
                        <h3 className="text-yellow-400 font-bold mb-4 text-sm flex items-center gap-2 border-b border-yellow-900/30 pb-2">
                            🟡 Modificados ({deltaData.changed.length})
                        </h3>
                        <div className="space-y-2">
                            {deltaData.changed.length === 0 && <p className="text-zinc-700 text-xs italic font-mono">Sin alteraciones.</p>}
                            {deltaData.changed.map(p => (
                                <div key={p.port} className="text-xs text-zinc-300 bg-yellow-950/30 p-2 rounded border border-yellow-900/50 font-mono shadow-inner">
                                    PORT: <span className="text-white font-bold">{p.port}</span>
                                    <div className="text-[10px] text-zinc-500 mt-1">
                                        {p.old?.service} ➔ <span className="text-yellow-400">{p.new?.service}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Delta;