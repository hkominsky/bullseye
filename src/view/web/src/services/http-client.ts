import authService from './auth.ts';
import { ApiError } from './utils/types.ts';

/**
 * HTTP client for making authenticated API requests.
 */
export class HttpClient {
  private static readonly BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  /**
   * Builds the request configuration with authentication headers.
   * 
   * @param token - The authentication token to include in the request.
   * @param options - Additional fetch options to merge with defaults.
   * @returns RequestInit configuration object with headers and options.
   */
  private static buildRequestConfig(token: string, options: RequestInit): RequestInit {
    return {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    };
  }

  /**
   * Handles 401 Unauthorized responses by logging out the user and redirecting to login.
   * 
   * @throws Error indicating authentication has expired.
   */
  private static handleUnauthorized(): never {
    authService.logout();
    window.location.href = '/login';
    throw new Error('Authentication expired');
  }

  /**
   * Extracts and formats error message from a failed response.
   * 
   * @param response - The failed fetch response.
   * @returns Promise resolving to a formatted error message string.
   */
  private static async extractErrorMessage(response: Response): Promise<string> {
    let errorMessage = `HTTP ${response.status}`;
    
    try {
      const error: ApiError = await response.json();
      errorMessage = error.message || error.detail || errorMessage;
    } catch {
      // Use the default message
    }
    
    return errorMessage;
  }

  /**
   * Makes an authenticated API request with proper typing and error handling.
   * 
   * @param endpoint - The API endpoint path (e.g., '/api/stocks/info/AAPL').
   * @param options - Optional fetch configuration options.
   * @returns Promise resolving to the typed response data.
   * @throws Error if no authentication token is available, authentication expires, or the request fails.
   */
  static async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const token = authService.getToken();
    
    if (!token) {
      throw new Error('No authentication token available');
    }

    const url = `${this.BASE_URL}${endpoint}`;
    const config = this.buildRequestConfig(token, options);

    const response = await fetch(url, config);

    if (response.status === 401) {
      this.handleUnauthorized();
    }

    if (!response.ok) {
      const errorMessage = await this.extractErrorMessage(response);
      throw new Error(errorMessage);
    }

    return response.json() as Promise<T>;
  }
}