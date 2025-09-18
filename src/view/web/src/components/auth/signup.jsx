import './auth.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';
import logoImage from '../../assets/logo.png';
import authService from '../../services/authService';

/**
 * A comprehensive user registration form with validation and external authentication options.
 * Provides a clean, accessible interface for new users to create accounts.
 * 
 * @returns {JSX.Element} The signup form component
 */
function Signup() {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  /**
   * Handles input field changes and updates form state
   * @param {Event} e - The input change event
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  /**
   * Initiates Google OAuth signup process
   */
  const handleGoogleSignup = () => {
    console.log('Google signup clicked');
  };

  /**
   * Initiates GitHub OAuth signup process
   */
  const handleGitHubSignup = () => {
    console.log('GitHub signup clicked');
  };

  /**
   * Validates form fields before submission
   * 
   * @returns {boolean} True if form is valid, false otherwise
   */
  const validateForm = () => {
    if (!formData.firstName.trim()) {
      setError('First name is required');
      return false;
    }
    
    if (!formData.lastName.trim()) {
      setError('Last name is required');
      return false;
    }
    
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    
    return true;
  };

  /**
   * Handles form submission for user registration
   * Validates form, calls authService, and handles success/error states
   * 
   * @param {Event} e - The form submit event
   */
  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const userData = {
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirmPassword
      };

      await authService.signup(userData);
      
      navigate('/home');
    } catch (error) {
      setError(error.message || 'Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Navigates user to the login page
   */
  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <div className="auth-container">
      {/* Left side - Background area */}
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
          <h1 className="auth-title">Get Started</h1>
          <h2 className="auth-description">Comprehensive market intelligence made simple.</h2>
          
          {/* Error message display */}
          {error && <div className="error-message">{error}</div>}

          {/* Main signup form */}
          <form className="auth-form" onSubmit={handleSignup}>
            <div className="form-group">
              <input
                type="text"
                name="firstName"
                className="form-input"
                placeholder="First Name"
                value={formData.firstName}
                onChange={handleInputChange}
                required
                aria-label="First Name"
              />
            </div>
            
            <div className="form-group">
              <input
                type="text"
                name="lastName"
                className="form-input"
                placeholder="Last Name"
                value={formData.lastName}
                onChange={handleInputChange}
                required
                aria-label="Last Name"
              />
            </div>
            
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
                minLength="6"
                aria-label="Password"
              />
            </div>
            
            <div className="form-group">
              <input
                type="password"
                name="confirmPassword"
                className="form-input"
                placeholder="Confirm Password"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                required
                aria-label="Confirm Password"
              />
            </div>
            
            <button 
              type="submit" 
              className="auth-button" 
              disabled={isLoading}
              aria-label={isLoading ? 'Signing up...' : 'Sign Up'}
            >
              {isLoading ? 'Signing up...' : 'Sign Up'}
            </button>
          </form>

          {/* Divider for external auth options */}
          <div className="divider">
            <span className="divider-line"></span>
            <span className="divider-text">Or Sign Up With</span>
            <span className="divider-line"></span>
          </div>
          
          {/* External authentication buttons */}
          <div className="external-auth-container">
            <button 
              className="external-auth-button" 
              onClick={handleGoogleSignup}
              aria-label="Sign up with Google"
            >
              <GoogleIcon className="external-auth-icon" />
              Google
            </button>
            
            <button 
              className="external-auth-button" 
              onClick={handleGitHubSignup}
              aria-label="Sign up with GitHub"
            >
              <GitHubIcon className="external-auth-icon" />
              GitHub
            </button>
          </div>
          
          {/* Footer link to login page */}
          <p className="auth-footer-text">
            Already have an account? <span className="auth-footer-link" onClick={handleLogin}>Log in 🡭</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Signup;