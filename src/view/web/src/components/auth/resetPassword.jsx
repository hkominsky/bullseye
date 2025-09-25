import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from './authLayout';
import authService from '../../services/authService';

/**
 * Password reset component that handles email submission and confirmation states
 * @returns {JSX.Element} The rendered password reset form or confirmation screen
 */
function ResetPassword() {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    email: ''
  });
  
  const [error, setError] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isOnCooldown, setIsOnCooldown] = useState(false);
  const cooldownTime = 10000;
  const opacityDisabled = 0.6;
  const opacityEnabled = 1.0;

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
   * Validates that email field is not empty
   * @returns {boolean} True if email is provided, false otherwise
   */
  const validateEmailRequired = () => {
    if (!formData.email.trim()) {
      setError('Email is required');
      return false;
    }
    return true;
  };

  /**
   * Validates email format using regex pattern
   * @returns {boolean} True if email format is valid, false otherwise
   */
  const validateEmailFormat = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      return false;
    }
    return true;
  };

  /**
   * Validates the email form field by checking both requirement and format
   * @returns {boolean} True if email is valid, false otherwise
   */
  const validateForm = () => {
    return validateEmailRequired() && validateEmailFormat();
  };

  /**
   * Activates cooldown timer to prevent spam resend requests
   * @returns {void}
   */
  const activateResendCooldown = () => {
    setIsOnCooldown(true);
    setTimeout(() => setIsOnCooldown(false), cooldownTime);
  };

  /**
   * Sends password reset email and handles cooldown for resend
   * @returns {Promise<void>}
   */
  const sendResetEmail = async () => {
    setIsLoading(true);

    try {
      await authService.resetPassword(formData.email);
      setIsSubmitted(true);
      if (isSubmitted) {
        activateResendCooldown();
      }
    } catch (error) {
      setError(error.message || 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles form submission and password reset process
   * @param {Event} e - The form submit event
   * @returns {Promise<void>}
   */
  const handleResetPassword = async (e) => {
    e?.preventDefault();
    setError('');

    if (!isSubmitted && !validateForm()) {
      return;
    }

    await sendResetEmail();
  };

  /**
   * Navigates back to the login page
   * @returns {void}
   */
  const handleBack = () => {
    navigate('/login', { state: { direction: 'back' } });
  };

  /**
   * Checks if resend functionality should be disabled
   * @returns {boolean} True if resend should be disabled, false otherwise
   */
  const shouldDisableResend = () => {
    return isOnCooldown || isLoading;
  };

  /**
   * Handles resend email functionality with cooldown protection
   * @returns {Promise<void>}
   */
  const handleResend = async () => {
    if (shouldDisableResend()) {
      return;
    }
    
    setError('');
    await handleResetPassword();
  };

  if (isSubmitted) {
    const isResendDisabled = shouldDisableResend();
    
    return (
      <AuthLayout
        title="Check Your Email"
        description={`We've sent a password reset link to ${formData.email}.`}
        showBackButton={false}
        error={error}
      >
        <div className="auth-form">
          <button 
            type="button" 
            className="auth-button" 
            onClick={handleBack}
            disabled={isLoading}
            aria-label="Back"
          >
            Back
          </button>
        </div>

        <p className="auth-footer-text">
          Didn't see the email? {' '}
          <span 
            className={`auth-resend-link ${isResendDisabled ? 'disabled' : ''}`}
            onClick={isResendDisabled ? undefined : handleResend}
            style={{ 
              cursor: isResendDisabled ? 'not-allowed' : 'pointer',
              opacity: isResendDisabled ? opacityDisabled : opacityEnabled
            }}
          >
            Resend
          </span>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Forgot Password"
      description="Enter your email address and we'll send you a link to reset your password."
      showBackButton={true}
      error={error}
    >
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
          className={`auth-button ${isLoading ? 'loading' : ''}`}
          disabled={isLoading}
          aria-label="Send Email"
        >
          Send Email
        </button>
      </form>
    </AuthLayout>
  );
}

export default ResetPassword;