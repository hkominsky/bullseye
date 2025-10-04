import '../styles/auth.css';
import { motion } from 'framer-motion';
import logoImage from '../../../assets/img/logo.png';
import { AuthLayoutProps } from '../utils/types';

/**
 * Reusable authentication layout component that provides consistent UI structure
 * for all authentication pages with animated transitions
 * 
 * @param {AuthLayoutProps} props - Component props
 * @param {string} props.title - Main title displayed on the auth card
 * @param {string} props.description - Description text displayed below title
 * @param {ReactNode} props.children - Form content rendered inside the card
 * @param {string} [props.error] - Error message to display above form
 * @returns The rendered authentication layout
 */
function AuthLayout({ 
  title, 
  description, 
  children, 
  error
}: AuthLayoutProps) {
  const slideVariants = {
    initial: { 
      x: 100, 
      opacity: 0 
    },
    animate: { 
      x: 0, 
      opacity: 1 
    },
    exit: { 
      x: -100, 
      opacity: 0 
    }
  };

  const transition = {
    type: "tween" as const,
    ease: "easeInOut" as const,
    duration: 0.4
  };

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