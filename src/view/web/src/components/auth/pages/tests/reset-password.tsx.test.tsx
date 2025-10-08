import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, useNavigate } from 'react-router-dom';
import '@testing-library/jest-dom';
import ResetPassword from '../reset-password.tsx';
import userAuthService from '../../../../services/auth.ts';

// Mocks
jest.mock('../../../services/auth');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn()
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

const renderResetPassword = () => {
  const mockNavigate = jest.fn();
  
  jest.mocked(useNavigate).mockReturnValue(mockNavigate);
  
  return {
    ...render(
      <BrowserRouter>
        <ResetPassword />
      </BrowserRouter>
    ),
    mockNavigate
  };
};

describe('ResetPassword Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Rendering - Initial State', () => {
    it('should render reset password form with all required fields', () => {
      renderResetPassword();
      
      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Send Email' })).toBeInTheDocument();
    });

    it('should render title and description', () => {
      renderResetPassword();
      
      expect(screen.getByText('Forgot Password?')).toBeInTheDocument();
      expect(screen.getByText("Enter your email address and we'll send you a reset link.")).toBeInTheDocument();
    });

    it('should render back to login link', () => {
      renderResetPassword();
      
      expect(screen.getByText('Remember your password?')).toBeInTheDocument();
      expect(screen.getByText('Back to Login')).toBeInTheDocument();
    });

    it('should have email input with correct attributes', () => {
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email') as HTMLInputElement;
      
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('required');
      expect(emailInput).toHaveAttribute('aria-label', 'Email Address');
    });
  });

  describe('Form Interactions', () => {
    it('should update email field on change', () => {
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email') as HTMLInputElement;
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      
      expect(emailInput.value).toBe('test@example.com');
    });
  });

  describe('Form Validation', () => {
    it('should show error when submitting empty form', async () => {
      renderResetPassword();
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email is required');
      });
    });

    it('should show error when email is whitespace only', async () => {
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: '   ' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email is required');
      });
    });

    it('should show error for invalid email format - missing @', async () => {
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'invalidemail.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter a valid email address');
      });
    });

    it('should show error for invalid email format - missing domain', async () => {
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter a valid email address');
      });
    });

    it('should show error for invalid email format - missing local part', async () => {
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: '@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter a valid email address');
      });
    });

    it('should accept valid email format', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'valid@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledWith('valid@example.com');
      });
    });
  });

  describe('Form Submission', () => {
    it('should call resetPassword service with correct email', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledWith('test@example.com');
      });
    });

    it('should display success screen after successful submission', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Check Your Email')).toBeInTheDocument();
      });
      
      expect(screen.getByText("We've sent a password reset link to test@example.com.")).toBeInTheDocument();
    });

    it('should display error message on submission failure', async () => {
      const mockResetPassword = jest.fn().mockRejectedValue(new Error('Email not found'));
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email not found');
      });
    });

    it('should display generic error message when error has no message', async () => {
      const mockResetPassword = jest.fn().mockRejectedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Failed to send reset email. Please try again.');
      });
    });

    it('should disable submit button while loading', async () => {
      const mockResetPassword = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' }) as HTMLButtonElement;
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      expect(submitButton.disabled).toBe(true);
      
      await waitFor(() => {
        expect(submitButton.disabled).toBe(false);
      });
    });

    it('should add loading class to submit button while processing', async () => {
      const mockResetPassword = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      expect(submitButton.className).toContain('loading');
      
      await waitFor(() => {
        expect(submitButton.className).not.toContain('loading');
      });
    });

    it('should clear error when submitting valid form', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      
      const emailInput = screen.getByPlaceholderText('Email');
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Success State', () => {
    it('should render success screen with correct email', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Check Your Email')).toBeInTheDocument();
      });
      
      expect(screen.getByText("We've sent a password reset link to user@example.com.")).toBeInTheDocument();
    });

    it('should render Back button on success screen', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Back' })).toBeInTheDocument();
      });
    });

    it('should render Resend link on success screen', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      expect(screen.getByText("Didn't see the email?")).toBeInTheDocument();
    });

    it('should hide email input form on success screen', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Email')).not.toBeInTheDocument();
      });
    });
  });

  describe('Resend Functionality', () => {
    it('should resend email when Resend link is clicked', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      mockResetPassword.mockClear();
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledWith('test@example.com');
      });
    });

    it('should activate cooldown after resending', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      mockResetPassword.mockClear();
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledTimes(1);
      });
      
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledTimes(1);
      });
    });

    it('should disable resend link during cooldown period', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(resendLink.className).toContain('disabled');
      });
      
      expect(resendLink).toHaveStyle({ cursor: 'not-allowed', opacity: 0.6 });
    });

    it('should re-enable resend link after cooldown period', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(resendLink.className).toContain('disabled');
      });
      
      jest.advanceTimersByTime(10000);
      
      await waitFor(() => {
        expect(resendLink.className).not.toContain('disabled');
      });
      
      expect(resendLink).toHaveStyle({ cursor: 'pointer', opacity: 1.0 });
    });

    it('should disable resend link while loading', async () => {
      const mockResetPassword = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      expect(resendLink.className).toContain('disabled');
      expect(resendLink).toHaveStyle({ cursor: 'not-allowed' });
    });

    it('should display error on resend failure', async () => {
      const mockResetPassword = jest.fn()
        .mockResolvedValueOnce({})
        .mockRejectedValueOnce(new Error('Network error'));
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Network error');
      });
    });

    it('should clear error before resending', async () => {
      const mockResetPassword = jest.fn()
        .mockResolvedValueOnce({})
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('First error');
      });
      
      jest.advanceTimersByTime(10000);
      
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('should navigate to login when "Back to Login" is clicked from initial form', () => {
      const { mockNavigate } = renderResetPassword();
      const backToLoginLink = screen.getByText('Back to Login');
      
      fireEvent.click(backToLoginLink);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('should navigate to login when "Back" button is clicked from success screen', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      const { mockNavigate } = renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Back' })).toBeInTheDocument();
      });
      
      const backButton = screen.getByRole('button', { name: 'Back' });
      fireEvent.click(backButton);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('should disable Back button while loading on success screen', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Back' })).toBeInTheDocument();
      });
      
      mockResetPassword.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      const backButton = screen.getByRole('button', { name: 'Back' }) as HTMLButtonElement;
      expect(backButton.disabled).toBe(true);
    });
  });

  describe('Cooldown Timing', () => {
    it('should use 10 second cooldown period', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(resendLink.className).toContain('disabled');
      });
      
      jest.advanceTimersByTime(9000);
      expect(resendLink.className).toContain('disabled');
      
      jest.advanceTimersByTime(1000);
      
      await waitFor(() => {
        expect(resendLink.className).not.toContain('disabled');
      });
    });

    it('should allow multiple resends after each cooldown expires', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      
      fireEvent.click(resendLink);
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledTimes(2);
      });
      
      jest.advanceTimersByTime(10000);
      
      fireEvent.click(resendLink);
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledTimes(3);
      });
    });
  });

  describe('Edge Cases', () => {
    it('should trim whitespace from email before validation', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: '  test@example.com  ' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledWith('  test@example.com  ');
      });
    });

    it('should handle special characters in email', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'user+tag@example.co.uk' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockResetPassword).toHaveBeenCalledWith('user+tag@example.co.uk');
      });
    });

    it('should not validate format when email is empty', async () => {
      renderResetPassword();
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email is required');
      });
      
      expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument();
    });
  });

  describe('Resend Link Styling', () => {
    it('should have pointer cursor when enabled', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      jest.advanceTimersByTime(10000);
      
      const resendLink = screen.getByText('Resend');
      expect(resendLink).toHaveStyle({ cursor: 'pointer', opacity: 1.0 });
    });

    it('should have not-allowed cursor when disabled', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(resendLink).toHaveStyle({ cursor: 'not-allowed', opacity: 0.6 });
      });
    });

    it('should have disabled class when on cooldown', async () => {
      const mockResetPassword = jest.fn().mockResolvedValue({});
      (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
      
      renderResetPassword();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Send Email' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Resend')).toBeInTheDocument();
      });
      
      const resendLink = screen.getByText('Resend');
      fireEvent.click(resendLink);
      
      await waitFor(() => {
        expect(resendLink.className).toContain('disabled');
      });
    });
  });

  describe('Email Validation Regex', () => {
    const validEmails = [
      'simple@example.com',
      'user.name@example.com',
      'user+tag@example.co.uk',
      'user_name@example-domain.com',
      'user123@test.org'
    ];

    const invalidEmails = [
      'invalid',
      '@example.com',
      'user@',
      'user@.com',
      'user@domain',
      'user @example.com',
      'user@exam ple.com'
    ];

    validEmails.forEach(email => {
      it(`should accept valid email: ${email}`, async () => {
        const mockResetPassword = jest.fn().mockResolvedValue({});
        (userAuthService.resetPassword as jest.Mock) = mockResetPassword;
        
        renderResetPassword();
        const emailInput = screen.getByPlaceholderText('Email');
        const submitButton = screen.getByRole('button', { name: 'Send Email' });
        
        fireEvent.change(emailInput, { target: { value: email } });
        fireEvent.click(submitButton);
        
        await waitFor(() => {
          expect(mockResetPassword).toHaveBeenCalledWith(email);
        });
      });
    });

    invalidEmails.forEach(email => {
      it(`should reject invalid email: ${email}`, async () => {
        renderResetPassword();
        const emailInput = screen.getByPlaceholderText('Email');
        const submitButton = screen.getByRole('button', { name: 'Send Email' });
        
        fireEvent.change(emailInput, { target: { value: email } });
        fireEvent.click(submitButton);
        
        await waitFor(() => {
          expect(screen.getByRole('alert')).toHaveTextContent('Please enter a valid email address');
        });
      });
    });
  });
});