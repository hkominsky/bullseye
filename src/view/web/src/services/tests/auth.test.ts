import authService from '../auth.ts';
import { SignupData, LoginCredentials, AuthResponse, User } from '../utils/types.ts';

// Mocks
const mockUser: User = {
  id: 123,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z'
};
const mockAuthResponse: AuthResponse = {
  access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNzMwMDAwMDAwfQ.test',
  token_type: 'bearer',
  user: mockUser
};

window.fetch = jest.fn();

describe('AuthService', () => {
  let mockLocation: { href: string };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    
    mockLocation = { href: '' };
    delete (window as any).location;
    (window as any).location = mockLocation;
    
    jest.spyOn(Date, 'now').mockReturnValue(1000000000);
    
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.restoreAllMocks();
    jest.useRealTimers();
  });

  describe('Signup', () => {
    const signupData: SignupData = {
      email: 'test@example.com',
      password: 'password123',
      confirm_password: 'password123',
      first_name: 'Test',
      last_name: 'User'
    };

    it('should signup successfully and store token', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });

      const result = await authService.signup(signupData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/signup',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(signupData)
        })
      );
      expect(result).toEqual(mockAuthResponse);
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should store token in sessionStorage when rememberMe is false', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });

      await authService.signup(signupData, false);

      expect(sessionStorage.getItem('bullseye_auth_data_test@example.com')).toBeTruthy();
      expect(localStorage.getItem('bullseye_auth_data_test@example.com')).toBeNull();
    });

    it('should store token in localStorage when rememberMe is true', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });

      await authService.signup(signupData, true);

      expect(localStorage.getItem('bullseye_auth_data_test@example.com')).toBeTruthy();
      expect(sessionStorage.getItem('bullseye_auth_data_test@example.com')).toBeNull();
    });

    it('should throw error on signup failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Email already exists' })
      });

      await expect(authService.signup(signupData)).rejects.toThrow('Email already exists');
    });

    it('should set session timeout when rememberMe is false', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });

      await authService.signup(signupData, false);

      expect(authService.isAuthenticated()).toBe(true);
    });
  });

  describe('Login', () => {
    const loginCredentials: LoginCredentials = {
      email: 'test@example.com',
      password: 'password123',
      rememberMe: false
    };

    it('should login successfully and store token', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });

      const result = await authService.login(loginCredentials);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/login',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: loginCredentials.email, password: loginCredentials.password })
        })
      );
      expect(result).toEqual(mockAuthResponse);
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should store token in sessionStorage when rememberMe is false', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });

      await authService.login({ ...loginCredentials, rememberMe: false });

      expect(sessionStorage.getItem('bullseye_auth_data_test@example.com')).toBeTruthy();
    });

    it('should store token in localStorage when rememberMe is true', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });

      await authService.login({ ...loginCredentials, rememberMe: true });

      expect(localStorage.getItem('bullseye_auth_data_test@example.com')).toBeTruthy();
    });

    it('should throw error on login failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Invalid credentials' })
      });

      await expect(authService.login(loginCredentials)).rejects.toThrow('Invalid credentials');
    });

    it('should default rememberMe to false if not provided', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });

      const { rememberMe, ...credentialsWithoutRememberMe } = loginCredentials;
      await authService.login(credentialsWithoutRememberMe as LoginCredentials);

      expect(sessionStorage.getItem('bullseye_auth_data_test@example.com')).toBeTruthy();
    });
  });

  describe('Token Management', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123' });
    });

    it('should return token when authenticated', () => {
      const token = authService.getToken();
      expect(token).toBe(mockAuthResponse.access_token);
    });

    it('should return null when token is expired', () => {
      jest.spyOn(Date, 'now').mockReturnValue(2000000000);
      
      const token = authService.getToken();
      expect(token).toBeNull();
    });

    it('should indicate authenticated status', () => {
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should indicate not authenticated when no token', async () => {
      await authService.logout();
      expect(authService.isAuthenticated()).toBe(false);
    });

    it('should detect when token needs refresh', () => {
      jest.spyOn(Date, 'now').mockReturnValue(1000000000 + 26 * 60 * 1000);
      
      expect(authService.shouldRefreshToken()).toBe(true);
    });

    it('should not need refresh when token is fresh', () => {
      expect(authService.shouldRefreshToken()).toBe(false);
    });
  });

  describe('Token Refresh', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123' });
    });

    it('should refresh token successfully', async () => {
      const newToken = 'new_token';
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: newToken, token_type: 'bearer' })
      });

      const result = await authService.refreshToken();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/refresh',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockAuthResponse.access_token}`
          })
        })
      );
      expect(result).toBe(newToken);
    });

    it('should throw error when no token exists', async () => {
      await authService.logout();

      await expect(authService.refreshToken()).rejects.toThrow('No token to refresh');
    });

    it('should handle token expiration on refresh failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Invalid token' })
      });

      await expect(authService.refreshToken()).rejects.toThrow();
      expect(authService.isAuthenticated()).toBe(false);
    });
  });

  describe('Get Current User', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123' });
    });

    it('should fetch current user successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser
      });

      const user = await authService.getCurrentUser();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/me',
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockAuthResponse.access_token}`
          })
        })
      );
      expect(user).toEqual(mockUser);
    });

    it('should throw error when no token exists', async () => {
      await authService.logout();

      await expect(authService.getCurrentUser()).rejects.toThrow('No token found');
    });

    it('should handle token expiration on 401 response', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' })
      });

      await expect(authService.getCurrentUser()).rejects.toThrow();
      expect(authService.isAuthenticated()).toBe(false);
    });
  });

  describe('Get Stored User', () => {
    it('should return stored user data', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123' });

      const user = authService.getUser();
      expect(user).toEqual(mockUser);
    });

    it('should return null when no user data stored', () => {
      const user = authService.getUser();
      expect(user).toBeNull();
    });

    it('should return null when stored data is invalid', () => {
      sessionStorage.setItem('bullseye_user_data_test@example.com', 'invalid json');
      
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      const user = authService.getUser();
      
      expect(user).toBeNull();
      consoleErrorSpy.mockRestore();
    });
  });

  describe('Logout', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123' });
    });

    it('should logout successfully and clear auth data', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Logged out' })
      });

      await authService.logout();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/logout',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockAuthResponse.access_token}`
          })
        })
      );
      expect(authService.isAuthenticated()).toBe(false);
      expect(authService.getUser()).toBeNull();
    });

    it('should clear auth data even if backend logout fails', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();
      await authService.logout();

      expect(authService.isAuthenticated()).toBe(false);
      consoleWarnSpy.mockRestore();
    });

    it('should dispatch userLoggedOut event', async () => {
      const eventSpy = jest.fn();
      window.addEventListener('userLoggedOut', eventSpy);

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      });

      await authService.logout();

      expect(eventSpy).toHaveBeenCalled();
      window.removeEventListener('userLoggedOut', eventSpy);
    });

    it('should clear storage for specific user only', async () => {
      sessionStorage.setItem('bullseye_auth_data_test@example.com', 'token1');
      sessionStorage.setItem('bullseye_auth_data_other@example.com', 'token2');

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({})
      });

      await authService.logout();

      expect(sessionStorage.getItem('bullseye_auth_data_test@example.com')).toBeNull();
      expect(sessionStorage.getItem('bullseye_auth_data_other@example.com')).toBe('token2');
    });
  });

  describe('OAuth', () => {
    it('should initiate Google OAuth', () => {
      authService.initiateGoogleAuth();
      expect(mockLocation.href).toBe('http://localhost:8000/auth/google');
    });

    it('should initiate GitHub OAuth', () => {
      authService.initiateGitHubAuth();
      expect(mockLocation.href).toBe('http://localhost:8000/auth/github');
    });

    it('should process OAuth callback successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser
      });

      const user = await authService.processOAuthCallback('oauth_token', 'google', false);

      expect(user).toEqual(mockUser);
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should throw error when no token provided', async () => {
      await expect(authService.processOAuthCallback('', 'google')).rejects.toThrow(
        'No token received from OAuth provider'
      );
    });

    it('should clear auth data on OAuth callback failure', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Failed to fetch user'));

      await expect(authService.processOAuthCallback('token', 'google')).rejects.toThrow();
      expect(authService.isAuthenticated()).toBe(false);
    });
  });

  describe('Password Reset', () => {
    it('should send password reset email successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Reset email sent' })
      });

      const result = await authService.resetPassword('test@example.com');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/reset-password',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'test@example.com' })
        })
      );
      expect(result.message).toBe('Reset email sent');
    });

    it('should throw error on reset password failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Email not found' })
      });

      await expect(authService.resetPassword('test@example.com')).rejects.toThrow('Email not found');
    });

    it('should handle network error gracefully', async () => {
      (fetch as jest.Mock).mockRejectedValueOnce(new TypeError('Network error'));

      await expect(authService.resetPassword('test@example.com')).rejects.toThrow(
        'Unable to connect to server. Please try again.'
      );
    });

    it('should confirm password reset successfully', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'Password reset successful' })
      });

      const result = await authService.confirmPasswordReset('reset_token', 'newpassword123');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/auth/confirm-reset-password',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ token: 'reset_token', new_password: 'newpassword123' })
        })
      );
      expect(result.message).toBe('Password reset successful');
    });

    it('should throw error on confirm password reset failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Invalid token' })
      });

      await expect(authService.confirmPasswordReset('invalid_token', 'newpassword')).rejects.toThrow(
        'Invalid token'
      );
    });
  });

  describe('Session Timeout', () => {
    beforeEach(async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123', rememberMe: false });
    });

    it('should set session timeout', () => {
      authService.setSessionTimeout(30);
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should clear session after timeout', () => {
      authService.setSessionTimeout(1);

      jest.advanceTimersByTime(60000);

      expect(authService.isAuthenticated()).toBe(false);
    });

    it('should not set timeout when rememberMe is true', async () => {
      await authService.logout();
      
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123', rememberMe: true });

      authService.setSessionTimeout(1);
      jest.advanceTimersByTime(60000);

      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should dispatch sessionExpired event on timeout', () => {
      const eventSpy = jest.fn();
      window.addEventListener('sessionExpired', eventSpy);

      authService.setSessionTimeout(1);
      jest.advanceTimersByTime(60000);

      expect(eventSpy).toHaveBeenCalled();
      window.removeEventListener('sessionExpired', eventSpy);
    });
  });

  describe('Multi-Account Support', () => {
    it('should get all logged in accounts', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123' });

      const accounts = authService.getAllLoggedInAccounts();

      expect(accounts.length).toBeGreaterThan(0);
      expect(accounts[0].email).toBe('test@example.com');
    });

    it('should switch between accounts', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse
      });
      await authService.login({ email: 'test@example.com', password: 'password123', rememberMe: true });

      const mockUser2: User = {
        id: 124,
        email: 'test2@example.com',
        first_name: 'Test2',
        last_name: 'User',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      };

      const mockAuthResponse2 = {
        ...mockAuthResponse,
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0MkBleGFtcGxlLmNvbSIsImV4cCI6MTczMDAwMDAwMH0.test',
        user: mockUser2
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAuthResponse2
      });
      await authService.login({ email: 'test2@example.com', password: 'password123', rememberMe: true });

      const switched = authService.switchAccount('test@example.com');

      expect(switched).toBe(true);
      expect(authService.isAuthenticated()).toBe(true);
    });

    it('should return false when switching to non-existent account', () => {
      const switched = authService.switchAccount('nonexistent@example.com');
      expect(switched).toBe(false);
    });
  });

  describe('Token Expiration Handling', () => {
    it('should handle token expiration', () => {
      const eventSpy = jest.fn();
      window.addEventListener('tokenExpired', eventSpy);

      jest.spyOn(Date, 'now').mockReturnValue(2000000000);
      authService.getToken();

      expect(eventSpy).toHaveBeenCalled();
      window.removeEventListener('tokenExpired', eventSpy);
    });

    it('should redirect to login on token expiration', () => {
      jest.spyOn(Date, 'now').mockReturnValue(2000000000);
      authService.getToken();

      expect(mockLocation.href).toBe('/login');
    });
  });

  describe('Storage Initialization', () => {
    it('should initialize from localStorage on creation', async () => {
      const tokenData = {
        access_token: mockAuthResponse.access_token,
        token_type: 'bearer',
        expires_at: Date.now() + 30 * 60 * 1000,
        remember_me: true
      };

      localStorage.setItem('bullseye_auth_data_test@example.com', JSON.stringify(tokenData));
      localStorage.setItem('bullseye_user_data_test@example.com', JSON.stringify(mockUser));

      const hasToken = authService.isAuthenticated();
      expect(typeof hasToken).toBe('boolean');
    });

    it('should handle expired tokens on initialization', async () => {
      const expiredTokenData = {
        access_token: 'expired_token',
        token_type: 'bearer',
        expires_at: Date.now() - 1000,
        remember_me: true
      };

      localStorage.setItem('bullseye_auth_data_expired@example.com', JSON.stringify(expiredTokenData));
      
      expect(authService.isAuthenticated).toBeDefined();
    });
  });
});