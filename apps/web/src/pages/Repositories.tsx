import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Github, 
  Upload, 
  Search, 
  Trash2, 
  RefreshCw, 
  Eye,
  HelpCircle,
  FileCode
} from 'lucide-react';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card.tsx';
import { Badge } from '../components/ui/Badge.tsx';
import { useUIStore } from '../stores/ui.ts';
import { api } from '../services/api.ts';
import RepositoryDetail from './RepositoryDetail.tsx';

const Repositories: React.FC = () => {
  const queryClient = useQueryClient();
  const { addNotification } = useUIStore();
  
  // UI states
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [visibility, setVisibility] = useState('all');
  const [method, setMethod] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  
  // Dialog visibility states
  const [isGitHubOpen, setIsGitHubOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [cloneUrl, setCloneUrl] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Fetch repositories
  const { data: repos = [] } = useQuery({
    queryKey: ['repositories', search, visibility, method, sortBy],
    queryFn: async () => {
      let url = `/repositories?sort_by=${sortBy}`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      if (visibility !== 'all') url += `&visibility=${visibility}`;
      if (method !== 'all') url += `&import_method=${method}`;
      
      const response = await api.get(url);
      return response.data;
    }
  });

  // Mutations
  const importGitHub = useMutation({
    mutationFn: async (url: string) => {
      const response = await api.post('/repositories/github', { clone_url: url });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
      addNotification('Repository import initiated successfully!', 'success');
      setIsGitHubOpen(false);
      setCloneUrl('');
    },
    onError: (err: any) => {
      const msg = err.error?.message || 'Failed to import repository.';
      addNotification(msg, 'error');
    }
  });

  const uploadZip = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post('/repositories/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
      addNotification('Repository ZIP uploaded successfully!', 'success');
      setIsUploadOpen(false);
      setUploadFile(null);
    },
    onError: (err: any) => {
      const msg = err.error?.message || 'Failed to upload ZIP archive.';
      addNotification(msg, 'error');
    }
  });

  const deleteRepo = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/repositories/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
      addNotification('Repository deleted successfully.', 'success');
      if (selectedRepoId) setSelectedRepoId(null);
    }
  });

  const refreshRepo = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/repositories/${id}/refresh`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
      addNotification('Repository refresh job enqueued.', 'success');
    }
  });

  const handleGitHubSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cloneUrl) return;
    importGitHub.mutate(cloneUrl);
  };

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    uploadZip.mutate(uploadFile);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setUploadFile(e.target.files[0]);
    }
  };

  // If a repo is selected, render detail subpage
  if (selectedRepoId) {
    return (
      <RepositoryDetail 
        repoId={selectedRepoId} 
        onBack={() => setSelectedRepoId(null)} 
      />
    );
  }

  return (
    <div className="space-y-6 select-none relative">
      
      {/* Title & Import trigger actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold font-display tracking-tight text-white">Repository Explorer</h2>
          <p className="text-muted-foreground text-sm">Analyze and manage your workspace code repositories.</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setIsGitHubOpen(true)}>
            <Github className="mr-2 h-4.5 w-4.5" /> Clone Repo
          </Button>
          <Button variant="secondary" onClick={() => setIsUploadOpen(true)}>
            <Upload className="mr-2 h-4.5 w-4.5" /> Upload ZIP
          </Button>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col md:flex-row gap-4 items-center bg-card/25 p-4 rounded-xl border border-border/40 backdrop-blur-xs">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="Search repositories..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-10 pl-9 pr-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
          />
        </div>
        
        <div className="flex flex-wrap gap-3 w-full md:w-auto items-center">
          {/* Visibility filter */}
          <select 
            value={visibility} 
            onChange={(e) => setVisibility(e.target.value)}
            className="h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md cursor-pointer focus:outline-hidden"
          >
            <option value="all">All Visibility</option>
            <option value="public">Public</option>
            <option value="private">Private</option>
          </select>

          {/* Import method filter */}
          <select 
            value={method} 
            onChange={(e) => setMethod(e.target.value)}
            className="h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md cursor-pointer focus:outline-hidden"
          >
            <option value="all">All Sources</option>
            <option value="github">GitHub Clones</option>
            <option value="upload">Local Uploads</option>
          </select>

          {/* Sort order */}
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md cursor-pointer focus:outline-hidden"
          >
            <option value="recent">Recently Imported</option>
            <option value="name">Name</option>
            <option value="updated">Last Updated</option>
          </select>
        </div>
      </div>

      {/* Grid List View */}
      {repos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {repos.map((repo: any) => (
            <Card key={repo.id} className="flex flex-col justify-between border-border/40 hover:border-border/80 transition-all duration-300">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <Badge variant={repo.visibility === 'private' ? 'secondary' : 'outline'}>
                    {repo.visibility}
                  </Badge>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                    repo.import_status === 'completed' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                    repo.import_status === 'failed' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' :
                    'bg-amber-500/10 border-amber-500/20 text-amber-400 animate-pulse'
                  }`}>
                    {repo.import_status || 'Ready'}
                  </span>
                </div>
                <CardTitle className="truncate text-base">{repo.owner}/{repo.name}</CardTitle>
                <CardDescription className="line-clamp-2 min-h-[40px] text-xs mt-1 text-zinc-400 leading-normal">
                  {repo.description || 'No description provided.'}
                </CardDescription>
              </CardHeader>
              
              <CardContent className="py-2 text-xs text-muted-foreground space-y-2">
                {/* Languages display */}
                {repo.languages && Object.keys(repo.languages).length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {Object.entries(repo.languages).slice(0, 3).map(([lang, pct]: any) => (
                      <span key={lang} className="px-1.5 py-0.5 bg-secondary/80 text-foreground border border-border/30 rounded-md text-[10px]">
                        {lang} ({pct}%)
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-zinc-500 italic text-[10px]">No languages scanned</div>
                )}
                
                <div className="flex justify-between items-center text-[10px] pt-1 text-zinc-500">
                  <span>Method: {repo.import_method === 'github' ? 'GitHub' : 'Local ZIP'}</span>
                  <span>Size: {(repo.size / 1024).toFixed(1)} MB</span>
                </div>
              </CardContent>

              <CardFooter className="pt-3 border-t border-border/40 mt-3 flex justify-between gap-2">
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => setSelectedRepoId(repo.id)}
                  className="flex-1"
                >
                  <Eye className="mr-1.5 h-3.5 w-3.5" /> View
                </Button>
                
                <Button 
                  size="sm" 
                  variant="ghost" 
                  onClick={() => refreshRepo.mutate(repo.id)}
                  title="Pull / Sync"
                  className="h-8 w-8 p-0"
                  disabled={repo.import_status === 'running'}
                >
                  <RefreshCw className={`h-3.5 w-3.5 text-zinc-400 ${repo.import_status === 'running' ? 'animate-spin' : ''}`} />
                </Button>

                <Button 
                  size="sm" 
                  variant="ghost" 
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this repository? This cannot be undone.')) {
                      deleteRepo.mutate(repo.id);
                    }
                  }}
                  title="Delete"
                  className="h-8 w-8 p-0 hover:bg-rose-500/10 hover:text-rose-400"
                >
                  <Trash2 className="h-3.5 w-3.5 text-rose-500" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <div className="w-full flex items-center justify-center min-h-[300px] border border-dashed border-border rounded-xl p-8 text-center bg-card/10 select-none">
          <div className="flex flex-col items-center justify-center space-y-4 max-w-sm">
            <div className="p-3 bg-violet-600/10 border border-violet-600/20 text-violet-400 rounded-full">
              <HelpCircle className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold tracking-tight text-white font-display">No repositories indexed</h3>
            <p className="text-xs text-muted-foreground">
              You haven't linked any repositories to this workspace workspace yet. Connect a GitHub repository or drag-and-drop a ZIP to construct codebase graphs.
            </p>
          </div>
        </div>
      )}

      {/* GitHub Import Dialog Dialog */}
      {isGitHubOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fade-in">
          <Card className="max-w-md w-full border-border/60">
            <CardHeader>
              <CardTitle>Clone GitHub Repository</CardTitle>
              <CardDescription>Enter the HTTPS clone URL of any public repository.</CardDescription>
            </CardHeader>
            <form onSubmit={handleGitHubSubmit}>
              <CardContent className="space-y-4">
                <div className="space-y-1.5 text-left">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Clone HTTPS URL</label>
                  <input 
                    type="text" 
                    placeholder="https://github.com/owner/repository.git" 
                    value={cloneUrl}
                    onChange={(e) => setCloneUrl(e.target.value)}
                    required
                    className="w-full h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2 border-t border-border/40 pt-4">
                <Button variant="ghost" type="button" onClick={() => { setIsGitHubOpen(false); setCloneUrl(''); }}>
                  Cancel
                </Button>
                <Button type="submit" loading={importGitHub.isPending}>
                  Import Repository
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}

      {/* Local ZIP Upload Dialog Dialog */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fade-in">
          <Card className="max-w-md w-full border-border/60">
            <CardHeader>
              <CardTitle>Upload Codebase ZIP</CardTitle>
              <CardDescription>Upload a local folder compressed into a ZIP archive.</CardDescription>
            </CardHeader>
            <form onSubmit={handleUploadSubmit}>
              <CardContent className="space-y-4 text-center">
                <div className="border border-dashed border-border rounded-lg p-8 flex flex-col items-center justify-center gap-3 bg-secondary/20">
                  <FileCode className="h-10 w-10 text-zinc-500" />
                  <input 
                    type="file" 
                    accept=".zip"
                    onChange={handleFileChange}
                    required
                    id="zip-uploader"
                    className="hidden"
                  />
                  <label htmlFor="zip-uploader" className="cursor-pointer text-sm font-semibold text-violet-400 hover:underline">
                    {uploadFile ? uploadFile.name : "Select ZIP file from disk"}
                  </label>
                  <span className="text-[10px] text-muted-foreground">Supports files up to 50MB</span>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end gap-2 border-t border-border/40 pt-4">
                <Button variant="ghost" type="button" onClick={() => { setIsUploadOpen(false); setUploadFile(null); }}>
                  Cancel
                </Button>
                <Button type="submit" loading={uploadZip.isPending} disabled={!uploadFile}>
                  Upload & Extract
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>
      )}

    </div>
  );
};

export default Repositories;
