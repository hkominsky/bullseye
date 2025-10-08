import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ToastProvider, useToast } from '../toast-context.tsx';

// Tests
const TestComponent = () => {
  const { showToast } = useToast();

  return (
    <div>
      <button onClick={() => showToast('Success message', 'success')}>
        Show Success
      </button>
      <button onClick={() => showToast('Error message', 'error')}>
        Show Error
      </button>
      <button onClick={() => showToast('Custom message', 'success')}>
        Show Custom
      </button>
    </div>
  );
};

const renderWithToastProvider = (component: React.ReactElement) => {
  return render(<ToastProvider>{component}</ToastProvider>);
};

describe('ToastContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('ToastProvider', () => {
    it('should render children', () => {
      renderWithToastProvider(<div>Test Child</div>);

      expect(screen.getByText('Test Child')).toBeInTheDocument();
    });

    it('should render toast container', () => {
      const { container } = renderWithToastProvider(<div>Test</div>);

      expect(container.querySelector('.toast-container')).toBeInTheDocument();
    });

    it('should not render any toasts initially', () => {
      const { container } = renderWithToastProvider(<div>Test</div>);

      const toasts = container.querySelectorAll('.toast');
      expect(toasts.length).toBe(0);
    });
  });

  describe('useToast Hook', () => {
    it('should throw error when used outside ToastProvider', () => {
      // Suppress console.error for this test
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      const ComponentWithoutProvider = () => {
        useToast();
        return <div>Test</div>;
      };

      expect(() => render(<ComponentWithoutProvider />)).toThrow(
        'useToast must be used within ToastProvider'
      );

      consoleErrorSpy.mockRestore();
    });

    it('should provide showToast function', () => {
      renderWithToastProvider(<TestComponent />);

      const successButton = screen.getByRole('button', { name: 'Show Success' });
      expect(successButton).toBeInTheDocument();
    });
  });

  describe('Success Toast', () => {
    it('should display success toast when showToast is called', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      expect(screen.getByText('Success message')).toBeInTheDocument();
    });

    it('should apply success class to success toast', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      const toast = container.querySelector('.toast-success');
      expect(toast).toBeInTheDocument();
    });

    it('should display success icon for success toast', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      expect(screen.getByText('✓')).toBeInTheDocument();
    });

    it('should display success icon with correct class', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      const icon = screen.getByText('✓');
      expect(icon).toHaveClass('toast-icon');
    });

    it('should display message with correct class', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      const message = screen.getByText('Success message');
      expect(message).toHaveClass('toast-message');
    });

    it('should auto-remove success toast after 3 seconds', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);
      expect(screen.getByText('Success message')).toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(screen.queryByText('Success message')).not.toBeInTheDocument();
    });

    it('should not remove success toast before 3 seconds', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      act(() => {
        jest.advanceTimersByTime(2999);
      });

      expect(screen.getByText('Success message')).toBeInTheDocument();
    });
  });

  describe('Error Toast', () => {
    it('should display error toast when showToast is called', () => {
      renderWithToastProvider(<TestComponent />);
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(errorButton);

      expect(screen.getByText('Error message')).toBeInTheDocument();
    });

    it('should apply error class to error toast', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(errorButton);

      const toast = container.querySelector('.toast-error');
      expect(toast).toBeInTheDocument();
    });

    it('should display error icon for error toast', () => {
      renderWithToastProvider(<TestComponent />);
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(errorButton);

      expect(screen.getByText('✕')).toBeInTheDocument();
    });

    it('should display error icon with correct class', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(errorButton);

      const icon = screen.getByText('✕');
      expect(icon).toHaveClass('toast-icon');
    });

    it('should auto-remove error toast after 4 seconds', () => {
      renderWithToastProvider(<TestComponent />);
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(errorButton);
      expect(screen.getByText('Error message')).toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(4000);
      });

      expect(screen.queryByText('Error message')).not.toBeInTheDocument();
    });

    it('should not remove error toast before 4 seconds', () => {
      renderWithToastProvider(<TestComponent />);
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(errorButton);

      act(() => {
        jest.advanceTimersByTime(3999);
      });

      expect(screen.getByText('Error message')).toBeInTheDocument();
    });
  });

  describe('Multiple Toasts', () => {
    it('should display multiple toasts at once', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(successButton);
      fireEvent.click(errorButton);

      expect(screen.getByText('Success message')).toBeInTheDocument();
      expect(screen.getByText('Error message')).toBeInTheDocument();
    });

    it('should display toasts with unique keys', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);
      fireEvent.click(successButton);

      const toasts = container.querySelectorAll('.toast');
      expect(toasts.length).toBe(2);
    });

    it('should remove toasts independently based on their type', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(successButton);
      fireEvent.click(errorButton);

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(screen.queryByText('Success message')).not.toBeInTheDocument();
      expect(screen.getByText('Error message')).toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.queryByText('Error message')).not.toBeInTheDocument();
    });

    it('should handle showing same message multiple times', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const customButton = screen.getByRole('button', { name: 'Show Custom' });

      fireEvent.click(customButton);
      fireEvent.click(customButton);
      fireEvent.click(customButton);

      const messages = screen.getAllByText('Custom message');
      expect(messages.length).toBe(3);
    });
  });

  describe('Manual Removal', () => {
    it('should remove toast when clicked', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);
      expect(screen.getByText('Success message')).toBeInTheDocument();

      const toast = container.querySelector('.toast');
      fireEvent.click(toast!);

      expect(screen.queryByText('Success message')).not.toBeInTheDocument();
    });

    it('should remove only clicked toast when multiple exist', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });
      const errorButton = screen.getByRole('button', { name: 'Show Error' });

      fireEvent.click(successButton);
      fireEvent.click(errorButton);

      const toasts = container.querySelectorAll('.toast');
      fireEvent.click(toasts[0]);

      expect(screen.queryByText('Success message')).not.toBeInTheDocument();
      expect(screen.getByText('Error message')).toBeInTheDocument();
    });

    it('should prevent auto-removal timer when toast is manually removed', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);
      
      const toast = container.querySelector('.toast');
      fireEvent.click(toast!);

      expect(screen.queryByText('Success message')).not.toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      // Should not throw or cause issues
      expect(screen.queryByText('Success message')).not.toBeInTheDocument();
    });
  });

  describe('Toast Structure', () => {
    it('should have correct base class for toast', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      const toast = container.querySelector('.toast');
      expect(toast).toHaveClass('toast');
    });

    it('should have both base and type classes', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      const toast = container.querySelector('.toast');
      expect(toast).toHaveClass('toast', 'toast-success');
    });

    it('should contain icon span', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      const icon = screen.getByText('✓');
      expect(icon.tagName).toBe('SPAN');
    });

    it('should contain message span', () => {
      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      const message = screen.getByText('Success message');
      expect(message.tagName).toBe('SPAN');
    });
  });

  describe('Toast IDs', () => {
    it('should generate unique IDs for each toast', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      const originalDateNow = Date.now;
      let counter = 1000;
      Date.now = jest.fn(() => counter++);

      fireEvent.click(successButton);
      fireEvent.click(successButton);
      fireEvent.click(successButton);

      const toasts = container.querySelectorAll('.toast');
      expect(toasts.length).toBe(3);

      Date.now = originalDateNow;
    });

    it('should use timestamp-based IDs', () => {
      const originalDateNow = Date.now;
      const mockTimestamp = 1234567890;
      Date.now = jest.fn(() => mockTimestamp);

      renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);

      expect(Date.now).toHaveBeenCalled();

      Date.now = originalDateNow;
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty message', () => {
      const EmptyMessageComponent = () => {
        const { showToast } = useToast();
        return (
          <button onClick={() => showToast('', 'success')}>
            Show Empty
          </button>
        );
      };

      renderWithToastProvider(<EmptyMessageComponent />);
      const button = screen.getByRole('button', { name: 'Show Empty' });

      fireEvent.click(button);

      const icon = screen.getByText('✓');
      expect(icon).toBeInTheDocument();
    });

    it('should handle very long message', () => {
      const longMessage = 'A'.repeat(500);
      const LongMessageComponent = () => {
        const { showToast } = useToast();
        return (
          <button onClick={() => showToast(longMessage, 'success')}>
            Show Long
          </button>
        );
      };

      renderWithToastProvider(<LongMessageComponent />);
      const button = screen.getByRole('button', { name: 'Show Long' });

      fireEvent.click(button);

      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('should handle special characters in message', () => {
      const specialMessage = '<script>alert("test")</script>';
      const SpecialMessageComponent = () => {
        const { showToast } = useToast();
        return (
          <button onClick={() => showToast(specialMessage, 'success')}>
            Show Special
          </button>
        );
      };

      renderWithToastProvider(<SpecialMessageComponent />);
      const button = screen.getByRole('button', { name: 'Show Special' });

      fireEvent.click(button);

      expect(screen.getByText(specialMessage)).toBeInTheDocument();
    });

    it('should handle rapid successive calls', () => {
      const { container } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      for (let i = 0; i < 10; i++) {
        fireEvent.click(successButton);
      }

      const toasts = container.querySelectorAll('.toast');
      expect(toasts.length).toBe(10);
    });
  });

  describe('Cleanup', () => {
    it('should clean up timers on unmount', () => {
      const { unmount } = renderWithToastProvider(<TestComponent />);
      const successButton = screen.getByRole('button', { name: 'Show Success' });

      fireEvent.click(successButton);
      
      unmount();

      // Should not throw or cause memory leaks
      act(() => {
        jest.runAllTimers();
      });
    });
  });
});