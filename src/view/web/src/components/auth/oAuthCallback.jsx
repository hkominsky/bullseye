import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from './authLayout';
import authService from '../../services/authService';

/**
 * OAuth callback component that handles return flow from OAuth providers
 * Processes authentication tokens and redirects users appropriately
 * @returns {JSX.Element} The rendered OAuth callback page with status indicators
 */
function OAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('processing');

  /**
   * Extracts OAuth parameters from URL search parameters
   * @returns {Object} Object containing token, provider, and error values
   */
  const extractOAuthParams = () => {
    return {
      token: searchParams.get('token'),
      provider: searchParams.get('provider'),
      error: searchParams.get('error')
    };
  };

  /**
   * Handles OAuth error responses and redirects to login
   * @param {string} error - The error parameter from OAuth response
   * @returns {void}
   */
  const handleOAuthError = (error) => {
    console.error('OAuth error:', error);
    setStatus('error');
    setTimeout(() => {
      navigate('/login?error=oauth_failed');
    }, 2000);
  };

  /**
   * Validates required OAuth parameters are present
   * @param {string} token - OAuth token from provider
   * @param {string} provider - OAuth provider identifier
   * @returns {boolean} True if parameters valid, false otherwise
   */
  const validateOAuthParams = (token, provider) => {
    if (!token || !provider) {
      setStatus('error');
      setTimeout(() => {
        navigate('/login?error=oauth_failed');
      }, 2000);
      return false;
    }
    return true;
  };

  /**
   * Processes OAuth token through authentication service
   * @param {string} token - OAuth token from provider
   * @param {string} provider - OAuth provider identifier
   * @returns {Promise<void>}
   */
  const processAuthToken = async (token, provider) => {
    setStatus('authenticating');
    await authService.processOAuthCallback(token, provider);
    setStatus('success');
  };

  /**
   * Redirects user to home page after successful authentication
   * @returns {void}
   */
  const redirectToHome = () => {
    setTimeout(() => {
      navigate('/home');
    }, 1000);
  };

  /**
   * Handles authentication failure and redirects to login
   * @param {Error} error - Error that occurred during OAuth processing
   * @returns {void}
   */
  const handleAuthFailure = (error) => {
    console.error('Failed to process OAuth callback:', error);
    setStatus('error');
    setTimeout(() => {
      navigate('/login?error=oauth_failed');
    }, 2000);
  };

  /**
   * Main callback handler that orchestrates OAuth authentication process
   * @returns {Promise<void>}
   */
  const handleCallback = async () => {
    try {
      const { token, provider, error } = extractOAuthParams();

      if (error) {
        handleOAuthError(error);
        return;
      }

      if (!validateOAuthParams(token, provider)) {
        return;
      }

      await processAuthToken(token, provider);
      redirectToHome();

    } catch (error) {
      handleAuthFailure(error);
    }
  };

  useEffect(() => {
    handleCallback();
  }, [searchParams, navigate]);

  /**
   * Returns appropriate status message based on current authentication state
   * @returns {string} User-friendly status message for current state
   */
  const getStatusMessage = () => {
    switch (status) {
      case 'processing':
        return 'Processing authentication...';
      case 'authenticating':
        return 'Completing sign in...';
      case 'success':
        return 'Successfully authenticated! Redirecting...';
      case 'error':
        return 'Authentication failed. Redirecting to login...';
      default:
        return 'Processing...';
    }
  };

  return (
    <AuthLayout
      title="Completing Sign In"
      description={getStatusMessage()}
    >
      <div className="callback-status-container">
        {(status === 'processing' || status === 'authenticating') && (
          <div className="loading-spinner">
            <div className="spinner"></div>
          </div>
        )}
        
        {status === 'success' && (
          <div className="status-icon success">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
        )}
        
        {status === 'error' && (
          <div className="status-icon error">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path
                d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
        )}
      </div>
    </AuthLayout>
  );
}

export default OAuthCallback;