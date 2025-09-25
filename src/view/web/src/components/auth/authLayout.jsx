import './auth.css';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import logoImage from '../../assets/logo.png';

/**
 * Reusable authentication layout component that provides consistent UI structure
 * for all authentication pages with animated transitions
 * 
 * @param {Object} props - Component props
 * @param {string} props.title - Main title displayed on the auth card
 * @param {string} props.description - Description text displayed below title
 * @param {React.ReactNode} props.children - Form content rendered inside the card
 * @param {boolean} [props.showBackButton=false] - Whether to show back button
 * @param {string} [props.error] - Error message to display above form
 * @param {Function} [props.onBackClick] - Custom back button click handler
 * @returns {JSX.Element} The rendered authentication layout
 */
function AuthLayout({ 
  title, 
  description, 
  children, 
  showBackButton = false, 
  error,
  onBackClick
}) {
  const navigate = useNavigate();
  const location = useLocation();

  /**
   * Handles back button click event
   * Uses custom handler if provided, otherwise navigates to login
   * @returns {void}
   */
  const handleBack = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      navigate('/login', { state: { direction: 'back' } });
    }
  };

  /**
   * Gets navigation direction from location state
   * @returns {string} Direction of navigation ('forward' or 'back')
   */
  const getDirection = () => {
    return location.state?.direction || 'forward';
  };

  /**
   * Determines if current navigation is backwards
   * @returns {boolean} True if navigating back, false otherwise
   */
  const checkIsBackNavigation = () => {
    return getDirection() === 'back';
  };

  /**
   * Creates slide animation variants based on navigation direction
   * @returns {Object} Framer Motion animation variants
   */
  const createSlideVariants = () => {
    const isBack = checkIsBackNavigation();
    
    return {
      initial: { 
        x: isBack ? -100 : 100, 
        opacity: 0 
      },
      animate: { 
        x: 0, 
        opacity: 1 
      },
      exit: { 
        x: isBack ? 100 : -100, 
        opacity: 0 
      }
    };
  };

  /**
   * Creates transition configuration for animations
   * @returns {Object} Framer Motion transition settings
   */
  const createTransition = () => {
    return {
      type: "tween",
      ease: "easeInOut",
      duration: 0.4
    };
  };

  const slideVariants = createSlideVariants();
  const transition = createTransition();

  return (
    <div className="auth-container">
      <div className="auth-left">
        <div className="auth-left-background"></div>
      </div>
      
      <div className="auth-right">
        <img 
          src={logoImage} 
          alt="Company Logo" 
          className="auth-logo"
        />
        
        <motion.div 
          className="auth-card"
          variants={slideVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={transition}
        >
          {showBackButton && (
            <div className="auth-back-button" onClick={handleBack}>
              <span className="auth-back-link">🡰</span>
            </div>
          )}
          
          <h1 className="auth-title">{title}</h1>
          <h2 className="auth-description">{description}</h2>
          
          {error && <div className="error-message">{error}</div>}

          {children}
        </motion.div>
      </div>
    </div>
  );
}

export default AuthLayout;