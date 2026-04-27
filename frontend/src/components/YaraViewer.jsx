import { Code } from 'lucide-react';


const YaraViewer = ({ code }) => {
  const highlightCode = (text) => {
    if (!text) return null;
    
    return text.split('\n').map((line, i) => {
      let safeLine = line.replace(/</g, '&lt;').replace(/>/g, '&gt;');

      
      let highlighted = safeLine
        .replace(/(\/\/.*)/g, "<span class='text-zinc-500 italic'>$1</span>")
        .replace(/^(rule)\s+([a-zA-Z0-9_]+)/g, "<span class='text-fuchsia-400 font-bold'>$1</span> <span class='text-cyan-400 font-bold'>$2</span>")
        .replace(/\b(meta:|strings:|condition:)\b/g, "<span class='text-fuchsia-400 font-bold'>$1</span>")
        .replace(/\b(and|or|not|all of them|any of them)\b/g, "<span class='text-fuchsia-500 font-bold'>$1</span>")
        .replace(/(\$[a-zA-Z0-9_]+)/g, "<span class='text-emerald-400'>$1</span>")
        .replace(/("[^"]*")/g, "<span class='text-amber-300'>$1</span>");

      return (
        <div key={i} className="flex hover:bg-zinc-800/40 px-4 whitespace-pre transition-colors">
         
          <span className="w-8 flex-shrink-0 text-zinc-600 select-none text-right mr-4 text-xs pt-[2px] font-mono border-r border-zinc-800/50 pr-2">
            {i + 1}
          </span>
          <span className="font-mono text-sm tracking-wide" dangerouslySetInnerHTML={{ __html: highlighted || ' ' }} />
        </div>
      );
    });
  };

  return (
    <div className="bg-[#0a0a0c] rounded-xl border border-zinc-800/80 overflow-hidden shadow-2xl max-w-4xl mx-auto ring-1 ring-white/5">
      <div className="bg-[#121214] px-4 py-2.5 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5 mr-3">
            <div className="w-3 h-3 rounded-full bg-red-500/80 border border-red-500/50"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500/80 border border-amber-500/50"></div>
            <div className="w-3 h-3 rounded-full bg-emerald-500/80 border border-emerald-500/50"></div>
          </div>
          <span className="text-zinc-400 text-xs font-bold uppercase tracking-widest flex items-center gap-2">
            <Code className="w-3.5 h-3.5 text-magenta-400" /> optiveil_rule.yar
          </span>
        </div>
        <span className="text-[10px] text-zinc-600 font-mono">UTF-8</span>
      </div>
      <div className="py-4 overflow-x-auto text-zinc-300 leading-relaxed custom-scrollbar pb-6">
        {highlightCode(code)}
      </div>
    </div>
  );
};

export default YaraViewer;