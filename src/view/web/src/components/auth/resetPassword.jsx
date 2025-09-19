import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from './authLayout';
import authService from '../../services/authService';

/**
 * Password reset form component
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

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

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

  const handleResetPassword = async (e) => {
    e?.preventDefault();
    setError('');

    if (!isSubmitted && !validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await authService.resetPassword(formData.email);
      setIsSubmitted(true);
      if (isSubmitted) {
        setIsOnCooldown(true);
        setTimeout(() => setIsOnCooldown(false), cooldownTime);
      }
    } catch (error) {
      setError(error.message || 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/login', { state: { direction: 'back' } });
  };

  const handleResend = async () => {
    if (isOnCooldown || isLoading) {
      return;
    }
    
    setError('');
    await handleResetPassword();
  };

  if (isSubmitted) {
    const isResendDisabled = isLoading || isOnCooldown;
    
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