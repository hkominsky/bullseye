import './auth.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';
import authService from '../../services/authService';

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

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
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

  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <div className="auth-container">
      <div className="auth-left">
        <div className="auth-left-background"></div>
      </div>
      <div className="auth-right">
        <div className="auth-card">
          <h1 className="auth-title">💼 Market Brief</h1>
          <h2 className="auth-description">Sign up to continue</h2>
          
          {error && <div className="error-message">{error}</div>}
          
          <button className="external-auth-button" onClick={handleGoogleSignup}>
            <GoogleIcon className="external-auth-icon" />
            Continue with Google
          </button>
          
          <button className="external-auth-button" onClick={handleGitHubSignup}>
            <GitHubIcon className="external-auth-icon" />
            Continue with GitHub
          </button>
          
          <div className="divider">
            <span className="divider-line"></span>
            <span className="divider-text">or</span>
            <span className="divider-line"></span>
          </div>
          
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
              />
            </div>
            
            <button type="submit" className="auth-button" disabled={isLoading}>
              CREATE ACCOUNT
            </button>
          </form>
          
          <p className="auth-footer-text">
            Already have an account? <span className="auth-footer-link" onClick={handleLogin}>Log in</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Signup;