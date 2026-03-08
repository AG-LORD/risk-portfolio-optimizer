import { useState } from "react";
import "../styles/login.css";

function LoginPage({ onLogin }) {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin();
  };

  return (

    <div className="login-container">

      <div className="login-card">

        {/* TITLE */}

        <div className="login-title">

          <h1>Risk-Aware Portfolio Optimizer</h1>

          <p>
            Sign in to access your portfolio dashboard
          </p>

        </div>


        {/* FORM */}

        <form onSubmit={handleSubmit} className="login-form">

          <div className="input-group">

            <label>Email</label>

            <input
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e)=>setEmail(e.target.value)}
              required
            />

          </div>


          <div className="input-group">

            <label>Password</label>

            <div className="password-box">

              <input
                type={showPassword ? "text" : "password"}
                placeholder="Enter password"
                value={password}
                onChange={(e)=>setPassword(e.target.value)}
                required
              />

              <button
                type="button"
                className="show-btn"
                onClick={()=>setShowPassword(!showPassword)}
              >
                {showPassword ? "Hide" : "Show"}
              </button>

            </div>

          </div>


          <div className="forgot">

            <a href="#">Forgot password?</a>

          </div>


          <button type="submit" className="login-btn">

            Sign In

          </button>

        </form>


        <div className="signup">

          Don't have an account?

          <span> Sign up</span>

        </div>

      </div>

    </div>

  );
}

export default LoginPage;