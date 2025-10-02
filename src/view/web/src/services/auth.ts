import { User, SignupData, LoginCredentials, AuthResponse, TokenData, ApiErrorResponse } from './utils/types.ts';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Authentication service that upports automatic token refresh, session management, and proper logout handling.
 */
class AuthService {
  private token: string | null = null;
  private tokenExpiry: number | null = null;
  private rememberMe: boolean = false;
  private sessionTimeout?: ReturnType<typeof setTimeout>;
  private refreshTimer?: ReturnType<typeof setTimeout>;
  private readonly TOKEN_KEY = 'bullseye_auth_data';
  private readonly USER_KEY = 'bullseye_user_data';
  private readonly REFRESH_THRESHOLD = 5 * 60 * 1000;

  constructor() {
    this.initializeFromStorage();
    this.setupActivityListeners();
    this.scheduleTokenRefresh();
  }

  /**
   * Initializes authentication state from stored data in localStorage or sessionStorage.
   */
  private initializeFromStorage(): void {
    const tokenData = this.getStoredTokenData();
    if (tokenData) {
      this.token = tokenData.access_token;
      this.tokenExpiry = tokenData.expires_at;
      this.rememberMe = tokenData.remember_me;
      
      if (Date.now() >= tokenData.expires_at) {
        this.clearAuthData();
      }
    }
  }

