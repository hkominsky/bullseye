import React from 'react';
import { Navigate } from 'react-router-dom';
import authService from '../../../services/auth.ts'
import { ProtectedRouteProps } from '../utils/types.ts';

/**
 * ProtectedRoute component that redirects to login if user is not authenticated.
 * 
 * @param children - The component to render if authenticated.
 * @returns The protected component or redirect to login.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};