import { useState } from 'react';
import { Terminal, Radar, Activity, GitBranch } from 'lucide-react';
import { auditService } from '../services/api';
import ParetoVisualization from './ParetoVisualization';


function AuditForm({ onScan, loading }) {
  const [target, setTarget] = useState('');
  const [stealth, setStealth] = useState(5);
  const [ports, setPorts] = useState(100);

  // Exploración del Frente de Pareto ANTES de escanear (SPEC-0006). El frente
  // solo depende del nº de puertos, no del target: se obtiene sin tocar la red.
  const [pareto, setPareto] = useState([]);
  const [selected, setSelected] = useState(null); // punto clicado -> config explícita
  const [loadingPareto, setLoadingPareto] = useState(false);
  const [paretoError, setParetoError] = useState('');

  const explorePareto = async () => {
    setLoadingPareto(true);
    setParetoError('');
    try {
      const data = await auditService.getParetoFront(ports);
      setPareto(data.pareto_front || []);
      setSelected(null); // al recargar el frente se descarta la selección previa
    } catch (err) {
      console.error('Error al obtener el Frente de Pareto:', err);
      setParetoError('No se pudo obtener el frente. ¿Está FastAPI corriendo?');
      setPareto([]);
    } finally {
      setLoadingPareto(false);
    }
  };

  // Punto que elegiría el slider `stealth` (mismo mapeo por percentil que el
  // backend: frente ordenado por ruido ascendente). Sirve para resaltar sin clic.
  const stealthPoint = (() => {
    const n = pareto.length;
    if (!n) return null;
    const percentile = (10 - parseInt(stealth)) / 9;
    const idx = Math.max(0, Math.min(n - 1, Math.trunc(percentile * (n - 1))));
    return pareto[idx];
  })();

  // Si el operador clicó un punto, se resalta y se envía ese; si no, manda el
  // slider (se resalta el equivalente y NO se envía config: decide `stealth`).
  const highlight = selected || stealthPoint;

  const handleSubmit = (e) => {
    e.preventDefault();
    onScan(target, stealth, ports, selected ? selected.config : null);
  };

  return (
    <div className="space-y-6">
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
            type="button"
            onClick={explorePareto}
            disabled={loadingPareto}
            className="w-full border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 font-semibold p-3 rounded flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loadingPareto ? <Activity className="animate-spin w-4 h-4" /> : <GitBranch className="w-4 h-4" />}
            {loadingPareto ? 'OPTIMIZANDO...' : 'EXPLORAR FRENTE DE PARETO'}
          </button>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-cyan-500 hover:bg-cyan-400 text-zinc-950 font-bold p-4 rounded flex items-center justify-center gap-3 disabled:opacity-50"
          >
            {loading ? <Activity className="animate-spin w-5 h-5" /> : <Radar className="w-5 h-5" />}
            {loading ? 'CALCULANDO NSGA-II...' : 'INICIAR AUDITORÍA'}
          </button>
        </div>
      </form>

      {paretoError && <p className="text-xs text-red-400">{paretoError}</p>}

      {pareto.length > 0 && (
        <div className="space-y-3">
          <ParetoVisualization data={pareto} selectedPoint={highlight} onSelect={(p) => setSelected(p)} />
          <div className="bg-[#121214] p-4 rounded-xl border border-zinc-800/80 text-xs leading-relaxed">
            {selected ? (
              <p className="text-zinc-300">
                Punto elegido — ruido <span className="text-red-400">{selected.noise.toFixed(2)}</span>,
                tiempo <span className="text-cyan-400">{selected.time.toFixed(1)}s</span>:
                espera {selected.config.wait_time_ms.toFixed(0)}ms · {selected.config.threads} hilos ·
                payload {selected.config.packet_size}B. <span className="text-emerald-400">Se usará esta config.</span>
              </p>
            ) : (
              <p className="text-zinc-500">
                Clica un punto para fijar esa solución. Sin clic, manda el slider de sigilo
                (resaltado el punto equivalente).
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AuditForm;
