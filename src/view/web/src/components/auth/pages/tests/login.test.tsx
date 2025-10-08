import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, useNavigate, useSearchParams } from 'react-router-dom';
import '@testing-library/jest-dom';
import Login from '../login.tsx';
import userAuthService from '../../../../services/auth.ts';

// Mocks
jest.mock('../../../services/auth');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn(),
  useSearchParams: jest.fn()
}));
jest.mock('../../../assets/svg/google-icon.svg', () => ({
  ReactComponent: () => <div>Google Icon</div>
}));
jest.mock('../../../assets/svg/github-icon.svg', () => ({
  ReactComponent: () => <div>GitHub Icon</div>
}));
jest.mock('../../../assets/svg/eye-icon.svg', () => ({
  ReactComponent: () => <div>Eye Icon</div>
}));
jest.mock('../../../assets/svg/eye-off-icon.svg', () => ({
  ReactComponent: () => <div>Eye Off Icon</div>
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

const renderLogin = (searchParams = '') => {
  const mockNavigate = jest.fn();
  const mockSearchParams = new URLSearchParams(searchParams);
  
  jest.mocked(useNavigate).mockReturnValue(mockNavigate);
  jest.mocked(useSearchParams).mockReturnValue([mockSearchParams, jest.fn()]);
  
  return {
    ...render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    ),
    mockNavigate
  };
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render login form with all required fields', () => {
      renderLogin();
      
      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
      expect(screen.getByText('Remember Me')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Log In' })).toBeInTheDocument();
    });

    it('should render OAuth login buttons', () => {
      renderLogin();
      
      expect(screen.getByRole('button', { name: /log in with google/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /log in with github/i })).toBeInTheDocument();
    });

    it('should render forgot password and signup links', () => {
      renderLogin();
      
      expect(screen.getByText('Forgot Password?')).toBeInTheDocument();
      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
    });

    it('should display OAuth error from URL params', () => {
      renderLogin('error=oauth_failed');
      
      expect(screen.getByRole('alert')).toHaveTextContent(
        'OAuth authentication failed. Please try again or use email/password login.'
      );
    });
  });

  describe('Form Interactions', () => {
    it('should update email field on change', () => {
      renderLogin();
      const emailInput = screen.getByPlaceholderText('Email') as HTMLInputElement;
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      
      expect(emailInput.value).toBe('test@example.com');
    });

    it('should update password field on change', () => {
      renderLogin();
      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement;
      
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      
      expect(passwordInput.value).toBe('password123');
    });

    it('should toggle remember me checkbox', () => {
      renderLogin();
      const checkbox = screen.getByRole('checkbox') as HTMLInputElement;
      
      expect(checkbox.checked).toBe(false);
      fireEvent.click(checkbox);
      expect(checkbox.checked).toBe(true);
    });

    it('should toggle password visibility', () => {
      renderLogin();
      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement;
      const toggleButton = screen.getByRole('button', { name: /show password/i });
      
      expect(passwordInput.type).toBe('password');
      fireEvent.click(toggleButton);
      expect(passwordInput.type).toBe('text');
      fireEvent.click(toggleButton);
      expect(passwordInput.type).toBe('password');
    });
  });

  describe('Form Submission', () => {
    it('should show error when submitting empty form', async () => {
      renderLogin();
      const submitButton = screen.getByRole('button', { name: 'Log In' });
      
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Please fill in all fields');
      });
    });

    it('should show error when email is missing', async () => {
      renderLogin();
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Log In' });
      
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Please fill in all fields');
      });
    });

    it('should show error when password is missing', async () => {
      renderLogin();
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Log In' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Please fill in all fields');
      });
    });

    it('should call login service with correct data on successful submission', async () => {
      const mockLogin = jest.fn().mockResolvedValue({});
      (userAuthService.login as jest.Mock) = mockLogin;
      
      const { mockNavigate } = renderLogin();
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Log In' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
          rememberMe: false
        });
      });
      
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('should set session timeout when remember me is not checked', async () => {
      const mockLogin = jest.fn().mockResolvedValue({});
      const mockSetSessionTimeout = jest.fn();
      (userAuthService.login as jest.Mock) = mockLogin;
      (userAuthService.setSessionTimeout as jest.Mock) = mockSetSessionTimeout;
      
      renderLogin();
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Log In' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSetSessionTimeout).toHaveBeenCalledWith(30);
      });
    });

    it('should not set session timeout when remember me is checked', async () => {
      const mockLogin = jest.fn().mockResolvedValue({});
      const mockSetSessionTimeout = jest.fn();
      (userAuthService.login as jest.Mock) = mockLogin;
      (userAuthService.setSessionTimeout as jest.Mock) = mockSetSessionTimeout;
      
      renderLogin();
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const checkbox = screen.getByRole('checkbox');
      const submitButton = screen.getByRole('button', { name: 'Log In' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(checkbox);
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled();
      });
      
      expect(mockSetSessionTimeout).not.toHaveBeenCalled();
    });

    it('should display error message on login failure', async () => {
      const mockLogin = jest.fn().mockRejectedValue(new Error('Invalid credentials'));
      (userAuthService.login as jest.Mock) = mockLogin;
      
      renderLogin();
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Log In' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Invalid credentials');
      });
    });

    it('should disable submit button while loading', async () => {
      const mockLogin = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.login as jest.Mock) = mockLogin;
      
      renderLogin();
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Log In' }) as HTMLButtonElement;
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      expect(submitButton.disabled).toBe(true);
      
      await waitFor(() => {
        expect(submitButton.disabled).toBe(false);
      });
    });
  });

  describe('OAuth Authentication', () => {
    it('should initiate Google OAuth on button click', () => {
      const mockInitiateGoogleAuth = jest.fn();
      (userAuthService.initiateGoogleAuth as jest.Mock) = mockInitiateGoogleAuth;
      
      renderLogin();
      const googleButton = screen.getByRole('button', { name: /log in with google/i });
      
      fireEvent.click(googleButton);
      
      expect(mockInitiateGoogleAuth).toHaveBeenCalled();
    });

    it('should initiate GitHub OAuth on button click', () => {
      const mockInitiateGitHubAuth = jest.fn();
      (userAuthService.initiateGitHubAuth as jest.Mock) = mockInitiateGitHubAuth;
      
      renderLogin();
      const githubButton = screen.getByRole('button', { name: /log in with github/i });
      
      fireEvent.click(githubButton);
      
      expect(mockInitiateGitHubAuth).toHaveBeenCalled();
    });

    it('should handle Google OAuth initiation error', () => {
      const mockInitiateGoogleAuth = jest.fn().mockImplementation(() => {
        throw new Error('OAuth failed');
      });
      (userAuthService.initiateGoogleAuth as jest.Mock) = mockInitiateGoogleAuth;
      
      renderLogin();
      const googleButton = screen.getByRole('button', { name: /log in with google/i });
      
      fireEvent.click(googleButton);
      
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Failed to initiate Google authentication. Please try again.'
      );
    });
  });

  describe('Navigation', () => {
    it('should navigate to forgot password page', () => {
      const { mockNavigate } = renderLogin();
      const forgotPasswordButton = screen.getByText('Forgot Password?');
      
      fireEvent.click(forgotPasswordButton);
      
      expect(mockNavigate).toHaveBeenCalledWith('/reset-password', {
        state: { direction: 'forward' }
      });
    });

    it('should navigate to signup page', () => {
      const { mockNavigate } = renderLogin();
      const signupLink = screen.getByText(/sign up/i);
      
      fireEvent.click(signupLink);
      
      expect(mockNavigate).toHaveBeenCalledWith('/signup', {
        state: { direction: 'forward' }
      });
    });
  });
});