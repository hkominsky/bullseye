import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, useNavigate, useSearchParams } from 'react-router-dom';
import '@testing-library/jest-dom';
import ResetPasswordConfirm from '../reset-password-confirm.tsx';
import userAuthService from '../../../../services/auth.ts';

// Mocks
jest.mock('../../../services/auth');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
  useSearchParams: jest.fn()
}));

jest.mock('../widgets/auth-layout.tsx', () => {
  return function AuthLayout({ title, description, error, children }: any) {
    return (
      <div>
        <h1>{title}</h1>
        <p>{description}</p>
        {error && <div role="alert">{error}</div>}
        {children}
      </div>
    );
  };
});

const renderResetPasswordConfirm = (token: string | null = 'valid-token') => {
  const mockNavigate = jest.fn();
  const mockSearchParams = new URLSearchParams();
  
  if (token) {
    mockSearchParams.set('token', token);
  }
  
  jest.mocked(useNavigate).mockReturnValue(mockNavigate);
  jest.mocked(useSearchParams).mockReturnValue([mockSearchParams, jest.fn()]);
  
  return {
    ...render(
      <BrowserRouter>
        <ResetPasswordConfirm />
      </BrowserRouter>
    ),
    mockNavigate
  };
};

describe('ResetPasswordConfirm Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render reset password form with all required fields', () => {
      renderResetPasswordConfirm();
      
      expect(screen.getByPlaceholderText('New Password')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Confirm New Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Reset Password' })).toBeInTheDocument();
    });

    it('should render title and description', () => {
      renderResetPasswordConfirm();
      
      expect(screen.getByText('Reset Your Password')).toBeInTheDocument();
      expect(screen.getByText('Enter your new password below.')).toBeInTheDocument();
    });

    it('should render back to login link', () => {
      renderResetPasswordConfirm();
      
      expect(screen.getByText('Remember your password?')).toBeInTheDocument();
      expect(screen.getByText('Back to Login')).toBeInTheDocument();
    });

    it('should display error when token is missing from URL', () => {
      renderResetPasswordConfirm(null);
      
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid or missing reset token');
    });

    it('should disable submit button when token is missing', () => {
      renderResetPasswordConfirm(null);
      const submitButton = screen.getByRole('button', { name: 'Reset Password' }) as HTMLButtonElement;
      
      expect(submitButton.disabled).toBe(true);
    });
  });

  describe('Form Interactions', () => {
    it('should update new password field on change', () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password') as HTMLInputElement;
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      
      expect(newPasswordInput.value).toBe('newpassword123');
    });

    it('should update confirm password field on change', () => {
      renderResetPasswordConfirm();
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password') as HTMLInputElement;
      
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      
      expect(confirmPasswordInput.value).toBe('newpassword123');
    });
  });

  describe('Form Validation', () => {
    it('should show error when submitting empty form', async () => {
      renderResetPasswordConfirm();
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('All fields are required');
      });
    });

    it('should show error when new password is missing', async () => {
      renderResetPasswordConfirm();
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('All fields are required');
      });
    });

    it('should show error when confirm password is missing', async () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('All fields are required');
      });
    });

    it('should show error when password is less than 8 characters', async () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'short' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'short' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Password must be at least 8 characters long');
      });
    });

    it('should show error when passwords do not match', async () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'differentpass123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Passwords do not match');
      });
    });

    it('should validate password length before checking if passwords match', async () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'short' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'different' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Password must be at least 8 characters long');
      });
    });
  });

  describe('Form Submission', () => {
    it('should call confirmPasswordReset service with correct data on successful submission', async () => {
      const mockConfirmPasswordReset = jest.fn().mockResolvedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm('reset-token-123');
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockConfirmPasswordReset).toHaveBeenCalledWith('reset-token-123', 'newpassword123');
      });
    });

    it('should display success screen after successful password reset', async () => {
      const mockConfirmPasswordReset = jest.fn().mockResolvedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Password Reset Successful')).toBeInTheDocument();
      });
      
      expect(screen.getByText('Your password has been successfully reset. You can now log in with your new password.')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Go to Login' })).toBeInTheDocument();
    });

    it('should display error message on password reset failure', async () => {
      const mockConfirmPasswordReset = jest.fn().mockRejectedValue(new Error('Invalid or expired token'));
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Invalid or expired token');
      });
    });

    it('should display generic error message when error has no message', async () => {
      const mockConfirmPasswordReset = jest.fn().mockRejectedValue(new Error());
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to reset password. Please try again.');
      });
    });

    it('should disable submit button while loading', async () => {
      const mockConfirmPasswordReset = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' }) as HTMLButtonElement;
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      expect(submitButton.disabled).toBe(true);
      
      await waitFor(() => {
        expect(submitButton.disabled).toBe(false);
      });
    });

    it('should clear error when submitting valid form', async () => {
      const mockConfirmPasswordReset = jest.fn().mockResolvedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('should navigate to login when "Back to Login" is clicked', () => {
      const { mockNavigate } = renderResetPasswordConfirm();
      const backToLoginLink = screen.getByText('Back to Login');
      
      fireEvent.click(backToLoginLink);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('should navigate to login when "Go to Login" button is clicked after success', async () => {
      const mockConfirmPasswordReset = jest.fn().mockResolvedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      const { mockNavigate } = renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Password Reset Successful')).toBeInTheDocument();
      });
      
      const goToLoginButton = screen.getByRole('button', { name: 'Go to Login' });
      fireEvent.click(goToLoginButton);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  describe('Token Handling', () => {
    it('should extract token from URL parameters on mount', () => {
      renderResetPasswordConfirm('test-token-456');
      
      const submitButton = screen.getByRole('button', { name: 'Reset Password' }) as HTMLButtonElement;
      expect(submitButton.disabled).toBe(false);
    });

    it('should not allow submission without valid token', async () => {
      const mockConfirmPasswordReset = jest.fn().mockResolvedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm(null);
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockConfirmPasswordReset).not.toHaveBeenCalled();
      });
    });
  });

  describe('Success State', () => {
    it('should show success message with proper styling', async () => {
      const mockConfirmPasswordReset = jest.fn().mockResolvedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Password Reset Successful')).toBeInTheDocument();
      });
      
      expect(screen.queryByPlaceholderText('New Password')).not.toBeInTheDocument();
      expect(screen.queryByPlaceholderText('Confirm New Password')).not.toBeInTheDocument();
    });

    it('should not show back to login link on success screen', async () => {
      const mockConfirmPasswordReset = jest.fn().mockResolvedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Password Reset Successful')).toBeInTheDocument();
      });
      
      expect(screen.queryByText('Remember your password?')).not.toBeInTheDocument();
      expect(screen.queryByText('Back to Login')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle whitespace-only passwords as empty', async () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: '   ' } });
      fireEvent.change(confirmPasswordInput, { target: { value: '   ' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('All fields are required');
      });
    });

    it('should handle password exactly 8 characters long', async () => {
      const mockConfirmPasswordReset = jest.fn().mockResolvedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: '12345678' } });
      fireEvent.change(confirmPasswordInput, { target: { value: '12345678' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockConfirmPasswordReset).toHaveBeenCalledWith('valid-token', '12345678');
      });
    });

    it('should handle service errors without message property', async () => {
      const mockConfirmPasswordReset = jest.fn().mockRejectedValue({});
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to reset password. Please try again.');
      });
    });
  });

  describe('Loading State', () => {
    it('should add loading class to submit button while processing', async () => {
      const mockConfirmPasswordReset = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' });
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      expect(submitButton.className).toContain('loading');
      
      await waitFor(() => {
        expect(submitButton.className).not.toContain('loading');
      });
    });

    it('should re-enable button after error', async () => {
      const mockConfirmPasswordReset = jest.fn().mockRejectedValue(new Error('Test error'));
      (userAuthService.confirmPasswordReset as jest.Mock) = mockConfirmPasswordReset;
      
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      const submitButton = screen.getByRole('button', { name: 'Reset Password' }) as HTMLButtonElement;
      
      fireEvent.change(newPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'newpassword123' } });
      fireEvent.click(submitButton);
      
      expect(submitButton.disabled).toBe(true);
      
      await waitFor(() => {
        expect(submitButton.disabled).toBe(false);
      });
    });
  });

  describe('Input Attributes', () => {
    it('should have required attribute on password inputs', () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      
      expect(newPasswordInput).toHaveAttribute('required');
      expect(confirmPasswordInput).toHaveAttribute('required');
    });

    it('should have minLength attribute set to 8 on password inputs', () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password');
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password');
      
      expect(newPasswordInput).toHaveAttribute('minLength', '8');
      expect(confirmPasswordInput).toHaveAttribute('minLength', '8');
    });

    it('should have password type on both inputs', () => {
      renderResetPasswordConfirm();
      const newPasswordInput = screen.getByPlaceholderText('New Password') as HTMLInputElement;
      const confirmPasswordInput = screen.getByPlaceholderText('Confirm New Password') as HTMLInputElement;
      
      expect(newPasswordInput.type).toBe('password');
      expect(confirmPasswordInput.type).toBe('password');
    });
  });
});