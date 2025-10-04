import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Login from './components/auth/pages/login.tsx';
import SignUp from './components/auth/pages/signup.tsx';
import ResetPassword from './components/auth/pages/reset-password.tsx';
import ResetPasswordConfirm from './components/auth/pages/reset-password-confirm.tsx';
import OAuthCallback from './components/auth/widgets/oauth-callback.tsx';
import Dashboard from './components/dashboard/pages/dashboard.tsx';
import { ProtectedRoute } from './components/auth/widgets/protected-route.tsx';

/**
 * AppRoutes component that handles routing logic with animations.
 * 
 * @returns The rendered routes based on current location.
 */
function AppRoutes() {
  const location = useLocation();
  
  const animatedRoutes: string[] = ['/login', '/signup', '/reset-password', '/reset-password-confirm'];
  const shouldAnimate: boolean = animatedRoutes.includes(location.pathname);
  
  if (location.pathname === '/auth/callback') {
    return (
      <Routes>
        <Route path="/auth/callback" element={<OAuthCallback />} />
      </Routes>
    );
  }
  
  if (shouldAnimate) {
    return (
      <AnimatePresence mode="wait" initial={false}>
        <Routes location={location} key={location.pathname}>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/reset-password-confirm" element={<ResetPasswordConfirm />} />
        </Routes>
      </AnimatePresence>
    );
  }
  
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
    </Routes>
  );
}

/**
 * Main App component that provides router context.
 * 
 * @returns The rendered application with routing.
 */
function App() {
  return (
    <Router>
      <AppRoutes />
    </Router>
  );
}

export default App;