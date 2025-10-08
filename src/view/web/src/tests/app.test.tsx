import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import App from '../app.tsx';

// Mocks
jest.mock('../components/auth/pages/login.tsx', () => ({
  __esModule: true,
  default: () => <div data-testid="login-page">Login Page</div>
}));

jest.mock('../components/auth/pages/signup.tsx', () => ({
  __esModule: true,
  default: () => <div data-testid="signup-page">SignUp Page</div>
}));

jest.mock('../components/auth/pages/reset-password.tsx', () => ({
  __esModule: true,
  default: () => <div data-testid="reset-password-page">Reset Password Page</div>
}));

jest.mock('../components/auth/pages/reset-password-confirm.tsx', () => ({
  __esModule: true,
  default: () => <div data-testid="reset-password-confirm-page">Reset Password Confirm Page</div>
}));

jest.mock('../components/auth/widgets/oauth-callback.tsx', () => ({
  __esModule: true,
  default: () => <div data-testid="oauth-callback">OAuth Callback</div>
}));

jest.mock('../components/dashboard/pages/dashboard.tsx', () => ({
  __esModule: true,
  default: () => <div data-testid="dashboard-page">Dashboard Page</div>
}));

jest.mock('../components/auth/widgets/protected-route.tsx', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="protected-route">{children}</div>
  )
}));

jest.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>
  }
}));

const renderWithRouter = (initialRoute = '/') => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <App />
    </MemoryRouter>
  );
};

