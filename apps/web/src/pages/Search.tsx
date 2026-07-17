import React, { useState } from 'react';
import { Search as SearchIcon, HelpCircle, Code, Server, Key } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState.tsx';


const Search: React.FC = () => {
  const [query, setQuery] = useState('');

  const sampleQueries = [
    { text: "Where is auth handled?", icon: Key },
    { text: "JWT token validation logic", icon: Code },
    { text: "Database connection session initialization", icon: Server }
  ];

  return (
    <div className="space-y-8 select-none">
      
      {/* Title Header */}
      <div>
        <h2 className="text-3xl font-bold font-display tracking-tight text-white">Semantic Search</h2>
        <p className="text-muted-foreground text-sm">Query codebase files by intent and structure, rather than just raw keyword match.</p>
      </div>

      {/* Query Bar */}
      <div className="relative">
        <SearchIcon className="absolute left-3 top-3.5 h-5 w-5 text-muted-foreground" />
        <input 
          type="text" 
          placeholder="Ask a question about the repository or enter code structure queries..." 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full h-12 pl-11 pr-4 bg-card text-foreground border border-border rounded-lg text-base focus:outline-hidden focus:ring-1 focus:ring-[#a21caf] shadow-xs glass-panel"
        />
      </div>

      {/* Main Search Panel / Empty State */}
      <div className="space-y-6">
        
        {/* Sample query triggers */}
        <div className="space-y-2.5">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Example queries</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {sampleQueries.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div 
                  key={idx}
                  onClick={() => setQuery(item.text)}
                  className="p-4 border border-border bg-card/25 hover:bg-card/65 transition-all rounded-lg flex items-center gap-3 cursor-pointer select-none"
                >
                  <div className="p-2 bg-violet-600/10 rounded-lg text-violet-400">
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                  <span className="text-xs font-medium text-foreground">{item.text}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Empty state visual */}
        <EmptyState 
          title="Connect a repository to search"
          description="Once your project is linked and parsed, RepoLens generates vectors and token trees allowing both full-text keyword indexing and semantic reasoning query filters."
          icon={HelpCircle}
        />

      </div>

    </div>
  );
};

export default Search;
