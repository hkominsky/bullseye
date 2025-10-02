import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from './auth-layout.tsx';
import userAuthService from '../../../services/auth.ts';
import SuccessIcon from '../../../assets/svg/success-icon.svg';
import ErrorIcon from '../../../assets/svg/error-icon.svg';
import { OAuthParams, AuthStatus } from '../utils/types.ts';

const ERROR_REDIRECT_DELAY = 2000;
const SUCCESS_REDIRECT_DELAY = 1000;

const STATUS_MESSAGES: Record<string, string> = {
  processing: 'Processing authentication...',
  authenticating: 'Completing sign in...',
  success: 'Successfully authenticated! Redirecting...',
  error: 'Authentication failed. Redirecting to login...',
};
const DEFAULT_MSG = 'Processing...';

/**
 * OAuth callback component that handles return flow from OAuth providers.
 * 
 * @returns The rendered OAuth callback page with status indicators.
 */
function OAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<AuthStatus>('processing');

  /**
   * Extracts OAuth parameters from URL search params.
   * 
   * @returns {OAuthParams} Object containing token, provider, and error parameters.
   */
  const extractOAuthParams = useCallback((): OAuthParams => {
    return {
      token: searchParams.get('token'),
      provider: searchParams.get('provider'),
      error: searchParams.get('error')
    };
  }, [searchParams]);

  /**
   * Redirects to a specified route after a delay.
   * 
   * @param {string} route - The route to navigate to.
   * @param {number} delay - Delay in milliseconds before navigation.
   */
  const redirectWithDelay = useCallback((route: string, delay: number): void => {
    setTimeout(() => {
      navigate(route);
    }, delay);
  }, [navigate]);

  /**
   * Handles OAuth error scenarios by updating status and redirecting to login.
   * 
   * @param {string} error - The error message to log.
   */
  const handleOAuthError = useCallback((error: string): void => {
    console.error('OAuth error:', error);
    setStatus('error');
    redirectWithDelay('/login?error=oauth_failed', ERROR_REDIRECT_DELAY);
  }, [redirectWithDelay]);

  /**
   * Validates that required OAuth parameters are present.
   * 
   * @param {string | null} token - OAuth token from URL parameters.
   * @param {string | null} provider - OAuth provider from URL parameters.
   * @returns {boolean} True if parameters are valid, false otherwise.
   */
  const validateOAuthParams = useCallback((token: string | null, provider: string | null): boolean => {
    if (!token || !provider) {
      setStatus('error');
      redirectWithDelay('/login?error=oauth_failed', ERROR_REDIRECT_DELAY);
      return false;
    }
    return true;
  }, [redirectWithDelay]);

  /**
   * Processes the OAuth authentication token with the auth service.
   * 
   * @param {string} token - Valid OAuth token.
   * @param {string} provider - OAuth provider name.
   * @returns {Promise<void>} Promise that resolves when authentication is complete.
   */
  const processAuthToken = useCallback(async (token: string, provider: string): Promise<void> => {
    setStatus('authenticating');
    await userAuthService.processOAuthCallback(token, provider);
    setStatus('success');
  }, []);

  /**
   * Main callback handler that orchestrates the OAuth flow.
   * 
   * @returns {Promise<void>} Promise that resolves when callback processing is complete.
   */
  const handleCallback = useCallback(async (): Promise<void> => {
    try {
      const { token, provider, error } = extractOAuthParams();

      if (error) {
        handleOAuthError(error);
        return;
      }

      if (!validateOAuthParams(token, provider)) {
        return;
      }

      await processAuthToken(token!, provider!);
      redirectWithDelay('/dashboard', SUCCESS_REDIRECT_DELAY);

    } catch (error: any) {
      console.error('Failed to process OAuth callback:', error);
      setStatus('error');
      redirectWithDelay('/login?error=oauth_failed', ERROR_REDIRECT_DELAY);
    }
  }, [extractOAuthParams, handleOAuthError, validateOAuthParams, processAuthToken, redirectWithDelay]);

  /**
   * Returns appropriate status message based on current authentication state.
   */
  const getStatusMessage = (): string =>
    STATUS_MESSAGES[status] ?? DEFAULT_MSG;

  /**
   * Renders the appropriate status icon based on current authentication state.
   * 
   * @returns {React.ReactElement | null} Status icon component or null.
   */
  const renderStatusIcon = (): React.ReactElement | null => {
    if (status === 'processing' || status === 'authenticating') {
      return (
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      );
    }
    
    if (status === 'success') {
      return (
        <div className="status-icon success">
          <img src={SuccessIcon} alt="Success" width="24" height="24" />
        </div>
      );
    }
    
    if (status === 'error') {
      return (
        <div className="status-icon error">
          <img src={ErrorIcon} alt="Error" width="24" height="24" />
        </div>
      );
    }
    
    return null;
  };

  useEffect(() => {
    handleCallback();
  }, [handleCallback]);

  return (
    <AuthLayout
      title="Completing Sign In"
      description={getStatusMessage()}
    >
      <div className="callback-status-container">
        {renderStatusIcon()}
      </div>
    </AuthLayout>
  );
}

export default OAuthCallback;