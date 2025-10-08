import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AuthLayout from '../auth-layout.tsx';

// Mocks
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>
  }
}));
jest.mock('../../../assets/img/logo.png', () => 'logo.png');
jest.mock('../styles/auth.css', () => ({}));

describe('AuthLayout Component', () => {
  describe('Rendering', () => {
    it('should render title correctly', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('should render description correctly', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Test Description')).toBeInTheDocument();
    });

    it('should render children content', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Custom Form Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Custom Form Content')).toBeInTheDocument();
    });

    it('should render logo image with correct attributes', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const logo = screen.getByAltText('Company Logo');
      expect(logo).toBeInTheDocument();
      expect(logo).toHaveAttribute('src', 'logo.png');
      expect(logo).toHaveClass('auth-logo');
    });

    it('should render main container structure', () => {
      const { container } = render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(container.querySelector('.auth-container')).toBeInTheDocument();
      expect(container.querySelector('.auth-left')).toBeInTheDocument();
      expect(container.querySelector('.auth-right')).toBeInTheDocument();
      expect(container.querySelector('.auth-card')).toBeInTheDocument();
    });

    it('should render left background element', () => {
      const { container } = render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(container.querySelector('.auth-left-background')).toBeInTheDocument();
    });

    it('should render title with correct class', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const title = screen.getByText('Test Title');
      expect(title).toHaveClass('auth-title');
      expect(title.tagName).toBe('H1');
    });

    it('should render description with correct class', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const description = screen.getByText('Test Description');
      expect(description).toHaveClass('auth-description');
      expect(description.tagName).toBe('H2');
    });
  });

  describe('Error Handling', () => {
    it('should display error message when error prop is provided', () => {
      render(
        <AuthLayout 
          title="Test Title" 
          description="Test Description"
          error="Something went wrong"
        >
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('should not display error element when error prop is empty string', () => {
      render(
        <AuthLayout 
          title="Test Title" 
          description="Test Description"
          error=""
        >
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
    });

    it('should not display error element when error prop is undefined', () => {
      const { container } = render(
        <AuthLayout 
          title="Test Title" 
          description="Test Description"
        >
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(container.querySelector('.error-message')).not.toBeInTheDocument();
    });

    it('should render error message with correct class', () => {
      const { container } = render(
        <AuthLayout 
          title="Test Title" 
          description="Test Description"
          error="Error occurred"
        >
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const errorElement = container.querySelector('.error-message');
      expect(errorElement).toBeInTheDocument();
      expect(errorElement).toHaveTextContent('Error occurred');
    });

    it('should display multiple different errors', () => {
      const { rerender } = render(
        <AuthLayout 
          title="Test Title" 
          description="Test Description"
          error="First error"
        >
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('First error')).toBeInTheDocument();
      
      rerender(
        <AuthLayout 
          title="Test Title" 
          description="Test Description"
          error="Second error"
        >
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.queryByText('First error')).not.toBeInTheDocument();
      expect(screen.getByText('Second error')).toBeInTheDocument();
    });
  });

  describe('Children Rendering', () => {
    it('should render form elements as children', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <form>
            <input type="text" placeholder="Username" />
            <button type="submit">Submit</button>
          </form>
        </AuthLayout>
      );
      
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Submit' })).toBeInTheDocument();
    });

    it('should render multiple child elements', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>First Child</div>
          <div>Second Child</div>
          <div>Third Child</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('First Child')).toBeInTheDocument();
      expect(screen.getByText('Second Child')).toBeInTheDocument();
      expect(screen.getByText('Third Child')).toBeInTheDocument();
    });

    it('should render complex nested children', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>
            <p>Paragraph</p>
            <button>Button</button>
            <div>
              <span>Nested span</span>
            </div>
          </div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Paragraph')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Button' })).toBeInTheDocument();
      expect(screen.getByText('Nested span')).toBeInTheDocument();
    });
  });

  describe('Framer Motion Integration', () => {
    it('should render motion.div with correct variants', () => {
      const { container } = render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const authCard = container.querySelector('.auth-card');
      expect(authCard).toBeInTheDocument();
    });

    it('should have initial variant properties', () => {
      const { container } = render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const authCard = container.querySelector('.auth-card');
      expect(authCard).toHaveAttribute('initial', 'initial');
    });

    it('should have animate variant properties', () => {
      const { container } = render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const authCard = container.querySelector('.auth-card');
      expect(authCard).toHaveAttribute('animate', 'animate');
    });

    it('should have exit variant properties', () => {
      const { container } = render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const authCard = container.querySelector('.auth-card');
      expect(authCard).toHaveAttribute('exit', 'exit');
    });
  });

  describe('Props Handling', () => {
    it('should handle long title text', () => {
      const longTitle = 'This is a very long title that should still render correctly';
      render(
        <AuthLayout title={longTitle} description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('should handle long description text', () => {
      const longDescription = 'This is a very long description that provides detailed information about the authentication process';
      render(
        <AuthLayout title="Test Title" description={longDescription}>
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText(longDescription)).toBeInTheDocument();
    });

    it('should handle special characters in title', () => {
      render(
        <AuthLayout title="Welcome! Let's Get Started 🚀" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText("Welcome! Let's Get Started 🚀")).toBeInTheDocument();
    });

    it('should handle special characters in description', () => {
      render(
        <AuthLayout title="Test Title" description="Sign up & get started - it's free!">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText("Sign up & get started - it's free!")).toBeInTheDocument();
    });

    it('should handle long error messages', () => {
      const longError = 'This is a very long error message that explains in detail what went wrong with the authentication process';
      render(
        <AuthLayout 
          title="Test Title" 
          description="Test Description"
          error={longError}
        >
          <div>Test Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText(longError)).toBeInTheDocument();
    });
  });

  describe('Layout Structure', () => {
    it('should render error message before children', () => {
      const { container } = render(
        <AuthLayout 
          title="Test Title" 
          description="Test Description"
          error="Error message"
        >
          <div className="test-child">Test Content</div>
        </AuthLayout>
      );
      
      const authCard = container.querySelector('.auth-card');
      const errorMessage = container.querySelector('.error-message');
      const testChild = container.querySelector('.test-child');
      
      expect(authCard).toBeInTheDocument();
      expect(errorMessage).toBeInTheDocument();
      expect(testChild).toBeInTheDocument();
      
      const cardChildren = Array.from(authCard?.children || []);
      const errorIndex = cardChildren.indexOf(errorMessage as Element);
      const childIndex = cardChildren.indexOf(testChild as Element);
      
      expect(errorIndex).toBeLessThan(childIndex);
    });

    it('should render title before description', () => {
      const { container } = render(
        <AuthLayout title="Title" description="Description">
          <div>Content</div>
        </AuthLayout>
      );
      
      const authCard = container.querySelector('.auth-card');
      const title = screen.getByText('Title');
      const description = screen.getByText('Description');
      
      const cardChildren = Array.from(authCard?.children || []);
      const titleIndex = cardChildren.indexOf(title as Element);
      const descriptionIndex = cardChildren.indexOf(description as Element);
      
      expect(titleIndex).toBeLessThan(descriptionIndex);
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(
        <AuthLayout title="Main Title" description="Subtitle">
          <div>Content</div>
        </AuthLayout>
      );
      
      const h1 = screen.getByRole('heading', { level: 1 });
      const h2 = screen.getByRole('heading', { level: 2 });
      
      expect(h1).toHaveTextContent('Main Title');
      expect(h2).toHaveTextContent('Subtitle');
    });

    it('should have accessible logo alt text', () => {
      render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const logo = screen.getByAltText('Company Logo');
      expect(logo).toBeInTheDocument();
    });
  });

  describe('Re-rendering', () => {
    it('should update title when props change', () => {
      const { rerender } = render(
        <AuthLayout title="Original Title" description="Description">
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Original Title')).toBeInTheDocument();
      
      rerender(
        <AuthLayout title="Updated Title" description="Description">
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.queryByText('Original Title')).not.toBeInTheDocument();
      expect(screen.getByText('Updated Title')).toBeInTheDocument();
    });

    it('should update description when props change', () => {
      const { rerender } = render(
        <AuthLayout title="Title" description="Original Description">
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Original Description')).toBeInTheDocument();
      
      rerender(
        <AuthLayout title="Title" description="Updated Description">
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.queryByText('Original Description')).not.toBeInTheDocument();
      expect(screen.getByText('Updated Description')).toBeInTheDocument();
    });

    it('should update error when props change', () => {
      const { rerender } = render(
        <AuthLayout 
          title="Title" 
          description="Description"
          error="First error"
        >
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('First error')).toBeInTheDocument();
      
      rerender(
        <AuthLayout 
          title="Title" 
          description="Description"
          error="Second error"
        >
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.queryByText('First error')).not.toBeInTheDocument();
      expect(screen.getByText('Second error')).toBeInTheDocument();
    });

    it('should update children when props change', () => {
      const { rerender } = render(
        <AuthLayout title="Title" description="Description">
          <div>Original Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Original Content')).toBeInTheDocument();
      
      rerender(
        <AuthLayout title="Title" description="Description">
          <div>Updated Content</div>
        </AuthLayout>
      );
      
      expect(screen.queryByText('Original Content')).not.toBeInTheDocument();
      expect(screen.getByText('Updated Content')).toBeInTheDocument();
    });

    it('should remove error when error prop becomes empty', () => {
      const { rerender, container } = render(
        <AuthLayout 
          title="Title" 
          description="Description"
          error="Error message"
        >
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('Error message')).toBeInTheDocument();
      
      rerender(
        <AuthLayout 
          title="Title" 
          description="Description"
          error=""
        >
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.queryByText('Error message')).not.toBeInTheDocument();
      expect(container.querySelector('.error-message')).not.toBeInTheDocument();
    });

    it('should add error when error prop becomes populated', () => {
      const { rerender } = render(
        <AuthLayout 
          title="Title" 
          description="Description"
        >
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.queryByText('New error')).not.toBeInTheDocument();
      
      rerender(
        <AuthLayout 
          title="Title" 
          description="Description"
          error="New error"
        >
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(screen.getByText('New error')).toBeInTheDocument();
    });
  });

  describe('Different Use Cases', () => {
    it('should work with login form children', () => {
      render(
        <AuthLayout title="Login" description="Welcome back">
          <form>
            <input type="email" placeholder="Email" />
            <input type="password" placeholder="Password" />
            <button type="submit">Log In</button>
          </form>
        </AuthLayout>
      );
      
      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Log In' })).toBeInTheDocument();
    });

    it('should work with signup form children', () => {
      render(
        <AuthLayout title="Sign Up" description="Create an account">
          <form>
            <input type="text" placeholder="Name" />
            <input type="email" placeholder="Email" />
            <input type="password" placeholder="Password" />
            <button type="submit">Sign Up</button>
          </form>
        </AuthLayout>
      );
      
      expect(screen.getByPlaceholderText('Name')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Email')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign Up' })).toBeInTheDocument();
    });

    it('should work with password reset confirmation children', () => {
      render(
        <AuthLayout title="Check Your Email" description="We sent you a link">
          <button type="button">Back to Login</button>
        </AuthLayout>
      );
      
      expect(screen.getByRole('button', { name: 'Back to Login' })).toBeInTheDocument();
    });
  });

  describe('Motion Props', () => {
    it('should pass variants prop to motion.div', () => {
      const { container } = render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const authCard = container.querySelector('.auth-card');
      expect(authCard).toHaveAttribute('variants');
    });

    it('should pass transition prop to motion.div', () => {
      const { container } = render(
        <AuthLayout title="Test Title" description="Test Description">
          <div>Test Content</div>
        </AuthLayout>
      );
      
      const authCard = container.querySelector('.auth-card');
      expect(authCard).toHaveAttribute('transition');
    });
  });

  describe('Empty States', () => {
    it('should render with empty string title', () => {
      render(
        <AuthLayout title="" description="Description">
          <div>Content</div>
        </AuthLayout>
      );
      
      const title = screen.getByRole('heading', { level: 1 });
      expect(title).toHaveTextContent('');
    });

    it('should render with empty string description', () => {
      render(
        <AuthLayout title="Title" description="">
          <div>Content</div>
        </AuthLayout>
      );
      
      const description = screen.getByRole('heading', { level: 2 });
      expect(description).toHaveTextContent('');
    });

    it('should render without children', () => {
      const { container } = render(
        <AuthLayout title="Title" description="Description">
          {null}
        </AuthLayout>
      );
      
      expect(container.querySelector('.auth-card')).toBeInTheDocument();
    });
  });

  describe('CSS Classes', () => {
    it('should apply all required CSS classes to container elements', () => {
      const { container } = render(
        <AuthLayout title="Title" description="Description">
          <div>Content</div>
        </AuthLayout>
      );
      
      expect(container.querySelector('.auth-container')).toBeInTheDocument();
      expect(container.querySelector('.auth-left')).toBeInTheDocument();
      expect(container.querySelector('.auth-left-background')).toBeInTheDocument();
      expect(container.querySelector('.auth-right')).toBeInTheDocument();
      expect(container.querySelector('.auth-logo')).toBeInTheDocument();
      expect(container.querySelector('.auth-card')).toBeInTheDocument();
      expect(container.querySelector('.auth-title')).toBeInTheDocument();
      expect(container.querySelector('.auth-description')).toBeInTheDocument();
    });
  });

  describe('Content Isolation', () => {
    it('should render multiple instances independently', () => {
      const { container: container1 } = render(
        <AuthLayout title="Title 1" description="Description 1">
          <div>Content 1</div>
        </AuthLayout>
      );
      
      const { container: container2 } = render(
        <AuthLayout title="Title 2" description="Description 2">
          <div>Content 2</div>
        </AuthLayout>
      );
      
      expect(container1.querySelector('.auth-container')).toBeInTheDocument();
      expect(container2.querySelector('.auth-container')).toBeInTheDocument();
    });
  });
});