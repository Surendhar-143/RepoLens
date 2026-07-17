import React from 'react';
import { Network, Activity } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState.tsx';

const Architecture: React.FC = () => {
  return (
    <div className="space-y-8 select-none">
      
      {/* Title Header */}
      <div>
        <h2 className="text-3xl font-bold font-display tracking-tight text-white">Architecture Explorer</h2>
        <p className="text-muted-foreground text-sm">Visualize system components, call trees, layered imports, and database schemas.</p>
      </div>

      {/* Main Graph Panel Workspace (Skeletal layout) */}
      <div className="h-[550px] relative border border-border rounded-xl bg-[#030014]/40 flex items-center justify-center p-6 overflow-hidden">
        
        {/* Decorative Grid Background */}
        <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[linear-gradient(to_right,#808080_1px,transparent_1px),linear-gradient(to_bottom,#808080_1px,transparent_1px)] bg-[size:24px_24px]" />
        
        <div className="max-w-md text-center space-y-4 z-10">
          <EmptyState 
            title="Interactive Graph Workspace"
            description="After indexing, this viewport renders interactive nodes of package namespaces, database tables, and call chains powered by React Flow and NetworkX."
            icon={Network}
          />
        </div>

      </div>

      {/* Detail info bar */}
      <div className="p-4 border border-emerald-500/10 bg-emerald-500/5 rounded-lg flex items-start gap-3">
        <Activity className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="text-xs text-zinc-400 leading-relaxed">
          <span className="font-semibold text-white">Graph Rendering Engine: </span>
          React Flow is configured to orchestrate interactive node canvases dynamically. Once repository analysis begins, call graphs will automatically update based on code files.
        </div>
      </div>

    </div>
  );
};

export default Architecture;
