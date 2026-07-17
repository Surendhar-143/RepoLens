import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router';
import { Mail, Key, User as UserIcon, ShieldAlert } from 'lucide-react';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card.tsx';
import { useUIStore } from '../stores/ui.ts';
import axios from 'axios';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const { addNotification } = useUIStore();
  
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !username || !password) return;

    setLoading(true);
    setErrorMsg('');
    try {
      await axios.post('/api/v1/auth/register', {
        email,
        username,
        password,
        name: name || null
      });

      addNotification('Account created successfully! Please log in.', 'success');
      navigate('/login');
    } catch (err: any) {
      console.error(err);
      const detail = err.response?.data?.error?.message || 'Registration failed. Please check inputs.';
      setErrorMsg(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030014] flex items-center justify-center p-6 relative overflow-hidden select-none">
      
      {/* Background Gradients */}
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
          <CardTitle className="text-2xl font-bold font-display tracking-tight text-white">Create Account</CardTitle>
          <CardDescription>Get started with RepoLens Codebase Intelligence</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">

          {errorMsg && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/25 rounded-lg flex items-center gap-2.5 text-xs text-rose-400">
              <ShieldAlert className="h-4 w-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4">
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
              <label className="text-xs font-semibold text-muted-foreground uppercase">Username</label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <input 
                  type="text" 
                  required
                  placeholder="username" 
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full h-10 pl-9 pr-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="space-y-1.5 text-left">
              <label className="text-xs font-semibold text-muted-foreground uppercase">Full Name (Optional)</label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <input 
                  type="text" 
                  placeholder="John Doe" 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
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
                  placeholder="•••••••• (Min 6 chars)" 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-10 pl-9 pr-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                  disabled={loading}
                />
              </div>
            </div>

            <Button type="submit" loading={loading} className="w-full h-10 mt-4 text-sm font-semibold">
              Register Account
            </Button>
          </form>

          <p className="text-xs text-center text-muted-foreground mt-4">
            Already have an account?{' '}
            <Link to="/login" className="text-[#f5d0fe] hover:underline font-semibold">
              Log In
            </Link>
          </p>

        </CardContent>
      </Card>

    </div>
  );
};

export default Register;
