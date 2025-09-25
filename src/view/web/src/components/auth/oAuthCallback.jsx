import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import authService from '../../services/authService';

function OAuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('processing');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const token = searchParams.get('token');
        const provider = searchParams.get('provider');
        const error = searchParams.get('error');

        if (error) {
          console.error('OAuth error:', error);
          setStatus('error');
          setTimeout(() => {
            navigate('/login?error=oauth_failed');
          }, 2000);
          return;
        }

        if (!token || !provider) {
          setStatus('error');
          setTimeout(() => {
            navigate('/login?error=oauth_failed');
          }, 2000);
          return;
        }

        setStatus('authenticating');

        await authService.processOAuthCallback(token, provider);
        
        setStatus('success');
        
        setTimeout(() => {
          navigate('/home');
        }, 1000);

      } catch (error) {
        console.error('Failed to process OAuth callback:', error);
        setStatus('error');
        setTimeout(() => {
          navigate('/login?error=oauth_failed');
        }, 2000);
      }
    };

    handleCallback();
  }, [searchParams, navigate]);

  return (
    <div className="oauth-callback-container">
      <div className="oauth-callback-content">
        {/* Loading Spinner */}
        <div className={`loading-spinner ${status}`}>
          <div className="spinner"></div>
        </div>
        
        {/* Status Icon */}
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

      <style jsx>{`
        .oauth-callback-container {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
        }

        .oauth-callback-content {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          position: relative;
        }

        .loading-spinner {
          width: 60px;
          height: 60px;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .spinner {
          width: 60px;
          height: 60px;
          border: 3px solid rgba(255, 255, 255, 0.3);
          border-radius: 50%;
          border-top-color: #ffffff;
          animation: spin 1s ease-in-out infinite;
        }

        .loading-spinner.success .spinner,
        .loading-spinner.error .spinner {
          display: none;
        }

        .status-icon {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          animation: fadeIn 0.3s ease-in-out;
        }

        .status-icon.success {
          background-color: rgba(125, 202, 156, 0.2);
          color: #7dca9c;
          border: 2px solid #7dca9c;
        }

        .status-icon.error {
          background-color: rgba(231, 76, 60, 0.2);
          color: #e74c3c;
          border: 2px solid #e74c3c;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: scale(0.8);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        /* Add some subtle floating animation */
        .oauth-callback-content {
          animation: float 3s ease-in-out infinite;
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-10px);
          }
        }
      `}</style>
    </div>
  );
}

export default OAuthCallback;