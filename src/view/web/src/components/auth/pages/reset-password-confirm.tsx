import { useState, useEffect, FormEvent, ChangeEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from '../widgets/auth-layout.tsx';
import userAuthService from '../../../services/auth.ts';

/**
 * Password reset confirmation component that handles the password reset using the token from the email link.
 */
function ResetPasswordConfirm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [token, setToken] = useState<string>('');
  const [newPassword, setNewPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSuccess, setIsSuccess] = useState<boolean>(false);

  const MIN_PASSWORD_LENGTH: number = 8;

  /**
   * Extract token from URL on component mount.
   */
  useEffect(() => {
    const tokenFromUrl = searchParams.get('token');
    
    if (!tokenFromUrl) {
      setError('Invalid or missing reset token');
    } else {
      setToken(tokenFromUrl);
    }
  }, [searchParams]);

  /**
   * Handles input field changes.
   */
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    
    if (name === 'newPassword') {
      setNewPassword(value);
    } else if (name === 'confirmPassword') {
      setConfirmPassword(value);
    }
  };

  /**
   * Validates password meets minimum requirements.
   */
  const validatePasswordLength = (): boolean => {
    if (newPassword.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters long`);
      return false;
    }
    return true;
  };

  /**
   * Validates passwords match.
   */
  const validatePasswordsMatch = (): boolean => {
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    return true;
  };

  /**
   * Validates the entire form.
   */
  const validateForm = (): boolean => {
    if (!newPassword.trim() || !confirmPassword.trim()) {
      setError('All fields are required');
      return false;
    }
    
    return validatePasswordLength() && validatePasswordsMatch();
  };

  /**
   * Handles form submission and password reset.
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError('Invalid reset token');
      return;
    }

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await userAuthService.confirmPasswordReset(token, newPassword);
      setIsSuccess(true);
    } catch (error: any) {
      setError(error.message || 'Failed to reset password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Navigates to login page.
   */
  const handleGoToLogin = (): void => {
    navigate('/login');
  };

  if (isSuccess) {
    return (
      <AuthLayout
        title="Password Reset Successful"
        description="Your password has been successfully reset. You can now log in with your new password."
        error=""
      >
        <div className="auth-form">
          <button 
            type="button" 
            className="auth-button" 
            onClick={handleGoToLogin}
          >
            Go to Login
          </button>
        </div>
      </AuthLayout>
    );
  }

  // Reset form
  return (
    <AuthLayout
      title="Reset Your Password"
      description="Enter your new password below."
      error={error}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <input
            type="password"
            name="newPassword"
            className="form-input"
            placeholder="New Password"
            value={newPassword}
            onChange={handleInputChange}
            required
            minLength={MIN_PASSWORD_LENGTH}
          />
        </div>

        <div className="form-group">
          <input
            type="password"
            name="confirmPassword"
            className="form-input"
            placeholder="Confirm New Password"
            value={confirmPassword}
            onChange={handleInputChange}
            required
            minLength={MIN_PASSWORD_LENGTH}
          />
        </div>
        
        <button 
          type="submit" 
          className={`auth-button ${isLoading ? 'loading' : ''}`}
          disabled={isLoading || !token}
        >
          Reset Password
        </button>
      </form>

      <p className="auth-footer-text">
        Remember your password? <span className="auth-color-link" onClick={handleGoToLogin}>Back to Login</span>
      </p>
    </AuthLayout>
  );
}

export default ResetPasswordConfirm;