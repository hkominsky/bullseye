const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Authentication service for handling user authentication, token management, and API requests.
 */
class AuthService {
  /**
   * Initialize AuthService with token from localStorage if available.
   */
  constructor() {
    this.token = localStorage.getItem('access_token');
  }

  /**
   * Store authentication token in memory and localStorage.
   * @param {string} token - JWT access token
   */
  setToken(token) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  /**
   * Retrieve the current authentication token.
   * @returns {string|null} The access token or null if not found
   */
  getToken() {
    return this.token || localStorage.getItem('access_token');
  }

  /**
   * Clear authentication token and user data from storage.
   */
  removeToken() {
    this.token = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  }

  /**
   * Register a new user account and automatically log them in.
   * @param {Object} userData - User registration data
   * @param {string} userData.email - User's email address
   * @param {string} userData.password - User's password
   * @param {string} userData.confirm_password - Password confirmation
   * @param {string} userData.first_name - User's first name
   * @param {string} userData.last_name - User's last name
   * @returns {Promise<Object>} Promise resolving to authentication response with token and user data
   * @throws {Error} If signup fails or passwords don't match
   */
  async signup(userData) {
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

      this.setToken(data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

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
   * @returns {Promise<Object>} Promise resolving to authentication response with token and user data
   * @throws {Error} If login fails due to invalid credentials
   */
  async login(credentials) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      this.setToken(data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      return data;
    } catch (error) {
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
      localStorage.setItem('user', JSON.stringify(user));
      return user;
    } catch (error) {
      this.removeToken();
      throw error;
    }
  }

  /**
   * Log out the current user by clearing stored data.
   */
  logout() {
    this.removeToken();
  }

  /**
   * Check if user is currently authenticated.
   * @returns {boolean} True if user has a valid token, false otherwise
   */
  isAuthenticated() {
    return !!this.getToken();
  }

  /**
   * Get stored user data from localStorage.
   * @returns {Object|null} Parsed user object or null if not found
   */
  getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }
}

export default new AuthService();