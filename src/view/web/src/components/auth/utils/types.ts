export interface ProtectedRouteProps {
  children: React.ReactNode;
}

export interface OAuthParams {
  token: string | null;
  provider: string | null;
  error: string | null;
}

export type AuthStatus = 'processing' | 'authenticating' | 'success' | 'error';

export interface LoginFormData {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface SignupFormData {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

export interface UserData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}