import { useMemo } from 'react';
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { ShieldAlert } from 'lucide-react';

// Colores por nivel de riesgo (coherentes con el resto del dashboard).
const riskStyles = (risk) => {
  const r = (risk || '').toLowerCase();
  if (r.includes('alto') || r.includes('crítico')) return { border: '#f87171', text: 'text-red-400' };
  if (r.includes('medio')) return { border: '#fbbf24', text: 'text-amber-400' };
  return { border: '#34d399', text: 'text-emerald-400' };
};

// Layout por niveles: la profundidad de un paso es 1 + la de su dependencia más
// profunda (0 si es un punto de entrada). El saneo del backend garantiza que las
// dependencias apuntan a ids menores, así que procesar por id ascendente basta.
function layout(steps) {
  const byId = new Map(steps.map((s) => [s.id, s]));
  const hasDeps = steps.some((s) => (s.depends_on || []).length > 0);
  const sorted = [...steps].sort((a, b) => a.id - b.id);

  const level = new Map();
  sorted.forEach((s, i) => {
    const deps = hasDeps ? (s.depends_on || []) : (i > 0 ? [sorted[i - 1].id] : []);
    const lv = deps.length
      ? Math.max(...deps.map((d) => (level.get(d) ?? 0) + 1))
      : 0;
    level.set(s.id, lv);
  });

  // Reparte horizontalmente los pasos que comparten nivel.
  const perLevel = new Map();
  const COL = 300, ROW = 170;
  const nodes = sorted.map((s) => {
    const lv = level.get(s.id);
    const col = perLevel.get(lv) || 0;
    perLevel.set(lv, col + 1);
    const st = riskStyles(s.risk);
    return {
      id: String(s.id),
      position: { x: col * COL, y: lv * ROW },
      data: {
        label: (
          <div className="text-left">
            <div className="text-[9px] uppercase tracking-widest text-zinc-500 font-bold mb-1">
              Fase {s.id}: <span className="text-zinc-300">{s.phase}</span>
            </div>
            <div className="text-white text-xs font-medium mb-1">{s.action}</div>
            <div className="flex items-center gap-2 text-[9px]">
              <span className={`uppercase font-bold ${st.text}`}>Riesgo {s.risk}</span>
              {s.mitre_technique && <span className="text-cyan-400 font-mono">{s.mitre_technique}</span>}
            </div>
          </div>
        ),
      },
      style: {
        background: '#0a0a0b',
        border: `1px solid ${st.border}`,
        borderRadius: 10,
        padding: 12,
        width: 240,
        color: '#fff',
      },
    };
  });

  // Aristas: cada dependencia (o la cadena lineal en el fallback) es un edge.
  const edges = [];
  sorted.forEach((s, i) => {
    const deps = hasDeps ? (s.depends_on || []) : (i > 0 ? [sorted[i - 1].id] : []);
    deps.forEach((d) => {
      if (!byId.has(d)) return;
      edges.push({
        id: `e-${d}-${s.id}`,
        source: String(d),
        target: String(s.id),
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#52525b' },
        style: { stroke: '#52525b', strokeWidth: 1.5 },
      });
    });
  });

  return { nodes, edges };
}

function AttackRoadmap({ steps }) {
  const { nodes, edges } = useMemo(() => layout(steps || []), [steps]);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="bg-[#121214] p-6 rounded-xl border border-zinc-800 shadow-inner mt-8">
      <h3 className="text-cyan-400 text-xs font-bold uppercase tracking-widest mb-6 flex items-center gap-2">
        <ShieldAlert className="w-4 h-4" />
        Ruta de Ataque Sugerida (Grafo IA)
      </h3>
      <div style={{ width: '100%', height: '520px' }} className="bg-[#0a0a0c] rounded-lg border border-zinc-800/80 overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          fitViewOptions={{ padding: 0.25 }}
          minZoom={0.4}
          maxZoom={1.5}
          nodesDraggable={false}
          nodesConnectable={false}
        >
          <Background color="#27272a" gap={24} size={1.5} variant="dots" />
          <Controls showInteractive={false} className="bg-[#121214] border-zinc-800 fill-zinc-400 shadow-xl" />
        </ReactFlow>
      </div>
    </div>
  );
}

export default AttackRoadmap;
