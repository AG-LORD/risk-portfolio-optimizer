import { useRef, useState } from "react";
import "../styles/kyc.css";

const STEPS = ["PAN Card", "Aadhaar", "Selfie", "Review", "Done"];

function StepIndicator({ current }) {
  return (
    <div className="kyc-steps">
      {STEPS.map((label, i) => (
        <div key={label} className={`kyc-step ${i < current ? "done" : i === current ? "active" : ""}`}>
          <div className="kyc-step-circle">{i < current ? "✓" : i + 1}</div>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

function FileUploadBox({ label, hint, value, onChange, accept }) {
  const ref = useRef();
  return (
    <div className="kyc-upload-box" onClick={() => ref.current.click()}>
      <input
        ref={ref}
        type="file"
        accept={accept || "image/*,.pdf"}
        style={{ display: "none" }}
        onChange={(e) => onChange(e.target.files[0] || null)}
      />
      {value ? (
        <div className="kyc-file-chosen">
          <span className="kyc-file-icon">📎</span>
          <span className="kyc-file-name">{value.name}</span>
          <span className="kyc-file-size">{(value.size / 1024).toFixed(1)} KB</span>
        </div>
      ) : (
        <>
          <div className="kyc-upload-icon">⬆</div>
          <p className="kyc-upload-label">{label}</p>
          <small className="kyc-upload-hint">{hint}</small>
        </>
      )}
    </div>
  );
}

export default function KYCPage({ onKYCComplete }) {
  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);

  // Step 0 — PAN
  const [panNumber, setPanNumber] = useState("");
  const [panFile, setPanFile] = useState(null);
  const [panError, setPanError] = useState("");

  // Step 1 — Aadhaar
  const [aadhaarNumber, setAadhaarNumber] = useState("");
  const [aadhaarFront, setAadhaarFront] = useState(null);
  const [aadhaarBack, setAadhaarBack] = useState(null);
  const [aadhaarError, setAadhaarError] = useState("");

  // Step 2 — Selfie
  const [selfieFile, setSelfieFile] = useState(null);
  const [selfieError, setSelfieError] = useState("");

  const validatePAN = (value) => /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(value.trim().toUpperCase());
  const validateAadhaar = (value) => /^\d{12}$/.test(value.replace(/\s/g, ""));

  const goNext = () => {
    if (step === 0) {
      if (!validatePAN(panNumber)) {
        setPanError("Enter a valid PAN number (e.g. ABCDE1234F)");
        return;
      }
      if (!panFile) {
        setPanError("Please upload your PAN card image or PDF");
        return;
      }
      setPanError("");
    }

    if (step === 1) {
      if (!validateAadhaar(aadhaarNumber)) {
        setAadhaarError("Enter a valid 12-digit Aadhaar number");
        return;
      }
      if (!aadhaarFront || !aadhaarBack) {
        setAadhaarError("Please upload both front and back of your Aadhaar card");
        return;
      }
      setAadhaarError("");
    }

    if (step === 2) {
      if (!selfieFile) {
        setSelfieError("Please upload a selfie for face match");
        return;
      }
      setSelfieError("");
    }

    setStep((s) => s + 1);
  };

  const goBack = () => setStep((s) => Math.max(0, s - 1));

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://127.0.0.1:5000/kyc/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        }
      });
      const data = await res.json();
      if (!res.ok) {
        alert(data.error || "KYC submission failed. Please try again.");
        setSubmitting(false);
        return;
      }
      // Save to localStorage so App.js knows immediately
      localStorage.setItem("kyc_status", "approved");
      setStep(4); // Done
    } catch (err) {
      alert("Server error. Make sure the backend is running.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="kyc-page">
      <div className="kyc-card">
        <div className="kyc-header">
          <h2>Identity Verification (KYC)</h2>
          <p>Complete this once to unlock your portfolio dashboard. Your data is kept secure and never shared.</p>
        </div>

        <StepIndicator current={step} />

        {/* ─── Step 0: PAN ─── */}
        {step === 0 && (
          <div className="kyc-section">
            <h3>PAN Card Details</h3>
            <p className="kyc-section-hint">Your PAN is used for identity verification as required by SEBI regulations.</p>
            <label>PAN Number</label>
            <input
              className="kyc-input"
              type="text"
              placeholder="ABCDE1234F"
              maxLength={10}
              value={panNumber}
              onChange={(e) => setPanNumber(e.target.value.toUpperCase())}
            />
            <label>Upload PAN Card</label>
            <FileUploadBox
              label="Click to upload PAN card"
              hint="Accepted: JPG, PNG, PDF — max 5 MB"
              value={panFile}
              onChange={setPanFile}
            />
            {panError && <p className="kyc-error">{panError}</p>}
          </div>
        )}

        {/* ─── Step 1: Aadhaar ─── */}
        {step === 1 && (
          <div className="kyc-section">
            <h3>Aadhaar Details</h3>
            <p className="kyc-section-hint">Upload both sides of your Aadhaar card for address and identity proof.</p>
            <label>Aadhaar Number</label>
            <input
              className="kyc-input"
              type="text"
              placeholder="1234 5678 9012"
              maxLength={14}
              value={aadhaarNumber}
              onChange={(e) => {
                const digits = e.target.value.replace(/\D/g, "").slice(0, 12);
                setAadhaarNumber(digits.replace(/(.{4})/g, "$1 ").trim());
              }}
            />
            <label>Aadhaar Front</label>
            <FileUploadBox
              label="Upload front side"
              hint="Shows your name, DOB, photo"
              value={aadhaarFront}
              onChange={setAadhaarFront}
            />
            <label>Aadhaar Back</label>
            <FileUploadBox
              label="Upload back side"
              hint="Shows your address"
              value={aadhaarBack}
              onChange={setAadhaarBack}
            />
            {aadhaarError && <p className="kyc-error">{aadhaarError}</p>}
          </div>
        )}

        {/* ─── Step 2: Selfie ─── */}
        {step === 2 && (
          <div className="kyc-section">
            <h3>Face Verification</h3>
            <p className="kyc-section-hint">Take or upload a clear selfie. We'll match it with your PAN and Aadhaar photo.</p>
            <div className="kyc-selfie-tips">
              <span>✓ Good lighting</span>
              <span>✓ Face clearly visible</span>
              <span>✗ No sunglasses</span>
              <span>✗ No blur</span>
            </div>
            <FileUploadBox
              label="Upload selfie"
              hint="JPG or PNG — face should be clearly visible"
              value={selfieFile}
              onChange={setSelfieFile}
              accept="image/*"
            />
            {selfieError && <p className="kyc-error">{selfieError}</p>}
          </div>
        )}

        {/* ─── Step 3: Review ─── */}
        {step === 3 && (
          <div className="kyc-section">
            <h3>Review Your Submission</h3>
            <p className="kyc-section-hint">Please confirm your details before submitting. This cannot be undone.</p>
            <div className="kyc-review-grid">
              <div className="kyc-review-row">
                <span>PAN Number</span>
                <strong>{panNumber}</strong>
              </div>
              <div className="kyc-review-row">
                <span>PAN Document</span>
                <strong className="kyc-file-pill">📎 {panFile?.name}</strong>
              </div>
              <div className="kyc-review-row">
                <span>Aadhaar Number</span>
                <strong>{aadhaarNumber}</strong>
              </div>
              <div className="kyc-review-row">
                <span>Aadhaar Front</span>
                <strong className="kyc-file-pill">📎 {aadhaarFront?.name}</strong>
              </div>
              <div className="kyc-review-row">
                <span>Aadhaar Back</span>
                <strong className="kyc-file-pill">📎 {aadhaarBack?.name}</strong>
              </div>
              <div className="kyc-review-row">
                <span>Selfie</span>
                <strong className="kyc-file-pill">📎 {selfieFile?.name}</strong>
              </div>
            </div>
            <p className="kyc-disclaimer">
              By submitting, you confirm that all details are accurate and belong to you. This is a mock KYC simulation — no data is transmitted or stored externally.
            </p>
          </div>
        )}

        {/* ─── Step 4: Done ─── */}
        {step === 4 && (
          <div className="kyc-success">
            <div className="kyc-success-icon">✓</div>
            <h3>KYC Verified!</h3>
            <p>Your identity has been successfully verified. You can now access your portfolio dashboard.</p>
            <button className="kyc-btn-primary" onClick={onKYCComplete}>
              Go to Dashboard →
            </button>
          </div>
        )}

        {/* ─── Navigation Buttons ─── */}
        {step < 4 && (
          <div className="kyc-nav">
            {step > 0 && (
              <button className="kyc-btn-secondary" onClick={goBack} disabled={submitting}>
                ← Back
              </button>
            )}
            {step < 3 && (
              <button className="kyc-btn-primary" onClick={goNext}>
                Continue →
              </button>
            )}
            {step === 3 && (
              <button className="kyc-btn-primary" onClick={handleSubmit} disabled={submitting}>
                {submitting ? (
                  <span className="kyc-spinner" />
                ) : null}
                {submitting ? "Verifying..." : "Submit KYC"}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
