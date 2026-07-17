import React, { useEffect } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router';
import { useAuthStore, UserProfile } from '../stores/auth.ts';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, setAuth } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    // Intercept token from GitHub OAuth redirects
    const params = new URLSearchParams(location.search);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    if (accessToken && refreshToken) {
      // Decode JWT user details (or fetch via api)
      try {
        const payloadBase64 = accessToken.split('.')[1];
        const payload = JSON.parse(window.atob(payloadBase64));
        
        const mockUser: UserProfile = {
          id: payload.sub,
          email: 'github-user@repolens.com',
          name: 'Connected GitHub Developer',
        };

        setAuth(accessToken, mockUser);
        
        // Clean URL query parameters
        navigate('/dashboard', { replace: true });
      } catch (e) {
        console.error('Failed to parse OAuth tokens', e);
      }
    }
  }, [location, setAuth, navigate]);

  if (!isAuthenticated) {
    // Redirect to login page but save the target path
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
