import { useState } from "react";
import "../styles/login.css";

function LoginPage({ onLogin, onSignup }) {

  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [name,     setName]     = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [isSignup,     setIsSignup]     = useState(false);
  const [error,        setError]        = useState("");
  const [loading,      setLoading]      = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const url = isSignup
      ? "http://127.0.0.1:5000/signup"
      : "http://127.0.0.1:5000/login";

    const payload = isSignup
      ? { name, email, password }
      : { email, password };

    try {
      const res  = await fetch(url, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        // If login is blocked because KYC is pending, tell the user clearly.
        if (res.status === 403 && data.requires_kyc) {
          setError("Your account exists but KYC is not yet complete. Please register again or contact support.");
        } else {
          setError(data.error || "Something went wrong");
        }
        return;
      }

      if (isSignup) {
        // Signup returns a token + kyc_status so the app goes straight to KYC.
        localStorage.setItem("token", data.token);
        localStorage.setItem("kyc_status", data.user?.kyc_status || "pending");
        onSignup(data.token, data.user?.kyc_status || "pending");
      } else {
        // Login only reaches here when kyc_status === "approved" (backend enforces).
        localStorage.setItem("token", data.token);
        localStorage.setItem("kyc_status", data.user?.kyc_status || "approved");
        onLogin(data.user?.kyc_status || "approved");
      }

    } catch (err) {
      console.error(err);
      setError("Server error — make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">

        <div className="login-title">
          <h1>Risk-Aware Portfolio Optimizer</h1>
          <p>
            {isSignup
              ? "Create an account — KYC verification follows"
              : "Sign in to access your portfolio dashboard"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">

          {isSignup && (
            <div className="input-group">
              <label>Name</label>
              <input
                type="text"
                placeholder="Your full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
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
              onChange={(e) => setEmail(e.target.value)}
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
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="show-btn"
                onClick={() => setShowPassword(!showPassword)}
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

          {error && (
            <p style={{ color: "#f87171", fontSize: "13px", margin: 0 }}>
              {error}
            </p>
          )}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading
              ? "Please wait…"
              : isSignup
              ? "Create Account & Start KYC"
              : "Sign In"}
          </button>

        </form>

        <div className="signup">
          {isSignup ? "Already have an account?" : "Don't have an account?"}
          <span onClick={() => { setIsSignup(!isSignup); setError(""); }}>
            {isSignup ? " Sign in" : " Sign up"}
          </span>
        </div>

      </div>
    </div>
  );
}

export default LoginPage;
