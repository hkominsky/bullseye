// App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import Login from './components/auth/login';
import SignUp from './components/auth/signup';
import ResetPassword from './components/auth/resetPassword';

function AnimatedRoutes() {
  const location = useLocation();
  
  const animatedRoutes = ['/login', '/signup', '/reset-password'];
  const shouldAnimate = animatedRoutes.includes(location.pathname);
  
  if (shouldAnimate) {
    return (
      <AnimatePresence mode="wait" initial={false}>
        <Routes location={location} key={location.pathname}>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/reset-password" element={<ResetPassword />} />
        </Routes>
      </AnimatePresence>
    );
  }
  
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/home" element={<h1>Home Page - Protected</h1>} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AnimatedRoutes />
    </Router>
  );
}

export default App;