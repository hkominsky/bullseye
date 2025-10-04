export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
  updated_at: string;
  oauth_provider?: string | null;
  oauth_provider_id?: string | null;
  watchlist_tickers?: string | null;
  reserve_tickers?: string | null;
}

export interface SignupData {
  email: string;
  password: string;
  confirm_password: string;
  first_name: string;
  last_name: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface TokenData {
  access_token: string;
  token_type: string;
  expires_at: number;
  remember_me: boolean;
}

export interface ApiErrorResponse {
  detail: string;
}

export interface StockSuggestion {
  symbol: string;
  name: string;
}

export interface StockSearchResponse {
  suggestions: StockSuggestion[];
}

export interface StockValidationResponse {
  valid: boolean;
  symbol: string;
  name?: string | null;
  error?: string | null;
}

export interface ApiError {
  message?: string;
  detail?: string;
}

export interface EmailJobResponse {
  message: string;
  ticker_count: number;
  tickers: string[];
  status: 'processing' | 'completed' | 'failed';
}