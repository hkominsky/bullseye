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
    <div className="login-container">
      <div className="login-left">
      </div>
      <div className="login-right">
        <div className="login-card">
          <h1 className="login-title">Sign up for Market Brief</h1>
          
          <button className="external-login-button" onClick={handleGoogleSignup}>
            <GoogleIcon className="external-login-icon" />
            Continue with Google
          </button>
          
          <button className="external-login-button" onClick={handleGitHubSignup}>
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
                type="text"
                id="firstName"
                className="form-input"
                placeholder="First Name"
              />
            </div>
            <div className="form-group">
              <input
                type="text"
                id="lastName"
                className="form-input"
                placeholder="Last Name"
              />
            </div>
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
            <div className="form-group">
              <input
                type="password"
                id="confirmPassword"
                className="form-input"
                placeholder="Confirm Password"
              />
            </div>
            
            <button onClick={handleSignup} className="login-button">
              SIGN UP
            </button>
          </div>
          <p className="registration-text">Already have an account? <span className="registration-span" onClick={handleLogin}>Log in</span></p>
        </div>
      </div>
    </div>
  );
}

export default Signup;