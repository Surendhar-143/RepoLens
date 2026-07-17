import React from 'react';
import { useNavigate } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { 
  GitBranch, 
  Search, 
  Network, 
  ArrowRight,
  Cpu,
  FileCode,
  Github
} from 'lucide-react';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card.tsx';
import { useAuthStore } from '../stores/auth.ts';
import { api } from '../services/api.ts';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // Query repositories from backend
  const { data: repos = [] } = useQuery({
    queryKey: ['repositories'],
    queryFn: async () => {
      const response = await api.get('/repositories');
      return response.data;
    }
  });

  // Calculate dynamic metrics
  const repoCount = repos.length;
  const totalSize = repos.reduce((acc: number, curr: any) => acc + (curr.size || 0), 0);
  const githubConnected = !!user?.github_username;
  
  // Format sizing (KB to MB/GB)
  const formatSize = (kb: number) => {
    if (kb < 1024) return `${kb} KB`;
    const mb = kb / 1024;
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    return `${(mb / 1024).toFixed(1)} GB`;
  };

  const metrics = [
    { name: 'Workspace Repositories', value: repoCount.toString(), desc: 'Index repositories', icon: GitBranch },
    { name: 'Workspace Size', value: formatSize(totalSize), desc: 'Disk cache utilization', icon: FileCode },
    { name: 'GitHub Integration', value: githubConnected ? 'Connected' : 'Offline', desc: user?.github_username || 'Link account in Settings', icon: Github },
    { name: 'AI Reasoning Threads', value: '0', desc: 'Awaiting Phase 2 indexing', icon: Cpu }
  ];

  const quickActions = [
    {
      title: "Connect a Repository",
      description: "Link a public/private GitHub repository or upload a local project structure to begin parsing.",
      icon: GitBranch,
      actionText: "Import Repository",
      path: "/dashboard/repositories"
    },
    {
      title: "Semantic Code Search",
      description: "Query your codebase using natural language concepts (e.g. 'JWT verification flow').",
      icon: Search,
      actionText: "Query Codebase",
      path: "/dashboard/search"
    },
    {
      title: "Explore Architecture",
      description: "Navigate class relations, package graphs, and functional dependencies interactively.",
      icon: Network,
      actionText: "Visualise Graphs",
      path: "/dashboard/architecture"
    }
  ];

  return (
    <div className="space-y-8 select-none">
      
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold font-display tracking-tight text-white">
            Welcome, {user?.name || user?.email?.split('@')[0] || 'Developer'}
          </h2>
          <p className="text-muted-foreground text-sm">Here is a summary of your workspace intelligence.</p>
        </div>
        <Button onClick={() => navigate('/dashboard/repositories')}>
          <GitBranch className="mr-2 h-4 w-4" /> Import New Repository
        </Button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {metrics.map((metric, idx) => {
          const Icon = metric.icon;
          return (
            <Card key={idx} className="bg-card/40 border-border/40 hover:border-border/80 transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-xs font-semibold text-muted-foreground tracking-wider uppercase">{metric.name}</span>
                  <div className="p-1.5 bg-[#a21caf]/10 border border-[#a21caf]/20 rounded-lg text-[#a21caf]">
                    <Icon className="h-4.5 w-4.5" />
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-2xl font-extrabold font-display text-white">{metric.value}</span>
                  <span className="text-xs text-muted-foreground">{metric.desc}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Recent Activity / Repository lists */}
      {repoCount > 0 ? (
        <Card className="border-border/40">
          <CardHeader>
            <CardTitle>Recent Repositories</CardTitle>
            <CardDescription>Your recently added code workspaces and parsing statuses.</CardDescription>
          </CardHeader>
          <CardContent className="divide-y divide-border/60">
            {repos.slice(0, 3).map((repo: any) => (
              <div 
                key={repo.id} 
                className="py-4 first:pt-0 last:pb-0 flex items-center justify-between cursor-pointer hover:bg-white/[0.01] px-2 rounded-lg"
                onClick={() => navigate(`/dashboard/repositories?id=${repo.id}`)} // Redirect to explorer detail
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-[#a21caf]/10 rounded-lg text-[#a21caf]">
                    <GitBranch className="h-4.5 w-4.5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-white">{repo.owner}/{repo.name}</h4>
                    <p className="text-xs text-muted-foreground">Default branch: {repo.default_branch}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                    repo.import_status === 'completed' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
                    repo.import_status === 'failed' ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' :
                    'bg-amber-500/10 border-amber-500/20 text-amber-400 animate-pulse'
                  }`}>
                    {repo.import_status || 'Ready'}
                  </span>
                  <ChevronIcon className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {/* Quick Action / Feature Prompts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-4">
        {quickActions.map((action, idx) => {
          const Icon = action.icon;
          return (
            <Card key={idx} className="flex flex-col justify-between bg-card/20 hover:bg-card/45 transition-all duration-300 border-border/40">
              <CardHeader className="p-6 pb-4">
                <div className="p-2.5 bg-[#a21caf]/10 border border-[#a21caf]/20 rounded-lg text-[#a21caf] w-fit mb-4">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle className="mb-2">{action.title}</CardTitle>
                <CardDescription className="text-zinc-400 text-sm leading-relaxed">{action.description}</CardDescription>
              </CardHeader>
              <CardContent className="p-6 pt-0 mt-auto">
                <Button 
                  variant="outline" 
                  className="w-full justify-between"
                  onClick={() => navigate(action.path)}
                >
                  {action.actionText} <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

    </div>
  );
};

// Simple helper Chevron Icon
const ChevronIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" {...props}>
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

export default Dashboard;