  /**
   * Sets up activity listeners for session management.
   */
  private setupActivityListeners(): void {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, this.handleUserActivity.bind(this), true);
    });
  }

  /**
   * Handles user activity events to reset session timeout.
   */
  private handleUserActivity(): void {
    if (this.isAuthenticated() && !this.rememberMe) {
      this.resetSessionTimeout();
    }
  }

  /**
   * Stores authentication data with expiration in appropriate storage.
   * 
   * @param authResponse - The authentication response containing token and user data.
   * @param remember - Whether to persist the session across browser restarts.
   */
  private storeTokenData(authResponse: AuthResponse, remember: boolean): void {
    const expiresAt = Date.now() + (30 * 60 * 1000);
    
    const tokenData: TokenData = {
      access_token: authResponse.access_token,
      token_type: authResponse.token_type,
      expires_at: expiresAt,
      remember_me: remember
    };

    const storage = remember ? localStorage : sessionStorage;
    const oppositeStorage = remember ? sessionStorage : localStorage;
    
    try {
      storage.setItem(this.TOKEN_KEY, JSON.stringify(tokenData));
      storage.setItem(this.USER_KEY, JSON.stringify(authResponse.user));
      
      oppositeStorage.removeItem(this.TOKEN_KEY);
      oppositeStorage.removeItem(this.USER_KEY);
      
      this.token = authResponse.access_token;
      this.tokenExpiry = expiresAt;
      this.rememberMe = remember;
      
      this.scheduleTokenRefresh();
    } catch (error) {
      console.error('Failed to store authentication data:', error);
      throw new Error('Failed to store authentication data');
    }
  }

  /**
   * Retrieves stored token data from localStorage or sessionStorage.
   * 
   * @returns The stored token data, or null if not found or invalid.
   */
  private getStoredTokenData(): TokenData | null {
    try {
      const stored = localStorage.getItem(this.TOKEN_KEY) || sessionStorage.getItem(this.TOKEN_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch (error) {
      console.error('Failed to parse stored token data:', error);
      this.clearAuthData();
      return null;
    }
  }

  /**
   * Schedules automatic token refresh before expiration.
   */
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

  /**
   * Handles token expiration by clearing authentication data and dispatching an event.
   */
  private handleTokenExpiration(): void {
    this.clearAuthData();
    window.dispatchEvent(new CustomEvent('tokenExpired', {
      detail: { reason: 'Token expired', redirectTo: '/login' }
    }));

    window.location.href = '/login';
  }

  /**
   * Clears all authentication data from memory and storage.
   */
  private clearAuthData(): void {
    this.token = null;
    this.tokenExpiry = null;
    this.rememberMe = false;
    
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    sessionStorage.removeItem(this.TOKEN_KEY);
    sessionStorage.removeItem(this.USER_KEY);
    
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
      this.sessionTimeout = undefined;
    }
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = undefined;
    }
  }

  /**
   * Retrieves the current authentication token.
   * 
   * @returns The current authentication token, or null if not authenticated or expired.
   */
  getToken(): string | null {
    if (this.tokenExpiry && Date.now() >= this.tokenExpiry) {
      this.handleTokenExpiration();
      return null;
    }
    return this.token;
  }

  /**
   * Checks if the user is currently authenticated with a valid token.
   * 
   * @returns True if the user has a valid authentication token, false otherwise.
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    return token !== null;
  }

  /**
   * Determines if the authentication token needs to be refreshed.
   * 
   * @returns True if the token should be refreshed, false otherwise.
   */
  shouldRefreshToken(): boolean {
    if (!this.tokenExpiry || !this.isAuthenticated()) return false;
    return Date.now() >= (this.tokenExpiry - this.REFRESH_THRESHOLD);
  }

  /**
   * Registers a new user account with the provided signup data.
   * 
   * @param userData - The user registration data including email, password, and name.
   * @param rememberMe - Whether to persist the session across browser restarts. Defaults to false.
   * @returns A promise that resolves to the authentication response containing token and user data.
   * @throws Error if signup fails or the server returns an error.
   */
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

  /**
   * Authenticates a user with the provided credentials.
   * 
   * @param credentials - The login credentials including email, password, and optional rememberMe flag.
   * @returns A promise that resolves to the authentication response containing token and user data.
   * @throws Error if login fails or credentials are invalid.
   */
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

  /**
   * Refreshes the authentication token before it expires.
   * 
   * @returns A promise that resolves to the new access token.
   * @throws Error if no token exists or refresh fails.
   */
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

  /**
   * Processes the OAuth callback after successful authentication with a third-party provider.
   * 
   * @param token - The authentication token received from the OAuth provider.
   * @param provider - The name of the OAuth provider (e.g., 'google', 'github').
   * @param rememberMe - Whether to persist the session across browser restarts. Defaults to false.
   * @returns A promise that resolves to the authenticated user's data.
   * @throws Error if no token is received or user data cannot be retrieved.
   */
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

  /**
   * Fetches the current user's information from the server.
   * 
   * @returns A promise that resolves to the current user's data.
   * @throws Error if no token exists, the request fails, or the user is unauthorized.
   */
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
      storage.setItem(this.USER_KEY, JSON.stringify(user));
      
      return user;
    } catch (error) {
      if (error instanceof Error && error.message.includes('401')) {
        this.handleTokenExpiration();
      }
      throw error;
    }
  }

  /**
   * Retrieves stored user data from localStorage or sessionStorage.
   * 
   * @returns The stored user data, or null if not found or invalid.
   */
  getUser(): User | null {
    try {
      const userData = localStorage.getItem(this.USER_KEY) || sessionStorage.getItem(this.USER_KEY);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Failed to parse user data:', error);
      return null;
    }
  }

  /**
   * Logs out the current user with proper cleanup.
   */
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
      
      // Dispatch logout event
      window.dispatchEvent(new CustomEvent('userLoggedOut'));
      
    } catch (error) {
      console.error('Logout error:', error);
      // Clear data anyway for security
      this.clearAuthData();
    }
  }

  /**
   * Sets a session timeout for non-remembered sessions.
   * 
   * @param timeoutMinutes - The number of minutes before the session expires. Defaults to 30.
   */
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

  /**
   * Resets the session timeout on user activity.
   */
  resetSessionTimeout(): void {
    if (!this.rememberMe && this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
      this.setSessionTimeout();
    }
  }

  /**
   * Initiates Google OAuth authentication flow.
   */
  initiateGoogleAuth(): void {
    window.location.href = `${API_BASE_URL}/auth/google`;
  }

  /**
   * Initiates GitHub OAuth authentication flow.
   */
  initiateGitHubAuth(): void {
    window.location.href = `${API_BASE_URL}/auth/github`;
  }

  /**
   * Sends a password reset email to the specified email address.
   * 
   * @param email - The email address to send the password reset link to.
   * @returns A promise that resolves to the server response.
   * @throws Error if the email cannot be sent or the server is unreachable.
   */
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

  /**
   * Confirms a password reset using the provided token and new password.
   * 
   * @param token - The password reset token received via email.
   * @param newPassword - The new password to set for the account.
   * @returns A promise that resolves to the server response.
   * @throws Error if the password reset fails or the token is invalid.
   */
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

  /**
   * Cleans up resources when the service is destroyed.
   */
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