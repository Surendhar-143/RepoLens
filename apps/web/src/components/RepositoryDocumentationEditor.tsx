import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { 
  FileText, 
  Sparkles, 
  Trash2, 
  Plus, 
  Save, 
  Download, 
  Activity, 
  ShieldCheck,
  LayoutTemplate
} from 'lucide-react';
import { api } from '../services/api.ts';
import { Button } from './ui/Button.tsx';
import { Card } from './ui/Card.tsx';
import { useUIStore } from '../stores/ui.ts';

interface RepositoryDocumentationEditorProps {
  repositoryId: string;
}

export const RepositoryDocumentationEditor: React.FC<RepositoryDocumentationEditorProps> = ({
  repositoryId
}) => {
  const { addNotification } = useUIStore();
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [selectedDocType, setSelectedDocType] = useState('README');

  // Query Docs List
  const { data: docs = [], refetch: refetchDocs } = useQuery({
    queryKey: ['documentation-list', repositoryId],
    queryFn: async () => {
      const response = await api.get(`/workspace/documentation?repository_id=${repositoryId}`);
      return response.data;
    }
  });

  // Query Engineering Reports List
  const { data: reports = [], refetch: refetchReports } = useQuery({
    queryKey: ['reports-list', repositoryId],
    queryFn: async () => {
      const response = await api.get(`/workspace/reports?repository_id=${repositoryId}`);
      return response.data;
    }
  });

  // Query Selected Doc detail
  const { data: activeDoc, refetch: refetchActiveDoc } = useQuery({
    queryKey: ['documentation-detail', activeDocId],
    queryFn: async () => {
      if (!activeDocId) return null;
      const response = await api.get(`/workspace/documentation/${activeDocId}`);
      setEditingContent(response.data.content);
      return response.data;
    },
    enabled: !!activeDocId
  });

  // Generate Doc mutation
  const generateDoc = useMutation({
    mutationFn: async (docType: string) => {
      const response = await api.post('/workspace/documentation/generate', {
        repository_id: repositoryId,
        doc_type: docType
      });
      return response.data;
    },
    onSuccess: (data) => {
      setShowGenerateModal(false);
      refetchDocs();
      setActiveDocId(data.id);
      addNotification('Documentation compiled successfully.', 'success');
    }
  });

  // Generate Report mutation
  const generateReport = useMutation({
    mutationFn: async (reportType: string) => {
      const response = await api.post('/workspace/reports/generate', {
        repository_id: repositoryId,
        report_type: reportType
      });
      return response.data;
    },
    onSuccess: () => {
      refetchReports();
      addNotification('Engineering health report compiled.', 'success');
    }
  });

  // Update Doc manual content edit mutation
  const updateDoc = useMutation({
    mutationFn: async () => {
      await api.patch(`/workspace/documentation/${activeDocId}`, {
        content: editingContent
      });
    },
    onSuccess: () => {
      refetchDocs();
      refetchActiveDoc();
      addNotification('Changes saved. Version incremented.', 'success');
    }
  });

  // Delete Doc mutation
  const deleteDoc = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/workspace/documentation/${id}`);
    },
    onSuccess: () => {
      if (activeDocId) setActiveDocId(null);
      refetchDocs();
    }
  });

  // Download raw markdown manual file
  const downloadMarkdown = () => {
    if (!activeDoc) return;
    const blob = new Blob([editingContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${activeDoc.title.toLowerCase().replace(/ /g, '_')}.md`;
    link.click();
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[550px] items-stretch select-none">
      
      {/* Sidebar files drawer */}
      <Card className="lg:col-span-1 bg-card/15 p-4 flex flex-col justify-between overflow-y-auto border-border/40 space-y-4">
        
        {/* Document section */}
        <div className="space-y-4">
          <div className="flex justify-between items-center border-b border-border/20 pb-2">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Guides & Manuals</h3>
            <Button variant="outline" size="icon" className="w-7 h-7" onClick={() => setShowGenerateModal(true)}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-1.5 text-xs">
            {docs.map((d: any) => (
              <div 
                key={d.id} 
                className={`group flex items-center justify-between p-2.5 rounded-lg cursor-pointer transition-all ${
                  activeDocId === d.id ? 'bg-[#a21caf]/15 text-[#f5d0fe]' : 'text-zinc-300 hover:bg-secondary/40'
                }`}
                onClick={() => setActiveDocId(d.id)}
              >
                <div className="flex items-center gap-1.5 truncate max-w-[80%]">
                  <FileText className="h-3.5 w-3.5 text-violet-400 shrink-0" />
                  <span className="truncate font-semibold">{d.title}</span>
                </div>
                <div className="flex items-center gap-1 select-none">
                  <span className="text-[8px] bg-zinc-900 border border-zinc-700 px-1 py-0.5 rounded-sm">v{d.version}</span>
                  <button 
                    onClick={(e) => { e.stopPropagation(); deleteDoc.mutate(d.id); }}
                    className="opacity-0 group-hover:opacity-100 hover:text-rose-400 p-0.5"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))}
            {docs.length === 0 && (
              <p className="text-[10px] text-zinc-500 italic py-2">No generated manuals.</p>
            )}
          </div>
        </div>

        {/* Reports section */}
        <div className="space-y-4 pt-4 border-t border-border/20">
          <div className="flex justify-between items-center border-b border-border/20 pb-2">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Telemetry Reports</h3>
            <Button variant="outline" size="icon" className="w-7 h-7" onClick={() => generateReport.mutate('health')}>
              <Activity className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-1.5 text-xs">
            {reports.map((r: any) => (
              <div 
                key={r.id} 
                className="flex items-center gap-2 p-2 bg-secondary/10 border border-border/30 rounded-lg"
              >
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
                <div className="truncate">
                  <span className="font-semibold text-zinc-300 block capitalize text-[10px]">{r.report_type} Scans</span>
                  <span className="text-[8px] text-zinc-500">{new Date(r.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
            {reports.length === 0 && (
              <p className="text-[10px] text-zinc-500 italic">No engineering reports compiled.</p>
            )}
          </div>
        </div>

      </Card>

      {/* Main split-pane content editor workspace */}
      <Card className="lg:col-span-3 flex flex-col justify-between overflow-hidden bg-card/25 border-border/40 relative">
        
        {activeDocId && activeDoc ? (
          <div className="flex flex-col h-full">
            
            {/* Top Toolbar */}
            <div className="flex justify-between items-center p-3 border-b border-border/40 bg-card/45 select-none">
              <div>
                <h4 className="font-bold text-xs text-white">{activeDoc.title}</h4>
                <p className="text-[9px] text-muted-foreground">Version {activeDoc.version} • Created on {new Date(activeDoc.created_at).toLocaleDateString()}</p>
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={downloadMarkdown} className="text-[10px] h-8 px-2.5">
                  <Download className="mr-1.5 h-3.5 w-3.5" /> Download MD
                </Button>
                <Button 
                  onClick={() => updateDoc.mutate()}
                  loading={updateDoc.isPending}
                  variant="primary"
                  size="sm"
                  className="text-[10px] h-8 px-2.5"
                >
                  <Save className="mr-1.5 h-3.5 w-3.5" /> Save Changes
                </Button>
              </div>
            </div>

            {/* Split pane editor views */}
            <div className="flex-1 min-h-0 grid grid-cols-2">
              
              {/* Textarea Editor */}
              <div className="border-r border-border/20 h-full p-3 select-text">
                <textarea
                  value={editingContent}
                  onChange={(e) => setEditingContent(e.target.value)}
                  className="w-full h-full bg-transparent text-xs text-zinc-300 font-mono focus:outline-hidden resize-none leading-relaxed"
                />
              </div>

              {/* Markdown HTML Render Preview */}
              <div className="h-full p-4 overflow-y-auto select-text bg-[#070514]/30 prose prose-invert max-w-none text-xs leading-relaxed space-y-4">
                {editingContent ? (
                  <div className="space-y-4 font-sans text-zinc-300">
                    {editingContent.split('\n\n').map((paragraph, pIdx) => {
                      if (paragraph.startsWith('# ')) {
                        return <h2 key={pIdx} className="text-base font-bold text-white border-b border-border/20 pb-2 mt-4">{paragraph.substring(2)}</h2>;
                      }
                      if (paragraph.startsWith('## ')) {
                        return <h3 key={pIdx} className="text-sm font-bold text-white mt-3">{paragraph.substring(3)}</h3>;
                      }
                      if (paragraph.startsWith('* ') || paragraph.startsWith('- ')) {
                        return (
                          <ul key={pIdx} className="list-disc pl-4 space-y-1 mt-2">
                            {paragraph.split('\n').map((li, liIdx) => (
                              <li key={liIdx}>{li.substring(2)}</li>
                            ))}
                          </ul>
                        );
                      }
                      if (paragraph.startsWith('```mermaid')) {
                        const diagram = paragraph.replace('```mermaid', '').replace('```', '').trim();
                        return (
                          <div key={pIdx} className="p-3 bg-violet-950/10 border border-violet-500/20 rounded-lg text-violet-400 font-mono text-[9px] whitespace-pre overflow-x-auto my-3">
                            <span className="text-[8px] font-bold text-violet-300 uppercase tracking-wider block mb-1">Visual Diagram Preview</span>
                            {diagram}
                          </div>
                        );
                      }
                      return <p key={pIdx} className="leading-relaxed">{paragraph}</p>;
                    })}
                  </div>
                ) : (
                  <p className="text-zinc-500 italic">No content written.</p>
                )}
              </div>

            </div>

          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 select-none">
            <LayoutTemplate className="h-10 w-10 text-zinc-500 mb-2" />
            <h4 className="font-semibold text-sm text-white">Documentation Workspace</h4>
            <p className="text-xs text-muted-foreground max-w-xs mt-1 mb-6">
              Create and manage architectural manuals, README guides, API endpoints lists, and local setup documentations.
            </p>
            <Button onClick={() => setShowGenerateModal(true)}>
              <Plus className="mr-1.5 h-4 w-4" /> Generate Document
            </Button>
          </div>
        )}

      </Card>

      {/* Generate Document Dialog Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs select-none">
          <div className="w-full max-w-sm bg-[#0b081a] border border-border/60 rounded-xl p-4 space-y-4">
            <h4 className="font-bold text-sm text-white flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-[#a21caf]" /> Compile Code Documentation
            </h4>
            
            <div className="space-y-1.5">
              <label className="text-[10px] font-bold text-muted-foreground uppercase">Manual Type</label>
              <select
                value={selectedDocType}
                onChange={(e) => setSelectedDocType(e.target.value)}
                className="w-full h-10 px-3 bg-secondary text-foreground text-xs border border-border rounded-lg cursor-pointer focus:outline-hidden"
              >
                <option value="README">README Improvements</option>
                <option value="architecture">Architecture Guide (Mermaid Maps)</option>
                <option value="api">REST API Reference Manual</option>
                <option value="database">Database ER Schema Manual</option>
                <option value="onboarding">Developer Onboarding Guide</option>
              </select>
            </div>

            <div className="flex justify-end gap-2 text-xs">
              <Button variant="outline" size="sm" onClick={() => setShowGenerateModal(false)}>
                Cancel
              </Button>
              <Button 
                onClick={() => generateDoc.mutate(selectedDocType)}
                loading={generateDoc.isPending}
                variant="primary"
                size="sm"
              >
                Compile view
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
