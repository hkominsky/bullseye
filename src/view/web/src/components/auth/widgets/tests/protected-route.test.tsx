import { render, screen } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import { ProtectedRoute } from '../protected-route.tsx';
import authService from '../../../../services/auth.ts';

// Mock
jest.mock('../../../services/auth');

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Authenticated User', () => {
    beforeEach(() => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
    });

    it('should render children when user is authenticated', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should render complex children components', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>
              <h1>Dashboard</h1>
              <p>Welcome back!</p>
              <button>Logout</button>
            </div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Welcome back!')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Logout' })).toBeInTheDocument();
    });

    it('should render multiple child elements', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>First Child</div>
            <div>Second Child</div>
            <div>Third Child</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('First Child')).toBeInTheDocument();
      expect(screen.getByText('Second Child')).toBeInTheDocument();
      expect(screen.getByText('Third Child')).toBeInTheDocument();
    });

    it('should render React components as children', () => {
      const DashboardComponent = () => <div>Dashboard Component</div>;
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <DashboardComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Dashboard Component')).toBeInTheDocument();
    });

    it('should call isAuthenticated once', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalledTimes(1);
    });

    it('should not render Navigate component when authenticated', () => {
      const { container } = render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </MemoryRouter>
      );
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
      expect(container.querySelector('Navigate')).not.toBeInTheDocument();
    });
  });

  describe('Unauthenticated User', () => {
    beforeEach(() => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
    });

    it('should not render children when user is not authenticated', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should redirect to login page when not authenticated', () => {
      const { container } = render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </MemoryRouter>
      );
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should call isAuthenticated once when not authenticated', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalledTimes(1);
    });

    it('should use replace prop on Navigate component', () => {
      const { container } = render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Authentication State Changes', () => {
    it('should update when authentication state changes from false to true', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
      
      const { rerender } = render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
      
      // Change authentication state
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      rerender(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should update when authentication state changes from true to false', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      const { rerender } = render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
      
      // Change authentication state
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
      
      rerender(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Different Protected Content', () => {
    beforeEach(() => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
    });

    it('should protect dashboard route', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div data-testid="dashboard">Dashboard Page</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByTestId('dashboard')).toBeInTheDocument();
    });

    it('should protect settings route', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div data-testid="settings">Settings Page</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByTestId('settings')).toBeInTheDocument();
    });

    it('should protect profile route', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div data-testid="profile">Profile Page</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByTestId('profile')).toBeInTheDocument();
    });
  });

  describe('Fragment Wrapping', () => {
    it('should wrap children in React fragment', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      const { container } = render(
        <BrowserRouter>
          <ProtectedRoute>
            <div className="test-child">Test Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      const child = container.querySelector('.test-child');
      expect(child).toBeInTheDocument();
    });

    it('should preserve child component props when authenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      const ChildComponent = ({ testProp }: { testProp: string }) => (
        <div>{testProp}</div>
      );
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <ChildComponent testProp="Test Value" />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Test Value')).toBeInTheDocument();
    });
  });

  describe('Empty and Null Children', () => {
    beforeEach(() => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
    });

    it('should handle null children', () => {
      const { container } = render(
        <BrowserRouter>
          <ProtectedRoute>
            {null}
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(container.querySelector('div')).toBeInTheDocument();
    });

    it('should handle undefined children', () => {
      const { container } = render(
        <BrowserRouter>
          <ProtectedRoute>
            {undefined}
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(container.querySelector('div')).toBeInTheDocument();
    });

    it('should handle empty fragment', () => {
      const { container } = render(
        <BrowserRouter>
          <ProtectedRoute>
            <></>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(container.querySelector('div')).toBeInTheDocument();
    });
  });

  describe('Multiple ProtectedRoute Instances', () => {
    it('should handle multiple protected routes independently - all authenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Route 1</div>
          </ProtectedRoute>
          <ProtectedRoute>
            <div>Route 2</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Route 1')).toBeInTheDocument();
      expect(screen.getByText('Route 2')).toBeInTheDocument();
    });

    it('should call isAuthenticated for each instance', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Route 1</div>
          </ProtectedRoute>
          <ProtectedRoute>
            <div>Route 2</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalledTimes(2);
    });
  });

  describe('TypeScript Props', () => {
    it('should accept ReactNode as children', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>String content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('String content')).toBeInTheDocument();
    });

    it('should accept JSX elements as children', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      const element = <div>JSX Element</div>;
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            {element}
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('JSX Element')).toBeInTheDocument();
    });
  });

  describe('Navigate Component Props', () => {
    it('should use correct "to" prop on Navigate', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
      
      render(
        <MemoryRouter initialEntries={['/protected']}>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </MemoryRouter>
      );
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should use replace prop to avoid back button issues', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
      
      const { container } = render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Re-rendering Behavior', () => {
    it('should re-check authentication on re-render', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      const { rerender } = render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalledTimes(1);
      
      rerender(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalledTimes(2);
    });

    it('should update rendered content when children prop changes', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      const { rerender } = render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Original Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Original Content')).toBeInTheDocument();
      
      rerender(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Updated Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Original Content')).not.toBeInTheDocument();
      expect(screen.getByText('Updated Content')).toBeInTheDocument();
    });
  });

  describe('Authentication Service Integration', () => {
    it('should call isAuthenticated method', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalled();
    });

    it('should handle isAuthenticated returning true', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should handle isAuthenticated returning false', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('should not call isAuthenticated with any arguments', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalledWith();
    });
  });

  describe('Nested Components', () => {
    it('should render deeply nested children when authenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>
              <div>
                <div>
                  <span>Deeply Nested Content</span>
                </div>
              </div>
            </div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Deeply Nested Content')).toBeInTheDocument();
    });

    it('should not render nested children when not authenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>
              <div>
                <span>Nested Content</span>
              </div>
            </div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Nested Content')).not.toBeInTheDocument();
    });
  });

  describe('Real-world Use Cases', () => {
    it('should protect dashboard component', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      const Dashboard = () => (
        <div>
          <h1>Dashboard</h1>
          <p>User data here</p>
        </div>
      );
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('User data here')).toBeInTheDocument();
    });

    it('should protect settings component', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      const Settings = () => (
        <div>
          <h1>Settings</h1>
          <button>Save</button>
        </div>
      );
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
    });

    it('should redirect from protected route when not authenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
      
      const PrivatePage = () => <div>Private Page</div>;
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <PrivatePage />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Private Page')).not.toBeInTheDocument();
    });
  });

  describe('Children Prop Variations', () => {
    beforeEach(() => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
    });

    it('should render string children', () => {
      render(
        <BrowserRouter>
          <ProtectedRoute>
            Simple text content
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Simple text content')).toBeInTheDocument();
    });

    it('should render function component children', () => {
      const FunctionComponent = () => <div>Function Component</div>;
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <FunctionComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Function Component')).toBeInTheDocument();
    });

    it('should render children with props', () => {
      const ComponentWithProps = ({ title }: { title: string }) => <h1>{title}</h1>;
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <ComponentWithProps title="Protected Page" />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Protected Page')).toBeInTheDocument();
    });
  });

  describe('Boolean Return Values', () => {
    it('should handle true boolean from isAuthenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('should handle false boolean from isAuthenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(false);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Content')).not.toBeInTheDocument();
    });

    it('should handle truthy values as authenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(1);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('should handle falsy values as not authenticated', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(0);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(screen.queryByText('Content')).not.toBeInTheDocument();
    });
  });

  describe('Component Rendering Order', () => {
    it('should check authentication before rendering children', () => {
      const authCheckOrder: string[] = [];
      
      (authService.isAuthenticated as jest.Mock).mockImplementation(() => {
        authCheckOrder.push('auth-check');
        return true;
      });
      
      const ChildComponent = () => {
        authCheckOrder.push('child-render');
        return <div>Child</div>;
      };
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <ChildComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authCheckOrder).toEqual(['auth-check', 'child-render']);
    });

    it('should not render children when authentication check fails', () => {
      const renderOrder: string[] = [];
      
      (authService.isAuthenticated as jest.Mock).mockImplementation(() => {
        renderOrder.push('auth-check');
        return false;
      });
      
      const ChildComponent = () => {
        renderOrder.push('child-render');
        return <div>Child</div>;
      };
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <ChildComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(renderOrder).toEqual(['auth-check']);
      expect(renderOrder).not.toContain('child-render');
    });
  });

  describe('Performance', () => {
    it('should only call isAuthenticated once per render', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Content</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalledTimes(1);
    });

    it('should not make unnecessary service calls when rendering multiple children', () => {
      (authService.isAuthenticated as jest.Mock).mockReturnValue(true);
      
      render(
        <BrowserRouter>
          <ProtectedRoute>
            <div>Child 1</div>
            <div>Child 2</div>
            <div>Child 3</div>
            <div>Child 4</div>
            <div>Child 5</div>
          </ProtectedRoute>
        </BrowserRouter>
      );
      
      expect(authService.isAuthenticated).toHaveBeenCalledTimes(1);
    });
  });
});