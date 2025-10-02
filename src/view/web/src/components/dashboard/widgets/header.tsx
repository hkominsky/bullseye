import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import logoImageLight from '../../../assets/img/logo-banner-light.png';
import logoImageDark from '../../../assets/img/logo-banner-dark.png'
import userAuthService from '../../../services/auth.ts';

/**
 * Dashboard header component with logo and user menu dropdown.
 */
export const Header: React.FC = () => {
  const navigate = useNavigate();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    return savedTheme === 'dark';
  });
  const dropdownRef = useRef<HTMLDivElement>(null);

  /**
   * Apply theme to document root on mount and when theme changes.
   */
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  /**
   * Handle user logout and token cleanup.
   */
  const handleLogout = async () => {
    try {
      await userAuthService.logout();
      navigate('/');
      setIsDropdownOpen(false);
    } catch (error) {
      console.error('Logout failed:', error);
      navigate('/');
      setIsDropdownOpen(false);
    }
  };

  /**
   * Handle converting the screen to light/dark mode.
   */
  const handleThemeChange = () => {
    setIsDarkMode(!isDarkMode);
    setIsDropdownOpen(false);
  };

  /**
   * Toggle dropdown menu.
   */
  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  /**
   * Setup click outside and scroll handlers.
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };

    const handleScroll = () => {
      setIsDropdownOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("scroll", handleScroll);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <header className="dashboard-header">
      <div className="dashboard-header-left">
        <img 
          src={isDarkMode ? logoImageDark : logoImageLight} 
          alt="Company Logo" 
          className="dashboard-logo" 
        />
      </div>
      
      <div className="dashboard-header-right">
        <div className="menu-dropdown" ref={dropdownRef}>
          <button 
            className="menu-button" 
            type="button" 
            onClick={toggleDropdown}
            aria-expanded={isDropdownOpen}
            aria-haspopup="true"
          >
            ☰
          </button>
          
          {isDropdownOpen && (
            <div className="dropdown-menu">
              <button 
                className="dropdown-item" 
                onClick={handleThemeChange}
              >
                {isDarkMode ? '☀︎ Light Mode' : '⏾ Dark Mode'}
              </button>
              <button 
                className="dropdown-item" 
                onClick={handleLogout}
              >
                ↪ Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};