import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { 
  ShieldAlert, 
  Settings, 
  Hourglass, 
  ToggleLeft, 
  ToggleRight, 
  Play, 
  Loader2
} from 'lucide-react';
import { api } from '../services/api.ts';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from './ui/Card.tsx';
import { Badge } from './ui/Badge.tsx';
import { useUIStore } from '../stores/ui.ts';

interface RepositoryQualityDashboardProps {
  repositoryId: string;
}

export const RepositoryQualityDashboard: React.FC<RepositoryQualityDashboardProps> = ({
  repositoryId
}) => {
  const { addNotification } = useUIStore();
  const [activeTab, setActiveTab] = useState<'findings' | 'rules' | 'debt'>('findings');
  const [severityFilter, setSeverityFilter] = useState('all');

  // Query Quality Findings list
  const { data: findings = [], refetch: refetchFindings, isLoading: isFindingsLoading } = useQuery({
    queryKey: ['quality-findings', repositoryId, severityFilter],
    queryFn: async () => {
      let url = `/quality/findings?repository_id=${repositoryId}`;
      if (severityFilter !== 'all') url += `&severity=${severityFilter}`;
      const response = await api.get(url);
      return response.data;
    }
  });

  // Query Active Rules List
  const { data: rules = [], refetch: refetchRules } = useQuery({
    queryKey: ['quality-rules'],
    queryFn: async () => {
      const response = await api.get('/quality/rules');
      return response.data;
    }
  });

  // Query Technical Debt metrics
  const { data: debt = { estimated_debt_remediation_hours: 0, initiatives: [] }, refetch: refetchDebt } = useQuery({
    queryKey: ['technical-debt', repositoryId],
    queryFn: async () => {
      const response = await api.post('/quality/reports/engineering', {
        repository_id: repositoryId
      });
      return response.data;
    }
  });

  // Run codebase scanners
  const triggerScan = useMutation({
    mutationFn: async () => {
      const response = await api.post('/quality/analyze', {
        repository_id: repositoryId
      });
      return response.data;
    },
    onSuccess: () => {
      refetchFindings();
      refetchDebt();
      addNotification('Repository quality scan completed.', 'success');
    }
  });

  // Rule settings toggle mutation
  const toggleRule = useMutation({
    mutationFn: async ({ id, isEnabled }: { id: string; isEnabled: boolean }) => {
      await api.patch(`/quality/rules/${id}`, {
        is_enabled: isEnabled
      });
    },
    onSuccess: () => {
      refetchRules();
      addNotification('Rule configuration updated.', 'success');
    }
  });

  // Simple math for health rating (derived from active findings count)
  const criticalCount = findings.filter((f: any) => f.severity === 'critical').length;
  const warningCount = findings.filter((f: any) => f.severity === 'warning').length;
  
  const qualityScore = Math.max(100 - warningCount * 5, 40);
  const securityScore = Math.max(100 - criticalCount * 20, 20);
  const overallScore = Math.round((qualityScore + securityScore) / 2);

  return (
    <div className="space-y-6 select-none">
      
      {/* Metrics Row Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-semibold">
        
        {/* Overall Health Card */}
        <Card className="flex flex-col justify-between p-4 bg-[#0b081a]">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Overall Health Score</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-display text-white">{overallScore}%</span>
              <span className={`text-[10px] ${overallScore > 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {overallScore > 80 ? 'Excellent' : 'Needs attention'}
              </span>
            </div>
          </div>
          <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden mt-3">
            <div className="bg-[#a21caf] h-full rounded-full" style={{ width: `${overallScore}%` }} />
          </div>
        </Card>

        {/* Security Rating Card */}
        <Card className="flex flex-col justify-between p-4 bg-[#0b081a]">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Security Score</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-display text-white">{securityScore}%</span>
              <span className="text-[10px] text-rose-400">{criticalCount} Critical Risks</span>
            </div>
          </div>
          <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden mt-3">
            <div className="bg-rose-500 h-full rounded-full" style={{ width: `${securityScore}%` }} />
          </div>
        </Card>

        {/* Maintainability Card */}
        <Card className="flex flex-col justify-between p-4 bg-[#0b081a]">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Code Smells Score</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-display text-white">{qualityScore}%</span>
              <span className="text-[10px] text-amber-400">{warningCount} Warnings</span>
            </div>
          </div>
          <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden mt-3">
            <div className="bg-amber-500 h-full rounded-full" style={{ width: `${qualityScore}%` }} />
          </div>
        </Card>

        {/* Technical Debt Card */}
        <Card className="flex flex-col justify-between p-4 bg-[#0b081a]">
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">Remediation Effort</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold font-display text-white">{debt.estimated_debt_remediation_hours} hrs</span>
              <span className="text-[10px] text-violet-400 block">Total Tech Debt</span>
            </div>
          </div>
          <div className="flex justify-between text-[9px] text-zinc-500 mt-3 select-none">
            <span>Scan updates: Daily</span>
            <button onClick={() => triggerScan.mutate()} className="text-[#a21caf] hover:underline flex items-center gap-1">
              <Play className="h-3 w-3" /> Rescan Now
            </button>
          </div>
        </Card>

      </div>

      {/* Tabs navigation panel */}
      <div className="flex border-b border-border/40 gap-1 overflow-x-auto pb-px select-none">
        {[
          { id: 'findings', name: 'Open Findings Center', icon: ShieldAlert },
          { id: 'debt', name: 'Remediation Board', icon: Hourglass },
          { id: 'rules', name: 'Code Quality Rules Settings', icon: Settings }
        ].map((tab) => {
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

      {/* Viewport Panels */}
      <div className="pt-2">
        
        {/* FINDINGS CENTER TABLE */}
        {activeTab === 'findings' && (
          <div className="space-y-4">
            
            {/* Toolbar filter */}
            <div className="flex justify-between items-center bg-card/25 p-3 rounded-lg border border-border/40 select-none">
              <span className="text-xs text-muted-foreground font-semibold">Active Code Smells</span>
              
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="h-8 px-2.5 bg-secondary text-foreground text-xs border border-border rounded-md cursor-pointer focus:outline-hidden"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical Risks</option>
                <option value="warning">Warnings</option>
                <option value="info">Info warnings</option>
              </select>
            </div>

            {/* List */}
            {isFindingsLoading ? (
              <div className="flex justify-center p-8">
                <Loader2 className="h-6 w-6 text-[#a21caf] animate-spin" />
              </div>
            ) : findings.length > 0 ? (
              <div className="space-y-3 select-text text-xs">
                {findings.map((f: any) => (
                  <Card key={f.id} className="p-4 flex flex-col justify-between hover:border-border/60 transition-all border-border/40">
                    <div className="flex justify-between items-start mb-2 select-none">
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.5 rounded-xs text-[8px] font-bold border uppercase ${
                          f.severity === 'critical' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' :
                          f.severity === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
                          'bg-zinc-500/10 border-zinc-700 text-zinc-400'
                        }`}>{f.severity}</span>
                        <Badge variant="outline" className="text-[8px] uppercase">{f.category}</Badge>
                      </div>
                      <span className="text-[10px] text-zinc-500 font-mono">Status: {f.status}</span>
                    </div>

                    <h4 className="font-bold text-sm text-white mb-1.5">{f.title}</h4>
                    <p className="text-zinc-300 leading-relaxed mb-3">{f.description}</p>
                    
                    {f.evidence && (
                      <pre className="p-2.5 bg-secondary/35 border border-border/30 rounded text-[9px] text-zinc-400 font-mono overflow-x-auto">
                        Evidence: {JSON.stringify(f.evidence)}
                      </pre>
                    )}
                  </Card>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-zinc-500 italic select-none">
                No active codebase warnings detected. Clean repository!
              </div>
            )}

          </div>
        )}

        {/* TECHNICAL DEBT BOARD */}
        {activeTab === 'debt' && (
          <Card>
            <CardHeader>
              <CardTitle>Technical Debt initiatives & Remediation Board</CardTitle>
              <CardDescription>Estimated metrics to refactor smells and resolve warnings.</CardDescription>
            </CardHeader>
            <CardContent>
              {debt.initiatives.length > 0 ? (
                <div className="space-y-3 text-xs select-text">
                  {debt.initiatives.map((ini: any, idx: number) => (
                    <div key={idx} className="p-3 bg-secondary/15 border border-border/40 hover:border-border/60 transition-all rounded-lg flex justify-between items-center">
                      <div>
                        <span className="font-semibold text-white block mb-0.5">{ini.title}</span>
                        <span className="text-[9px] text-zinc-500 font-mono">Remediation priority: {ini.priority}</span>
                      </div>
                      <Badge variant="outline" className="text-violet-400 border-violet-500/20 bg-violet-950/15">
                        {ini.remediation_hours} Hours
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-zinc-500 italic py-6 text-center select-none">No initiatives scoped.</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* ACTIVE RULES SETTINGS PANEL */}
        {activeTab === 'rules' && (
          <Card className="max-w-xl">
            <CardHeader>
              <CardTitle>Organizational Code Rules Manager</CardTitle>
              <CardDescription>Enable or disable static rules checkers and verify thresholds.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-xs select-none">
              {rules.map((rule: any) => (
                <div key={rule.id} className="flex justify-between items-center p-3 bg-secondary/15 border border-border/40 rounded-lg">
                  <div>
                    <span className="font-bold text-white block font-mono text-[11px] mb-0.5">{rule.name}</span>
                    <span className="text-[9px] text-zinc-500 uppercase tracking-wider">{rule.category} • Severity: {rule.severity}</span>
                  </div>
                  <button 
                    onClick={() => toggleRule.mutate({ id: rule.id, isEnabled: !rule.is_enabled })}
                    className="p-1 hover:text-white transition-all cursor-pointer text-[#a21caf]"
                  >
                    {rule.is_enabled ? <ToggleRight className="h-8 w-8 text-[#a21caf]" /> : <ToggleLeft className="h-8 w-8 text-zinc-600" />}
                  </button>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

      </div>

    </div>
  );
};
