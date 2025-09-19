// components/auth/login.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';
import { ReactComponent as EyeIcon } from '../../assets/eye-icon.svg';
import { ReactComponent as EyeOffIcon } from '../../assets/eye-off-icon.svg';
import AuthLayout from './authLayout';
import authService from '../../services/authService';

/**
 * User authentication form component
 */
function Login() {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
  };

  const handleGoogleLogin = () => {
    console.log('Google login clicked');
  };

  const handleGitHubLogin = () => {
    console.log('GitHub login clicked');
  };

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

  const handleForgotPassword = () => {
    navigate('/reset-password', { state: { direction: 'forward' } });
  };

  const handleSignup = () => {
    navigate('/signup', { state: { direction: 'forward' } });
  };

  return (
    <AuthLayout
      title="Welcome back"
      description="Enter your email and password to access your account."
      error={error}
    >
      {/* Login form */}
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
        
        {/* Updated password field with toggle */}
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

      {/* Divider */}
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
      
      {/* Footer link */}
      <p className="auth-footer-text">
        Don't have an account? <span className="auth-footer-link" onClick={handleSignup}>Sign up 🡭</span>
      </p>
    </AuthLayout>
  );
}

export default Login;