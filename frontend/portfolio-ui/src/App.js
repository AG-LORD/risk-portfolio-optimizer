import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import KYCPage from "./pages/KYCPage";
import LoginPage from "./pages/LoginPage";

function App() {
  const [loggedIn, setLoggedIn] = useState(!!localStorage.getItem("token"));

  // KYC is done only if server previously confirmed kyc_status === "approved"
  const [kycDone, setKycDone] = useState(
    localStorage.getItem("kyc_status") === "approved"
  );

  // Called by LoginPage with the kyc_status from the server response
  const handleLogin = (kycStatus) => {
    setLoggedIn(true);
    setKycDone(kycStatus === "approved");
  };

  const handleKYCComplete = () => {
    localStorage.setItem("kyc_status", "approved");
    setKycDone(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("hasSeenGuide"); // reset guide so it shows fresh next login
    // Don't remove kyc_status — login response from DB will always have the correct value
    setLoggedIn(false);
    setKycDone(false);
  };

  if (!loggedIn) {
    return <LoginPage onLogin={handleLogin} />;
  }

  if (!kycDone) {
    return <KYCPage onKYCComplete={handleKYCComplete} />;
  }

  return <Dashboard onLogout={handleLogout} />;
}

export default App;
