import './auth.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';
import logoImage from '../../assets/logo.png';
import authService from '../../services/authService';

/**
 * A user authentication form that allows existing users to sign into their accounts.
 * Provides secure login with validation, external OAuth options, and password recovery.
 * 
 * @returns {JSX.Element} The login form component
 */
function Login() {
  const navigate = useNavigate();
  
  // Form state management
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  /**
   * Handles input field changes and updates form state
   * 
   * @param {Event} e - The input change event
   */
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  /**
   * Initiates Google OAuth login process
   */
  const handleGoogleLogin = () => {
    console.log('Google login clicked');
  };

  /**
   * Initiates GitHub OAuth login process
   */
  const handleGitHubLogin = () => {
    console.log('GitHub login clicked');
  };

  /**
   * Handles form submission for user authentication
   * 
   * @param {Event} e - The form submit event
   */
const handleLogin = async (e) => {
  e.preventDefault();
  setError('');

  if (!formData.email || !formData.password) {
    setError('Please fill in all fields');
    return;
  }

  setIsLoading(true);

  try {
    await authService.login({
      email: formData.email,
      password: formData.password,
      rememberMe: formData.rememberMe
    });
    
    if (!formData.rememberMe) {
      authService.setSessionTimeout(30);
    }
    
    navigate('/home');
  } catch (error) {
    setError(error.message || 'Login failed. Please check your credentials.');
  } finally {
    setIsLoading(false);
  }
};

  /**
   * Initiates forgot password flow
   */
  const handleForgotPassword = () => {
    navigate('/reset-password');
  };

  /**
   * Navigates user to the signup page
   */
  const handleSignup = () => {
    navigate('/signup');
  };

  return (
    <div className="auth-container">
      {/* Left side - Background/branding area */}
      <div className="auth-left">
        <div className="auth-left-background"></div>
      </div>
      
      {/* Right side - Form content */}
      <div className="auth-right">
        {/* Logo in top right corner */}
        <img 
          src={logoImage} 
          alt="Company Logo" 
          className="auth-logo"
        />
        
        <div className="auth-card">
          {/* Header section */}
          <h1 className="auth-title">Welcome back</h1>
          <h2 className="auth-description">Enter your email and password to access your account.</h2>
          
          {/* Error message display */}
          {error && <div className="error-message">{error}</div>}

          {/* Main login form */}
          <form className="auth-form" onSubmit={handleLogin}>
            <div className="form-group">
              <input
                type="email"
                name="email"
                className="form-input"
                placeholder="Email"
                value={formData.email}
                onChange={handleInputChange}
                required
                aria-label="Email Address"
                autoComplete="email"
              />
            </div>
            
            <div className="form-group">
              <input
                type="password"
                name="password"
                className="form-input"
                placeholder="Password"
                value={formData.password}
                onChange={handleInputChange}
                required
                aria-label="Password"
                autoComplete="current-password"
              />
            </div>

            {/* Form options row */}
            <div className="form-options">
              <label className="remember-me">
                <input
                  type="checkbox"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleInputChange}
                />
                Remember Me
              </label>
              
              <button
                type="button"
                className="forgot-password"
                onClick={handleForgotPassword}
              >
                Forgot Password?
              </button>
            </div>
            
            <button 
              type="submit" 
              className="auth-button" 
              disabled={isLoading}
              aria-label={isLoading ? 'Logging in...' : 'Log In'}
            >
              {isLoading ? 'Logging in...' : 'Log In'}
            </button>
          </form>

          {/* Divider for external auth options */}
          <div className="divider">
            <span className="divider-line"></span>
            <span className="divider-text">Or Login With</span>
            <span className="divider-line"></span>
          </div>
          
          {/* External authentication buttons */}
          <div className="external-auth-container">
            <button 
              className="external-auth-button" 
              onClick={handleGoogleLogin}
              aria-label="Log in with Google"
            >
              <GoogleIcon className="external-auth-icon" />
              Google
            </button>
            
            <button 
              className="external-auth-button" 
              onClick={handleGitHubLogin}
              aria-label="Log in with GitHub"
            >
              <GitHubIcon className="external-auth-icon" />
              GitHub
            </button>
          </div>
          
          {/* Footer link to signup page */}
          <p className="auth-footer-text">
            Don't have an account? <span className="auth-footer-link" onClick={handleSignup}>Sign up 🡭</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;