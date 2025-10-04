import { User, SignupData, LoginCredentials, AuthResponse, TokenData, ApiErrorResponse } from './utils/types.ts';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class AuthService {
  private token: string | null = null;
  private tokenExpiry: number | null = null;
  private rememberMe: boolean = false;
  private currentUserEmail: string | null = null;
  private sessionTimeout?: ReturnType<typeof setTimeout>;
  private refreshTimer?: ReturnType<typeof setTimeout>;
  private readonly TOKEN_KEY_PREFIX = 'bullseye_auth_data';
  private readonly USER_KEY_PREFIX = 'bullseye_user_data';
  private readonly REFRESH_THRESHOLD = 5 * 60 * 1000;

  constructor() {
    this.initializeFromStorage();
    this.setupActivityListeners();
    this.scheduleTokenRefresh();
  }

  private getTokenKey(): string {
    return this.currentUserEmail 
      ? `${this.TOKEN_KEY_PREFIX}_${this.currentUserEmail}`
      : this.TOKEN_KEY_PREFIX;
  }

  private getUserKey(): string {
    return this.currentUserEmail 
      ? `${this.USER_KEY_PREFIX}_${this.currentUserEmail}`
      : this.USER_KEY_PREFIX;
  }

  private extractEmailFromToken(token: string): string | null {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.sub || null;
    } catch {
      return null;
    }
  }

  private getAllStoredAccounts(): string[] {
    const accounts = new Set<string>();
    
    [localStorage, sessionStorage].forEach(storage => {
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key?.startsWith(this.TOKEN_KEY_PREFIX + '_')) {
          const email = key.replace(this.TOKEN_KEY_PREFIX + '_', '');
          accounts.add(email);
        }
      }
    });
    
    return Array.from(accounts);
  }

  private initializeFromStorage(): void {
    const allKeys = this.getAllStoredAccounts();
    
    for (const email of allKeys) {
      this.currentUserEmail = email;
      const tokenData = this.getStoredTokenData();
      
      if (tokenData && Date.now() < tokenData.expires_at) {
        this.token = tokenData.access_token;
        this.tokenExpiry = tokenData.expires_at;
        this.rememberMe = tokenData.remember_me;
        return;
      }
    }
    
    this.currentUserEmail = null;
    this.clearAuthData();
  }

  private setupActivityListeners(): void {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, this.handleUserActivity.bind(this), true);
    });
  }

  private handleUserActivity(): void {
    if (this.isAuthenticated() && !this.rememberMe) {
      this.resetSessionTimeout();
    }
  }

  private storeTokenData(authResponse: AuthResponse, remember: boolean): void {
    const expiresAt = Date.now() + (30 * 60 * 1000);
    
    const email = this.extractEmailFromToken(authResponse.access_token);
    if (!email) {
      throw new Error('Invalid token: cannot extract user email');
    }
    
    this.currentUserEmail = email;
    
    const tokenData: TokenData = {
      access_token: authResponse.access_token,
      token_type: authResponse.token_type,
      expires_at: expiresAt,
      remember_me: remember
    };

    const storage = remember ? localStorage : sessionStorage;
    
    try {
      storage.setItem(this.getTokenKey(), JSON.stringify(tokenData));
      storage.setItem(this.getUserKey(), JSON.stringify(authResponse.user));
      
      this.token = authResponse.access_token;
      this.tokenExpiry = expiresAt;
      this.rememberMe = remember;
      
      this.scheduleTokenRefresh();
    } catch (error) {
      console.error('Failed to store authentication data:', error);
      throw new Error('Failed to store authentication data');
    }
  }

  private getStoredTokenData(): TokenData | null {
    try {
      const stored = localStorage.getItem(this.getTokenKey()) || 
                    sessionStorage.getItem(this.getTokenKey());
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.error('Failed to parse stored token data:', error);
      return null;
    }
  }

  private scheduleTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (!this.tokenExpiry || !this.isAuthenticated()) return;

    const timeUntilRefresh = this.tokenExpiry - Date.now() - this.REFRESH_THRESHOLD;
    
    if (timeUntilRefresh > 0) {
      this.refreshTimer = setTimeout(async () => {
        try {
          await this.refreshToken();
        } catch (error) {
          console.warn('Auto token refresh failed:', error);
          this.handleTokenExpiration();
        }
      }, timeUntilRefresh);
    }
  }

  private handleTokenExpiration(): void {
    this.clearAuthData();
    window.dispatchEvent(new CustomEvent('tokenExpired', {
      detail: { reason: 'Token expired', redirectTo: '/login' }
    }));

    window.location.href = '/login';
  }

  private clearAuthData(): void {
    if (this.currentUserEmail) {
      localStorage.removeItem(this.getTokenKey());
      localStorage.removeItem(this.getUserKey());
      sessionStorage.removeItem(this.getTokenKey());
      sessionStorage.removeItem(this.getUserKey());
    }
    
    this.token = null;
    this.tokenExpiry = null;
    this.rememberMe = false;
    this.currentUserEmail = null;
    
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
      this.sessionTimeout = undefined;
    }
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = undefined;
    }
  }

  getToken(): string | null {
    if (this.tokenExpiry && Date.now() >= this.tokenExpiry) {
      this.handleTokenExpiration();
      return null;
    }
    return this.token;
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    return token !== null;
  }

  shouldRefreshToken(): boolean {
    if (!this.tokenExpiry || !this.isAuthenticated()) return false;
    return Date.now() >= (this.tokenExpiry - this.REFRESH_THRESHOLD);
  }

  async signup(userData: SignupData, rememberMe: boolean = false): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data: AuthResponse | ApiErrorResponse = await response.json();

      if (!response.ok) {
        throw new Error((data as ApiErrorResponse).detail || 'Signup failed');
      }

      const authData = data as AuthResponse;
      this.storeTokenData(authData, rememberMe);
      
      if (!rememberMe) {
        this.setSessionTimeout();
      }

      return authData;
    } catch (error) {
      throw error;
    }
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const { email, password, rememberMe = false } = credentials;
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data: AuthResponse | ApiErrorResponse = await response.json();

      if (!response.ok) {
        throw new Error((data as ApiErrorResponse).detail || 'Login failed');
      }

      const authData = data as AuthResponse;
      this.storeTokenData(authData, rememberMe);
      
      if (!rememberMe) {
        this.setSessionTimeout();
      }

      return authData;
    } catch (error) {
      throw error;
    }
  }

  async refreshToken(): Promise<string> {
    try {
      const currentToken = this.getToken();
      if (!currentToken) {
        throw new Error('No token to refresh');
      }

      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${currentToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data: { access_token: string; token_type: string } = await response.json();
      
      const user = this.getUser();
      if (!user) throw new Error('User data not found');
      
      const authResponse: AuthResponse = {
        access_token: data.access_token,
        token_type: data.token_type,
        user: user
      };
      
      this.storeTokenData(authResponse, this.rememberMe);
      
      return data.access_token;
    } catch (error) {
      this.handleTokenExpiration();
      throw error;
    }
  }

  async processOAuthCallback(token: string, provider: string, rememberMe: boolean = false): Promise<User> {
    try {
      if (!token) {
        throw new Error('No token received from OAuth provider');
      }

      const tempAuthResponse: AuthResponse = {
        access_token: token,
        token_type: 'bearer',
        user: {} as User
      };

      this.token = token;
      this.tokenExpiry = Date.now() + (30 * 60 * 1000);
      
      const user = await this.getCurrentUser();
      
      tempAuthResponse.user = user;
      this.storeTokenData(tempAuthResponse, rememberMe);
      
      if (!rememberMe) {
        this.setSessionTimeout();
      }

      return user;
    } catch (error) {
      this.clearAuthData();
      throw error;
    }
  }

  async getCurrentUser(): Promise<User> {
    try {
      const token = this.getToken();
      if (!token) {
        throw new Error('No token found');
      }

      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          this.handleTokenExpiration();
        }
        throw new Error('Failed to get user info');
      }

      const user: User = await response.json();
      
      const storage = this.rememberMe ? localStorage : sessionStorage;
      storage.setItem(this.getUserKey(), JSON.stringify(user));
      
      return user;
    } catch (error) {
      if (error instanceof Error && error.message.includes('401')) {
        this.handleTokenExpiration();
      }
      throw error;
    }
  }

  getUser(): User | null {
    try {
      const userData = localStorage.getItem(this.getUserKey()) || 
                      sessionStorage.getItem(this.getUserKey());
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Failed to parse user data:', error);
      return null;
    }
  }

  async logout(): Promise<void> {
    try {
      const token = this.getToken();
      
      if (token) {
        try {
          await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
        } catch (error) {
          console.warn('Backend logout failed:', error);
        }
      }
      
      this.clearAuthData();
      
      window.dispatchEvent(new CustomEvent('userLoggedOut'));
      
    } catch (error) {
      console.error('Logout error:', error);
      this.clearAuthData();
    }
  }

  setSessionTimeout(timeoutMinutes: number = 30): void {
    if (!this.rememberMe && this.isAuthenticated()) {
      const timeoutMs = timeoutMinutes * 60 * 1000;
      
      if (this.sessionTimeout) {
        clearTimeout(this.sessionTimeout);
      }
      
      this.sessionTimeout = setTimeout(() => {
        console.log('Session expired due to inactivity');
        this.clearAuthData();
        window.dispatchEvent(new CustomEvent('sessionExpired', {
          detail: { reason: 'Inactivity timeout' }
        }));
        
        window.location.href = '/login';
      }, timeoutMs);
    }
  }

  resetSessionTimeout(): void {
    if (!this.rememberMe && this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
      this.setSessionTimeout();
    }
  }

  initiateGoogleAuth(): void {
    window.location.href = `${API_BASE_URL}/auth/google`;
  }

  initiateGitHubAuth(): void {
    window.location.href = `${API_BASE_URL}/auth/github`;
  }

  async resetPassword(email: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send reset email');
      }

      return data;
    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error('Unable to connect to server. Please try again.');
      }
      throw error;
    }
  }

  async confirmPasswordReset(token: string, newPassword: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/confirm-reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          token: token,
          new_password: newPassword 
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to reset password');
      }

      return data;
    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error('Unable to connect to server. Please try again.');
      }
      throw error;
    }
  }

  getAllLoggedInAccounts(): Array<{ email: string; user: User | null }> {
    return this.getAllStoredAccounts().map(email => ({
      email,
      user: this.getUserForEmail(email)
    }));
  }

  private getUserForEmail(email: string): User | null {
    try {
      const key = `${this.USER_KEY_PREFIX}_${email}`;
      const userData = localStorage.getItem(key) || sessionStorage.getItem(key);
      return userData ? JSON.parse(userData) : null;
    } catch {
      return null;
    }
  }

  switchAccount(email: string): boolean {
    const tempEmail = this.currentUserEmail;
    this.currentUserEmail = email;
    
    const tokenData = this.getStoredTokenData();
    if (tokenData && Date.now() < tokenData.expires_at) {
      this.token = tokenData.access_token;
      this.tokenExpiry = tokenData.expires_at;
      this.rememberMe = tokenData.remember_me;
      this.scheduleTokenRefresh();
      return true;
    }
    
    this.currentUserEmail = tempEmail;
    return false;
  }

  destroy(): void {
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
    }
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.removeEventListener(event, this.handleUserActivity.bind(this), true);
    });
  }
}

const authService = new AuthService();

export default authService;