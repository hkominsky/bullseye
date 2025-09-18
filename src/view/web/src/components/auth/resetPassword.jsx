import './auth.css';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import logoImage from '../../assets/logo.png';
import authService from '../../services/authService';

/**
 * A password reset form that allows users to request a password reset email.
 * Provides a clean, accessible interface for users to recover their accounts.
 * 
 * @returns {JSX.Element} The reset password form component
 */
function ResetPassword() {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    email: ''
  });
  
  const [error, setError] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

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
   * Validates form fields before submission
   * 
   * @returns {boolean} True if form is valid, false otherwise
   */
  const validateForm = () => {
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    
    return true;
  };

  /**
   * Handles form submission for password reset request
   * Validates form, calls authService, and handles success/error states
   * 
   * @param {Event} e - The form submit event
   */
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    try {
      await authService.resetPassword(formData.email);
      setIsSubmitted(true);
    } catch (error) {
      setError(error.message || 'Failed to send reset email. Please try again.');
    }
  };

  /**
   * Navigates user back to the previous page
   */
  const handleBack = () => {
    navigate(-1);
  };

  return (
    <div className="auth-container">
      {/* Background area */}
      <div className="auth-left">
        <div className="auth-left-background"></div>
      </div>
      
      {/* Form content */}
      <div className="auth-right">
        {/* Logo */}
        <img 
          src={logoImage} 
          alt="Company Logo" 
          className="auth-logo"
        />
        
        <div className="auth-card">
          {!isSubmitted ? (
            <>
              {/* Back button */}
              <div className="auth-back-button" onClick={handleBack}>
                <span className="auth-back-link">🡰</span>
              </div>
              
              {/* Header section */}
              <h1 className="auth-title">Forgot Password</h1>
              <h2 className="auth-description">Enter your email address and we'll send you a link to reset your password.</h2>
              
              {/* Error message */}
              {error && <div className="error-message">{error}</div>}

              {/* Form */}
              <form className="auth-form" onSubmit={handleResetPassword}>
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
                
                <button 
                  type="submit" 
                  className="auth-button"
                  aria-label="Send Email"
                >
                  Send Email
                </button>
              </form>
            </>
          ) : (
            <>
              {/* Back button */}
              <div className="auth-back-button" onClick={handleBack}>
                <span className="auth-back-link">🡰</span>
              </div>
              
              {/* Success state */}
              <h1 className="auth-title">Check Your Email</h1>
              <h2 className="auth-description">We've sent a password reset link to {formData.email}.</h2>
              
              <div className="auth-form">
                <button 
                  type="button" 
                  className="auth-button" 
                  onClick={handleBack}
                  aria-label="Back"
                >
                  Back
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ResetPassword;