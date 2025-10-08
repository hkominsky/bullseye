import { HttpClient } from '../http-client.ts';
import authService from '../auth.ts';

// Mocks
jest.mock('../auth.ts', () => ({
  __esModule: true,
  default: {
    getToken: jest.fn(),
    logout: jest.fn()
  }
}));

window.fetch = jest.fn() as jest.Mock;

interface MockResponseData {
  id: number;
  name: string;
  value: string;
}

const mockResponseData: MockResponseData = {
  id: 1,
  name: 'Test',
  value: 'test-value'
};

describe('HttpClient', () => {
  let mockLocation: { href: string };

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockLocation = { href: '' };
    delete (window as any).location;
    (window as any).location = mockLocation;
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Successful Requests', () => {
    beforeEach(() => {
      (authService.getToken as jest.Mock).mockReturnValue('valid-token');
    });

    it('should make successful GET request', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      const result = await HttpClient.request<MockResponseData>('/api/test');

      expect(window.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer valid-token'
          })
        })
      );
      expect(result).toEqual(mockResponseData);
    });

    it('should make successful POST request', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponseData
      });

      const result = await HttpClient.request<MockResponseData>(
        '/api/test',
        {
          method: 'POST',
          body: JSON.stringify({ name: 'test' })
        }
      );

      expect(window.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'test' }),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer valid-token'
          })
        })
      );
      expect(result).toEqual(mockResponseData);
    });

    it('should make successful PUT request', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      const result = await HttpClient.request<MockResponseData>(
        '/api/test/1',
        { method: 'PUT' }
      );

      expect(window.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/test/1'),
        expect.objectContaining({
          method: 'PUT'
        })
      );
      expect(result).toEqual(mockResponseData);
    });

    it('should make successful DELETE request', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => ({})
      });

      await HttpClient.request('/api/test/1', { method: 'DELETE' });

      expect(window.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/test/1'),
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });

    it('should include custom headers', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request<MockResponseData>(
        '/api/test',
        {
          headers: {
            'X-Custom-Header': 'custom-value'
          }
        }
      );

      expect(window.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer valid-token',
            'X-Custom-Header': 'custom-value'
          })
        })
      );
    });

    it('should construct correct URL with base URL', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/test');

      expect(window.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test',
        expect.any(Object)
      );
    });

    it('should return typed response data', async () => {
      interface CustomResponse {
        userId: number;
        username: string;
      }

      const customData: CustomResponse = {
        userId: 123,
        username: 'testuser'
      };

      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => customData
      });

      const result = await HttpClient.request<CustomResponse>('/api/user');

      expect(result.userId).toBe(123);
      expect(result.username).toBe('testuser');
    });
  });

  describe('Authentication', () => {
    it('should throw error when no token available', async () => {
      (authService.getToken as jest.Mock).mockReturnValue(null);

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('No authentication token available');
    });

    it('should include Bearer token in Authorization header', async () => {
      (authService.getToken as jest.Mock).mockReturnValue('test-token-123');
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/test');

      expect(window.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token-123'
          })
        })
      );
    });

    it('should call authService.getToken before each request', async () => {
      (authService.getToken as jest.Mock).mockReturnValue('valid-token');
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/test');

      expect(authService.getToken).toHaveBeenCalled();
    });
  });

  describe('401 Unauthorized Handling', () => {
    beforeEach(() => {
      (authService.getToken as jest.Mock).mockReturnValue('expired-token');
    });

    it('should handle 401 response by logging out', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Authentication expired');

      expect(authService.logout).toHaveBeenCalled();
    });

    it('should redirect to login on 401', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Authentication expired');

      expect(mockLocation.href).toBe('/login');
    });

    it('should handle 401 before other error handling', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Token expired' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Authentication expired');

      expect(authService.logout).toHaveBeenCalled();
      expect(mockLocation.href).toBe('/login');
    });
  });

  describe('Error Handling', () => {
    beforeEach(() => {
      (authService.getToken as jest.Mock).mockReturnValue('valid-token');
    });

    it('should throw error for 400 Bad Request', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid request data' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Invalid request data');
    });

    it('should throw error for 403 Forbidden', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'Access denied' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Access denied');
    });

    it('should throw error for 404 Not Found', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Resource not found' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Resource not found');
    });

    it('should throw error for 500 Internal Server Error', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Internal server error');
    });

    it('should extract error message from detail field', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Validation error: email required' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Validation error: email required');
    });

    it('should extract error message from message field', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Custom error message' })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Custom error message');
    });

    it('should use HTTP status as fallback when no error message', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({})
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('HTTP 500');
    });

    it('should handle JSON parse error gracefully', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON');
        }
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('HTTP 500');
    });

    it('should prioritize message over detail', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          message: 'Message field error',
          detail: 'Detail field error'
        })
      });

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Message field error');
    });

    it('should handle network errors', async () => {
      (window.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network request failed')
      );

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Network request failed');
    });

    it('should handle timeout errors', async () => {
      (window.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Request timeout')
      );

      await expect(
        HttpClient.request('/api/test')
      ).rejects.toThrow('Request timeout');
    });
  });

  describe('Request Configuration', () => {
    beforeEach(() => {
      (authService.getToken as jest.Mock).mockReturnValue('valid-token');
    });

    it('should always include Content-Type header', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/test');

      expect(window.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    it('should merge custom options with defaults', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/test', {
        method: 'POST',
        body: JSON.stringify({ data: 'test' })
      });

      expect(window.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ data: 'test' }),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer valid-token'
          })
        })
      );
    });

    it('should allow custom headers to override defaults', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/test', {
        headers: {
          'Content-Type': 'application/xml'
        }
      });

      expect(window.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/xml'
          })
        })
      );
    });

    it('should preserve additional fetch options', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/test', {
        cache: 'no-cache',
        credentials: 'include'
      });

      expect(window.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          cache: 'no-cache',
          credentials: 'include'
        })
      );
    });
  });

  describe('Static Class Behavior', () => {
    it('should not require instantiation', () => {
      expect(HttpClient.request).toBeDefined();
      expect(typeof HttpClient.request).toBe('function');
    });

    it('should be callable as static method', async () => {
      (authService.getToken as jest.Mock).mockReturnValue('valid-token');
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await expect(HttpClient.request('/api/test')).resolves.toBeDefined();
    });
  });

  describe('Edge Cases', () => {
    beforeEach(() => {
      (authService.getToken as jest.Mock).mockReturnValue('valid-token');
    });

    it('should handle empty response body', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => null
      });

      const result = await HttpClient.request('/api/test');
      expect(result).toBeNull();
    });

    it('should handle endpoint with query parameters', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/test?param=value&foo=bar');

      expect(window.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/test?param=value&foo=bar',
        expect.any(Object)
      );
    });

    it('should handle endpoint with special characters', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      await HttpClient.request('/api/stocks/BRK.B');

      expect(window.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/stocks/BRK.B',
        expect.any(Object)
      );
    });

    it('should handle very long endpoint paths', async () => {
      (window.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseData
      });

      const longPath = '/api/very/long/path/with/many/segments/to/test/url/construction';
      await HttpClient.request(longPath);

      expect(window.fetch).toHaveBeenCalledWith(
        `http://localhost:8000${longPath}`,
        expect.any(Object)
      );
    });
  });
});