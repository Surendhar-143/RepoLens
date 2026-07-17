import React from 'react';
import { useNavigate } from 'react-router';
import { 
  Terminal, 
  MessageSquare, 
  GitFork, 
  FileText, 
  Compass, 
  ArrowRight, 
  Search, 
  ShieldAlert, 
  Cpu
} from 'lucide-react';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardContent } from '../components/ui/Card.tsx';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: MessageSquare,
      title: "AI Repository Assistant",
      desc: "Interact with an AI assistant that answers complex architecture and workflow questions directly grounded in your codebase."
    },
    {
      icon: Compass,
      title: "Interactive Architecture Explorer",
      desc: "Automatically map layered software architecture, call stacks, and module execution lifecycles in responsive charts."
    },
    {
      icon: GitFork,
      title: "Dependency Intelligence",
      desc: "Detect circular imports, unused functions, internal coupling bottlenecks, and third-party dependency vulnerabilities."
    },
    {
      icon: Search,
      title: "Semantic Code Search",
      desc: "Search intent rather than exact words. Find where auth processes or payment webhooks reside, even if they lack matching keywords."
    },
    {
      icon: FileText,
      title: "Auto-Generated Documentation",
      desc: "Instantly create onboarding guides, API specifications, and folder maps kept automatically synchronized with your commits."
    },
    {
      icon: ShieldAlert,
      title: "Repository Health Analytics",
      desc: "Analyze project maintainability, duplicate logic density, code coverage alerts, and compile security assessments."
    }
  ];

  return (
    <div className="relative min-h-screen bg-[#030014] overflow-hidden flex flex-col font-sans">
      
      {/* Background Decorative Neon Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-violet-900/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[#a21caf]/10 blur-[120px] pointer-events-none" />

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-[#030014]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl font-bold font-display tracking-tight text-white flex items-center gap-1.5">
              <span className="p-1.5 bg-[#a21caf] rounded-md text-sm">🔎</span> RepoLens
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" onClick={() => navigate('/dashboard')}>
              Sign In
            </Button>
            <Button onClick={() => navigate('/dashboard')}>
              Get Started <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Hero Area */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-20 md:py-28 flex flex-col items-center justify-center text-center relative z-10">
        
        {/* Release Pill */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-violet-500/20 bg-violet-500/5 text-violet-400 text-xs font-semibold mb-6">
          <Cpu className="h-3 w-3" /> RepoLens v1.0.0 Setup Complete
        </div>

        {/* Hero Headlines */}
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold tracking-tight max-w-4xl leading-tight font-display mb-6">
          The Google Maps for <br />
          <span className="gradient-text">Software Architecture</span>
        </h1>

        <p className="text-lg md:text-xl text-zinc-400 max-w-2xl font-normal leading-relaxed mb-10">
          RepoLens combines deterministic code parsing and vector-based semantic search to build an interactive, AI-enriched Knowledge Graph of your repository.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-20">
          <Button size="lg" className="w-full sm:w-auto text-base" onClick={() => navigate('/dashboard')}>
            Explore Sandbox Dashboard <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
          <Button size="lg" variant="secondary" className="w-full sm:w-auto text-base border border-white/5 hover:border-white/10" onClick={() => window.open('https://github.com/Surendhar-143/RepoLens.git')}>
            <Terminal className="mr-2 h-5 w-5" /> View Git Source
          </Button>
        </div>

        {/* Features Grid */}
        <div className="w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-16 border-t border-white/5">
          {features.map((feat, idx) => {
            const IconComponent = feat.icon;
            return (
              <Card key={idx} className="bg-white/[0.01] border-white/5 hover:border-white/10 hover:bg-white/[0.02] transition-all duration-300">
                <CardContent className="p-6 text-left flex flex-col h-full justify-between">
                  <div className="space-y-4">
                    <div className="p-2.5 bg-violet-600/10 rounded-lg text-violet-400 w-fit">
                      <IconComponent className="h-6 w-6" />
                    </div>
                    <h3 className="text-lg font-semibold tracking-tight text-white font-display">
                      {feat.title}
                    </h3>
                    <p className="text-sm text-zinc-400 leading-relaxed">
                      {feat.desc}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 mt-12 bg-black/40">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-zinc-500">
          <div>
            &copy; {new Date().getFullYear()} RepoLens Intelligence Platform. Released under the MIT License.
          </div>
          <div className="flex items-center gap-6">
            <a href="https://github.com/Surendhar-143/RepoLens.git" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">GitHub</a>
            <a href="#" className="hover:text-white transition-colors">Documentation</a>
            <a href="#" className="hover:text-white transition-colors">Security Policy</a>
          </div>
        </div>
      </footer>

    </div>
  );
};

export default Landing;
