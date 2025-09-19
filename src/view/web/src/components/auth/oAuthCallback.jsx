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

        const user = await authService.processOAuthCallback(token, provider);
        
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

  const getStatusMessage = () => {
    switch (status) {
      case 'processing':
        return 'Processing authentication...';
      case 'authenticating':
        return 'Authenticating with OAuth provider...';
      case 'success':
        return 'Authentication successful! Redirecting...';
      case 'error':
        return 'Authentication failed. Redirecting to login...';
      default:
        return 'Processing...';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return '#7dca9c';
      case 'error':
        return '#e74c3c';
      default:
        return '#6c757d';
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: '#f8f9fa'
    }}>
      <div style={{
        textAlign: 'center',
        padding: '2rem',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        minWidth: '300px'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: `3px solid ${getStatusColor()}`,
          borderTop: '3px solid transparent',
          borderRadius: '50%',
          animation: status === 'error' || status === 'success' ? 'none' : 'spin 1s linear infinite',
          margin: '0 auto 1rem'
        }}></div>
        
        <p style={{ 
          color: getStatusColor(),
          fontSize: '16px',
          margin: 0 
        }}>
          {getStatusMessage()}
        </p>
        
        <style jsx>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  );
}

export default OAuthCallback;