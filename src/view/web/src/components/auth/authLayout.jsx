// components/auth/authLayout.jsx
import './auth.css';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import logoImage from '../../assets/logo.png';

/**
 * Reusable authentication layout component
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

  const handleBack = () => {
    if (onBackClick) {
      onBackClick();
    } else {
      navigate('/login', { state: { direction: 'back' } });
    }
  };

  const direction = location.state?.direction || 'forward';
  const isBackNavigation = direction === 'back';

  const slideVariants = {
    initial: { 
      x: isBackNavigation ? -100 : 100, 
      opacity: 0 
    },
    animate: { 
      x: 0, 
      opacity: 1 
    },
    exit: { 
      x: isBackNavigation ? 100 : -100, 
      opacity: 0 
    }
  };

  const transition = {
    type: "tween",
    ease: "easeInOut",
    duration: 0.4
  };

  return (
    <div className="auth-container">
      {/* Background area */}
      <div className="auth-left">
        <div className="auth-left-background"></div>
      </div>
      
      {/* Form content with animation */}
      <div className="auth-right">
        {/* Logo */}
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
          {/* Back button */}
          {showBackButton && (
            <div className="auth-back-button" onClick={handleBack}>
              <span className="auth-back-link">🡰</span>
            </div>
          )}
          
          {/* Header section */}
          <h1 className="auth-title">{title}</h1>
          <h2 className="auth-description">{description}</h2>
          
          {/* Error message */}
          {error && <div className="error-message">{error}</div>}

          {/* Form content */}
          {children}
        </motion.div>
      </div>
    </div>
  );
}

export default AuthLayout;