import React, { useState, useEffect, useMemo } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Search, 
  ShieldAlert, 
  Share2, 
  Download, 
  Bookmark, 
  Plus
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../services/api.ts';
import { Button } from './ui/Button.tsx';
import { useUIStore } from '../stores/ui.ts';

interface RepositoryGraphExplorerProps {
  graphData: {
    nodes: any[];
    edges: any[];
  };
  repositoryId?: string;
}

const TYPE_COLORS: Record<string, string> = {
  folder: '#4b5563',   // zinc-600
  file: '#2563eb',     // blue-600
  class: '#a21caf',    // violet-600
  function: '#059669', // emerald-600
  api: '#ca8a04',      // amber-600
  model: '#ea580c'     // orange-600
};

export const RepositoryGraphExplorer: React.FC<RepositoryGraphExplorerProps> = ({ graphData, repositoryId }) => {
  const { addNotification } = useUIStore();
  const [search, setSearch] = useState('');
  const [layout, setLayout] = useState<'spiral' | 'hierarchical' | 'force'>('spiral');
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  
  // Workspace Annotations & Bookmarks panel states
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [newAnnotationText, setNewAnnotationText] = useState('');
  const [bookmarkName, setBookmarkName] = useState('');
  const [showBookmarkModal, setShowBookmarkModal] = useState(false);

  const [activeFilters, setActiveFilters] = useState<Record<string, boolean>>({
    folder: true,
    file: true,
    class: true,
    function: true,
    api: true,
    model: true
  });

  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);

  // Query Annotations List
  const { data: annotations = [], refetch: refetchAnnotations } = useQuery({
    queryKey: ['annotations', repositoryId, selectedNode?.id],
    queryFn: async () => {
      if (!repositoryId || !selectedNode) return [];
      const response = await api.get(`/workspace/annotations/list?repository_id=${repositoryId}`);
      return response.data.filter((ann: any) => ann.target_id === selectedNode.id);
    },
    enabled: !!repositoryId && !!selectedNode
  });

  // Query Bookmarks List
  const { refetch: refetchBookmarks } = useQuery({
    queryKey: ['bookmarks', repositoryId],
    queryFn: async () => {
      if (!repositoryId) return [];
      const response = await api.get(`/workspace/bookmarks/list?repository_id=${repositoryId}`);
      return response.data;
    },
    enabled: !!repositoryId
  });

  // Add Annotation mutation
  const addAnnotation = useMutation({
    mutationFn: async (content: string) => {
      await api.post('/workspace/annotations', {
        repository_id: repositoryId,
        target_id: selectedNode.id,
        note_type: 'node',
        content
      });
    },
    onSuccess: () => {
      setNewAnnotationText('');
      refetchAnnotations();
      addNotification('Annotation pined.', 'success');
    }
  });

  // Add Bookmark mutation
  const saveBookmark = useMutation({
    mutationFn: async (name: string) => {
      await api.post('/workspace/bookmarks', {
        repository_id: repositoryId,
        name,
        view_state: { layout, activeFilters }
      });
    },
    onSuccess: () => {
      setBookmarkName('');
      setShowBookmarkModal(false);
      refetchBookmarks();
      addNotification('Layout bookmark saved.', 'success');
    }
  });

  // Export workspace diagram REST endpoint
  const handleExport = async (format: string) => {
    try {
      const response = await api.post('/workspace/export', {
        format,
        nodes: nodes.map(n => ({ id: n.id, label: n.name, type: n.type })),
        edges: edges.map(e => ({ source: e.source, target: e.target, label: e.type }))
      });
      
      const blob = new Blob([format === 'json' ? JSON.stringify(response.data, null, 2) : response.data], {
        type: format === 'json' ? 'application/json' : 'text/plain'
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `repository_architecture.${format}`;
      link.click();
      addNotification(`Graph exported as ${format.toUpperCase()}`, 'success');
    } catch (err) {
      addNotification('Failed to export graph.', 'error');
    }
  };

  // Client-Side Coordinate layouts computation to ensure 60 FPS transitions
  const computedNodes = useMemo(() => {
    const activeNodes = graphData.nodes.filter(n => {
      const matchesType = activeFilters[n.type] !== false;
      const matchesSearch = n.name.toLowerCase().includes(search.toLowerCase());
      return matchesType && matchesSearch;
    });

    if (layout === 'hierarchical') {
      // Top-Down hierarchical flow levels calculator
      const inDegree: Record<string, number> = {};
      const adj: Record<string, string[]> = {};
      activeNodes.forEach(n => {
        inDegree[n.id] = 0;
        adj[n.id] = [];
      });

      graphData.edges.forEach(e => {
        if (adj[e.source] && adj[e.target]) {
          adj[e.source].push(e.target);
          inDegree[e.target] = (inDegree[e.target] || 0) + 1;
        }
      });

      const levels: Record<string, number> = {};
      const queue = activeNodes.filter(n => inDegree[n.id] === 0).map(n => n.id);
      if (queue.length === 0 && activeNodes.length > 0) {
        queue.push(activeNodes[0].id);
      }

      let currentLvl = 0;
      const visited = new Set<string>();
      
      while (queue.length > 0 && currentLvl < 20) {
        const nextQueue: string[] = [];
        queue.forEach(nid => {
          levels[nid] = currentLvl;
          visited.add(nid);
          (adj[nid] || []).forEach(neighbor => {
            if (!visited.has(neighbor)) {
              nextQueue.push(neighbor);
            }
          });
        });
        queue.length = 0;
        queue.push(...Array.from(new Set(nextQueue)));
        currentLvl++;
      }

      activeNodes.forEach(n => {
        if (levels[n.id] === undefined) levels[n.id] = 0;
      });

      const levelGroups: Record<number, string[]> = {};
      Object.entries(levels).forEach(([nid, lvl]) => {
        levelGroups[lvl] = levelGroups[lvl] || [];
        levelGroups[lvl].push(nid);
      });

      return activeNodes.map(n => {
        const lvl = levels[n.id] || 0;
        const group = levelGroups[lvl] || [];
        const idx = group.indexOf(n.id);
        const count = group.length;
        
        const x = (idx - count / 2) * 200 + 400;
        const y = lvl * 160 + 100;
        
        return {
          ...n,
          data: { label: n.name, type: n.type },
          position: { x, y }
        };
      });

    } else if (layout === 'force') {
      // Force-directed circular layout
      const count = activeNodes.length;
      return activeNodes.map((n, idx) => {
        const angle = (2 * Math.PI * idx) / Math.max(count, 1);
        const radius = 220 + (idx % 3) * 60;
        const x = radius * Math.cos(angle) + 400;
        const y = radius * Math.sin(angle) + 300;

        return {
          ...n,
          data: { label: n.name, type: n.type },
          position: { x, y }
        };
      });

    } else {
      // Spiral placement (default distribution)
      return activeNodes.map((n, idx) => {
        const angle = 0.45 * idx;
        const radius = 55 * Math.sqrt(idx + 1);
        const x = radius * Math.cos(angle) + 400;
        const y = radius * Math.sin(angle) + 300;

        return {
          ...n,
          data: { label: n.name, type: n.type },
          position: { x, y }
        };
      });
    }
  }, [graphData.nodes, search, activeFilters, layout]);

  // Map active edges
  const computedEdges = useMemo(() => {
    const activeNodeIds = new Set(computedNodes.map(n => n.id));
    return graphData.edges.filter(e => 
      activeNodeIds.has(e.source) && activeNodeIds.has(e.target)
    ).map(e => ({
      ...e,
      style: { stroke: '#7c3aed', strokeWidth: 1.5, opacity: 0.6 },
      animated: e.type === 'CALLS' || e.type === 'ROUTES_TO'
    }));
  }, [graphData.edges, computedNodes]);

  useEffect(() => {
    setNodes(computedNodes.map(n => ({
      ...n,
      style: {
        background: '#0e0b1e',
        color: '#f4f4f5',
        border: `2px solid ${TYPE_COLORS[n.type] || '#475569'}`,
        borderRadius: '8px',
        padding: '10px',
        fontSize: '11px',
        fontWeight: 600,
        fontFamily: 'monospace',
        maxWidth: 180,
        cursor: 'pointer',
        boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)'
      }
    })));
    setEdges(computedEdges);
  }, [computedNodes, computedEdges, setNodes, setEdges]);

  // Deep Link handler (shares link with coordinate URL params)
  const generateShareableLink = () => {
    const url = new URL(window.location.href);
    url.searchParams.set('layout', layout);
    url.searchParams.set('filters', Object.keys(activeFilters).filter(k => activeFilters[k]).join(','));
    if (selectedNode) {
      url.searchParams.set('node', selectedNode.id);
    }
    navigator.clipboard.writeText(url.toString());
    addNotification('Deep link copied to clipboard!', 'success');
  };

  const onNodeClick = (_: any, node: any) => {
    setSelectedNode(node);
    setIsDrawerOpen(true);
  };

  const toggleFilter = (type: string) => {
    setActiveFilters(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  return (
    <div className="flex border border-border/40 rounded-xl overflow-hidden bg-card/15 h-[550px] relative items-stretch">
      
      {/* Visual Canvas Viewport */}
      <div className="flex-1 min-w-0 h-full relative">
        
        {/* Floating Toolbar Overlay */}
        <div className="absolute top-4 left-4 z-10 flex flex-col gap-3 select-none">
          {/* Search bar */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input 
              type="text" 
              placeholder="Search nodes..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-48 sm:w-56 h-9 pl-8 pr-3 bg-[#030014]/80 text-foreground text-xs border border-border/60 rounded-md focus:outline-hidden backdrop-blur-md"
            />
          </div>

          {/* Quick controls bar */}
          <div className="flex gap-2 bg-[#030014]/80 border border-border/60 p-1.5 rounded-lg backdrop-blur-md w-fit">
            
            {/* Layout selector dropdown */}
            <select
              value={layout}
              onChange={(e) => setLayout(e.target.value as any)}
              className="bg-transparent text-foreground text-[10px] font-bold border-none outline-hidden cursor-pointer"
            >
              <option value="spiral">Spiral</option>
              <option value="hierarchical">Hierarchical</option>
              <option value="force">Force-Directed</option>
            </select>

            <span className="text-zinc-700">|</span>

            {/* Bookmark view button */}
            <button onClick={() => setShowBookmarkModal(true)} className="p-0.5 hover:text-[#f5d0fe]" title="Bookmark layout">
              <Bookmark className="h-3.5 w-3.5" />
            </button>

            {/* Share deep link */}
            <button onClick={generateShareableLink} className="p-0.5 hover:text-[#f5d0fe]" title="Copy shareable link">
              <Share2 className="h-3.5 w-3.5" />
            </button>

            {/* Export DOT/GraphML */}
            <button onClick={() => handleExport('dot')} className="p-0.5 hover:text-[#f5d0fe]" title="Export DOT format">
              <Download className="h-3.5 w-3.5" />
            </button>

          </div>

          {/* Filters badge picker */}
          <div className="p-2.5 bg-[#030014]/80 border border-border/60 rounded-lg backdrop-blur-md flex flex-wrap gap-1.5 max-w-[240px]">
            {Object.keys(activeFilters).map(type => (
              <button
                key={type}
                onClick={() => toggleFilter(type)}
                className={`px-1.5 py-0.5 rounded text-[9px] font-semibold border transition-all cursor-pointer ${
                  activeFilters[type] 
                    ? 'bg-violet-950/20 text-violet-400 border-violet-500/40' 
                    : 'bg-[#030014]/30 text-zinc-500 border-zinc-800'
                }`}
              >
                <span className="capitalize">{type}</span>
              </button>
            ))}
          </div>

        </div>

        {/* React Flow Canvas canvas wrapper */}
        {graphData.nodes.length > 0 ? (
          <div className="w-full h-full bg-[#070514]">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              fitView
              minZoom={0.1}
              maxZoom={1.5}
            >
              <Background color="#7c3aed" gap={16} size={1} />
              <Controls style={{ background: '#0e0b1e', border: '1px solid #27272a', color: '#f4f4f5' }} />
              <MiniMap 
                style={{ background: '#0e0b1e', border: '1px solid #27272a' }}
                nodeColor={(node) => TYPE_COLORS[(node.data as any)?.type] || '#475569'}
                maskColor="rgba(0, 0, 0, 0.4)"
              />
            </ReactFlow>
          </div>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center text-center p-6 bg-[#070514]">
            <ShieldAlert className="h-10 w-10 text-zinc-500 mb-2" />
            <h4 className="font-semibold text-sm text-white">No nodes mapped</h4>
            <p className="text-xs text-zinc-500 max-w-xs mt-1">Run Codebase Analysis to synthesize a knowledge graph.</p>
          </div>
        )}

      </div>

      {/* Right Drawer Annotations Panel */}
      {isDrawerOpen && selectedNode && (
        <div className="w-80 border-l border-border/40 bg-[#0b081a] p-4 flex flex-col justify-between shrink-0 select-text overflow-y-auto relative animate-in slide-in-from-right duration-200">
          <div className="space-y-4">
            
            {/* Header info */}
            <div className="flex justify-between items-start border-b border-border/20 pb-3">
              <div>
                <span className="text-[9px] font-bold uppercase tracking-wider text-zinc-500">{selectedNode.type} Node</span>
                <h4 className="font-bold text-sm text-white font-mono truncate max-w-[200px]">{selectedNode.name || selectedNode.label}</h4>
              </div>
              <button 
                onClick={() => setIsDrawerOpen(false)}
                className="text-zinc-500 hover:text-white text-xs select-none"
              >
                ✕
              </button>
            </div>

            {/* Metadata descriptors list */}
            <div className="text-[10px] text-zinc-400 space-y-1.5 font-mono select-all bg-secondary/20 p-2.5 rounded-lg border border-border/20">
              <p>ID: {selectedNode.id}</p>
              <p>Line Range: {selectedNode.line_start || 1}-{selectedNode.line_end || 1}</p>
            </div>

            {/* Annotations listings */}
            <div className="space-y-3">
              <h5 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider select-none">Notes & Annotations</h5>
              
              <div className="space-y-2.5 max-h-[160px] overflow-y-auto">
                {annotations.map((ann: any) => (
                  <div key={ann.id} className="p-2.5 bg-secondary/15 border border-border/30 rounded text-[11px] text-zinc-300 relative group">
                    <p className="leading-normal">{ann.content}</p>
                    <span className="text-[8px] text-zinc-500 mt-1 block select-none">
                      {new Date(ann.created_at).toLocaleString()}
                    </span>
                  </div>
                ))}
                {annotations.length === 0 && (
                  <p className="text-[10px] text-zinc-500 italic select-none">No annotations saved yet.</p>
                )}
              </div>

              {/* Add annotation input */}
              <div className="space-y-2 pt-2 select-none">
                <textarea
                  placeholder="Add custom code review note..."
                  value={newAnnotationText}
                  onChange={(e) => setNewAnnotationText(e.target.value)}
                  rows={2}
                  className="w-full p-2 bg-secondary text-foreground text-[10px] border border-border rounded focus:outline-hidden"
                />
                <Button 
                  onClick={() => addAnnotation.mutate(newAnnotationText)}
                  disabled={!newAnnotationText.trim()}
                  size="sm"
                  className="w-full text-[10px]"
                >
                  <Plus className="mr-1 h-3 w-3" /> Pin Note
                </Button>
              </div>

            </div>

          </div>
        </div>
      )}

      {/* Bookmarks Modal Dialog */}
      {showBookmarkModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs select-none">
          <div className="w-full max-w-sm bg-[#0b081a] border border-border/60 rounded-xl p-4 space-y-4">
            <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
              <Bookmark className="h-4 w-4 text-violet-400" /> Save View Bookmark
            </h4>
            
            <input 
              type="text" 
              placeholder="e.g. Authentication Flow Layer"
              value={bookmarkName}
              onChange={(e) => setBookmarkName(e.target.value)}
              className="w-full h-10 px-3 bg-secondary text-foreground text-xs border border-border rounded-lg focus:outline-hidden"
            />

            <div className="flex justify-end gap-2 text-xs">
              <Button variant="outline" size="sm" onClick={() => setShowBookmarkModal(false)}>
                Cancel
              </Button>
              <Button 
                onClick={() => saveBookmark.mutate(bookmarkName)}
                disabled={!bookmarkName.trim()}
                variant="primary"
                size="sm"
              >
                Save view
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
