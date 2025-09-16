import './auth.css';
import { useNavigate } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';

function Signup() {
  const navigate = useNavigate();

  const handleGoogleSignup = () => {
    console.log('Google signup clicked');
  };

  const handleGitHubSignup = () => {
    console.log('GitHub signup clicked');
  };

  const handleSignup = (e) => {
    e.preventDefault();
    console.log('Regular signup submitted');
  };

  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <div className="auth-container">
      <div className="auth-left">
        <div className="auth-left-background"></div>
      </div>
      <div className="auth-right">
        <div className="auth-card">
          <h1 className="auth-title">💼 Market Brief</h1>
          <h2 className="auth-description">Sign up to continue</h2>
          
          <button className="external-auth-button" onClick={handleGoogleSignup}>
            <GoogleIcon className="external-auth-icon" />
            Continue with Google
          </button>
          
          <button className="external-auth-button" onClick={handleGitHubSignup}>
            <GitHubIcon className="external-auth-icon" />
            Continue with GitHub
          </button>
          
          <div className="divider">
            <span className="divider-line"></span>
            <span className="divider-text">or</span>
            <span className="divider-line"></span>
          </div>
          
          <form className="auth-form" onSubmit={handleSignup}>
            <div className="form-group">
              <input
                type="text"
                id="firstName"
                className="form-input"
                placeholder="First Name"
                required
              />
            </div>
            <div className="form-group">
              <input
                type="text"
                id="lastName"
                className="form-input"
                placeholder="Last Name"
                required
              />
            </div>
            <div className="form-group">
              <input
                type="email"
                id="email"
                className="form-input"
                placeholder="Email"
                required
              />
            </div>
            <div className="form-group">
              <input
                type="password"
                id="password"
                className="form-input"
                placeholder="Password"
                required
              />
            </div>
            <div className="form-group">
              <input
                type="password"
                id="confirmPassword"
                className="form-input"
                placeholder="Confirm Password"
                required
              />
            </div>
            
            <button type="submit" className="auth-button">
              SIGN UP
            </button>
          </form>
          
          <p className="auth-footer-text">
            Already have an account? <span className="auth-footer-link" onClick={handleLogin}>Log in</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Signup;