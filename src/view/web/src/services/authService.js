const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Authentication service for handling user authentication, token management, and API requests.
 * Supports "Remember Me" functionality using both localStorage and sessionStorage.
 */
class AuthService {
  /**
   * Initialize AuthService with token from storage if available.
   * Checks both localStorage (persistent) and sessionStorage (session-only) for tokens.
   */
  constructor() {
    this.token = this.getToken();
    this.rememberMe = this.isRemembered();
  }

  /**
   * Store authentication token based on remember preference.
   * @param {string} token - JWT access token
   * @param {boolean} remember - Whether to persist the token across browser sessions
   */
  setToken(token, remember = false) {
    this.token = token;
    this.rememberMe = remember;

    if (remember) {
      localStorage.setItem('access_token', token);
      localStorage.setItem('remember_me', 'true');
      sessionStorage.removeItem('access_token');
    } else {
      sessionStorage.setItem('access_token', token);
      localStorage.removeItem('access_token');
      localStorage.removeItem('remember_me');
    }
  }

  /**
   * Retrieve the current authentication token from appropriate storage.
   * @returns {string|null} The access token or null if not found
   */
  getToken() {
    return localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
  }

  /**
   * Check if the user chose to be remembered.
   * @returns {boolean} True if user selected "Remember Me"
   */
  isRemembered() {
    return localStorage.getItem('remember_me') === 'true';
  }

  /**
   * Store user data based on remember preference.
   * @param {Object} user - User data object
   * @param {boolean} remember - Whether to persist the user data
   */
  setUser(user, remember = false) {
    const userData = JSON.stringify(user);
    
    if (remember) {
      localStorage.setItem('user', userData);
      sessionStorage.removeItem('user');
    } else {
      sessionStorage.setItem('user', userData);
      localStorage.removeItem('user');
    }
  }

  /**
   * Clear authentication token and user data from all storage locations.
   */
  removeToken() {
    this.token = null;
    this.rememberMe = false;
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    localStorage.removeItem('remember_me');
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('user');
  }