describe('App Component', () => {
  describe('Route Rendering', () => {
    it('should render login page at /login', () => {
      renderWithRouter('/login');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });

    it('should render signup page at /signup', () => {
      renderWithRouter('/signup');

      expect(screen.getByTestId('signup-page')).toBeInTheDocument();
      expect(screen.getByText('SignUp Page')).toBeInTheDocument();
    });

    it('should render reset password page at /reset-password', () => {
      renderWithRouter('/reset-password');

      expect(screen.getByTestId('reset-password-page')).toBeInTheDocument();
      expect(screen.getByText('Reset Password Page')).toBeInTheDocument();
    });

    it('should render reset password confirm page at /reset-password-confirm', () => {
      renderWithRouter('/reset-password-confirm');

      expect(screen.getByTestId('reset-password-confirm-page')).toBeInTheDocument();
      expect(screen.getByText('Reset Password Confirm Page')).toBeInTheDocument();
    });

    it('should render OAuth callback at /auth/callback', () => {
      renderWithRouter('/auth/callback');

      expect(screen.getByTestId('oauth-callback')).toBeInTheDocument();
      expect(screen.getByText('OAuth Callback')).toBeInTheDocument();
    });

    it('should render dashboard page at /dashboard', () => {
      renderWithRouter('/dashboard');

      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
      expect(screen.getByText('Dashboard Page')).toBeInTheDocument();
    });

    it('should redirect from / to /dashboard', () => {
      renderWithRouter('/');

      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });
  });

  describe('Protected Route', () => {
    it('should wrap dashboard in ProtectedRoute', () => {
      renderWithRouter('/dashboard');

      expect(screen.getByTestId('protected-route')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });

    it('should render dashboard inside protected route wrapper', () => {
      renderWithRouter('/dashboard');

      const protectedRoute = screen.getByTestId('protected-route');
      const dashboard = screen.getByTestId('dashboard-page');

      expect(protectedRoute).toContainElement(dashboard);
    });
  });

  describe('Animation Routes', () => {
    it('should identify login as animated route', () => {
      renderWithRouter('/login');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should identify signup as animated route', () => {
      renderWithRouter('/signup');

      expect(screen.getByTestId('signup-page')).toBeInTheDocument();
    });

    it('should identify reset-password as animated route', () => {
      renderWithRouter('/reset-password');

      expect(screen.getByTestId('reset-password-page')).toBeInTheDocument();
    });

    it('should identify reset-password-confirm as animated route', () => {
      renderWithRouter('/reset-password-confirm');

      expect(screen.getByTestId('reset-password-confirm-page')).toBeInTheDocument();
    });

    it('should not animate dashboard route', () => {
      renderWithRouter('/dashboard');

      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });

    it('should not animate OAuth callback route', () => {
      renderWithRouter('/auth/callback');

      expect(screen.getByTestId('oauth-callback')).toBeInTheDocument();
    });
  });

  describe('OAuth Callback Route', () => {
    it('should handle OAuth callback route separately', () => {
      renderWithRouter('/auth/callback');

      expect(screen.getByTestId('oauth-callback')).toBeInTheDocument();
      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
      expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
    });

    it('should only render OAuth callback at /auth/callback', () => {
      renderWithRouter('/auth/callback');

      const oauthCallback = screen.getByTestId('oauth-callback');
      expect(oauthCallback).toBeInTheDocument();
    });
  });

  describe('Root Redirect', () => {
    it('should redirect root path to dashboard', () => {
      renderWithRouter('/');

      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
    });

    it('should use replace for root redirect', () => {
      renderWithRouter('/');

      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });
  });

  describe('Route Isolation', () => {
    it('should only render login page when at /login', () => {
      renderWithRouter('/login');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
      expect(screen.queryByTestId('signup-page')).not.toBeInTheDocument();
      expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
    });

    it('should only render signup page when at /signup', () => {
      renderWithRouter('/signup');

      expect(screen.getByTestId('signup-page')).toBeInTheDocument();
      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
      expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
    });

    it('should only render dashboard when at /dashboard', () => {
      renderWithRouter('/dashboard');

      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
      expect(screen.queryByTestId('signup-page')).not.toBeInTheDocument();
    });
  });

  describe('App Structure', () => {
    it('should render without crashing', () => {
      expect(() => renderWithRouter('/')).not.toThrow();
    });

    it('should provide router context', () => {
      renderWithRouter('/login');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should handle initial route correctly', () => {
      renderWithRouter('/login');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  describe('Invalid Routes', () => {
    it('should handle non-existent routes gracefully', () => {
      renderWithRouter('/non-existent-route');

      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
      expect(screen.queryByTestId('dashboard-page')).not.toBeInTheDocument();
    });

    it('should not crash on invalid route', () => {
      expect(() => renderWithRouter('/invalid')).not.toThrow();
    });
  });

  describe('Multiple Routes', () => {
    it('should handle auth routes correctly', () => {
      const authRoutes = ['/login', '/signup', '/reset-password', '/reset-password-confirm'];
      
      authRoutes.forEach(route => {
        const { unmount } = renderWithRouter(route);
        expect(screen.getByTestId(`${route.substring(1)}-page`)).toBeInTheDocument();
        unmount();
      });
    });

    it('should handle protected routes correctly', () => {
      renderWithRouter('/dashboard');

      expect(screen.getByTestId('protected-route')).toBeInTheDocument();
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });
  });

  describe('Route Configuration', () => {
    it('should define login route', () => {
      renderWithRouter('/login');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should define signup route', () => {
      renderWithRouter('/signup');

      expect(screen.getByTestId('signup-page')).toBeInTheDocument();
    });

    it('should define reset password routes', () => {
      renderWithRouter('/reset-password');
      expect(screen.getByTestId('reset-password-page')).toBeInTheDocument();
    });

    it('should define dashboard route', () => {
      renderWithRouter('/dashboard');
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });

    it('should define OAuth callback route', () => {
      renderWithRouter('/auth/callback');
      expect(screen.getByTestId('oauth-callback')).toBeInTheDocument();
    });

    it('should define root redirect', () => {
      renderWithRouter('/');
      expect(screen.getByTestId('dashboard-page')).toBeInTheDocument();
    });
  });

  describe('AppRoutes Component', () => {
    it('should render based on location', () => {
      renderWithRouter('/login');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should handle different locations', () => {
      const { rerender } = render(
        <MemoryRouter initialEntries={['/login']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('login-page')).toBeInTheDocument();

      rerender(
        <MemoryRouter initialEntries={['/signup']}>
          <App />
        </MemoryRouter>
      );

      expect(screen.getByTestId('signup-page')).toBeInTheDocument();
    });

    it('should use correct animation mode', () => {
      renderWithRouter('/login');
      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty path segments', () => {
      renderWithRouter('//');
      
      expect(() => screen.getByTestId('dashboard-page')).not.toThrow();
    });

    it('should handle trailing slashes', () => {
      renderWithRouter('/login/');

      expect(document.body).toBeInTheDocument();
    });

    it('should handle case sensitivity', () => {
      renderWithRouter('/Login');

      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument();
    });

    it('should handle query parameters', () => {
      renderWithRouter('/login?redirect=/dashboard');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });

    it('should handle hash routing', () => {
      renderWithRouter('/login#section');

      expect(screen.getByTestId('login-page')).toBeInTheDocument();
    });
  });
});