import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';
import { ReactComponent as EyeIcon } from '../../assets/eye-icon.svg';
import { ReactComponent as EyeOffIcon } from '../../assets/eye-off-icon.svg';
import AuthLayout from './authLayout';
import authService from '../../services/authService';

/**
 * Login component for user authentication with email/password and OAuth options
 * @returns {JSX.Element} The rendered login form
 */
function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const sessionLimit = 30;

  /**
   * Checks URL parameters for OAuth errors and sets appropriate error message
   * @returns {void}
   */
  const checkForOAuthError = () => {
    const errorParam = searchParams.get('error');
    if (errorParam === 'oauth_failed') {
      setError('OAuth authentication failed. Please try again or use email/password login.');
    }
  };

  useEffect(() => {
    checkForOAuthError();
  }, [searchParams]);

  /**
   * Handles input field changes and updates form data state
   * @param {Event} e - The input change event
   * @returns {void}
   */
  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  /**
   * Toggles password visibility between text and password input types
   * @returns {void}
   */
  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
  };

  /**
   * Initiates Google OAuth authentication flow
   * @returns {void}
   */
  const handleGoogleLogin = () => {
    try {
      setError('');
      authService.initiateGoogleAuth();
    } catch (error) {
      setError('Failed to initiate Google authentication. Please try again.');
    }
  };

  /**
   * Initiates GitHub OAuth authentication flow
   * @returns {void}
   */
  const handleGitHubLogin = () => {
    try {
      setError('');
      authService.initiateGitHubAuth();
    } catch (error) {
      setError('Failed to initiate GitHub authentication. Please try again.');
    }
  };

  /**
   * Validates that both email and password fields are filled
   * @returns {boolean} True if all required fields are filled, false otherwise
   */
  const validateLoginFields = () => {
    if (!formData.email || !formData.password) {
      setError('Please fill in all fields');
      return false;
    }
    return true;
  };

  /**
   * Sets session timeout if remember me option is not selected
   * @returns {void}
   */
  const configureSessionTimeout = () => {
    if (!formData.rememberMe) {
      authService.setSessionTimeout(sessionLimit);
    }
  };

  /**
   * Handles form submission and user login process
   * @param {Event} e - The form submit event
   * @returns {Promise<void>}
   */
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateLoginFields()) {
      return;
    }

    setIsLoading(true);

    try {
      await authService.login({
        email: formData.email,
        password: formData.password,
        rememberMe: formData.rememberMe
      });
      
      configureSessionTimeout();
      navigate('/home');
    } catch (error) {
      setError(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Navigates to the forgot password page
   * @returns {void}
   */
  const handleForgotPassword = () => {
    navigate('/reset-password', { state: { direction: 'forward' } });
  };

  /**
   * Navigates to the signup page
   * @returns {void}
   */
  const handleSignup = () => {
    navigate('/signup', { state: { direction: 'forward' } });
  };

  return (
    <AuthLayout
      title="Welcome back"
      description="Enter your email and password to access your account."
      error={error}
    >
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
        <div className="form-group password-input-container">
          <input
            type={showPassword ? "text" : "password"}
            name="password"
            className="form-input password-input"
            placeholder="Password"
            value={formData.password}
            onChange={handleInputChange}
            required
            aria-label="Password"
            autoComplete="current-password"
          />
          <button
            type="button"
            className="password-toggle-button"
            onClick={togglePasswordVisibility}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        </div>

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
          className={`auth-button ${isLoading ? 'loading' : ''}`}
          disabled={isLoading}
          aria-label="Log In"
        >
          Log In
        </button>
      </form>

      <div className="divider">
        <span className="divider-line"></span>
        <span className="divider-text">Or Login With</span>
        <span className="divider-line"></span>
      </div>
      
      <div className="external-auth-container">
        <button 
          className="external-auth-button" 
          onClick={handleGoogleLogin}
          aria-label="Log in with Google"
          disabled={isLoading}
        >
          <GoogleIcon className="external-auth-icon" />
          Google
        </button>
        
        <button 
          className="external-auth-button" 
          onClick={handleGitHubLogin}
          aria-label="Log in with GitHub"
          disabled={isLoading}
        >
          <GitHubIcon className="external-auth-icon" />
          GitHub
        </button>
      </div>
      
      <p className="auth-footer-text">
        Don't have an account? <span className="auth-footer-link" onClick={handleSignup}>Sign up 🡭</span>
      </p>
    </AuthLayout>
  );
}

export default Login;