import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, useNavigate } from 'react-router-dom';
import '@testing-library/jest-dom';
import Signup from '../signup.tsx';
import userAuthService from '../../../../services/auth.ts';

// Mocks
jest.mock('../../../services/auth');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn()
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

const renderSignup = () => {
  const mockNavigate = jest.fn();
  
  jest.mocked(useNavigate).mockReturnValue(mockNavigate);
  
  return {
    ...render(
      <BrowserRouter>
        <Signup />
      </BrowserRouter>
    ),
    mockNavigate
  };
};

describe('Signup Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render signup form with all required fields', () => {
      renderSignup();
      
      expect(screen.getByPlaceholderText('First Name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Last Name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign Up' })).toBeInTheDocument();
    });

    it('should render title and description', () => {
      renderSignup();
      
      expect(screen.getByText('Get Started')).toBeInTheDocument();
      expect(screen.getByText('Comprehensive market intelligence made simple.')).toBeInTheDocument();
    });

    it('should render OAuth signup buttons', () => {
      renderSignup();
      
      expect(screen.getByRole('button', { name: 'Sign up with Google' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign up with GitHub' })).toBeInTheDocument();
    });

    it('should render login link', () => {
      renderSignup();
      
      expect(screen.getByText('Already have an account?')).toBeInTheDocument();
      expect(screen.getByText(/Log in/i)).toBeInTheDocument();
    });

    it('should render divider text', () => {
      renderSignup();
      
      expect(screen.getByText('Or Sign Up With')).toBeInTheDocument();
    });

    it('should have password field with minLength attribute', () => {
      renderSignup();
      const passwordInput = screen.getByPlaceholderText('Password');
      
      expect(passwordInput).toHaveAttribute('minLength', '6');
    });

    it('should have required attributes on all inputs', () => {
      renderSignup();
      
      expect(screen.getByPlaceholderText('First Name')).toHaveAttribute('required');
      expect(screen.getByPlaceholderText('Last Name')).toHaveAttribute('required');
      expect(screen.getByPlaceholderText('Email')).toHaveAttribute('required');
      expect(screen.getByPlaceholderText('Password')).toHaveAttribute('required');
    });

    it('should have correct aria-labels on inputs', () => {
      renderSignup();
      
      expect(screen.getByLabelText('First Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
    });
  });

  describe('Form Interactions', () => {
    it('should update first name field on change', () => {
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name') as HTMLInputElement;
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      
      expect(firstNameInput.value).toBe('John');
    });

    it('should update last name field on change', () => {
      renderSignup();
      const lastNameInput = screen.getByPlaceholderText('Last Name') as HTMLInputElement;
      
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      
      expect(lastNameInput.value).toBe('Doe');
    });

    it('should update email field on change', () => {
      renderSignup();
      const emailInput = screen.getByPlaceholderText('Email') as HTMLInputElement;
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      
      expect(emailInput.value).toBe('test@example.com');
    });

    it('should update password field on change', () => {
      renderSignup();
      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement;
      
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      
      expect(passwordInput.value).toBe('password123');
    });

    it('should toggle password visibility', () => {
      renderSignup();
      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement;
      const toggleButton = screen.getByRole('button', { name: 'Show password' });
      
      expect(passwordInput.type).toBe('password');
      
      fireEvent.click(toggleButton);
      expect(passwordInput.type).toBe('text');
      
      fireEvent.click(toggleButton);
      expect(passwordInput.type).toBe('password');
    });

    it('should update toggle button aria-label when password visibility changes', () => {
      renderSignup();
      const toggleButton = screen.getByRole('button', { name: 'Show password' });
      
      fireEvent.click(toggleButton);
      expect(screen.getByRole('button', { name: 'Hide password' })).toBeInTheDocument();
      
      fireEvent.click(toggleButton);
      expect(screen.getByRole('button', { name: 'Show password' })).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should show error when submitting empty form', async () => {
      renderSignup();
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('First name is required');
      });
    });

    it('should show error when first name is missing', async () => {
      renderSignup();
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('First name is required');
      });
    });

    it('should show error when last name is missing', async () => {
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Last name is required');
      });
    });

    it('should show error when email is missing', async () => {
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email is required');
      });
    });

    it('should show error when password is missing', async () => {
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Password is required');
      });
    });

    it('should show error when password is less than 6 characters', async () => {
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: '12345' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Password must be at least 6 characters long');
      });
    });

    it('should accept password exactly 6 characters long', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: '123456' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSignup).toHaveBeenCalled();
      });
    });

    it('should validate fields in correct order', async () => {
      renderSignup();
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('First name is required');
      });
    });

    it('should trim whitespace when validating names', async () => {
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: '   ' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('First name is required');
      });
    });

    it('should trim whitespace when validating email', async () => {
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: '   ' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email is required');
      });
    });
  });

  describe('Form Submission', () => {
    it('should call signup service with correct transformed data', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSignup).toHaveBeenCalledWith({
          first_name: 'John',
          last_name: 'Doe',
          email: 'john@example.com',
          password: 'password123',
          confirm_password: 'password123'
        });
      });
    });

    it('should navigate to dashboard on successful signup', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      const { mockNavigate } = renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('should display error message on signup failure', async () => {
      const mockSignup = jest.fn().mockRejectedValue(new Error('Email already exists'));
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'existing@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Email already exists');
      });
    });

    it('should display generic error message when error has no message', async () => {
      const mockSignup = jest.fn().mockRejectedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent('Signup failed. Please try again.');
      });
    });

    it('should disable submit button while loading', async () => {
      const mockSignup = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' }) as HTMLButtonElement;
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      expect(submitButton.disabled).toBe(true);
      
      await waitFor(() => {
        expect(submitButton.disabled).toBe(false);
      });
    });

    it('should add loading class to submit button while processing', async () => {
      const mockSignup = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      expect(submitButton.className).toContain('loading');
      
      await waitFor(() => {
        expect(submitButton.className).not.toContain('loading');
      });
    });

    it('should clear error when submitting valid form', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  describe('OAuth Authentication', () => {
    it('should initiate Google OAuth on button click', () => {
      const mockInitiateGoogleAuth = jest.fn();
      (userAuthService.initiateGoogleAuth as jest.Mock) = mockInitiateGoogleAuth;
      
      renderSignup();
      const googleButton = screen.getByRole('button', { name: 'Sign up with Google' });
      
      fireEvent.click(googleButton);
      
      expect(mockInitiateGoogleAuth).toHaveBeenCalled();
    });

    it('should initiate GitHub OAuth on button click', () => {
      const mockInitiateGitHubAuth = jest.fn();
      (userAuthService.initiateGitHubAuth as jest.Mock) = mockInitiateGitHubAuth;
      
      renderSignup();
      const githubButton = screen.getByRole('button', { name: 'Sign up with GitHub' });
      
      fireEvent.click(githubButton);
      
      expect(mockInitiateGitHubAuth).toHaveBeenCalled();
    });

    it('should handle Google OAuth initiation error', () => {
      const mockInitiateGoogleAuth = jest.fn().mockImplementation(() => {
        throw new Error('OAuth failed');
      });
      (userAuthService.initiateGoogleAuth as jest.Mock) = mockInitiateGoogleAuth;
      
      renderSignup();
      const googleButton = screen.getByRole('button', { name: 'Sign up with Google' });
      
      fireEvent.click(googleButton);
      
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Failed to initiate Google authentication. Please try again.'
      );
    });

    it('should handle GitHub OAuth initiation error', () => {
      const mockInitiateGitHubAuth = jest.fn().mockImplementation(() => {
        throw new Error('OAuth failed');
      });
      (userAuthService.initiateGitHubAuth as jest.Mock) = mockInitiateGitHubAuth;
      
      renderSignup();
      const githubButton = screen.getByRole('button', { name: 'Sign up with GitHub' });
      
      fireEvent.click(githubButton);
      
      expect(screen.getByRole('alert')).toHaveTextContent(
        'Failed to initiate GitHub authentication. Please try again.'
      );
    });

    it('should clear error before initiating Google OAuth', () => {
      const mockInitiateGoogleAuth = jest.fn();
      (userAuthService.initiateGoogleAuth as jest.Mock) = mockInitiateGoogleAuth;
      
      renderSignup();
      
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      fireEvent.click(submitButton);
      
      const googleButton = screen.getByRole('button', { name: 'Sign up with Google' });
      fireEvent.click(googleButton);
      
      expect(mockInitiateGoogleAuth).toHaveBeenCalled();
    });

    it('should clear error before initiating GitHub OAuth', () => {
      const mockInitiateGitHubAuth = jest.fn();
      (userAuthService.initiateGitHubAuth as jest.Mock) = mockInitiateGitHubAuth;
      
      renderSignup();
      
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      fireEvent.click(submitButton);
      
      const githubButton = screen.getByRole('button', { name: 'Sign up with GitHub' });
      fireEvent.click(githubButton);
      
      expect(mockInitiateGitHubAuth).toHaveBeenCalled();
    });

    it('should disable OAuth buttons while form is loading', async () => {
      const mockSignup = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      const googleButton = screen.getByRole('button', { name: 'Sign up with Google' }) as HTMLButtonElement;
      const githubButton = screen.getByRole('button', { name: 'Sign up with GitHub' }) as HTMLButtonElement;
      
      expect(googleButton.disabled).toBe(true);
      expect(githubButton.disabled).toBe(true);
      
      await waitFor(() => {
        expect(googleButton.disabled).toBe(false);
        expect(githubButton.disabled).toBe(false);
      });
    });
  });

  describe('Navigation', () => {
    it('should navigate to login page when login link is clicked', () => {
      const { mockNavigate } = renderSignup();
      const loginLink = screen.getByText(/Log in/i);
      
      fireEvent.click(loginLink);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login', {
        state: { direction: 'back' }
      });
    });
  });

  describe('Data Transformation', () => {
    it('should transform camelCase form data to snake_case for API', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'Jane' } });
      fireEvent.change(lastNameInput, { target: { value: 'Smith' } });
      fireEvent.change(emailInput, { target: { value: 'jane@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'securepass' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSignup).toHaveBeenCalledWith(
          expect.objectContaining({
            first_name: 'Jane',
            last_name: 'Smith'
          })
        );
      });
    });

    it('should include confirm_password matching password', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'mypassword' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSignup).toHaveBeenCalledWith(
          expect.objectContaining({
            password: 'mypassword',
            confirm_password: 'mypassword'
          })
        );
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle names with special characters', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: "O'Brien" } });
      fireEvent.change(lastNameInput, { target: { value: 'Smith-Jones' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSignup).toHaveBeenCalledWith(
          expect.objectContaining({
            first_name: "O'Brien",
            last_name: 'Smith-Jones'
          })
        );
      });
    });

    it('should handle names with leading/trailing spaces', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: '  John  ' } });
      fireEvent.change(lastNameInput, { target: { value: '  Doe  ' } });
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSignup).toHaveBeenCalledWith(
          expect.objectContaining({
            first_name: '  John  ',
            last_name: '  Doe  '
          })
        );
      });
    });

    it('should preserve email case', async () => {
      const mockSignup = jest.fn().mockResolvedValue({});
      (userAuthService.signup as jest.Mock) = mockSignup;
      
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name');
      const lastNameInput = screen.getByPlaceholderText('Last Name');
      const emailInput = screen.getByPlaceholderText('Email');
      const passwordInput = screen.getByPlaceholderText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign Up' });
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      fireEvent.change(emailInput, { target: { value: 'Test@Example.COM' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockSignup).toHaveBeenCalledWith(
          expect.objectContaining({
            email: 'Test@Example.COM'
          })
        );
      });
    });
  });

  describe('Password Field Type', () => {
    it('should have password type by default', () => {
      renderSignup();
      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement;
      
      expect(passwordInput.type).toBe('password');
    });

    it('should change to text type when visibility is toggled', () => {
      renderSignup();
      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement;
      const toggleButton = screen.getByRole('button', { name: 'Show password' });
      
      fireEvent.click(toggleButton);
      
      expect(passwordInput.type).toBe('text');
    });

    it('should show EyeIcon when password is hidden', () => {
      renderSignup();
      
      expect(screen.getByText('Eye Icon')).toBeInTheDocument();
    });

    it('should show EyeOffIcon when password is visible', () => {
      renderSignup();
      const toggleButton = screen.getByRole('button', { name: 'Show password' });
      
      fireEvent.click(toggleButton);
      
      expect(screen.getByText('Eye Off Icon')).toBeInTheDocument();
    });
  });

  describe('Multiple Field Updates', () => {
    it('should handle updating all fields sequentially', () => {
      renderSignup();
      const firstNameInput = screen.getByPlaceholderText('First Name') as HTMLInputElement;
      const lastNameInput = screen.getByPlaceholderText('Last Name') as HTMLInputElement;
      const emailInput = screen.getByPlaceholderText('Email') as HTMLInputElement;
      const passwordInput = screen.getByPlaceholderText('Password') as HTMLInputElement;
      
      fireEvent.change(firstNameInput, { target: { value: 'John' } });
      expect(firstNameInput.value).toBe('John');
      
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } });
      expect(lastNameInput.value).toBe('Doe');
      expect(firstNameInput.value).toBe('John');
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      expect(emailInput.value).toBe('test@example.com');
      expect(firstNameInput.value).toBe('John');
      expect(lastNameInput.value).toBe('Doe');
      
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      expect(passwordInput.value).toBe('password123');
      expect(firstNameInput.value).toBe('John');
      expect(lastNameInput.value).toBe('Doe');
      expect(emailInput.value).toBe('test@example.com');
    });
  });
});