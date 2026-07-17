import React from 'react';
import { BookOpen, FileCode, Users, Terminal, Database } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState.tsx';
import { Card, CardContent } from '../components/ui/Card.tsx';

const Documentation: React.FC = () => {
  const docTypes = [
    { title: "Developer Onboarding", desc: "Build workspace setup commands and setup guides.", icon: Users },
    { title: "API Specifications", desc: "Discover REST, GraphQL, WebSocket endpoints automatically.", icon: Terminal },
    { title: "Database Architecture", desc: "Map schemas, relations, and ORM schemas into guides.", icon: Database },
    { title: "Codebase Folder Map", desc: "Describe the structural purpose of root subfolders.", icon: FileCode }
  ];

  return (
    <div className="space-y-8 select-none">
      
      {/* Title Header */}
      <div>
        <h2 className="text-3xl font-bold font-display tracking-tight text-white">Documentation Builder</h2>
        <p className="text-muted-foreground text-sm">Create and synchronize system manuals directly from code structures.</p>
      </div>

      {/* Grid of Doc Templates */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {docTypes.map((item, idx) => {
          const Icon = item.icon;
          return (
            <Card key={idx} className="bg-card/30 border-border/40 hover:border-border/60 hover:bg-card/45 transition-all cursor-pointer">
              <CardContent className="p-5 flex flex-col space-y-4">
                <div className="p-2 bg-violet-600/10 border border-violet-600/20 text-violet-400 rounded-lg w-fit">
                  <Icon className="h-5 w-5" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-semibold text-sm text-white font-display">{item.title}</h4>
                  <p className="text-xs text-muted-foreground leading-normal">{item.desc}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main empty state */}
      <EmptyState 
        title="Connect a repository to write documentation"
        description="RepoLens scans declarations and structure to compile comprehensive markdown documentation and developer resources."
        icon={BookOpen}
      />

    </div>
  );
};

export default Documentation;
