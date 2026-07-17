import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router';
import { 
  LayoutDashboard, 
  GitBranch, 
  Search, 
  Network, 
  BookOpen, 
  Settings, 
  Menu, 
  X, 
  Bell, 
  LogOut,
  ChevronRight
} from 'lucide-react';
import { useUIStore } from '../stores/ui.ts';
import { ThemeToggle } from '../components/ui/ThemeToggle.tsx';

const DashboardLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarOpen, toggleSidebar, notifications, dismissNotification } = useUIStore();

  const navigationItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Repositories', path: '/dashboard/repositories', icon: GitBranch },
    { name: 'Semantic Search', path: '/dashboard/search', icon: Search },
    { name: 'Architecture Explorer', path: '/dashboard/architecture', icon: Network },
    { name: 'Documentation Builder', path: '/dashboard/documentation', icon: BookOpen },
    { name: 'Settings', path: '/dashboard/settings', icon: Settings },
  ];

  const getBreadcrumbs = () => {
    const paths = location.pathname.split('/').filter(Boolean);
    return paths.map((p, idx) => {
      const isLast = idx === paths.length - 1;
      const url = `/${paths.slice(0, idx + 1).join('/')}`;
      const name = p.charAt(0).toUpperCase() + p.slice(1);
      return (
        <React.Fragment key={url}>
          {idx > 0 && <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />}
          <span 
            onClick={() => !isLast && navigate(url)}
            className={`cursor-pointer ${isLast ? 'text-foreground font-medium' : 'text-muted-foreground hover:text-foreground'}`}
          >
            {name}
          </span>
        </React.Fragment>
      );
    });
  };

  return (
    <div className="min-h-screen flex bg-background text-foreground transition-colors duration-300">
      
      {/* Notifications overlay stack */}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
        {notifications.map((notif) => (
          <div 
            key={notif.id} 
            className={`p-4 rounded-lg shadow-lg border flex items-center justify-between text-sm ${
              notif.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' :
              notif.type === 'warning' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' :
              'bg-blue-500/10 border-blue-500/20 text-blue-400'
            }`}
          >
            <span>{notif.message}</span>
            <button onClick={() => dismissNotification(notif.id)} className="p-1 hover:opacity-85">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Collapsible Sidebar */}
      <aside className={`border-r border-border bg-card flex flex-col transition-all duration-300 ${sidebarOpen ? 'w-64' : 'w-16'}`}>
        {/* Brand logo header */}
        <div className="h-16 flex items-center px-4 border-b border-border/60 gap-3 overflow-hidden select-none">
          <span 
            onClick={() => navigate('/')}
            className="p-1.5 bg-[#a21caf] text-white rounded-md text-sm font-bold cursor-pointer"
          >
            🔎
          </span>
          {sidebarOpen && (
            <span className="font-bold font-display tracking-tight text-white text-lg">
              RepoLens
            </span>
          )}
        </div>

        {/* Sidebar Nav Items */}
        <nav className="flex-1 p-3 flex flex-col gap-1.5 overflow-y-auto">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex items-center gap-3 p-2.5 rounded-lg text-sm font-medium transition-all cursor-pointer ${
                  isActive 
                    ? 'bg-[#a21caf]/15 text-[#f5d0fe] border-l-2 border-[#a21caf]' 
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                }`}
                title={!sidebarOpen ? item.name : undefined}
              >
                <Icon className="h-4.5 w-4.5 shrink-0" />
                {sidebarOpen && <span>{item.name}</span>}
              </button>
            );
          })}
        </nav>

        {/* User context footer */}
        <div className="p-3 border-t border-border/60">
          <button 
            onClick={() => navigate('/')} 
            className="flex items-center gap-3 p-2.5 rounded-lg text-sm text-rose-400 hover:bg-rose-500/10 w-full transition-all text-left cursor-pointer"
            title={!sidebarOpen ? "Log Out" : undefined}
          >
            <LogOut className="h-4.5 w-4.5 shrink-0" />
            {sidebarOpen && <span>Log Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Header toolbar */}
        <header className="h-16 border-b border-border/60 px-6 flex items-center justify-between bg-card/45 backdrop-blur-xs sticky top-0 z-40">
          <div className="flex items-center gap-4">
            <button 
              onClick={toggleSidebar} 
              className="p-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <Menu className="h-5 w-5" />
            </button>
            
            {/* Breadcrumb navigator */}
            <div className="hidden md:flex items-center gap-2 text-xs select-none">
              {getBreadcrumbs()}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Theme & Controls */}
            <ThemeToggle />
            <button className="p-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground relative cursor-pointer">
              <Bell className="h-4.5 w-4.5" />
              <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-[#a21caf] rounded-full" />
            </button>

            {/* Profile Dropdown Scaffold */}
            <div className="flex items-center gap-2 border-l border-border pl-4">
              <div className="w-8 h-8 rounded-full bg-[#a21caf]/20 flex items-center justify-center border border-[#a21caf]/30 text-[#a21caf] font-bold text-xs select-none">
                DEV
              </div>
              <div className="hidden lg:block text-left text-xs select-none">
                <p className="font-semibold text-foreground leading-tight">RepoLens User</p>
                <p className="text-muted-foreground text-[10px]">Developer role</p>
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Nested Content */}
        <main className="flex-1 p-6 overflow-y-auto max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>

    </div>
  );
};

export default DashboardLayout;
