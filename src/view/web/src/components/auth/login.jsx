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
    <div className="login-container">
      <div className="login-left">
      </div>
      <div className="login-right">
        <div className="login-card">
          <h1 className="login-title">Log in to Market Brief</h1>
          
          <button className="external-login-button" onClick={handleGoogleLogin}>
            <GoogleIcon className="external-login-icon" />
            Continue with Google
          </button>

          <button className="external-login-button" onClick={handleGitHubLogin}>
            <GitHubIcon className="external-login-icon" />
            Continue with GitHub
          </button>
          
          <div className="divider">
            <span className="divider-line"></span>
            <span className="divider-text">or</span>
            <span className="divider-line"></span>
          </div>
          
          <div className="login-form">
            <div className="form-group">
              <input
                type="email"
                id="email"
                className="form-input"
                placeholder="Email"
              />
            </div>
            <div className="form-group">
              <input
                type="password"
                id="password"
                className="form-input"
                placeholder="Password"
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
            
            <button onClick={handleLogin} className="login-button">
              LOGIN
            </button>
          </div>
          <p className="registration-text">Don't have an account? <span className="registration-span" onClick={handleSignUp}>Register</span></p>
        </div>
      </div>
    </div>
  );
}

export default Login;