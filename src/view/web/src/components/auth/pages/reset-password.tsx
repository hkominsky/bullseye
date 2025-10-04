import { useState, FormEvent, ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthLayout from '../widgets/auth-layout.tsx';
import userAuthService from '../../../services/auth.ts';

/**
 * Password reset component that handles email submission and confirmation states.
 * 
 * @returns The rendered password reset form or confirmation screen.
 */
function ResetPassword() {
  const navigate = useNavigate();
  
  const [email, setEmail] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isOnCooldown, setIsOnCooldown] = useState<boolean>(false);

  const COOLDOWN_TIME: number = 10000;
  const OPACITY_DISABLED: number = 0.6;
  const OPACITY_ENABLED: number = 1.0;

  /**
   * Handles input field changes and updates email state.
   * 
   * @param {ChangeEvent<HTMLInputElement>} e - The input change event.
   */
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setEmail(e.target.value);
  };

  /**
   * Validates that email field is not empty.
   * 
   * @returns {boolean} True if email is provided, false otherwise.
   */
  const validateEmailRequired = (): boolean => {
    if (!email.trim()) {
      setError('Email is required');
      return false;
    }
    return true;
  };

  /**
   * Validates email format using regex pattern.
   * 
   * @returns {boolean} True if email format is valid, false otherwise.
   */
  const validateEmailFormat = (): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return false;
    }
    return true;
  };

  /**
   * Validates the email form field by checking both requirement and format.
   * 
   * @returns {boolean} True if email is valid, false otherwise.
   */
  const validateForm = (): boolean => {
    return validateEmailRequired() && validateEmailFormat();
  };

  /**
   * Activates cooldown timer to prevent spam resend requests.
   * 
   * @returns {void}
   */
  const activateResendCooldown = (): void => {
    setIsOnCooldown(true);
    setTimeout(() => setIsOnCooldown(false), COOLDOWN_TIME);
  };

  /**
   * Sends password reset email and handles cooldown for resend.
   */
  const sendResetEmail = async (): Promise<void> => {
    setIsLoading(true);

    try {
      await userAuthService.resetPassword(email);
      setIsSubmitted(true);
      if (isSubmitted) {
        activateResendCooldown();
      }
    } catch (error: any) {
      setError(error.message || 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handles form submission and password reset process.
   * 
   * @param {FormEvent<HTMLFormElement>} [e] - The form submit event.
   * @returns {Promise<void>}
   */
  const handleResetPassword = async (e?: FormEvent<HTMLFormElement>): Promise<void> => {
    e?.preventDefault();
    setError('');

    if (!isSubmitted && !validateForm()) {
      return;
    }

    await sendResetEmail();
  };

  /**
   * Navigates back to the login page.
   */
  const handleGoToLogin = (): void => {
    navigate('/login');
  };

  /**
   * Checks if resend functionality should be disabled.
   * 
   * @returns {boolean} True if resend should be disabled, false otherwise.
   */
  const shouldDisableResend = (): boolean => {
    return isOnCooldown || isLoading;
  };

  /**
   * Handles resend email functionality with cooldown protection.
   */
  const handleResend = async (): Promise<void> => {
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
        description={`We've sent a password reset link to ${email}.`}
        error={error}
      >
        <div className="auth-form">
          <button 
            type="button" 
            className="auth-button" 
            onClick={handleGoToLogin}
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
              opacity: isResendDisabled ? OPACITY_DISABLED : OPACITY_ENABLED
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
      title="Forgot Password?"
      description="Enter your email address and we'll send you a reset link."
      error={error}
    >
      <form className="auth-form" onSubmit={handleResetPassword}>
        <div className="form-group">
          <input
            type="email"
            name="email"
            className="form-input"
            placeholder="Email"
            value={email}
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

      <p className="auth-footer-text">
        Remember your password? <span className="auth-color-link" onClick={handleGoToLogin}>Back to Login</span>
      </p>
    </AuthLayout>
  );
}

export default ResetPassword;