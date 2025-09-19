import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';
import { ReactComponent as EyeIcon } from '../../assets/eye-icon.svg';
import { ReactComponent as EyeOffIcon } from '../../assets/eye-off-icon.svg';
import AuthLayout from './authLayout';
import authService from '../../services/authService';

/**
 * User registration form component
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

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
  };

  const handleGoogleSignup = () => {
    console.log('Google signup clicked');
  };

  const handleGitHubSignup = () => {
    console.log('GitHub signup clicked');
  };

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
    
    if (formData.password.length < minPasswordLength) {
      setError(`Password must be at least ${minPasswordLength} characters long`);
      return false;
    }
    
    return true;
  };

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
        password: formData.password
      };

      await authService.signup(userData);
      
      navigate('/home');
    } catch (error) {
      setError(error.message || 'Signup failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

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
      
      <p className="auth-footer-text">
        Already have an account? <span className="auth-footer-link" onClick={handleLogin}>Log in 🡭</span>
      </p>
    </AuthLayout>
  );
}

export default Signup;