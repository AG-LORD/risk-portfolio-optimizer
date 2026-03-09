import { useState } from "react";
import "../styles/login.css";

function LoginPage({ onLogin }) {

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [isSignup, setIsSignup] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const url = isSignup
      ? "http://127.0.0.1:5000/signup"
      : "http://127.0.0.1:5000/login";

    const payload = isSignup
      ? { name, email, password }
      : { email, password };

    try {

      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        alert(data.error || "Something went wrong");
        return;
      }

      if (!isSignup) {
        localStorage.setItem("token", data.token);
        onLogin();
      } else {
        alert("Account created! Please login.");
        setIsSignup(false);
      }

    } catch (err) {
      console.error(err);
      alert("Server error");
    }
  };

  return (

    <div className="login-container">

      <div className="login-card">

        <div className="login-title">

          <h1>Risk-Aware Portfolio Optimizer</h1>

          <p>
            {isSignup
              ? "Create an account"
              : "Sign in to access your portfolio dashboard"}
          </p>

        </div>


        <form onSubmit={handleSubmit} className="login-form">

          {isSignup && (

            <div className="input-group">

              <label>Name</label>

              <input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e)=>setName(e.target.value)}
                required
              />

            </div>

          )}


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


          {!isSignup && (

            <div className="forgot">

              <a href="#">Forgot password?</a>

            </div>

          )}


          <button type="submit" className="login-btn">

            {isSignup ? "Create Account" : "Sign In"}

          </button>

        </form>


        <div className="signup">

          {isSignup ? "Already have an account?" : "Don't have an account?"}

          <span onClick={()=>setIsSignup(!isSignup)}>

            {isSignup ? " Sign in" : " Sign up"}

          </span>

        </div>

      </div>

    </div>

  );
}

export default LoginPage;