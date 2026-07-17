import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Search, History, Sparkles, Loader2, CornerDownLeft } from 'lucide-react';
import { api } from '../services/api.ts';

interface CommandPaletteProps {
  repositoryId: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectResult: (result: any) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  repositoryId,
  isOpen,
  onClose,
  onSelectResult
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Query Recent Searches History
  const { data: history = [], refetch: refetchHistory } = useQuery({
    queryKey: ['search-history'],
    queryFn: async () => {
      const response = await api.get('/search/history');
      return response.data;
    },
    enabled: isOpen && !query
  });

  // Query Suggestions Autocomplete
  const { data: suggestions = [] } = useQuery({
    queryKey: ['search-suggestions', repositoryId, query],
    queryFn: async () => {
      const response = await api.get(`/search/suggestions?repository_id=${repositoryId}&q=${encodeURIComponent(query)}`);
      return response.data;
    },
    enabled: isOpen && query.length >= 2
  });

  // Hybrid Search Results mutation
  const searchMutation = useMutation({
    mutationFn: async (searchQuery: string) => {
      const response = await api.post('/search', {
        repository_id: repositoryId,
        query: searchQuery,
        limit: 7
      });
      return response.data;
    },
    onSuccess: () => {
      refetchHistory();
    }
  });

  // Trigger search on query changes (debounced search style or manually)
  useEffect(() => {
    if (query.length >= 3) {
      const delay = setTimeout(() => {
        searchMutation.mutate(query);
      }, 300);
      return () => clearTimeout(delay);
    }
  }, [query]);

  // Keyboard navigation
  const items = query ? (searchMutation.data || suggestions.map((s: string) => ({ title: s, type: 'suggestion' }))) : history.map((h: any) => ({ title: h.query, type: 'history' }));

  useEffect(() => {
    setSelectedIndex(0);
  }, [query, items]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev + 1) % max(items.length, 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev - 1 + max(items.length, 1)) % max(items.length, 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (items.length > selectedIndex) {
        handleSelectItem(items[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  const max = (val: number, fallback: number) => val > 0 ? val : fallback;

  const handleSelectItem = (item: any) => {
    if (item.type === 'history' || item.type === 'suggestion') {
      setQuery(item.title);
      searchMutation.mutate(item.title);
    } else {
      onSelectResult(item);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/60 backdrop-blur-xs select-none">
      
      {/* Overlay Close trigger */}
      <div className="absolute inset-0" onClick={onClose} />

      {/* Command Palette Card Container */}
      <div 
        className="w-full max-w-xl bg-[#0b081a] border border-border/60 rounded-xl shadow-2xl flex flex-col overflow-hidden relative z-10 animate-in fade-in zoom-in-95 duration-150"
        onKeyDown={handleKeyDown}
      >
        
        {/* Input area */}
        <div className="relative flex items-center border-b border-border/40 p-4">
          <Search className="h-5 w-5 text-muted-foreground mr-3" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search codebase semantically... (e.g. JWT verification)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm text-foreground focus:outline-hidden"
          />
          {searchMutation.isPending && (
            <Loader2 className="h-4 w-4 text-[#a21caf] animate-spin" />
          )}
        </div>

        {/* Dynamic Items List */}
        <div className="max-h-[300px] overflow-y-auto p-2 space-y-1">
          {items.length > 0 ? (
            items.map((item: any, idx: number) => {
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={idx}
                  onClick={() => handleSelectItem(item)}
                  className={`flex items-center justify-between w-full text-left p-3 rounded-lg text-xs font-semibold cursor-pointer transition-all ${
                    isSelected ? 'bg-[#a21caf]/15 text-[#f5d0fe]' : 'text-zinc-300 hover:bg-secondary/20'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    {item.type === 'history' ? (
                      <History className="h-4 w-4 text-zinc-500 shrink-0" />
                    ) : item.type === 'suggestion' ? (
                      <Sparkles className="h-4 w-4 text-amber-500 shrink-0" />
                    ) : (
                      <BadgeType type={item.type} />
                    )}
                    <span className="truncate">{item.title}</span>
                    {item.file_path && (
                      <span className="text-[10px] text-zinc-500 font-mono truncate">{item.file_path}</span>
                    )}
                  </div>

                  {isSelected && (
                    <CornerDownLeft className="h-3 w-3 text-[#f5d0fe] shrink-0" />
                  )}
                </button>
              );
            })
          ) : (
            <div className="py-8 text-center select-none text-zinc-500 italic text-xs">
              {query.length >= 3 ? "No results found." : "Type a query to search codebase semantically..."}
            </div>
          )}
        </div>

        {/* Footer shortcuts helper */}
        <div className="p-3 bg-secondary/20 border-t border-border/40 flex justify-between text-[10px] text-zinc-500 font-medium">
          <span>Use <kbd className="px-1 bg-[#0b081a] border border-border rounded-sm">↑↓</kbd> to navigate, <kbd className="px-1 bg-[#0b081a] border border-border rounded-sm">Enter</kbd> to select</span>
          <span>ESC to close</span>
        </div>

      </div>

    </div>
  );
};

const BadgeType: React.FC<{ type: string }> = ({ type }) => {
  return (
    <span className={`px-1.5 py-0.5 rounded-xs text-[8px] font-bold border uppercase shrink-0 ${
      type === 'file' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' :
      type === 'class' ? 'bg-violet-500/10 border-violet-500/20 text-violet-400' :
      type === 'function' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
      'bg-amber-500/10 border-amber-500/20 text-amber-400'
    }`}>
      {type}
    </span>
  );
};
