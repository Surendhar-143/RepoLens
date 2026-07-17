import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import { 
  User, 
  Key, 
  Github, 
  Trash2, 
  Save, 
  ShieldAlert, 
  Lock,
  CloudLightning
} from 'lucide-react';
import { Button } from '../components/ui/Button.tsx';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../components/ui/Card.tsx';
import { useAuthStore } from '../stores/auth.ts';
import { useUIStore } from '../stores/ui.ts';
import { useThemeStore } from '../stores/theme.ts';
import { api } from '../services/api.ts';

const Settings: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, setAuth, clearAuth } = useAuthStore();
  const { addNotification } = useUIStore();
  const { theme, toggleTheme } = useThemeStore();

  // Profile forms states
  const [profileName, setProfileName] = useState(user?.name || '');
  const avatarUrl = user?.avatar_url || '';
  
  // Password change states
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // API credentials states
  const [openaiKey, setOpenaiKey] = useState(localStorage.getItem('repolens-openai-key') || '');
  const [geminiKey, setGeminiKey] = useState(localStorage.getItem('repolens-gemini-key') || '');

  // Mutations
  const updateProfile = useMutation({
    mutationFn: async (data: { name: string; avatar_url: string }) => {
      const response = await api.patch('/auth/profile', data);
      return response.data;
    },
    onSuccess: (updatedUser) => {
      const token = localStorage.getItem('repolens-token') || '';
      setAuth(token, updatedUser);
      addNotification('Profile details updated successfully!', 'success');
    },
    onError: (err: any) => {
      addNotification(err.error?.message || 'Failed to update profile.', 'error');
    }
  });

  const changePassword = useMutation({
    mutationFn: async (data: any) => {
      await api.post('/auth/change-password', data);
    },
    onSuccess: () => {
      addNotification('Password changed successfully!', 'success');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    },
    onError: (err: any) => {
      addNotification(err.error?.message || 'Password update failed.', 'error');
    }
  });

  const disconnectGitHub = useMutation({
    mutationFn: async () => {
      await api.delete('/github/disconnect');
    },
    onSuccess: () => {
      // Reload profile
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      // Update local user state
      if (user) {
        const updated = { ...user, github_username: undefined };
        const token = localStorage.getItem('repolens-token') || '';
        setAuth(token, updated);
      }
      addNotification('GitHub account disconnected.', 'success');
    },
    onError: (err: any) => {
      addNotification(err.error?.message || 'Failed to disconnect GitHub account.', 'error');
    }
  });

  const deleteAccount = useMutation({
    mutationFn: async () => {
      await api.delete('/auth/account');
    },
    onSuccess: () => {
      clearAuth();
      addNotification('Your account has been deleted.', 'info');
      navigate('/');
    },
    onError: (err: any) => {
      addNotification(err.error?.message || 'Account deletion failed.', 'error');
    }
  });

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfile.mutate({ name: profileName, avatar_url: avatarUrl });
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      addNotification('Passwords do not match.', 'warning');
      return;
    }
    changePassword.mutate({ old_password: oldPassword, new_password: newPassword });
  };

  const handleSaveAPIKeys = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('repolens-openai-key', openaiKey);
    localStorage.setItem('repolens-gemini-key', geminiKey);
    addNotification('API Keys saved locally.', 'success');
  };

  const handleGitHubToggle = () => {
    if (user?.github_username) {
      if (confirm('Disconnect GitHub account? Imported GitHub repositories will remain in the dashboard.')) {
        disconnectGitHub.mutate();
      }
    } else {
      // Launch authorize redirect callback flow
      const token = localStorage.getItem('repolens-token');
      window.location.href = `http://localhost:8000/api/v1/github/connect?state=${token}`;
    }
  };

  return (
    <div className="space-y-8 select-none">
      
      {/* Title Header */}
      <div>
        <h2 className="text-3xl font-bold font-display tracking-tight text-white">System Settings</h2>
        <p className="text-muted-foreground text-sm">Update profile, change passwords, and configure API integrations.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Profile Card */}
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <div className="p-2.5 bg-violet-600/10 border border-violet-600/20 text-violet-400 rounded-lg w-fit mb-4">
              <User className="h-5 w-5" />
            </div>
            <CardTitle>Profile Settings</CardTitle>
            <CardDescription>Configure display name and avatar urls.</CardDescription>
          </CardHeader>
          <form onSubmit={handleProfileSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-muted-foreground uppercase">Email Address</label>
                <input 
                  type="email" 
                  value={user?.email || ''} 
                  disabled 
                  className="w-full h-10 px-3 bg-secondary/40 text-muted-foreground border border-border/40 rounded-md cursor-not-allowed text-sm"
                />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-muted-foreground uppercase">Username</label>
                <input 
                  type="text" 
                  value={user?.username || ''} 
                  disabled 
                  className="w-full h-10 px-3 bg-secondary/40 text-muted-foreground border border-border/40 rounded-md cursor-not-allowed text-sm"
                />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-muted-foreground uppercase">Display Name</label>
                <input 
                  type="text" 
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  className="w-full h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                />
              </div>
            </CardContent>
            <CardFooter className="border-t border-border/40 pt-4 flex justify-end">
              <Button type="submit" loading={updateProfile.isPending}>
                <Save className="mr-1.5 h-4 w-4" /> Save Profile Details
              </Button>
            </CardFooter>
          </form>
        </Card>

        {/* Change Password Card */}
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <div className="p-2.5 bg-[#a21caf]/10 border border-[#a21caf]/20 text-[#a21caf] rounded-lg w-fit mb-4">
              <Lock className="h-5 w-5" />
            </div>
            <CardTitle>Change Password</CardTitle>
            <CardDescription>Change the password associated with local login credentials.</CardDescription>
          </CardHeader>
          <form onSubmit={handlePasswordSubmit}>
            <CardContent className="space-y-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-muted-foreground uppercase">Current Password</label>
                <input 
                  type="password" 
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-muted-foreground uppercase">New Password</label>
                <input 
                  type="password" 
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-muted-foreground uppercase">Confirm New Password</label>
                <input 
                  type="password" 
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                />
              </div>
            </CardContent>
            <CardFooter className="border-t border-border/40 pt-4 flex justify-end">
              <Button type="submit" loading={changePassword.isPending}>
                <Key className="mr-1.5 h-4 w-4" /> Update Password
              </Button>
            </CardFooter>
          </form>
        </Card>

        {/* GitHub integration & UI controls */}
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <div className="p-2.5 bg-violet-500/10 border border-violet-500/20 text-violet-400 rounded-lg w-fit mb-4">
              <Github className="h-5 w-5" />
            </div>
            <CardTitle>Integrations & Interface</CardTitle>
            <CardDescription>Link external git developer services and update styling settings.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            
            {/* GitHub connect switch */}
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-white">GitHub Connection</span>
                <span className="text-xs text-muted-foreground block">
                  {user?.github_username 
                    ? `Connected as @${user.github_username}` 
                    : 'Authorize RepoLens to access repositories'}
                </span>
              </div>
              <Button 
                variant={user?.github_username ? 'destructive' : 'primary'} 
                size="sm"
                onClick={handleGitHubToggle}
                loading={disconnectGitHub.isPending}
              >
                {user?.github_username ? 'Disconnect' : 'Connect Account'}
              </Button>
            </div>

            {/* Dark mode switch */}
            <div className="flex items-center justify-between pt-4 border-t border-border/40">
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-white">Theme Selection</span>
                <span className="text-xs text-muted-foreground block">Currently configured in {theme} mode</span>
              </div>
              <Button variant="secondary" size="sm" onClick={toggleTheme}>
                Switch to {theme === 'dark' ? 'Light' : 'Dark'} Mode
              </Button>
            </div>

          </CardContent>
        </Card>

        {/* API keys credentials */}
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-lg w-fit mb-4">
              <CloudLightning className="h-5 w-5" />
            </div>
            <CardTitle>AI Provider Keys</CardTitle>
            <CardDescription>Setup access tokens to interact with Claude and Gemini engines.</CardDescription>
          </CardHeader>
          <form onSubmit={handleSaveAPIKeys}>
            <CardContent className="space-y-4">
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-muted-foreground uppercase">OpenAI API Key</label>
                <input 
                  type="password" 
                  placeholder="sk-..."
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="w-full h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                />
              </div>
              <div className="space-y-1.5 text-left">
                <label className="text-xs font-semibold text-muted-foreground uppercase">Google Gemini API Key</label>
                <input 
                  type="password" 
                  placeholder="AIzaSy..."
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full h-10 px-3 bg-secondary text-foreground text-sm border border-border rounded-md focus:outline-hidden focus:ring-1 focus:ring-[#a21caf]"
                />
              </div>
            </CardContent>
            <CardFooter className="border-t border-border/40 pt-4 flex justify-end">
              <Button type="submit">
                <Save className="mr-1.5 h-4 w-4" /> Save Local API Keys
              </Button>
            </CardFooter>
          </form>
        </Card>

      </div>

      {/* Danger Zone Account Deletion */}
      <Card className="border border-rose-500/20 bg-rose-500/5 mt-8">
        <CardHeader>
          <div className="flex items-center gap-2 text-rose-400">
            <ShieldAlert className="h-5 w-5 shrink-0" />
            <CardTitle className="text-rose-400 text-lg">Danger Zone</CardTitle>
          </div>
          <CardDescription className="text-rose-300/80">
            Permanently delete your profile data. This will clear all linked repository caches.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-start pt-2">
          <Button 
            variant="destructive"
            onClick={() => {
              if (confirm('WARNING: Are you absolutely sure you want to delete your account? This action is permanent and cannot be reversed.')) {
                deleteAccount.mutate();
              }
            }}
            loading={deleteAccount.isPending}
          >
            <Trash2 className="mr-1.5 h-4 w-4" /> Permanently Delete Account
          </Button>
        </CardFooter>
      </Card>

    </div>
  );
};

export default Settings;
