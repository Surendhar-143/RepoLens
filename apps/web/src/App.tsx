import { Routes, Route } from 'react-router';
import Landing from './pages/Landing.tsx';
import DashboardLayout from './layouts/DashboardLayout.tsx';
import Dashboard from './pages/Dashboard.tsx';
import Repositories from './pages/Repositories.tsx';
import Search from './pages/Search.tsx';
import Architecture from './pages/Architecture.tsx';
import Documentation from './pages/Documentation.tsx';
import Settings from './pages/Settings.tsx';
import NotFound from './pages/NotFound.tsx';
import Login from './pages/Login.tsx';
import Register from './pages/Register.tsx';
import { ProtectedRoute } from './components/ProtectedRoute.tsx';

function App() {
  return (
    <Routes>
      {/* Public Landing Page */}
      <Route path="/" element={<Landing />} />
      
      {/* Authentication Pages */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Dashboard Protected Application Shell */}
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="repositories" element={<Repositories />} />
        <Route path="search" element={<Search />} />
        <Route path="architecture" element={<Architecture />} />
        <Route path="documentation" element={<Documentation />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      {/* Wildcard Fallback */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
