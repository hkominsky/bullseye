import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';
import { ReactComponent as EyeIcon } from '../../assets/eye-icon.svg';
import { ReactComponent as EyeOffIcon } from '../../assets/eye-off-icon.svg';
import AuthLayout from './authLayout';
import authService from '../../services/authService';

/**
 * Signup component for user registration with email/password and OAuth options
 * @returns {JSX.Element} The rendered signup form
 */
function Signup() {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const minPasswordLength = 6;

  /**
   * Handles input field changes and updates form data state
   * @param {Event} e - The input change event
   * @returns {void}
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
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
  const handleGoogleSignup = () => {
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
  const handleGitHubSignup = () => {
    try {
      setError('');
      authService.initiateGitHubAuth();
    } catch (error) {
      setError('Failed to initiate GitHub authentication. Please try again.');
    }
  };

  /**
   * Validates first name field
   * @returns {boolean} True if valid, false otherwise
   */
  const validateFirstName = () => {
    if (!formData.firstName.trim()) {
      setError('First name is required');
      return false;
    }
    return true;
  };

  /**
   * Validates last name field
   * @returns {boolean} True if valid, false otherwise
   */
  const validateLastName = () => {
    if (!formData.lastName.trim()) {
      setError('Last name is required');
      return false;
    }
    return true;
  };

  /**
   * Validates email field
   * @returns {boolean} True if valid, false otherwise
   */
  const validateEmail = () => {
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    return true;
  };

  /**
   * Validates password field including length requirements
   * @returns {boolean} True if valid, false otherwise
   */
  const validatePassword = () => {
    if (!formData.password) {
      setError('Password is required');
      return false;
    }
    
    if (formData.password.length < minPasswordLength) {
      setError(`Password must be at least ${minPasswordLength} characters long`);
      return false;
    }
    
    return true;
  };

  /**
   * Validates all form fields by calling individual validation methods
   * @returns {boolean} True if all fields are valid, false otherwise
   */
  const validateForm = () => {
    return validateFirstName() && 
           validateLastName() && 
           validateEmail() && 
           validatePassword();
  };

  /**
   * Transforms form data into the format expected by the auth service
   * @returns {Object} User data object for signup request
   */
  const transformUserData = () => {
    return {
      first_name: formData.firstName,
      last_name: formData.lastName,
      email: formData.email,
      password: formData.password,
      confirm_password: formData.password
    };
  };

  /**
   * Handles form submission and user signup process
   * @param {Event} e - The form submit event
   * @returns {Promise<void>}
   */
  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      const userData = transformUserData();
      await authService.signup(userData);
      navigate('/home');
    } catch (error) {
      setError(error.message || 'Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Navigates to the login page
   * @returns {void}
   */
  const handleLogin = () => {
    navigate('/login', { state: { direction: 'back' } });
  };

  return (
    <AuthLayout
      title="Get Started"
      description="Comprehensive market intelligence made simple."
      error={error}
    >
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
        
        <div className="form-group password-input-container">
          <input
            type={showPassword ? "text" : "password"}
            name="password"
            className="form-input password-input"
            placeholder="Password"
            value={formData.password}
            onChange={handleInputChange}
            required
            minLength={minPasswordLength}
            aria-label="Password"
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
        
        <button 
          type="submit" 
          className={`auth-button ${isLoading ? 'loading' : ''}`}
          disabled={isLoading}
          aria-label="Sign Up"
        >
          Sign Up
        </button>
      </form>

      <div className="divider">
        <span className="divider-line"></span>
        <span className="divider-text">Or Sign Up With</span>
        <span className="divider-line"></span>
      </div>
      
      <div className="external-auth-container">
        <button 
          className="external-auth-button" 
          onClick={handleGoogleSignup}
          aria-label="Sign up with Google"
          disabled={isLoading}
        >
          <GoogleIcon className="external-auth-icon" />
          Google
        </button>
        
        <button 
          className="external-auth-button" 
          onClick={handleGitHubSignup}
          aria-label="Sign up with GitHub"
          disabled={isLoading}
        >
          <GitHubIcon className="external-auth-icon" />
          GitHub
        </button>
      </div>
      
      <p className="auth-footer-text">
        Already have an account? <span className="auth-footer-link" onClick={handleLogin}>Log in 🡭</span>
      </p>
    </AuthLayout>
  );
}

export default Signup;