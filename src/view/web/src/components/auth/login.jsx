import './auth.css';
import { useNavigate } from 'react-router-dom';
import { ReactComponent as GoogleIcon } from '../../assets/google-icon.svg';
import { ReactComponent as GitHubIcon } from '../../assets/github-icon.svg';

function Login() {
  const navigate = useNavigate();

  const handleGoogleLogin = () => {
    console.log('Google login clicked');
  };

  const handleGitHubLogin = () => {
    console.log('GitHub login clicked');
  };

  const handleLogin = (e) => {
    e.preventDefault();
    console.log('Regular login submitted');
  };

  const handleForgotPassword = () => {
    console.log('Forgot password clicked');
  };

  const handleSignUp = () => {
    navigate('/signup');
  };

  return (
    <div className="auth-container">
    <div className="auth-left">
      <div className="auth-left-background"></div>
    </div>
      <div className="auth-right">
        <div className="auth-card">
          <h1 className="auth-title">💼 Market Brief</h1>
          <h2 className="auth-description">Log in to continue</h2>
          
          <button className="external-auth-button" onClick={handleGoogleLogin}>
            <GoogleIcon className="external-auth-icon" />
            Continue with Google
          </button>
          
          <button className="external-auth-button" onClick={handleGitHubLogin}>
            <GitHubIcon className="external-auth-icon" />
            Continue with GitHub
          </button>
          
          <div className="divider">
            <span className="divider-line"></span>
            <span className="divider-text">or</span>
            <span className="divider-line"></span>
          </div>
          
          <form className="auth-form" onSubmit={handleLogin}>
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
            
            <div className="form-options">
              <label className="remember-me">
                <input type="checkbox" id="remember" />
                Remember me
              </label>
              <button type="button" className="forgot-password" onClick={handleForgotPassword}>
                Forgot your password?
              </button>
            </div>
            
            <button type="submit" className="auth-button">
              LOGIN
            </button>
          </form>
          
          <p className="auth-footer-text">
            Don't have an account? <span className="auth-footer-link" onClick={handleSignUp}>Register</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;