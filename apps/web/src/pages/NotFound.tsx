import React from 'react';
import { useNavigate } from 'react-router';
import { AlertTriangle, Home } from 'lucide-react';
import { Button } from '../components/ui/Button.tsx';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#030014] flex flex-col items-center justify-center p-6 text-center select-none">
      <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-full mb-6">
        <AlertTriangle className="h-10 w-10" />
      </div>
      <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2 font-display">404 - Page Not Found</h1>
      <p className="text-muted-foreground text-sm max-w-sm leading-relaxed mb-8">
        The link you followed may be broken, or the page has been moved to a different workspace route.
      </p>
      <Button onClick={() => navigate('/')}>
        <Home className="mr-2 h-4 w-4" /> Back to Landing Page
      </Button>
    </div>
  );
};

export default NotFound;
