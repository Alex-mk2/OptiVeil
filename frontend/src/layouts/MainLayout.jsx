import { Outlet, Link, useLocation } from 'react-router-dom';
import { Shield, Radar, FileText } from 'lucide-react';

function MainLayout() {
  const location = useLocation();

  const navItemClass = (path) => `
    px-4 py-2 rounded-md flex items-center gap-2 text-sm font-semibold transition-all
    ${location.pathname.includes(path) 
      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' 
      : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'}
  `;

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-zinc-300 p-4 md:p-8 font-mono selection:bg-cyan-900 selection:text-cyan-100">
      
      <header className="mb-8 border-b border-zinc-800/50 pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="bg-cyan-500/10 p-3 rounded-lg border border-cyan-500/20">
            <Shield className="text-cyan-400 w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">OPTIVEIL <span className="text-cyan-400">CORE</span></h1>
            <p className="text-zinc-500 text-xs tracking-[0.2em] uppercase mt-1">Framework de Auditoría Evolutiva</p>
          </div>
        </div>

  
        <nav className="flex gap-2 bg-[#121214] p-1.5 rounded-lg border border-zinc-800/80">
          <Link to="/audit" className={navItemClass('audit')}>
            <Radar className="w-4 h-4" /> 
            <span>ESCANER TÁCTICO</span>
          </Link>
          <Link to="/reports" className={navItemClass('reports')}>
            <FileText className="w-4 h-4" /> 
            <span>BÓVEDA DE INTELIGENCIA</span>
          </Link>
        </nav>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default MainLayout;