import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ArrowLeft, 
  GitBranch, 
  Settings as SettingsIcon, 
  Search, 
  Network, 
  Activity,
  Save,
  Tag,
  Clock,
  Loader2,
  Folder,
  FolderOpen,
  File,
  BarChart,
  Play,
  CheckCircle,
  XCircle,
  FileCode,
  ShieldAlert,
  Sparkles,
  FileText,
  Building2
} from 'lucide-react';
import Editor from '@monaco-editor/react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

import { Button } from '../components/ui/Button.tsx';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card.tsx';
import { Badge } from '../components/ui/Badge.tsx';
import { useUIStore } from '../stores/ui.ts';
import { api } from '../services/api.ts';
import { RepositoryGraphExplorer } from '../components/RepositoryGraphExplorer.tsx';
import { CommandPalette } from '../components/CommandPalette.tsx';
import { RepositoryAIChat } from '../components/RepositoryAIChat.tsx';
import { RepositoryDocumentationEditor } from '../components/RepositoryDocumentationEditor.tsx';
import { RepositoryQualityDashboard } from '../components/RepositoryQualityDashboard.tsx';
import { EnterpriseAdminDashboard } from '../components/EnterpriseAdminDashboard.tsx';

interface RepositoryDetailProps {
  repoId: string;
  onBack: () => void;
}

const COLORS = ['#a21caf', '#7c3aed', '#2563eb', '#059669', '#ca8a04', '#dc2626', '#475569'];

