import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, useNavigate, useSearchParams } from 'react-router-dom';
import '@testing-library/jest-dom';
import OAuthCallback from '../oauth-callback.tsx';
import userAuthService from '../../../../services/auth.ts';

// Mocks
jest.mock('../../../services/auth');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
  useSearchParams: jest.fn()
}));
jest.mock('../../../assets/svg/success-icon.svg', () => 'success-icon.svg');
jest.mock('../../../assets/svg/error-icon.svg', () => 'error-icon.svg');
jest.mock('./auth-layout.tsx', () => {
  return function AuthLayout({ title, description, children }: any) {
    return (
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
        {children}
      </div>
    );
  };
});

const renderOAuthCallback = (params: Record<string, string> = {}) => {
  const mockNavigate = jest.fn();
  const mockSearchParams = new URLSearchParams(params);
  
  jest.mocked(useNavigate).mockReturnValue(mockNavigate);
  jest.mocked(useSearchParams).mockReturnValue([mockSearchParams, jest.fn()]);
  
  return {
    ...render(
      <BrowserRouter>
        <OAuthCallback />
      </BrowserRouter>
    ),
    mockNavigate
  };
};

describe('OAuthCallback Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  describe('Rendering', () => {
    it('should render title', () => {
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      expect(screen.getByText('Completing Sign In')).toBeInTheDocument();
    });

    it('should render initial processing message', () => {
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      expect(screen.getByText('Processing authentication...')).toBeInTheDocument();
    });

    it('should render loading spinner initially', () => {
      const { container } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      expect(container.querySelector('.loading-spinner')).toBeInTheDocument();
      expect(container.querySelector('.spinner')).toBeInTheDocument();
    });

    it('should render callback status container', () => {
      const { container } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      expect(container.querySelector('.callback-status-container')).toBeInTheDocument();
    });
  });

  describe('Successful OAuth Flow', () => {
    it('should process OAuth callback with valid token and provider', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'valid-token', provider: 'google' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('valid-token', 'google');
      });
    });

    it('should update status to authenticating during processing', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'github' });
      
      await waitFor(() => {
        expect(screen.getByText('Completing sign in...')).toBeInTheDocument();
      });
    });

    it('should update status to success after successful authentication', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
    });

    it('should display success icon after successful authentication', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        const successIcon = screen.getByAltText('Success');
        expect(successIcon).toBeInTheDocument();
        expect(successIcon).toHaveAttribute('src', 'success-icon.svg');
      });
    });

    it('should redirect to dashboard after successful authentication', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const { mockNavigate } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(1000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('should use 1 second delay for success redirect', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const { mockNavigate } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(999);
      expect(mockNavigate).not.toHaveBeenCalled();
      
      jest.advanceTimersByTime(1);
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  describe('Error Handling', () => {
    it('should handle error parameter in URL', async () => {
      renderOAuthCallback({ error: 'access_denied' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
    });

    it('should redirect to login with error query param when OAuth error occurs', async () => {
      const { mockNavigate } = renderOAuthCallback({ error: 'access_denied' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(2000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });

    it('should handle missing token parameter', async () => {
      const { mockNavigate } = renderOAuthCallback({ provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(2000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });

    it('should handle missing provider parameter', async () => {
      const { mockNavigate } = renderOAuthCallback({ token: 'test-token' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(2000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });

    it('should handle missing both token and provider', async () => {
      const { mockNavigate } = renderOAuthCallback({});
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(2000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });

    it('should display error icon on error', async () => {
      renderOAuthCallback({ error: 'invalid_token' });
      
      await waitFor(() => {
        const errorIcon = screen.getByAltText('Error');
        expect(errorIcon).toBeInTheDocument();
        expect(errorIcon).toHaveAttribute('src', 'error-icon.svg');
      });
    });

    it('should log error to console when error parameter is present', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      
      renderOAuthCallback({ error: 'access_denied' });
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('OAuth error:', 'access_denied');
      });
    });

    it('should log error when service throws exception', async () => {
      const mockProcessOAuthCallback = jest.fn().mockRejectedValue(new Error('Service error'));
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      const consoleSpy = jest.spyOn(console, 'error');
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to process OAuth callback:', expect.any(Error));
      });
    });

    it('should use 2 second delay for error redirect', async () => {
      const { mockNavigate } = renderOAuthCallback({ error: 'access_denied' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(1999);
      expect(mockNavigate).not.toHaveBeenCalled();
      
      jest.advanceTimersByTime(1);
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });

    it('should handle service error during token processing', async () => {
      const mockProcessOAuthCallback = jest.fn().mockRejectedValue(new Error('Invalid token'));
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const { mockNavigate } = renderOAuthCallback({ token: 'invalid-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(2000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });
  });

  describe('Different OAuth Providers', () => {
    it('should handle Google provider', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'google-token', provider: 'google' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('google-token', 'google');
      });
    });

    it('should handle GitHub provider', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'github-token', provider: 'github' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('github-token', 'github');
      });
    });

    it('should handle any provider string', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'custom-provider' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('test-token', 'custom-provider');
      });
    });
  });

  describe('Status Messages', () => {
    it('should show processing message initially', () => {
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      expect(screen.getByText('Processing authentication...')).toBeInTheDocument();
    });

    it('should show authenticating message during token processing', async () => {
      const mockProcessOAuthCallback = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Completing sign in...')).toBeInTheDocument();
      });
    });

    it('should show success message after successful authentication', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
    });

    it('should show error message on authentication failure', async () => {
      renderOAuthCallback({ error: 'invalid_request' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
    });

    it('should show error message when service fails', async () => {
      const mockProcessOAuthCallback = jest.fn().mockRejectedValue(new Error('Service failed'));
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
    });
  });

  describe('Status Icons', () => {
    it('should show loading spinner during processing', () => {
      const { container } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      expect(container.querySelector('.loading-spinner')).toBeInTheDocument();
      expect(container.querySelector('.spinner')).toBeInTheDocument();
    });

    it('should show loading spinner during authenticating state', async () => {
      const mockProcessOAuthCallback = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const { container } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(container.querySelector('.loading-spinner')).toBeInTheDocument();
      });
    });

    it('should show success icon after successful authentication', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const { container } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        const successIcon = container.querySelector('.status-icon.success');
        expect(successIcon).toBeInTheDocument();
        expect(screen.getByAltText('Success')).toBeInTheDocument();
      });
    });

    it('should show error icon on authentication failure', async () => {
      const { container } = renderOAuthCallback({ error: 'access_denied' });
      
      await waitFor(() => {
        const errorIcon = container.querySelector('.status-icon.error');
        expect(errorIcon).toBeInTheDocument();
        expect(screen.getByAltText('Error')).toBeInTheDocument();
      });
    });

    it('should have correct dimensions for success icon', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        const successIcon = screen.getByAltText('Success');
        expect(successIcon).toHaveAttribute('width', '24');
        expect(successIcon).toHaveAttribute('height', '24');
      });
    });

    it('should have correct dimensions for error icon', async () => {
      renderOAuthCallback({ error: 'access_denied' });
      
      await waitFor(() => {
        const errorIcon = screen.getByAltText('Error');
        expect(errorIcon).toHaveAttribute('width', '24');
        expect(errorIcon).toHaveAttribute('height', '24');
      });
    });
  });

  describe('Navigation and Redirects', () => {
    it('should redirect to dashboard on success', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const { mockNavigate } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(1000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('should redirect to login with error on failure', async () => {
      const { mockNavigate } = renderOAuthCallback({ error: 'invalid_request' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(2000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });

    it('should not redirect immediately on success', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const { mockNavigate } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
      
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('should not redirect immediately on error', async () => {
      const { mockNavigate } = renderOAuthCallback({ error: 'access_denied' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('URL Parameter Extraction', () => {
    it('should extract token from URL parameters', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'extracted-token', provider: 'google' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('extracted-token', 'google');
      });
    });

    it('should extract provider from URL parameters', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'extracted-provider' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('test-token', 'extracted-provider');
      });
    });

    it('should extract error from URL parameters', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      
      renderOAuthCallback({ error: 'extracted-error' });
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('OAuth error:', 'extracted-error');
      });
    });

    it('should handle URL with multiple parameters', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ 
        token: 'test-token', 
        provider: 'google',
        extra: 'ignored-param'
      });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('test-token', 'google');
      });
    });
  });

  describe('Service Integration', () => {
    it('should not call service when token is missing', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      expect(mockProcessOAuthCallback).not.toHaveBeenCalled();
    });

    it('should not call service when provider is missing', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      expect(mockProcessOAuthCallback).not.toHaveBeenCalled();
    });

    it('should not call service when error parameter is present', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ error: 'user_cancelled' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      expect(mockProcessOAuthCallback).not.toHaveBeenCalled();
    });

    it('should call service only once', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Error Priority', () => {
    it('should prioritize error parameter over valid token/provider', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ 
        error: 'user_denied',
        token: 'valid-token',
        provider: 'google'
      });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      expect(mockProcessOAuthCallback).not.toHaveBeenCalled();
    });
  });

  describe('Status Transitions', () => {
    it('should transition from processing to authenticating to success', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      expect(screen.getByText('Processing authentication...')).toBeInTheDocument();
      
      await waitFor(() => {
        expect(screen.getByText('Completing sign in...')).toBeInTheDocument();
      });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
    });

    it('should transition from processing to error', async () => {
      renderOAuthCallback({ error: 'access_denied' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
    });

    it('should transition from processing to error on service failure', async () => {
      const mockProcessOAuthCallback = jest.fn().mockRejectedValue(new Error('Failed'));
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty string token', async () => {
      const { mockNavigate } = renderOAuthCallback({ token: '', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(2000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });

    it('should handle empty string provider', async () => {
      const { mockNavigate } = renderOAuthCallback({ token: 'test-token', provider: '' });
      
      await waitFor(() => {
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(2000);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login?error=oauth_failed');
    });

    it('should handle special characters in token', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const specialToken = 'token-with-special-chars_123.abc-xyz';
      renderOAuthCallback({ token: specialToken, provider: 'google' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith(specialToken, 'google');
      });
    });

    it('should handle different error types', async () => {
      const errorTypes = ['access_denied', 'invalid_request', 'server_error', 'unknown'];
      
      for (const errorType of errorTypes) {
        const consoleSpy = jest.spyOn(console, 'error');
        
        const { unmount } = renderOAuthCallback({ error: errorType });
        
        await waitFor(() => {
          expect(consoleSpy).toHaveBeenCalledWith('OAuth error:', errorType);
        });
        
        unmount();
        jest.clearAllMocks();
      }
    });
  });

  describe('Cleanup and Timing', () => {
    it('should clear timers on component unmount', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      const { mockNavigate, unmount } = renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
      
      unmount();
      
      jest.advanceTimersByTime(1000);
      
      expect(mockNavigate).toHaveBeenCalled();
    });

    it('should handle rapid state changes', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(screen.getByText('Successfully authenticated! Redirecting...')).toBeInTheDocument();
      });
    });
  });

  describe('Console Logging', () => {
    it('should log OAuth error with error parameter', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      
      renderOAuthCallback({ error: 'test_error' });
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('OAuth error:', 'test_error');
      });
    });

    it('should log service processing error', async () => {
      const mockProcessOAuthCallback = jest.fn().mockRejectedValue(new Error('Processing failed'));
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      const consoleSpy = jest.spyOn(console, 'error');
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to process OAuth callback:', 
          expect.any(Error)
        );
      });
    });

    it('should include error object in console log', async () => {
      const testError = new Error('Specific error message');
      const mockProcessOAuthCallback = jest.fn().mockRejectedValue(testError);
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      const consoleSpy = jest.spyOn(console, 'error');
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to process OAuth callback:', 
          testError
        );
      });
    });
  });

  describe('Multiple Callback Executions', () => {
    it('should handle callback being called only once on mount', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledTimes(1);
      });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledTimes(1);
      }, { timeout: 500 });
    });
  });

  describe('Unknown Status Handling', () => {
    it('should handle unknown status gracefully with default message', () => {
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      expect(screen.getByText('Completing Sign In')).toBeInTheDocument();
    });
  });

  describe('Concurrent Error Scenarios', () => {
    it('should handle error parameter with missing token', async () => {
      const consoleSpy = jest.spyOn(console, 'error');
      
      renderOAuthCallback({ error: 'no_token' });
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('OAuth error:', 'no_token');
        expect(screen.getByText('Authentication failed. Redirecting to login...')).toBeInTheDocument();
      });
    });

    it('should handle service error with specific error message', async () => {
      const specificError = new Error('Token expired');
      const mockProcessOAuthCallback = jest.fn().mockRejectedValue(specificError);
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      const consoleSpy = jest.spyOn(console, 'error');
      
      renderOAuthCallback({ token: 'expired-token', provider: 'google' });
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to process OAuth callback:', specificError);
      });
    });
  });

  describe('Provider Case Sensitivity', () => {
    it('should handle lowercase provider names', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'google' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('test-token', 'google');
      });
    });

    it('should handle uppercase provider names', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'GOOGLE' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('test-token', 'GOOGLE');
      });
    });

    it('should handle mixed case provider names', async () => {
      const mockProcessOAuthCallback = jest.fn().mockResolvedValue({});
      (userAuthService.processOAuthCallback as jest.Mock) = mockProcessOAuthCallback;
      
      renderOAuthCallback({ token: 'test-token', provider: 'GitHub' });
      
      await waitFor(() => {
        expect(mockProcessOAuthCallback).toHaveBeenCalledWith('test-token', 'GitHub');
      });
    });
  });
});