  /**
   * Register a new user account and automatically log them in.
   * @param {Object} userData - User registration data
   * @param {string} userData.email - User's email address
   * @param {string} userData.password - User's password
   * @param {string} userData.confirm_password - Password confirmation
   * @param {string} userData.first_name - User's first name
   * @param {string} userData.last_name - User's last name
   * @param {boolean} [rememberMe=false] - Whether to remember the user across sessions
   * @returns {Promise<Object>} Promise resolving to authentication response with token and user data
   * @throws {Error} If signup fails or passwords don't match
   */
  async signup(userData, rememberMe = false) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Signup failed');
      }

      this.setToken(data.access_token, rememberMe);
      this.setUser(data.user, rememberMe);

      return data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Authenticate user with email and password.
   * @param {Object} credentials - User login credentials
   * @param {string} credentials.email - User's email address
   * @param {string} credentials.password - User's password
   * @param {boolean} [credentials.rememberMe=false] - Whether to remember the user across sessions
   * @returns {Promise<Object>} Promise resolving to authentication response with token and user data
   * @throws {Error} If login fails due to invalid credentials
   */
  async login(credentials) {
    try {
      const { email, password, rememberMe = false } = credentials;
      
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      this.setToken(data.access_token, rememberMe);
      this.setUser(data.user, rememberMe);

      return data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Initiate Google OAuth authentication flow.
   * Redirects user to Google's authorization server.
   */
  initiateGoogleAuth() {
    window.location.href = `${API_BASE_URL}/auth/google`;
  }

  /**
   * Initiate GitHub OAuth authentication flow.
   * Redirects user to GitHub's authorization server.
   */
  initiateGitHubAuth() {
    window.location.href = `${API_BASE_URL}/auth/github`;
  }

  /**
   * Process OAuth callback with token from URL parameters.
   * Called after successful OAuth redirect from providers.
   * @param {string} token - JWT token from OAuth callback
   * @param {string} provider - OAuth provider ('google' or 'github')
   * @param {boolean} rememberMe - Whether to persist the session
   * @returns {Promise<Object>} Promise resolving to user data
   */
  async processOAuthCallback(token, provider, rememberMe = false) {
    try {
      if (!token) {
        throw new Error('No token received from OAuth provider');
      }

      this.setToken(token, rememberMe);

      const user = await this.getCurrentUser();

      return user;
    } catch (error) {
      this.removeToken();
      throw error;
    }
  }

  /**
   * Send password reset email to user.
   * @param {string} email - User's email address
   * @returns {Promise<Object>} Promise resolving to success message
   * @throws {Error} If password reset request fails
   */
  async resetPassword(email) {
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
   * Confirm password reset with token and new password.
   * @param {string} token - Reset token from email link
   * @param {string} newPassword - User's new password
   * @returns {Promise<Object>} Promise resolving to success message
   * @throws {Error} If password reset confirmation fails
   */
  async confirmPasswordReset(token, newPassword) {
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
   * Fetch current user information using the stored token.
   * @returns {Promise<Object>} Promise resolving to user data
   * @throws {Error} If no token is found or request fails
   */
  async getCurrentUser() {
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
        throw new Error('Failed to get user info');
      }

      const user = await response.json();
      this.setUser(user, this.rememberMe);
      
      return user;
    } catch (error) {
      this.removeToken();
      throw error;
    }
  }

  /**
   * Log out the current user by clearing stored data.
   * Optionally can preserve remember me preference for future logins.
   * @param {boolean} [clearRememberPreference=true] - Whether to clear the remember me preference
   */
  logout(clearRememberPreference = true) {
    if (clearRememberPreference) {
      this.removeToken();
    } else {
      const wasRemembered = this.rememberMe;
      this.removeToken();
      if (wasRemembered) {
        localStorage.setItem('remember_me', 'true');
      }
    }
  }

  /**
   * Check if user is currently authenticated.
   * @returns {boolean} True if user has a valid token, false otherwise
   */
  isAuthenticated() {
    return !!this.getToken();
  }

  /**
   * Get stored user data from appropriate storage location.
   * @returns {Object|null} Parsed user object or null if not found
   */
  getUser() {
    const userData = localStorage.getItem('user') || sessionStorage.getItem('user');
    return userData ? JSON.parse(userData) : null;
  }

  /**
   * Refresh the authentication token if it's close to expiring.
   * This method would typically be called periodically or before making API requests.
   * @returns {Promise<string>} Promise resolving to new token
   * @throws {Error} If refresh fails
   */
  async refreshToken() {
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

      const data = await response.json();
      
      this.setToken(data.access_token, this.rememberMe);
      
      return data.access_token;
    } catch (error) {
      this.removeToken();
      throw error;
    }
  }

  /**
   * Set session timeout for non-remembered sessions.
   * This helps improve security by automatically logging out inactive users.
   * @param {number} timeoutMinutes - Minutes of inactivity before auto-logout
   */
  setSessionTimeout(timeoutMinutes = 30) {
    if (!this.rememberMe && this.isAuthenticated()) {
      const timeoutMs = timeoutMinutes * 60 * 1000;
      
      if (this.sessionTimeout) {
        clearTimeout(this.sessionTimeout);
      }
      
      this.sessionTimeout = setTimeout(() => {
        console.log('Session expired due to inactivity');
        this.logout();
        window.dispatchEvent(new CustomEvent('sessionExpired'));
      }, timeoutMs);
    }
  }

  /**
   * Reset session timeout on user activity.
   * Call this method on user interactions to prevent automatic logout.
   */
  resetSessionTimeout() {
    if (!this.rememberMe && this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
      this.setSessionTimeout();
    }
  }
}

const authService = new AuthService();

export default authService;