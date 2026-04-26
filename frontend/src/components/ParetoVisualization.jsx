import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

function ParetoVisualization({ data, selectedPoint }) {
  return (
    <div className="bg-[#121214] p-6 rounded-xl border border-zinc-800 shadow-inner h-[350px]">
      <h3 className="text-cyan-400 text-xs font-bold uppercase tracking-widest mb-6 flex items-center gap-2">
        <div className="w-2 h-2 bg-cyan-400 animate-pulse rounded-full" />
        Frente de Pareto: Noise vs Time (NSGA-II)
      </h3>
      
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          
          <XAxis 
            type="number" 
            dataKey="noise" 
            name="Ruido" 
            unit=" pts" 
            stroke="#a1a1aa" // Subimos el brillo al eje (zinc-400)
            fontSize={10}
            tick={{ fill: '#a1a1aa' }}
            label={{ value: 'Riesgo Detección (f1)', position: 'insideBottom', offset: -10, fill: '#f4f4f5' }} // Texto en blanco zinc-100
          />
          
          <YAxis 
            type="number" 
            dataKey="time" 
            name="Tiempo" 
            unit="s" 
            stroke="#a1a1aa" 
            fontSize={10}
            tick={{ fill: '#a1a1aa' }}
            label={{ value: 'Tiempo (f2)', angle: -90, position: 'insideLeft', offset: 10, fill: '#f4f4f5' }}
          />

          <Tooltip 
            cursor={{ strokeDasharray: '3 3', stroke: '#52525b' }} 
            contentStyle={{ 
              backgroundColor: '#18181b', 
              border: '1px solid #3f3f46', 
              borderRadius: '8px',
              fontSize: '12px'
            }}
            itemStyle={{ color: '#22d3ee' }} // Color cian para los valores
            labelStyle={{ display: 'none' }} // Escondemos el label interno si no se usa
          />

          <Scatter name="Configuraciones" data={data}>
            {data.map((entry, index) => {
              // Comprobamos si es el punto seleccionado para destacarlo
              const isSelected = entry.noise === selectedPoint?.noise && entry.time === selectedPoint?.time;
              return (
                <Cell 
                  key={`cell-${index}`} 
                  fill={isSelected ? '#22d3ee' : '#155e75'} 
                  fillOpacity={isSelected ? 1 : 0.6}
                  r={isSelected ? 7 : 4}
                  stroke={isSelected ? '#fff' : 'none'}
                  strokeWidth={2}
                />
              );
            })}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ParetoVisualization;