const RepositoryDetail: React.FC<RepositoryDetailProps> = ({ repoId, onBack }) => {
  const queryClient = useQueryClient();
  const { addNotification } = useUIStore();
  const [activeTab, setActiveTab] = useState<'overview' | 'files' | 'symbols' | 'dependencies' | 'search' | 'assistant' | 'documentation' | 'quality' | 'enterprise' | 'architecture' | 'flows' | 'metrics' | 'statistics' | 'configurations' | 'logs' | 'settings'>('overview');
  
  // Settings forms local states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isAutoSync, setIsAutoSync] = useState(false);
  const [syncInterval, setSyncInterval] = useState(24);
  const [tagsInput, setTagsInput] = useState('');

  // Files Tab States
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({});
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);

  // Command palette state
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  // Search tab states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFilterType, setSearchFilterType] = useState<string>('all');

  // Trigger search keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Query details
  const { data: repo, isLoading: isRepoLoading, error: repoError } = useQuery({
    queryKey: ['repository', repoId],
    queryFn: async () => {
      const response = await api.get(`/repositories/${repoId}`);
      const data = response.data;
      
      setName(data.name);
      setDescription(data.description || '');
      if (data.settings) {
        setIsAutoSync(data.settings.is_auto_sync);
        setSyncInterval(data.settings.sync_interval_hours);
      }
      if (data.tags) {
        setTagsInput(data.tags.map((t: any) => t.tag_name).join(', '));
      }
      return data;
    }
  });

  // Query File Structure
  const { data: filesTree = { folders: [], files: [] } } = useQuery({
    queryKey: ['repository-files', repoId],
    queryFn: async () => {
      const response = await api.get(`/repositories/${repoId}/files`);
      return response.data;
    },
    enabled: activeTab === 'files' || activeTab === 'configurations'
  });

  // Query Selected File Content
  const { data: selectedFile, isLoading: isFileLoading } = useQuery({
    queryKey: ['file-content', selectedFileId],
    queryFn: async () => {
      const response = await api.get(`/files/${selectedFileId}`);
      return response.data;
    },
    enabled: !!selectedFileId
  });

  // Query Symbols
  const [symbolSearch, setSymbolSearch] = useState('');
  const [symbolKind, setSymbolKind] = useState('all');
  const { data: symbols = [] } = useQuery({
    queryKey: ['repository-symbols', repoId, symbolKind, symbolSearch],
    queryFn: async () => {
      let url = `/repositories/${repoId}/symbols`;
      const params = [];
      if (symbolKind !== 'all') params.push(`kind=${symbolKind}`);
      if (symbolSearch) params.push(`search=${encodeURIComponent(symbolSearch)}`);
      if (params.length) url += `?${params.join('&')}`;
      
      const response = await api.get(url);
      return response.data;
    },
    enabled: activeTab === 'symbols'
  });

  // Query Dependencies
  const { data: dependencies = [] } = useQuery({
    queryKey: ['repository-dependencies', repoId],
    queryFn: async () => {
      const response = await api.get(`/repositories/${repoId}/dependencies`);
      return response.data;
    },
    enabled: activeTab === 'dependencies'
  });

  // Query Graph Data
  const { data: graphData = { nodes: [], edges: [] }, isLoading: isGraphLoading } = useQuery({
    queryKey: ['repository-graph', repoId],
    queryFn: async () => {
      const response = await api.get(`/repositories/${repoId}/graph`);
      return response.data;
    },
    enabled: activeTab === 'architecture'
  });

  // Query API Flows
  const { data: flows = [], isLoading: isFlowsLoading } = useQuery({
    queryKey: ['repository-flows', repoId],
    queryFn: async () => {
      const response = await api.get(`/repositories/${repoId}/architecture/flows`);
      return response.data;
    },
    enabled: activeTab === 'flows'
  });

  // Query Metrics
  const { data: metrics = { coupling: 0.0, cohesion: 100.0, nodes_count: 0, edges_count: 0, circular_dependencies: [], dead_code: [] }, isLoading: isMetricsLoading } = useQuery({
    queryKey: ['repository-metrics', repoId],
    queryFn: async () => {
      const response = await api.get(`/repositories/${repoId}/metrics`);
      return response.data;
    },
    enabled: activeTab === 'metrics'
  });

  // Query Statistics
  const { data: stats = { loc: 0, files_count: 0, folders_count: 0, languages: {}, frameworks: [] } } = useQuery({
    queryKey: ['repository-statistics', repoId],
    queryFn: async () => {
      const response = await api.get(`/repositories/${repoId}/statistics`);
      return response.data;
    },
    enabled: activeTab === 'statistics' || activeTab === 'overview'
  });

  // Query Search Tab Results
  const { data: searchResults = [], isLoading: isSearchLoading } = useQuery({
    queryKey: ['search-query', repoId, searchQuery, searchFilterType],
    queryFn: async () => {
      const response = await api.post('/search', {
        repository_id: repoId,
        query: searchQuery,
        chunk_type: searchFilterType === 'all' ? null : searchFilterType,
        limit: 15
      });
      return response.data;
    },
    enabled: activeTab === 'search' && searchQuery.length >= 3
  });

  // Query Analysis Status Logs
  const { data: jobStatus, refetch: refetchJob } = useQuery({
    queryKey: ['repository-analysis-job', repoId],
    queryFn: async () => {
      const response = await api.get(`/repositories/${repoId}/analysis`);
      return response.data;
    },
    refetchInterval: (query) => {
      const data = query.state.data as any;
      return (data && data.status === 'running') ? 1500 : false;
    }
  });

  // Mutation to Trigger Analyze code
  const triggerAnalyze = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/repositories/${repoId}/analyze`);
      return response.data;
    },
    onSuccess: () => {
      addNotification('Repository analysis job enqueued.', 'success');
      refetchJob();
      setActiveTab('logs');
    },
    onError: (err: any) => {
      addNotification(err.error?.message || 'Failed to trigger codebase analysis.', 'error');
    }
  });

  // Mutation to update details
  const updateRepo = useMutation({
    mutationFn: async (updatedData: any) => {
      const response = await api.patch(`/repositories/${repoId}`, updatedData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repository', repoId] });
      addNotification('Repository details saved.', 'success');
    }
  });

  const handleSettingsSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const tagsList = tagsInput.split(',').map(t => t.trim()).filter(Boolean);
    updateRepo.mutate({
      name,
      description,
      is_auto_sync: isAutoSync,
      sync_interval_hours: syncInterval,
      tags: tagsList
    });
  };

  const toggleFolder = (path: string) => {
    setExpandedFolders(prev => ({
      ...prev,
      [path]: !prev[path]
    }));
  };

  // Jump from search result to code files view
  const handleSelectSearchResult = (result: any) => {
    setSelectedFileId(result.file_id);
    setActiveTab('files');
    addNotification(`Opening file explorer: ${result.file_path}`, 'success');
  };

  // Helper map for Monaco syntax files language
  const getEditorLanguage = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (ext === 'py') return 'python';
    if (ext === 'js' || ext === 'jsx') return 'javascript';
    if (ext === 'ts' || ext === 'tsx') return 'typescript';
    if (ext === 'html') return 'html';
    if (ext === 'css') return 'css';
    if (ext === 'json') return 'json';
    if (ext === 'md') return 'markdown';
    if (ext === 'yaml' || ext === 'yml') return 'yaml';
    if (ext === 'toml') return 'toml';
    return 'plaintext';
  };

  if (isRepoLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-2 text-xs">
        <Loader2 className="h-8 w-8 text-[#a21caf] animate-spin" />
        <span className="text-sm text-muted-foreground font-medium">Fetching workspace settings...</span>
      </div>
    );
  }

  if (repoError || !repo) {
    return (
      <Card className="max-w-md mx-auto text-center p-6 border-dashed border-rose-500/30 bg-rose-500/5">
        <CardContent className="space-y-4">
          <p className="text-sm font-semibold text-rose-400">Failed to load repository details.</p>
          <Button variant="outline" onClick={onBack}>
            Back to Repositories
          </Button>
        </CardContent>
      </Card>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: Activity },
    { id: 'files', name: 'Files', icon: Folder },
    { id: 'symbols', name: 'Symbols', icon: FileCode },
    { id: 'dependencies', name: 'Dependencies', icon: Network },
    { id: 'search', name: 'Semantic Search', icon: Search },
    { id: 'assistant', name: 'AI Assistant', icon: Sparkles },
    { id: 'documentation', name: 'Docs & Reports', icon: FileText },
    { id: 'quality', name: 'Quality & Security', icon: ShieldAlert },
    { id: 'enterprise', name: 'Enterprise & Admin', icon: Building2 },
    { id: 'architecture', name: 'Architecture', icon: Network },
    { id: 'flows', name: 'Flows', icon: GitBranch },
    { id: 'metrics', name: 'Metrics', icon: BarChart },
    { id: 'statistics', name: 'Statistics', icon: BarChart },
    { id: 'configurations', name: 'Configurations', icon: SettingsIcon },
    { id: 'logs', name: 'Analysis Logs', icon: Play },
    { id: 'settings', name: 'Settings', icon: SettingsIcon }
  ];

  // Group files by directory tree path
  const rootFiles = filesTree.files.filter((f: any) => f.folder_id === filesTree.folders.find((fol: any) => fol.path === "")?.id);
  const chartData = Object.entries(stats.languages || {}).map(([name, val]: any) => ({
    name,
    value: val.size
  }));

  return (
    <div className="space-y-6 select-none relative">
      
      {/* Search Hotkey Overlay Trigger bar */}
      <CommandPalette 
        repositoryId={repoId}
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectResult={handleSelectSearchResult}
      />

      {/* Title back triggers */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <Button variant="outline" size="icon" onClick={onBack} className="rounded-full w-9 h-9 border-border/60">
            <ArrowLeft className="h-4.5 w-4.5" />
          </Button>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-2xl font-bold font-display tracking-tight text-white">{repo.owner}/{repo.name}</h2>
              <Badge variant={repo.visibility === 'private' ? 'secondary' : 'outline'}>{repo.visibility}</Badge>
            </div>
            <p className="text-muted-foreground text-xs">{repo.clone_url || 'ZIP Codebase Upload'}</p>
          </div>
        </div>
        
        <div className="flex gap-2">
          {/* Quick search shortcut trigger */}
          <Button variant="outline" size="sm" onClick={() => setIsCommandPaletteOpen(true)} className="border-border/60 text-xs">
            <Search className="mr-1.5 h-3.5 w-3.5" /> Search Codebase <kbd className="ml-2 px-1 py-0.5 bg-zinc-900 border border-zinc-700 rounded-sm text-[8px]">Ctrl+K</kbd>
          </Button>
          <Button 
            onClick={() => triggerAnalyze.mutate()}
            loading={triggerAnalyze.isPending || (jobStatus && jobStatus.status === 'running')}
            variant="primary"
            size="sm"
          >
            <Play className="mr-1.5 h-3.5 w-3.5" /> Analyze Codebase
          </Button>
        </div>
      </div>

      {/* Tabs navigation bar */}
      <div className="flex border-b border-border/40 gap-1 overflow-x-auto pb-px">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-3 px-4 border-b-2 text-xs font-semibold tracking-wide transition-all cursor-pointer whitespace-nowrap ${
                isActive 
                  ? 'border-[#a21caf] text-[#f5d0fe]' 
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{tab.name}</span>
            </button>
          );
        })}
      </div>

      {/* Panels viewport */}
      <div className="pt-2">
        
        {/* OVERVIEW PANEL */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2 space-y-6">
              <CardHeader className="pb-2 border-b border-border/40">
                <CardTitle>Codebase Summary</CardTitle>
                <CardDescription>Key telemetry descriptors scanned structurally.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 text-sm">
                <div className="space-y-4">
                  <div>
                    <span className="text-xs text-muted-foreground block mb-0.5">Lines of Code (LOC)</span>
                    <span className="text-lg font-bold text-white font-display">{(stats.loc || 0).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block mb-0.5">Total Folder Nodes</span>
                    <span className="font-semibold text-white">{stats.folders_count || 0} folders</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block mb-0.5">File System Size</span>
                    <span className="font-semibold text-white">{(repo.size / 1024).toFixed(1)} MB ({repo.size} KB)</span>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <span className="text-xs text-muted-foreground block mb-0.5">Detected Frameworks</span>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {stats.frameworks && stats.frameworks.length > 0 ? (
                        stats.frameworks.map((fw: string) => (
                          <Badge key={fw} variant="outline" className="border-violet-500/30 text-violet-400 bg-violet-950/20">
                            {fw}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-xs italic text-zinc-500">None detected</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block mb-0.5">Categorization Tags</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {repo.tags && repo.tags.length > 0 ? (
                        repo.tags.map((t: any) => (
                          <Badge key={t.tag_name} variant="outline" className="text-[10px]">{t.tag_name}</Badge>
                        ))
                      ) : (
                        <span className="text-xs italic text-zinc-500">No tags configured</span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>

              {repo.last_commit_hash && (
                <div className="mx-6 p-4 border border-border/40 bg-secondary/15 rounded-lg text-xs space-y-1.5 select-text">
                  <div className="flex justify-between items-center text-muted-foreground border-b border-border/40 pb-1.5 mb-1.5">
                    <span className="font-semibold uppercase text-[9px] tracking-wider">Latest Branch Commit</span>
                    <span className="font-mono text-zinc-300">{repo.last_commit_hash.substring(0, 8)}</span>
                  </div>
                  <p className="font-medium text-white">{repo.last_commit_message}</p>
                  <p className="text-[10px] text-zinc-500">
                    Committed on {new Date(repo.last_commit_at).toLocaleString()}
                  </p>
                </div>
              )}
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Languages Distribution</CardTitle>
                <CardDescription>Source code size allocation percentage.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {stats.languages && Object.keys(stats.languages).length > 0 ? (
                  Object.entries(stats.languages).map(([lang, info]: any) => (
                    <div key={lang} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-zinc-200">{lang}</span>
                        <span className="text-[#f5d0fe]">{info.percentage}%</span>
                      </div>
                      <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                        <div 
                          className="bg-[#a21caf] h-full rounded-full" 
                          style={{ width: `${info.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-zinc-500 text-xs italic text-center py-8">Trigger analysis to resolve statistics.</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* FILES EXPLORER PANEL (MONACO VIEWER) */}
        {activeTab === 'files' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[600px] items-stretch">
            
            {/* Sidebar tree directory */}
            <Card className="lg:col-span-1 overflow-y-auto bg-card/15 p-4 border-border/40">
              <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Workspace Files</h3>
              
              <div className="space-y-1 text-xs">
                {/* Recursively build file system tree */}
                {filesTree.folders.map((fol: any) => {
                  if (fol.path === "") return null;
                  const isExpanded = expandedFolders[fol.path];
                  const childFiles = filesTree.files.filter((fi: any) => fi.folder_id === fol.id);
                  
                  return (
                    <div key={fol.id} className="space-y-1">
                      <button 
                        onClick={() => toggleFolder(fol.path)}
                        className="flex items-center gap-1.5 w-full text-left py-1 text-zinc-300 hover:text-white hover:bg-secondary/40 px-1 rounded-sm cursor-pointer"
                      >
                        {isExpanded ? <FolderOpen className="h-3.5 w-3.5 text-violet-400 shrink-0" /> : <Folder className="h-3.5 w-3.5 text-violet-400 shrink-0" />}
                        <span className="truncate">{fol.name}</span>
                      </button>
                      
                      {isExpanded && childFiles.map((fi: any) => (
                        <button
                          key={fi.id}
                          onClick={() => setSelectedFileId(fi.id)}
                          className={`flex items-center gap-1.5 w-full text-left py-0.5 pl-6 pr-1 hover:bg-secondary/40 rounded-sm cursor-pointer ${
                            selectedFileId === fi.id ? 'bg-[#a21caf]/10 text-[#f5d0fe] border-l-2 border-[#a21caf]' : 'text-zinc-400 hover:text-zinc-200'
                          }`}
                        >
                          <File className="h-3 w-3 shrink-0" />
                          <span className="truncate">{fi.name}</span>
                        </button>
                      ))}
                    </div>
                  );
                })}

                {/* Root Files */}
                {rootFiles.map((fi: any) => (
                  <button
                    key={fi.id}
                    onClick={() => setSelectedFileId(fi.id)}
                    className={`flex items-center gap-1.5 w-full text-left py-1 px-1.5 hover:bg-secondary/40 rounded-sm cursor-pointer ${
                      selectedFileId === fi.id ? 'bg-[#a21caf]/10 text-[#f5d0fe] border-l-2 border-[#a21caf]' : 'text-zinc-400 hover:text-zinc-200'
                    }`}
                  >
                    <File className="h-3.5 w-3.5 shrink-0 text-zinc-500" />
                    <span className="truncate">{fi.name}</span>
                  </button>
                ))}
              </div>
            </Card>

            {/* Monaco Viewport Code Block */}
            <Card className="lg:col-span-3 flex flex-col justify-between overflow-hidden bg-card/25 border-border/40 select-text">
              {selectedFileId && selectedFile ? (
                <div className="flex flex-col h-full">
                  <div className="flex justify-between items-center p-3 border-b border-border/40 bg-card/45 select-none">
                    <div>
                      <h4 className="font-semibold text-xs text-white">{selectedFile.name}</h4>
                      <p className="text-[10px] text-muted-foreground">{selectedFile.path}</p>
                    </div>
                    <Badge variant="outline" className="text-[10px]">
                      {(selectedFile.size).toFixed(1)} KB
                    </Badge>
                  </div>
                  
                  <div className="flex-1 min-h-0 relative">
                    {isFileLoading ? (
                      <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                        <Loader2 className="h-6 w-6 text-[#a21caf] animate-spin" />
                      </div>
                    ) : null}
                    <Editor
                      height="100%"
                      defaultLanguage={getEditorLanguage(selectedFile.name)}
                      theme="vs-dark"
                      value={selectedFile.content || ""}
                      options={{
                        readOnly: true,
                        fontSize: 12,
                        minimap: { enabled: true },
                        wordWrap: "on",
                        scrollBeyondLastLine: false,
                        automaticLayout: true
                      }}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-center p-6 select-none">
                  <FileCode className="h-10 w-10 text-zinc-500 mb-2" />
                  <h4 className="font-semibold text-sm text-white">No file opened</h4>
                  <p className="text-xs text-muted-foreground max-w-xs mt-1">
                    Select any code file from the directory explorer sidebar tree to open it.
                  </p>
                </div>
              )}
            </Card>
          </div>
        )}

        {/* SYMBOLS EXPLORER PANEL */}
        {activeTab === 'symbols' && (
          <div className="space-y-6">
            
            {/* Search toolbar */}
            <div className="flex flex-col sm:flex-row gap-4 items-center bg-card/25 p-4 rounded-xl border border-border/40">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <input 
                  type="text" 
                  placeholder="Filter symbols by name..." 
                  value={symbolSearch}
                  onChange={(e) => setSymbolSearch(e.target.value)}
                  className="w-full h-10 pl-9 pr-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                />
              </div>
              <select
                value={symbolKind}
                onChange={(e) => setSymbolKind(e.target.value)}
                className="h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md cursor-pointer focus:outline-hidden"
              >
                <option value="all">All Kinds</option>
                <option value="class">Classes</option>
                <option value="function">Functions</option>
              </select>
            </div>

            {/* List grid */}
            {symbols.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {symbols.map((sym: any) => (
                  <Card key={sym.id} className="p-4 flex flex-col justify-between hover:border-border/60 transition-all text-xs">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant={sym.kind === 'class' ? 'default' : 'secondary'}>
                          {sym.kind}
                        </Badge>
                        <span className="text-[10px] text-zinc-500 font-mono">Lines: {sym.line_start}-{sym.line_end}</span>
                      </div>
                      <h4 className="font-bold text-sm text-white font-mono truncate">{sym.name}</h4>
                      <p className="text-[10px] text-muted-foreground truncate mt-0.5">{sym.file_path}</p>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-center text-zinc-500 text-xs italic py-8">No symbols match search filters.</p>
            )}

          </div>
        )}

        {/* DEPENDENCIES TAB */}
        {activeTab === 'dependencies' && (
          <Card>
            <CardHeader>
              <CardTitle>Imports Tracer</CardTitle>
              <CardDescription>Map references and dependencies across codebase file boundaries.</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              {dependencies.length > 0 ? (
                <table className="w-full text-left text-xs divide-y divide-border/40 select-text">
                  <thead>
                    <tr className="text-muted-foreground uppercase text-[10px] font-semibold">
                      <th className="py-2.5 px-3">Importing File</th>
                      <th className="py-2.5 px-3">Target Reference</th>
                      <th className="py-2.5 px-3">Trace Kind</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/20 text-zinc-300 font-mono">
                    {dependencies.map((dep: any) => (
                      <tr key={dep.id} className="hover:bg-white/[0.01]">
                        <td className="py-2 px-3 break-all">{dep.file_path}</td>
                        <td className="py-2 px-3 break-all text-[#f5d0fe]">{dep.target_file_path}</td>
                        <td className="py-2 px-3 capitalize">
                          <Badge variant="outline" className="text-[9px]">{dep.type}</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-zinc-500 italic text-xs py-8 text-center">No dependency nodes mapped.</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* SEMANTIC SEARCH TAB */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            
            {/* Search Input Bar */}
            <div className="flex flex-col sm:flex-row gap-4 items-center bg-card/25 p-4 rounded-xl border border-border/40 select-none">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-3 top-3 h-4.5 w-4.5 text-zinc-500" />
                <input 
                  type="text" 
                  placeholder="Enter intention query... (e.g. user authentication, db initialization)" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-10 pl-10 pr-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden"
                />
              </div>
              <select
                value={searchFilterType}
                onChange={(e) => setSearchFilterType(e.target.value)}
                className="h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md cursor-pointer focus:outline-hidden"
              >
                <option value="all">All Types</option>
                <option value="file">Files Only</option>
                <option value="class">Classes</option>
                <option value="function">Functions</option>
                <option value="api">REST APIs</option>
                <option value="model">DB Models</option>
              </select>
            </div>

            {/* Results Grid List */}
            {isSearchLoading ? (
              <div className="flex flex-col items-center justify-center py-12 gap-2 text-xs">
                <Loader2 className="h-6 w-6 text-[#a21caf] animate-spin" />
                <span className="text-muted-foreground">Running hybrid semantic ranking...</span>
              </div>
            ) : searchResults.length > 0 ? (
              <div className="space-y-4 select-text">
                {searchResults.map((result: any, idx: number) => (
                  <Card key={idx} className="p-4 flex flex-col justify-between hover:border-border/60 transition-all text-xs">
                    <div>
                      <div className="flex items-center justify-between mb-2 select-none">
                        <div className="flex items-center gap-2">
                          <span className={`px-1.5 py-0.5 rounded-xs text-[8px] font-bold border uppercase ${
                            result.type === 'file' ? 'bg-blue-500/10 border-blue-500/20 text-blue-400' :
                            result.type === 'class' ? 'bg-violet-500/10 border-violet-500/20 text-violet-400' :
                            result.type === 'function' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                            'bg-amber-500/10 border-amber-500/20 text-amber-400'
                          }`}>{result.type}</span>
                          <span className="text-[10px] text-zinc-500 font-mono truncate">{result.file_path}</span>
                        </div>
                        <Badge variant="outline" className="text-[10px]">
                          Score: {result.score}
                        </Badge>
                      </div>

                      <h4 className="font-bold text-sm text-white font-mono mb-2">{result.title}</h4>
                      <pre className="p-3 bg-secondary/35 border border-border/30 rounded-lg text-[10px] text-zinc-300 font-mono overflow-x-auto select-all max-h-[140px]">
                        {result.content_preview}
                      </pre>
                    </div>

                    <CardFooter className="p-0 pt-3 flex justify-end select-none">
                      <Button variant="outline" size="sm" onClick={() => handleSelectSearchResult(result)}>
                        Jump to Code Location
                      </Button>
                    </CardFooter>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 select-none text-zinc-500 italic text-xs">
                {searchQuery.length >= 3 ? "No semantic matches found." : "Type at least 3 characters to trigger semantic similarity search."}
              </div>
            )}

          </div>
        )}

        {/* AI ASSISTANT STREAMING CHAT TAB */}
        {activeTab === 'assistant' && (
          <RepositoryAIChat 
            repositoryId={repoId}
            onSelectFile={handleSelectSearchResult}
          />
        )}

        {/* DOCS & REPORTS GENERATOR EDITOR TAB */}
        {activeTab === 'documentation' && (
          <RepositoryDocumentationEditor repositoryId={repoId} />
        )}

        {/* QUALITY & SECURITY COMPLIANCE DASHBOARD */}
        {activeTab === 'quality' && (
          <RepositoryQualityDashboard repositoryId={repoId} />
        )}

        {/* ENTERPRISE ADMIN PANEL — API Keys, Webhooks, Orgs, Audit */}
        {activeTab === 'enterprise' && (
          <EnterpriseAdminDashboard repositoryId={repoId} />
        )}

        {/* ARCHITECTURE CANVAS (REACT FLOW) */}
        {activeTab === 'architecture' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center select-none">
              <div>
                <h3 className="text-lg font-bold text-white">Visual Architecture Graph</h3>
                <p className="text-xs text-muted-foreground">Interactive map of imports, inheritance class trees, methods calls, and API routing structures.</p>
              </div>
            </div>
            {isGraphLoading ? (
              <div className="flex flex-col items-center justify-center min-h-[400px] gap-2">
                <Loader2 className="h-8 w-8 text-[#a21caf] animate-spin" />
                <span className="text-sm text-muted-foreground">Compiling visual layout...</span>
              </div>
            ) : (
              <RepositoryGraphExplorer graphData={graphData} repositoryId={repoId} />
            )}
          </div>
        )}

        {/* FLOWS PANEL */}
        {activeTab === 'flows' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>REST Call Flow Tracer</CardTitle>
                <CardDescription>Traces request flows starting from API paths down to database ORM models.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 select-text text-xs">
                {isFlowsLoading ? (
                  <div className="flex justify-center p-8">
                    <Loader2 className="h-6 w-6 text-[#a21caf] animate-spin" />
                  </div>
                ) : flows.length > 0 ? (
                  flows.map((flow: any, idx: number) => (
                    <div key={idx} className="p-4 bg-secondary/15 border border-border/40 rounded-lg flex flex-col md:flex-row gap-4 justify-between items-stretch">
                      
                      {/* Left: Endpoint Details */}
                      <div className="flex-1 flex flex-col justify-center space-y-1.5 md:border-r md:border-border/40 md:pr-4">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-sm text-[9px] font-bold border ${
                            flow.method === 'GET' ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-400' : 'bg-blue-500/10 border-blue-500/25 text-blue-400'
                          }`}>{flow.method}</span>
                          <span className="font-bold text-sm text-white font-mono">{flow.route_path}</span>
                        </div>
                        <span className="text-[10px] text-zinc-400">Target controller: <span className="font-mono text-zinc-300">{flow.controller_name || '-'}</span></span>
                      </div>

                      {/* Right: Path Flow Visualization */}
                      <div className="flex-2 flex items-center gap-2 flex-wrap font-mono select-none">
                        <div className="px-2 py-1 bg-secondary border border-border/60 rounded text-[10px] text-zinc-300">Route</div>
                        <span className="text-violet-400">➔</span>
                        <div className="px-2 py-1 bg-violet-950/20 border border-violet-500/30 rounded text-[10px] text-violet-400 font-semibold truncate max-w-[120px]">
                          {flow.controller_name || 'Controller'}
                        </div>
                        <span className="text-violet-400">➔</span>
                        
                        {flow.database_models.length > 0 ? (
                          flow.database_models.map((m: any) => (
                            <div key={m.model_id} className="px-2 py-1 bg-orange-950/20 border border-orange-500/30 rounded text-[10px] text-orange-400 font-semibold">
                              {m.model_name} Model
                            </div>
                          ))
                        ) : (
                          <div className="px-2 py-1 bg-zinc-950/20 border border-zinc-800 rounded text-[10px] text-zinc-500 italic">No DB interactions</div>
                        )}
                      </div>

                    </div>
                  ))
                ) : (
                  <p className="text-zinc-500 italic text-center py-6">No API endpoint pathways mapped.</p>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* METRICS PANEL */}
        {activeTab === 'metrics' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Coupling & Cohesion Gauge Cards */}
            <Card className="flex flex-col justify-between">
              <CardHeader>
                <CardTitle>Architecture Scores</CardTitle>
                <CardDescription>Coupling and cohesion stats.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 pt-2">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-zinc-300">Package Coupling index</span>
                    <span className="text-white font-mono">{metrics.coupling}%</span>
                  </div>
                  <div className="w-full bg-secondary h-2.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-violet-600 h-full rounded-full"
                      style={{ width: `${metrics.coupling}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground block leading-normal">
                    Low coupling is optimal, indicating subsystems communicate through clean API boundaries.
                  </span>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-border/20">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-zinc-300">Package Cohesion index</span>
                    <span className="text-white font-mono">{metrics.cohesion}%</span>
                  </div>
                  <div className="w-full bg-secondary h-2.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#a21caf] h-full rounded-full"
                      style={{ width: `${metrics.cohesion}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground block leading-normal">
                    High cohesion represents clean, focused module properties executing related operations.
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Circular Dependencies Alerts */}
            <Card className="lg:col-span-2 select-text">
              <CardHeader>
                <CardTitle>Circular Dependency Chains</CardTitle>
                <CardDescription>Traced import loops that could cause loading exceptions.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-2 text-xs">
                {isMetricsLoading ? (
                  <div className="flex justify-center py-6">
                    <Loader2 className="h-5 w-5 text-[#a21caf] animate-spin" />
                  </div>
                ) : metrics.circular_dependencies && metrics.circular_dependencies.length > 0 ? (
                  metrics.circular_dependencies.map((loop: string[], idx: number) => (
                    <div key={idx} className="p-3 bg-rose-500/5 border border-rose-500/20 rounded-lg flex items-start gap-2.5 text-rose-400">
                      <ShieldAlert className="h-4.5 w-4.5 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-semibold text-xs text-rose-300 mb-1">Import Loop #{idx + 1}</h4>
                        <p className="font-mono leading-normal text-zinc-300">{loop.join(' ➔ ')}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center gap-2 p-3.5 bg-emerald-500/5 border border-emerald-500/20 text-emerald-400 rounded-lg select-none">
                    <CheckCircle className="h-4.5 w-4.5 shrink-0" />
                    <span className="text-xs font-semibold">Clean architecture! No circular loops detected.</span>
                  </div>
                )}
              </CardContent>
            </Card>

          </div>
        )}

        {/* STATISTICS VIEW */}
        {activeTab === 'statistics' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Numeric Indicators */}
            <Card className="lg:col-span-1 space-y-4">
              <CardHeader>
                <CardTitle>Indicators</CardTitle>
                <CardDescription>Codebase nodes counts.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm font-semibold">
                <div className="flex justify-between border-b border-border/20 pb-2">
                  <span className="text-zinc-400">Total Code Lines (LOC)</span>
                  <span className="text-white font-mono">{stats.loc || 0}</span>
                </div>
                <div className="flex justify-between border-b border-border/20 pb-2">
                  <span className="text-zinc-400">Folders Count</span>
                  <span className="text-white font-mono">{stats.folders_count || 0}</span>
                </div>
                <div className="flex justify-between border-b border-border/20 pb-2">
                  <span className="text-zinc-400">Files Count</span>
                  <span className="text-white font-mono">{stats.files_count || 0}</span>
                </div>
              </CardContent>
            </Card>

            {/* Recharts Pie Distributions Chart */}
            <Card className="lg:col-span-2 flex flex-col justify-between">
              <CardHeader>
                <CardTitle>Languages Sizes Composition</CardTitle>
                <CardDescription>Language sizes distribution chart (in KB).</CardDescription>
              </CardHeader>
              <CardContent className="h-[250px] w-full flex items-center justify-center">
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {chartData.map((_entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => `${value} KB`} />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-zinc-500 italic text-xs">No language size allocations resolved.</p>
                )}
              </CardContent>
            </Card>

          </div>
        )}

        {/* CONFIGURATION FILES */}
        {activeTab === 'configurations' && (
          <Card>
            <CardHeader>
              <CardTitle>Environment & Build Configurations</CardTitle>
              <CardDescription>Scanned build descriptors and integration files.</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Check if target files exist in codebase */}
              {filesTree.files.length > 0 ? (
                <div className="space-y-4">
                  {filesTree.files.filter((fi: any) => 
                    fi.name.includes("package.json") ||
                    fi.name.includes("Cargo.toml") ||
                    fi.name.includes("requirements.txt") ||
                    fi.name.includes("Dockerfile") ||
                    fi.name.includes("docker-compose") ||
                    fi.name.includes("pyproject.toml") ||
                    fi.name.includes("schema.prisma")
                  ).map((fi: any) => (
                    <div 
                      key={fi.id} 
                      className="p-3 bg-secondary/15 border border-border/40 hover:border-border/80 transition-all rounded-lg flex justify-between items-center cursor-pointer"
                      onClick={() => { setSelectedFileId(fi.id); setActiveTab('files'); }}
                    >
                      <div className="flex items-center gap-2">
                        <SettingsIcon className="h-4 w-4 text-violet-400" />
                        <div>
                          <span className="text-xs font-mono font-semibold text-white">{fi.name}</span>
                          <span className="text-[10px] text-muted-foreground block">{fi.path}</span>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-[9px]">
                        {(fi.size).toFixed(1)} KB
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-zinc-500 italic text-xs text-center py-6">No build or environment descriptors discovered.</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* ANALYSIS LOGS / JOB STATS */}
        {activeTab === 'logs' && (
          <Card className="max-w-xl">
            <CardHeader>
              <CardTitle>Static Analysis Engine Status</CardTitle>
              <CardDescription>Check status and logs of parsing pipelines.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {jobStatus ? (
                <div className="space-y-4">
                  {/* Status Indicator */}
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-semibold text-muted-foreground uppercase">Pipeline State</span>
                    <div className="flex items-center gap-1.5">
                      {jobStatus.status === 'completed' && <CheckCircle className="h-4 w-4 text-emerald-500" />}
                      {jobStatus.status === 'failed' && <XCircle className="h-4 w-4 text-rose-500" />}
                      {jobStatus.status === 'running' && <Loader2 className="h-4 w-4 text-amber-500 animate-spin" />}
                      <span className={`text-xs font-semibold capitalize ${
                        jobStatus.status === 'completed' ? 'text-emerald-400' :
                        jobStatus.status === 'failed' ? 'text-rose-400' : 'text-amber-400'
                      }`}>{jobStatus.status}</span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="space-y-1.5">
                    <div className="flex justify-between text-[11px] font-semibold text-zinc-400">
                      <span>Analysis progress</span>
                      <span>{jobStatus.progress}%</span>
                    </div>
                    <div className="w-full bg-secondary h-2.5 rounded-full overflow-hidden border border-border/40">
                      <div 
                        className="bg-[#a21caf] h-full rounded-full transition-all duration-300"
                        style={{ width: `${jobStatus.progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Errors display */}
                  {jobStatus.error_message && (
                    <div className="p-3.5 bg-rose-500/10 border border-rose-500/25 rounded-lg flex items-center gap-2 text-xs text-rose-400">
                      <ShieldAlert className="h-4 w-4 shrink-0" />
                      <span>{jobStatus.error_message}</span>
                    </div>
                  )}

                  {jobStatus.updated_at && (
                    <span className="text-[10px] text-zinc-500 block">
                      Last update: {new Date(jobStatus.updated_at).toLocaleString()}
                    </span>
                  )}
                </div>
              ) : (
                <p className="text-zinc-500 text-xs italic text-center py-6">No analysis logs recorded for this repository.</p>
              )}

            </CardContent>
            <CardFooter className="border-t border-border/40 pt-4 flex justify-between">
              <span className="text-[10px] text-muted-foreground max-w-[70%]">
                Statically crawls files, extracts imports syntax trees, and maps ORM relations.
              </span>
              <Button 
                onClick={() => triggerAnalyze.mutate()}
                loading={triggerAnalyze.isPending || (jobStatus && jobStatus.status === 'running')}
                size="sm"
              >
                <Play className="mr-1.5 h-3.5 w-3.5" /> Re-Analyze
              </Button>
            </CardFooter>
          </Card>
        )}

        {/* SETTINGS PREFERENCES PANEL */}
        {activeTab === 'settings' && (
          <Card className="max-w-2xl">
            <CardHeader>
              <CardTitle>Repository Preferences</CardTitle>
              <CardDescription>Update workspace parameters and auto pull sync rates.</CardDescription>
            </CardHeader>
            <form onSubmit={handleSettingsSubmit}>
              <CardContent className="space-y-6">
                
                {/* Repo Display Name */}
                <div className="space-y-1.5 text-left">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Repository Name</label>
                  <input 
                    type="text" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    className="w-full h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                  />
                </div>

                {/* Description */}
                <div className="space-y-1.5 text-left">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Description</label>
                  <textarea 
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                    className="w-full p-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf] resize-none"
                  />
                </div>

                {/* Tag categorizations */}
                <div className="space-y-1.5 text-left">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Tags</label>
                  <div className="relative">
                    <Tag className="absolute left-3 top-3 h-4.5 w-4.5 text-muted-foreground" />
                    <input 
                      type="text" 
                      placeholder="frontend, backend, utility (comma separated)" 
                      value={tagsInput}
                      onChange={(e) => setTagsInput(e.target.value)}
                      className="w-full h-10 pl-10 pr-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                    />
                  </div>
                </div>

                {/* Auto pull sync parameters */}
                <div className="space-y-4 pt-2 border-t border-border/40">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <span className="text-sm font-semibold text-white">Periodic Pull Sync</span>
                      <span className="text-xs text-muted-foreground block">Automatically pull branch commits periodically.</span>
                    </div>
                    <input 
                      type="checkbox" 
                      checked={isAutoSync}
                      onChange={(e) => setIsAutoSync(e.target.checked)}
                      className="w-4 h-4 rounded border-border text-[#a21caf] focus:ring-[#a21caf] cursor-pointer"
                    />
                  </div>

                  {isAutoSync && (
                    <div className="flex items-center gap-3">
                      <Clock className="h-4.5 w-4.5 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">Pull sync frequency:</span>
                      <select 
                        value={syncInterval}
                        onChange={(e) => setSyncInterval(parseInt(e.target.value))}
                        className="h-9 px-3 bg-secondary text-foreground text-xs border border-border rounded-md cursor-pointer focus:outline-hidden"
                      >
                        <option value="6">Every 6 Hours</option>
                        <option value="12">Every 12 Hours</option>
                        <option value="24">Daily (24 Hours)</option>
                        <option value="168">Weekly (7 Days)</option>
                      </select>
                    </div>
                  )}
                </div>

              </CardContent>
              <CardFooter className="border-t border-border/40 pt-4 flex justify-end">
                <Button type="submit" loading={updateRepo.isPending}>
                  <Save className="mr-1.5 h-4 w-4" /> Save Repository Configurations
                </Button>
              </CardFooter>
            </form>
          </Card>
        )}

      </div>

    </div>
  );
};

export default RepositoryDetail;
