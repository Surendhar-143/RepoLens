import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router';
import { Github, Key, Mail, ShieldAlert } from 'lucide-react';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card.tsx';
import { useAuthStore } from '../stores/auth.ts';
import { useUIStore } from '../stores/ui.ts';
import axios from 'axios';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const { addNotification } = useUIStore();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return;

    setLoading(true);
    setErrorMsg('');
    try {
      const response = await axios.post('/api/v1/auth/login', { email, password });
      const { access_token, refresh_token: _refresh_token } = response.data;
      
      // Fetch user profile info
      const profileResp = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      });

      setAuth(access_token, profileResp.data);
      addNotification('Logged in successfully!', 'success');
      navigate('/dashboard');
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.error?.message || 'Invalid email or password credentials.';
      setErrorMsg(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleGitHubLogin = () => {
    // Redirect browser to backend GitHub authorization connector route
    window.location.href = 'http://localhost:8000/api/v1/github/connect';
  };

  return (
    <div className="min-h-screen bg-[#030014] flex items-center justify-center p-6 relative overflow-hidden select-none">
      
      {/* Gradients Background */}
      <div className="absolute top-[-10%] left-[-15%] w-[40%] h-[40%] rounded-full bg-violet-900/10 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-15%] w-[40%] h-[40%] rounded-full bg-[#a21caf]/10 blur-[100px] pointer-events-none" />

      <Card className="max-w-md w-full bg-card/65 border-border/40 backdrop-blur-md relative z-10">
        <CardHeader className="text-center space-y-2">
          <span 
            onClick={() => navigate('/')}
            className="p-2 bg-[#a21caf] text-white rounded-md text-base font-bold w-fit mx-auto select-none cursor-pointer"
          >
            🔎
          </span>
          <CardTitle className="text-2xl font-bold font-display tracking-tight text-white">Welcome Back</CardTitle>
          <CardDescription>Enter your account credentials to access RepoLens</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          
          {errorMsg && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/25 rounded-lg flex items-center gap-2.5 text-xs text-rose-400">
              <ShieldAlert className="h-4 w-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-1.5 text-left">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <input 
                  type="email" 
                  required
                  placeholder="developer@repolens.com" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-10 pl-9 pr-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Password</label>
              <div className="relative">
                <Key className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <input 
                  type="password" 
                  required
                  placeholder="••••••••" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-10 pl-9 pr-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                  disabled={loading}
                />
              </div>
            </div>

            <Button type="submit" loading={loading} className="w-full h-10 mt-2 text-sm font-semibold">
              Sign In to Dashboard
            </Button>
          </form>

          {/* Social login partition */}
          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-border/60"></div>
            <span className="flex-shrink mx-4 text-muted-foreground text-xs uppercase font-semibold">Or continue with</span>
            <div className="flex-grow border-t border-border/60"></div>
          </div>

          <Button 
            variant="outline" 
            className="w-full h-10 border-border hover:border-zinc-700 active:bg-secondary font-semibold text-sm"
            onClick={handleGitHubLogin}
            disabled={loading}
          >
            <Github className="mr-2 h-4 w-4 text-white" /> Connect with GitHub
          </Button>

          <p className="text-xs text-center text-muted-foreground mt-4">
            Don't have an account?{' '}
            <Link to="/register" className="text-[#f5d0fe] hover:underline font-semibold">
              Register Here
            </Link>
          </p>

        </CardContent>
      </Card>

    </div>
  );
};

export default Login;
