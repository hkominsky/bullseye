import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, useNavigate } from 'react-router-dom';
import '@testing-library/jest-dom';
import { Header } from '../header.tsx';
import userAuthService from '../../../../services/auth.ts';

// Mocks
jest.mock('../../../../services/auth.ts');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: jest.fn()
}));
jest.mock('../../../assets/img/logo-banner-light.png', () => 'logo-light.png');
jest.mock('../../../assets/img/logo-banner-dark.png', () => 'logo-dark.png');

const renderHeader = () => {
  const mockNavigate = jest.fn();
  jest.mocked(useNavigate).mockReturnValue(mockNavigate);

  return {
    ...render(
      <BrowserRouter>
        <Header />
      </BrowserRouter>
    ),
    mockNavigate
  };
};

describe('Header Component', () => {
  let originalLocalStorage: Storage;

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock localStorage
    originalLocalStorage = window.localStorage;
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
      length: 0,
      key: jest.fn()
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'localStorage', {
      value: originalLocalStorage,
      writable: true
    });
    document.documentElement.removeAttribute('data-theme');
  });

  describe('Rendering', () => {
    it('should render header with logo and menu button', () => {
      renderHeader();

      expect(screen.getByAltText('Company Logo')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '☰' })).toBeInTheDocument();
    });

    it('should render light mode logo by default when no theme is saved', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue(null);
      
      renderHeader();
      const logo = screen.getByAltText('Company Logo') as HTMLImageElement;

      expect(logo.src).toContain('logo-light.png');
    });

    it('should render light mode logo when light theme is saved', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('light');
      
      renderHeader();
      const logo = screen.getByAltText('Company Logo') as HTMLImageElement;

      expect(logo.src).toContain('logo-light.png');
    });

    it('should render dark mode logo when dark theme is saved', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('dark');
      
      renderHeader();
      const logo = screen.getByAltText('Company Logo') as HTMLImageElement;

      expect(logo.src).toContain('logo-dark.png');
    });

    it('should not show dropdown menu initially', () => {
      renderHeader();

      expect(screen.queryByText(/light mode/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/sign out/i)).not.toBeInTheDocument();
    });

    it('should set aria-expanded to false initially', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });

      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('should set aria-haspopup to true', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });

      expect(menuButton).toHaveAttribute('aria-haspopup', 'true');
    });
  });

  describe('Theme Management', () => {
    it('should apply light theme on mount when no saved theme', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue(null);
      
      renderHeader();

      expect(document.documentElement.hasAttribute('data-theme')).toBe(false);
      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'light');
    });

    it('should apply light theme on mount when light is saved', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('light');
      
      renderHeader();

      expect(document.documentElement.hasAttribute('data-theme')).toBe(false);
      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'light');
    });

    it('should apply dark theme on mount when dark is saved', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('dark');
      
      renderHeader();

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark');
    });

    it('should toggle to dark mode when theme button is clicked', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('light');
      
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const themeButton = screen.getByText(/dark mode/i);
      fireEvent.click(themeButton);

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark');
    });

    it('should toggle to light mode when theme button is clicked in dark mode', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('dark');
      
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const themeButton = screen.getByText(/light mode/i);
      fireEvent.click(themeButton);

      expect(document.documentElement.hasAttribute('data-theme')).toBe(false);
      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'light');
    });

    it('should update logo when switching from light to dark mode', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('light');
      
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const themeButton = screen.getByText(/dark mode/i);
      fireEvent.click(themeButton);

      const logo = screen.getByAltText('Company Logo') as HTMLImageElement;
      expect(logo.src).toContain('logo-dark.png');
    });

    it('should update logo when switching from dark to light mode', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('dark');
      
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const themeButton = screen.getByText(/light mode/i);
      fireEvent.click(themeButton);

      const logo = screen.getByAltText('Company Logo') as HTMLImageElement;
      expect(logo.src).toContain('logo-light.png');
    });
  });

  describe('Dropdown Menu', () => {
    it('should open dropdown when menu button is clicked', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });

      fireEvent.click(menuButton);

      expect(screen.getByText(/dark mode/i)).toBeInTheDocument();
      expect(screen.getByText(/sign out/i)).toBeInTheDocument();
    });

    it('should close dropdown when menu button is clicked again', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });

      fireEvent.click(menuButton);
      expect(screen.getByText(/sign out/i)).toBeInTheDocument();

      fireEvent.click(menuButton);
      expect(screen.queryByText(/sign out/i)).not.toBeInTheDocument();
    });

    it('should set aria-expanded to true when dropdown is open', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });

      fireEvent.click(menuButton);

      expect(menuButton).toHaveAttribute('aria-expanded', 'true');
    });

    it('should display correct theme option in light mode', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('light');
      
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      expect(screen.getByText('⏾ Dark Mode')).toBeInTheDocument();
    });

    it('should display correct theme option in dark mode', () => {
      (localStorage.getItem as jest.Mock).mockReturnValue('dark');
      
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      expect(screen.getByText('☀︎ Light Mode')).toBeInTheDocument();
    });

    it('should close dropdown after theme change', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const themeButton = screen.getByText(/dark mode/i);
      fireEvent.click(themeButton);

      expect(screen.queryByText(/sign out/i)).not.toBeInTheDocument();
    });

    it('should close dropdown when clicking outside', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      expect(screen.getByText(/sign out/i)).toBeInTheDocument();

      fireEvent.mouseDown(document.body);

      expect(screen.queryByText(/sign out/i)).not.toBeInTheDocument();
    });

    it('should not close dropdown when clicking inside dropdown', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const dropdown = screen.getByText(/sign out/i).closest('.dropdown-menu');
      fireEvent.mouseDown(dropdown!);

      expect(screen.getByText(/sign out/i)).toBeInTheDocument();
    });

    it('should close dropdown on scroll', () => {
      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      expect(screen.getByText(/sign out/i)).toBeInTheDocument();

      fireEvent.scroll(document);

      expect(screen.queryByText(/sign out/i)).not.toBeInTheDocument();
    });
  });

  describe('Logout Functionality', () => {
    it('should call logout service when sign out is clicked', async () => {
      const mockLogout = jest.fn().mockResolvedValue({});
      (userAuthService.logout as jest.Mock) = mockLogout;

      const { mockNavigate } = renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const signOutButton = screen.getByText(/sign out/i);
      fireEvent.click(signOutButton);

      await waitFor(() => {
        expect(mockLogout).toHaveBeenCalled();
      });

      expect(mockNavigate).toHaveBeenCalledWith('/');
    });

    it('should close dropdown after successful logout', async () => {
      const mockLogout = jest.fn().mockResolvedValue({});
      (userAuthService.logout as jest.Mock) = mockLogout;

      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const signOutButton = screen.getByText(/sign out/i);
      fireEvent.click(signOutButton);

      await waitFor(() => {
        expect(mockLogout).toHaveBeenCalled();
      });

      expect(screen.queryByText(/sign out/i)).not.toBeInTheDocument();
    });

    it('should navigate to home page on successful logout', async () => {
      const mockLogout = jest.fn().mockResolvedValue({});
      (userAuthService.logout as jest.Mock) = mockLogout;

      const { mockNavigate } = renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const signOutButton = screen.getByText(/sign out/i);
      fireEvent.click(signOutButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('should navigate to home page even if logout fails', async () => {
      const mockLogout = jest.fn().mockRejectedValue(new Error('Logout failed'));
      (userAuthService.logout as jest.Mock) = mockLogout;
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();

      const { mockNavigate } = renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const signOutButton = screen.getByText(/sign out/i);
      fireEvent.click(signOutButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });

      expect(consoleErrorSpy).toHaveBeenCalledWith('Logout failed:', expect.any(Error));
      consoleErrorSpy.mockRestore();
    });

    it('should close dropdown even if logout fails', async () => {
      const mockLogout = jest.fn().mockRejectedValue(new Error('Logout failed'));
      (userAuthService.logout as jest.Mock) = mockLogout;
      jest.spyOn(console, 'error').mockImplementation();

      renderHeader();
      const menuButton = screen.getByRole('button', { name: '☰' });
      fireEvent.click(menuButton);

      const signOutButton = screen.getByText(/sign out/i);
      fireEvent.click(signOutButton);

      await waitFor(() => {
        expect(mockLogout).toHaveBeenCalled();
      });

      expect(screen.queryByText(/sign out/i)).not.toBeInTheDocument();
    });
  });

  describe('Event Listener Cleanup', () => {
    it('should remove event listeners on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(document, 'removeEventListener');
      
      const { unmount } = renderHeader();
      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('mousedown', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function));

      removeEventListenerSpy.mockRestore();
    });
  });
});