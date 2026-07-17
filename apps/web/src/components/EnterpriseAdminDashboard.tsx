import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Key,
  Webhook,
  Building2,
  ShieldCheck,
  Trash2,
  Plus,
  Copy,
  Check,
  Globe,
  Clock,
  AlertTriangle,
  Loader2,
  ChevronRight,
  Lock,
  Activity
} from 'lucide-react';
import { api } from '../services/api.ts';
import { Button } from './ui/Button.tsx';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from './ui/Card.tsx';
import { Badge } from './ui/Badge.tsx';
import { useUIStore } from '../stores/ui.ts';

interface EnterpriseAdminDashboardProps {
  repositoryId: string;
}

export const EnterpriseAdminDashboard: React.FC<EnterpriseAdminDashboardProps> = ({
  repositoryId
}) => {
  const { addNotification } = useUIStore();
  const [activeTab, setActiveTab] = useState<'organizations' | 'api-keys' | 'webhooks' | 'audit'>('api-keys');

  // — API Keys State —
  const [newKeyName, setNewKeyName] = useState('');
  const [freshToken, setFreshToken] = useState<string | null>(null);
  const [tokenCopied, setTokenCopied] = useState(false);
  const [showTokenModal, setShowTokenModal] = useState(false);

  // — Webhook State —
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookSecret, setWebhookSecret] = useState('');
  const [showWebhookForm, setShowWebhookForm] = useState(false);

  // — Org State —
  const [orgName, setOrgName] = useState('');
  const [showOrgForm, setShowOrgForm] = useState(false);

  // Queries
  const { data: apiKeys = [], refetch: refetchKeys } = useQuery({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const res = await api.get('/enterprise/api-keys');
      return res.data;
    }
  });

  const { data: webhooks = [], refetch: refetchWebhooks } = useQuery({
    queryKey: ['webhooks', repositoryId],
    queryFn: async () => {
      const res = await api.get(`/enterprise/webhooks?repository_id=${repositoryId}`);
      return res.data;
    }
  });

  const { data: organizations = [], refetch: refetchOrgs } = useQuery({
    queryKey: ['organizations'],
    queryFn: async () => {
      const res = await api.get('/enterprise/organizations');
      return res.data;
    },
    enabled: activeTab === 'organizations'
  });

  const { data: auditLogs = [], isLoading: isAuditLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      const res = await api.get('/enterprise/audit');
      return res.data;
    },
    enabled: activeTab === 'audit'
  });

  // Mutations
  const createApiKey = useMutation({
    mutationFn: async (name: string) => {
      const res = await api.post('/enterprise/api-keys', { name });
      return res.data;
    },
    onSuccess: (data: { token: string; id: string }) => {
      setFreshToken(data.token);
      setShowTokenModal(true);
      setNewKeyName('');
      refetchKeys();
      addNotification('API key generated. Save the token — it will not be shown again.', 'success');
    }
  });

  const revokeApiKey = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/enterprise/api-keys/${id}`);
    },
    onSuccess: () => {
      refetchKeys();
      addNotification('API key revoked successfully.', 'success');
    }
  });

  const registerWebhook = useMutation({
    mutationFn: async () => {
      const res = await api.post('/enterprise/webhooks', {
        repository_id: repositoryId,
        target_url: webhookUrl,
        secret_token: webhookSecret
      });
      return res.data;
    },
    onSuccess: () => {
      setWebhookUrl('');
      setWebhookSecret('');
      setShowWebhookForm(false);
      refetchWebhooks();
      addNotification('Webhook endpoint registered successfully.', 'success');
    }
  });

  const createOrganization = useMutation({
    mutationFn: async (name: string) => {
      const res = await api.post('/enterprise/organizations', { name });
      return res.data;
    },
    onSuccess: () => {
      setOrgName('');
      setShowOrgForm(false);
      refetchOrgs();
      addNotification('Organization created.', 'success');
    }
  });

  const handleCopyToken = () => {
    if (!freshToken) return;
    navigator.clipboard.writeText(freshToken);
    setTokenCopied(true);
    setTimeout(() => setTokenCopied(false), 2500);
  };

  // Audit action icon map
  const getActionIcon = (action: string) => {
    if (action.includes('api_key')) return <Key className="h-3.5 w-3.5 text-violet-400" />;
    if (action.includes('webhook')) return <Webhook className="h-3.5 w-3.5 text-blue-400" />;
    if (action.includes('organization')) return <Building2 className="h-3.5 w-3.5 text-emerald-400" />;
    return <Activity className="h-3.5 w-3.5 text-zinc-400" />;
  };

  const tabs = [
    { id: 'api-keys', label: 'API Keys', icon: Key, count: apiKeys.length },
    { id: 'webhooks', label: 'Webhooks', icon: Webhook, count: webhooks.length },
    { id: 'organizations', label: 'Organizations', icon: Building2, count: organizations.length },
    { id: 'audit', label: 'Audit Trail', icon: ShieldCheck, count: null }
  ];

  return (
    <div className="space-y-6 select-none">

      {/* Header metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <Card className="p-4 flex items-center gap-3 bg-[#0b081a]">
          <div className="h-9 w-9 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center shrink-0">
            <Key className="h-4.5 w-4.5 text-violet-400" />
          </div>
          <div>
            <p className="text-muted-foreground text-[10px] font-semibold uppercase">API Keys</p>
            <p className="text-xl font-bold text-white font-display">{apiKeys.length}</p>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-3 bg-[#0b081a]">
          <div className="h-9 w-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
            <Webhook className="h-4.5 w-4.5 text-blue-400" />
          </div>
          <div>
            <p className="text-muted-foreground text-[10px] font-semibold uppercase">Webhooks</p>
            <p className="text-xl font-bold text-white font-display">{webhooks.length}</p>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-3 bg-[#0b081a]">
          <div className="h-9 w-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
            <Building2 className="h-4.5 w-4.5 text-emerald-400" />
          </div>
          <div>
            <p className="text-muted-foreground text-[10px] font-semibold uppercase">Organizations</p>
            <p className="text-xl font-bold text-white font-display">{organizations.length}</p>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-3 bg-[#0b081a]">
          <div className="h-9 w-9 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
            <ShieldCheck className="h-4.5 w-4.5 text-amber-400" />
          </div>
          <div>
            <p className="text-muted-foreground text-[10px] font-semibold uppercase">Audit Events</p>
            <p className="text-xl font-bold text-white font-display">{auditLogs.length}</p>
          </div>
        </Card>
      </div>

      {/* Tab bar */}
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
              <Icon className="h-3.5 w-3.5 shrink-0" />
              <span>{tab.label}</span>
              {tab.count !== null && tab.count > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full text-[9px] bg-secondary border border-border/40 font-bold">
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* — API KEYS PANEL — */}
      {activeTab === 'api-keys' && (
        <div className="space-y-4">
          {/* Create form */}
          <Card className="p-4 border-border/40">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex-1 min-w-[200px]">
                <input
                  type="text"
                  placeholder="Token display name (e.g. CI Pipeline Key)"
                  value={newKeyName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewKeyName(e.target.value)}
                  className="w-full h-9 px-3 bg-secondary text-foreground text-xs border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                />
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={() => newKeyName.trim() && createApiKey.mutate(newKeyName.trim())}
                loading={createApiKey.isPending}
                disabled={!newKeyName.trim()}
              >
                <Plus className="mr-1.5 h-3.5 w-3.5" /> Generate Token
              </Button>
            </div>
          </Card>

          {/* Keys table */}
          {apiKeys.length > 0 ? (
            <div className="space-y-2 select-text">
              {apiKeys.map((k: any) => (
                <Card key={k.id} className="p-3.5 flex items-center justify-between hover:border-border/60 transition-all border-border/40 text-xs">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-md bg-violet-500/10 border border-violet-500/20 flex items-center justify-center shrink-0">
                      <Key className="h-3.5 w-3.5 text-violet-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-white">{k.name}</p>
                      <p className="text-[9px] text-muted-foreground">
                        <Clock className="inline h-2.5 w-2.5 mr-0.5" />
                        Created {new Date(k.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 select-none">
                    <Badge variant="outline" className="text-[9px] text-emerald-400 border-emerald-500/20">Active</Badge>
                    <button
                      onClick={() => revokeApiKey.mutate(k.id)}
                      className="text-zinc-600 hover:text-rose-400 transition-colors cursor-pointer p-1"
                      title="Revoke key"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-10 text-zinc-500 text-xs italic">
              No API tokens generated. Create one to authenticate the CLI or VS Code extension.
            </div>
          )}
        </div>
      )}

      {/* — WEBHOOKS PANEL — */}
      {activeTab === 'webhooks' && (
        <div className="space-y-4">
          {/* Register form */}
          {showWebhookForm ? (
            <Card className="p-4 border-border/40 space-y-3">
              <h4 className="text-xs font-bold text-white">Register Outbound Webhook</h4>
              <input
                type="url"
                placeholder="Target URL (e.g. https://api.yourplatform.com/hooks)"
                value={webhookUrl}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWebhookUrl(e.target.value)}
                className="w-full h-9 px-3 bg-secondary text-foreground text-xs border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
              />
              <input
                type="text"
                placeholder="HMAC signing secret"
                value={webhookSecret}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWebhookSecret(e.target.value)}
                className="w-full h-9 px-3 bg-secondary text-foreground text-xs border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf] font-mono"
              />
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={() => setShowWebhookForm(false)}>Cancel</Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => registerWebhook.mutate()}
                  loading={registerWebhook.isPending}
                  disabled={!webhookUrl.trim() || !webhookSecret.trim()}
                >
                  Register Endpoint
                </Button>
              </div>
            </Card>
          ) : (
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setShowWebhookForm(true)}>
                <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Webhook
              </Button>
            </div>
          )}

          {/* Webhook list */}
          {webhooks.length > 0 ? (
            <div className="space-y-2 text-xs select-text">
              {webhooks.map((wh: any) => (
                <Card key={wh.id} className="p-3.5 flex items-center justify-between hover:border-border/60 transition-all border-border/40">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-md bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                      <Globe className="h-3.5 w-3.5 text-blue-400" />
                    </div>
                    <div>
                      <p className="font-mono font-semibold text-white truncate max-w-[280px]">{wh.target_url}</p>
                      <p className="text-[9px] text-muted-foreground">
                        Registered {new Date(wh.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={wh.is_active
                      ? 'text-emerald-400 border-emerald-500/20 text-[9px]'
                      : 'text-zinc-500 border-zinc-700 text-[9px]'}
                  >
                    {wh.is_active ? 'Active' : 'Disabled'}
                  </Badge>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-10 text-zinc-500 text-xs italic">
              No webhook endpoints configured. Add one to receive signed event payloads.
            </div>
          )}
        </div>
      )}

      {/* — ORGANIZATIONS PANEL — */}
      {activeTab === 'organizations' && (
        <div className="space-y-4">
          {showOrgForm ? (
            <Card className="p-4 border-border/40 space-y-3">
              <h4 className="text-xs font-bold text-white">Create Organization</h4>
              <input
                type="text"
                placeholder="Organization name (e.g. Acme Engineering)"
                value={orgName}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOrgName(e.target.value)}
                className="w-full h-9 px-3 bg-secondary text-foreground text-xs border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
              />
              <div className="flex gap-2 justify-end">
                <Button variant="outline" size="sm" onClick={() => setShowOrgForm(false)}>Cancel</Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => createOrganization.mutate(orgName.trim())}
                  loading={createOrganization.isPending}
                  disabled={!orgName.trim()}
                >
                  Create Organization
                </Button>
              </div>
            </Card>
          ) : (
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setShowOrgForm(true)}>
                <Plus className="mr-1.5 h-3.5 w-3.5" /> New Organization
              </Button>
            </div>
          )}

          {organizations.length > 0 ? (
            <div className="space-y-2 text-xs">
              {organizations.map((org: any) => (
                <Card key={org.id} className="p-3.5 flex items-center justify-between hover:border-border/60 transition-all border-border/40">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0 text-base font-black text-emerald-400">
                      {org.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-semibold text-white">{org.name}</p>
                      <p className="text-[9px] text-muted-foreground">
                        Created {new Date(org.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[9px]">Owner</Badge>
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-10 text-zinc-500 text-xs italic">
              No organizations created. Teams and multi-tenant access begin here.
            </div>
          )}
        </div>
      )}

      {/* — AUDIT TRAIL LOGS — */}
      {activeTab === 'audit' && (
        <Card>
          <CardHeader className="border-b border-border/40">
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-amber-400" />
              Security Compliance Audit Trail
            </CardTitle>
            <CardDescription>All security-relevant actions are recorded here for compliance and investigation.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {isAuditLoading ? (
              <div className="flex justify-center p-10">
                <Loader2 className="h-5 w-5 text-[#a21caf] animate-spin" />
              </div>
            ) : auditLogs.length > 0 ? (
              <div className="divide-y divide-border/20 select-text">
                {auditLogs.map((log: any, idx: number) => (
                  <div key={log.id || idx} className="flex items-start gap-3 px-4 py-3 hover:bg-white/[0.01] transition-colors">
                    <div className="mt-0.5 h-6 w-6 rounded-md bg-secondary border border-border/40 flex items-center justify-center shrink-0">
                      {getActionIcon(log.action)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-0.5">
                        <span className="text-xs font-semibold text-white font-mono">{log.action}</span>
                        <span className="text-[9px] text-zinc-500 whitespace-nowrap">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>
                      {log.metadata && Object.keys(log.metadata).length > 0 && (
                        <pre className="text-[9px] text-zinc-400 font-mono leading-relaxed overflow-x-auto">
                          {JSON.stringify(log.metadata, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-10 text-center text-zinc-500 text-xs italic">
                No audit events recorded yet.
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* — FRESH TOKEN MODAL — */}
      {showTokenModal && freshToken && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md bg-[#0b081a] border border-amber-500/30 rounded-xl p-5 space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
              <h4 className="font-bold text-sm text-white">Save Your API Token Now</h4>
            </div>
            <p className="text-[10px] text-amber-300/80 leading-relaxed bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
              This token will <strong>not</strong> be shown again after you close this dialog. Copy it to a secure location before continuing.
            </p>
            <div className="flex items-center gap-2 p-3 bg-secondary border border-border/50 rounded-lg font-mono text-xs select-all break-all">
              <Lock className="h-3.5 w-3.5 text-violet-400 shrink-0" />
              <span className="flex-1 text-[#f5d0fe]">{freshToken}</span>
            </div>
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyToken}
                className={tokenCopied ? 'border-emerald-500/40 text-emerald-400' : ''}
              >
                {tokenCopied
                  ? <><Check className="mr-1.5 h-3.5 w-3.5" /> Copied!</>
                  : <><Copy className="mr-1.5 h-3.5 w-3.5" /> Copy Token</>
                }
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => { setShowTokenModal(false); setFreshToken(null); }}
              >
                I've saved it — Close
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
