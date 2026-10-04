
import { useEffect, useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

const STATUS_DETAILS = {
  TRUSTED: "Cryptographically validated provenance from a trusted issuer.",
  SELF_ASSERTED:
    "Provenance information exists, but the signing issuer is not trusted.",
  UNVERIFIABLE: "No sufficient cryptographic provenance was found.",
  TAMPERED:
    "The file no longer matches its cryptographically recorded provenance.",
  INCONSISTENT:
    "Provenance evidence contains conflicting or invalid information.",
};

function App() {
  const [page, setPage] = useState("home");
  const [menuOpen, setMenuOpen] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [registerForm, setRegisterForm] = useState({
    model: "",
    model_identifier: "",
    model_type: "",
    tool: "",
    issuer: "",
  });

  const navigate = (nextPage) => {
    setPage(nextPage);
    setMenuOpen(false);
    setMessage("");
  };

  const handleAuth = (e) => {
    e.preventDefault();
    setMessage("UI prototype only. Connect authentication to your backend.");
  };

  const handleFile = (e) => {
    setFile(e.target.files?.[0] || null);
    setResult(null);
    setMessage("");
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/provenance/history?limit=20`,
      );
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      setHistory(payload.items || []);
    } catch (error) {
      console.error("Failed to load provenance history", error);
    }
  };

  useEffect(() => {
    if (page === "provenance") {
      fetchHistory();
    }
  }, [page]);

  const submitArtifact = async (mode) => {
    if (!file) {
      setMessage("Please choose a file before submitting.");
      return;
    }

    setLoading(true);
    setMessage("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      if (mode === "register") {
        Object.entries(registerForm).forEach(([key, value]) => {
          if (value) formData.append(key, value);
        });
      }

      const response = await fetch(`${API_BASE}/api/provenance/${mode}`, {
        method: "POST",
        body: formData,
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "The request failed.");
      }

      setResult(payload);
      if (mode === "register") {
        await fetchHistory();
      }
      setMessage(payload.success ? "Request complete." : "Request failed.");
    } catch (error) {
      setMessage(error.message || "Unable to complete the request.");
    } finally {
      setLoading(false);
    }
  };

  const renderArtifactSummary = (artifact) => {
    const status = artifact?.status || "UNVERIFIABLE";
    const statusDescription =
      STATUS_DETAILS[status] || STATUS_DETAILS.UNVERIFIABLE;
    return (
      <div className="workspace-card">
        <div className="form-kicker">RESULT</div>
        <h2>Verification outcome</h2>
        <div className={`result-banner status-${String(status).toLowerCase()}`}>
          <span className="result-banner-icon" aria-hidden="true">
            {status === "TRUSTED" ? "✓" : status === "TAMPERED" || status === "INCONSISTENT" ? "!" : "◈"}
          </span>
          <div className="result-banner-copy">
            <strong>{artifact?.filename || file?.name || "Digital artifact"}</strong>
            <small>{statusDescription}</small>
          </div>
          <span className="status-badge">
            {status === "TRUSTED" ? "✓ " : status === "TAMPERED" || status === "INCONSISTENT" ? "! " : "◈ "}{status.replaceAll("_", " ")}
          </span>
        </div>

        <div className="result-grid">
          <div className="result-field"><span>MODEL</span><strong>{artifact?.model || "Not provided"}</strong></div>
          <div className="result-field"><span>MODEL ID</span><strong>{artifact?.model_identifier || "Not provided"}</strong></div>
          <div className="result-field"><span>MODEL TYPE</span><strong>{artifact?.model_type || "Not provided"}</strong></div>
          <div className="result-field"><span>TOOL</span><strong>{artifact?.tool || "Not provided"}</strong></div>
          <div className="result-field"><span>ISSUER</span><strong>{artifact?.issuer || "Not provided"}</strong></div>
          <div className="result-field"><span>C2PA EVIDENCE</span><strong className={artifact?.c2pa_found ? "value-valid" : "value-neutral"}><span aria-hidden="true">{artifact?.c2pa_found ? "✓ " : "— "}</span>{artifact?.c2pa_found ? "Found" : "Not found"}</strong></div>
          <div className="result-field"><span>VALIDATION</span><strong className={String(artifact?.validation_state || "").toLowerCase().includes("valid") ? "value-valid" : ""}>{artifact?.validation_state || "Not available"}</strong></div>
          <div className="result-field"><span>SHA-256 FINGERPRINT</span><strong className="hash-value" title={artifact?.sha256 || "Not available"}>{artifact?.sha256 || "Not available"}</strong></div>
          <div className="result-field"><span>BLOCKCHAIN</span><strong className={String(artifact?.blockchain?.status || "").toLowerCase().includes("anchor") && !String(artifact?.blockchain?.status || "").toLowerCase().includes("not") ? "value-valid" : ""}>{artifact?.blockchain?.status || "NOT ANCHORED"}</strong></div>
          <div className="result-field"><span>TRANSACTION HASH</span><strong className="hash-value" title={artifact?.blockchain?.tx_hash || "Not available"}>{artifact?.blockchain?.tx_hash || "Not available"}</strong></div>
        </div>
      </div>
    );
  };

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: "▦" },
    { id: "verify", label: "Verify Artifact", icon: "◈" },
    { id: "register", label: "Register Artifact", icon: "+" },
    { id: "provenance", label: "Provenance History", icon: "↗" },
  ];

  return (
    <main className="app-shell">
      <div className="background-shape shape-one" />
      <div className="background-shape shape-two" />
      <div className="background-shape shape-three" />

      <header className="topbar">
        <button className="brand" onClick={() => navigate("home")}>
          <span className="brand-symbol">M</span>
          <span>
            MODEL<span className="brand-light">LEDGER</span>
          </span>
        </button>

        <span className="top-caption">DIGITAL PROVENANCE / WEB 3.0</span>

        <button
          className="mobile-menu"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation"
        >
          ☰
        </button>

        <nav className={`top-links ${menuOpen ? "show-menu" : ""}`}>
          {page === "home" ? (
            <>
              <button onClick={() => navigate("home")}>Home</button>
              <button onClick={() => navigate("dashboard")}>Explore</button>
              <button onClick={() => navigate("provenance")}>About</button>
              <button
                className="nav-login"
                onClick={() => {
                  setAuthMode("login");
                  navigate("auth");
                }}
              >
                Login ↗
              </button>
              <button
                className="nav-signup"
                onClick={() => {
                  setAuthMode("signup");
                  navigate("auth");
                }}
              >
                Get Started
              </button>
            </>
          ) : (
            <>
              <button onClick={() => navigate("dashboard")}>Dashboard</button>
              <button onClick={() => navigate("verify")}>Verification</button>
              <button onClick={() => navigate("provenance")}>Provenance</button>
              <button className="nav-signup" onClick={() => navigate("home")}>
                Home ↗
              </button>
            </>
          )}
        </nav>
      </header>

      {page !== "home" && page !== "auth" && (
        <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
          <div className="side-label">WORKSPACE</div>
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`side-link ${page === item.id ? "active" : ""}`}
              onClick={() => navigate(item.id)}
            >
              <span className="side-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
          <div className="sidebar-bottom">
            <div className="avatar">A</div>
            <div>
              <strong>Guest User</strong>
              <small>Prototype account</small>
            </div>
          </div>
        </aside>
      )}

      {page === "home" && (
        <section className="hero-section">
          <div className="hero-sidebar">
            <span className="vertical-text">TRACE · VERIFY · PROVE</span>
            <span className="sidebar-dash" />
            <span className="vertical-small">DIGITAL CONTENT PROVENANCE</span>
          </div>

          <div className="hero-content">
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              DIGITAL CONTENT PROVENANCE
            </div>
            <h1 className="hero-brand-title">
              MODEL<span>LEDGER</span>
            </h1>
            <h2 className="hero-tagline">Trace. Verify. Prove Digital Trust in the AI Era.</h2>
            <p className="hero-description">
              Follow the story behind digital content. ModelLedger helps you inspect provenance evidence, verify artifact fingerprints, and explore trusted records—so digital trust can be built on evidence, not guesses.
            </p>
            <div className="hero-actions">
              <button
                className="primary-button"
                onClick={() => {
                  setAuthMode("signup");
                  navigate("auth");
                }}
              >
                GET STARTED <span>↗</span>
              </button>
              <button
                className="secondary-button"
                onClick={() => navigate("verify")}
              >
                VERIFY AN ARTIFACT <span>→</span>
              </button>
            </div>
            <div className="hero-footnote">
              <span className="foot-line" />
              BLOCKCHAIN-BACKED PROVENANCE
            </div>
          </div>

          <div className="hero-visual hero-logo-visual">
            <img
              className="hero-logo-image"
              src="/modelledger-logo.jpg"
              alt="ModelLedger digital provenance emblem"
            />
            <div className="visual-caption">
              <span>01 / 04</span>
              <span>PROVENANCE STARTS HERE</span>
            </div>
          </div>

          <div className="hero-bottom">
            <span>01 — DIGITAL TRUST</span>
            <span>BUILT FOR THE AI ERA</span>
            <span>SCROLL TO EXPLORE ↓</span>
          </div>
        </section>
      )}

      {page === "auth" && (
        <section className="content-page auth-page">
          <div className="auth-art">
            <span className="eyebrow">MODELLEDGER / ACCESS</span>
            <h1>
              YOUR
              <br />
              CONTENT.
              <br />
              <span className="outlined-text">YOUR PROOF.</span>
            </h1>
            <p>Secure the origin of your digital creations.</p>
            <div className="auth-art-circle">M</div>
          </div>

          <div className="auth-form-area">
            <div className="form-card">
              <div className="form-kicker">WELCOME TO MODELLEDGER</div>
              <h2>
                {authMode === "login" ? "Welcome back." : "Create account."}
              </h2>
              <p className="form-description">
                {authMode === "login"
                  ? "Sign in to access your provenance workspace."
                  : "Start registering and verifying your digital artifacts."}
              </p>

              <form onSubmit={handleAuth}>
                {authMode === "signup" && (
                  <label>
                    Full name
                    <input type="text" placeholder="Your name" required />
                  </label>
                )}
                <label>
                  Email address
                  <input
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </label>
                <label>
                  Password
                  <input
                    type="password"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </label>
                <button className="primary-button form-submit" type="submit">
                  {authMode === "login" ? "SIGN IN" : "CREATE ACCOUNT"} ↗
                </button>
              </form>

              {message && <p className="notice">{message}</p>}

              <div className="form-switch">
                {authMode === "login"
                  ? "Don't have an account?"
                  : "Already have an account?"}
                <button
                  onClick={() => {
                    setAuthMode(authMode === "login" ? "signup" : "login");
                    setMessage("");
                  }}
                >
                  {authMode === "login" ? "Sign up" : "Log in"}
                </button>
              </div>
              <button className="back-home" onClick={() => navigate("home")}>
                ← Back to home
              </button>
            </div>
          </div>
        </section>
      )}

      {page === "dashboard" && (
        <section className="content-page workspace-page">
          <div className="page-heading">
            <div>
              <div className="eyebrow">YOUR WORKSPACE / 01</div>
              <h1>
                Dashboard<span className="heading-period">.</span>
              </h1>
              <p>Manage your digital artifacts and their provenance.</p>
            </div>
            <button
              className="primary-button"
              onClick={() => navigate("register")}
            >
              + REGISTER ARTIFACT
            </button>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <span>TOTAL ARTIFACTS</span>
              <strong>{history.length || "—"}</strong>
              <small>Registered artifacts</small>
            </div>
            <div className="stat-card">
              <span>VERIFICATIONS</span>
              <strong>—</strong>
              <small>Verification requests</small>
            </div>
            <div className="stat-card">
              <span>PROVENANCE RECORDS</span>
              <strong>{history.length || "—"}</strong>
              <small>Recorded history</small>
            </div>
          </div>

          <div className="workspace-card">
            <div className="workspace-card-header">
              <div>
                <span className="form-kicker">ARTIFACT MANAGEMENT</span>
                <h2>Your recent artifacts</h2>
              </div>
              <button
                className="text-button"
                onClick={() => navigate("provenance")}
              >
                VIEW HISTORY ↗
              </button>
            </div>
            {history.length ? (
              <div style={{ display: "grid", gap: 12 }}>
                {history.slice(0, 5).map((item) => (
                  <div key={item.id} className="selected-file">
                    <span>◈</span>
                    <div>
                      <strong>{item.filename}</strong>
                      <small>{item.status}</small>
                    </div>
                    <button
                      onClick={() => {
                        setResult({ artifact: item });
                        setPage("verify");
                      }}
                    >
                      Open
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">◈</div>
                <h3>No artifacts yet</h3>
                <p>
                  Register a digital creation to start building its provenance
                  record.
                </p>
                <button
                  className="secondary-button"
                  onClick={() => navigate("register")}
                >
                  REGISTER YOUR FIRST ARTIFACT →
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {(page === "verify" || page === "register") && (
        <section className="content-page workspace-page">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                WORKSPACE / {page === "verify" ? "02" : "03"}
              </div>
              <h1>
                {page === "verify" ? "Verify Artifact" : "Register Artifact"}
                <span className="heading-period">.</span>
              </h1>
              <p>
                {page === "verify"
                  ? "Check an artifact against existing provenance records."
                  : "Create a fingerprint and submit the artifact for provenance registration."}
              </p>
            </div>
          </div>

          <div className="upload-layout">
            <div className="workspace-card upload-card">
              <div className="form-kicker">
                {page === "verify"
                  ? "ARTIFACT VERIFICATION"
                  : "NEW REGISTRATION"}
              </div>
              <h2>
                {page === "verify"
                  ? "Upload your file."
                  : "Register your creation."}
              </h2>
              <p className="form-description">
                {page === "verify"
                  ? "Select the digital artifact you want to verify."
                  : "Select the file you created to start the registration process."}
              </p>

              <label className="upload-zone">
                <input
                  type="file"
                  accept="image/*,video/*,audio/*,.pdf,.txt"
                  onChange={handleFile}
                />
                <span className="upload-icon">↑</span>
                <strong>{file ? file.name : "Drop your file here"}</strong>
                <span>
                  {file ? "File selected" : "or click to browse your device"}
                </span>
                <small>Images, videos, audio and documents</small>
              </label>

              {file && (
                <div className="selected-file">
                  <span>◈</span>
                  <div>
                    <strong>{file.name}</strong>
                    <small>{(file.size / 1024 / 1024).toFixed(2)} MB</small>
                  </div>
                  <button onClick={() => setFile(null)}>×</button>
                </div>
              )}

              {page === "register" && (
                <>
                  <label className="input-label">
                    Model name
                    <input
                      type="text"
                      className="text-input"
                      value={registerForm.model}
                      onChange={(e) =>
                        setRegisterForm({
                          ...registerForm,
                          model: e.target.value,
                        })
                      }
                      placeholder="Optional: Gemini, GPT, Claude..."
                    />
                  </label>
                  <label className="input-label">
                    Model identifier
                    <input
                      type="text"
                      className="text-input"
                      value={registerForm.model_identifier}
                      onChange={(e) =>
                        setRegisterForm({
                          ...registerForm,
                          model_identifier: e.target.value,
                        })
                      }
                      placeholder="Optional model ID"
                    />
                  </label>
                  <label className="input-label">
                    Model type
                    <input
                      type="text"
                      className="text-input"
                      value={registerForm.model_type}
                      onChange={(e) =>
                        setRegisterForm({
                          ...registerForm,
                          model_type: e.target.value,
                        })
                      }
                      placeholder="Optional model type"
                    />
                  </label>
                  <label className="input-label">
                    Tool
                    <input
                      type="text"
                      className="text-input"
                      value={registerForm.tool}
                      onChange={(e) =>
                        setRegisterForm({
                          ...registerForm,
                          tool: e.target.value,
                        })
                      }
                      placeholder="Optional generation tool"
                    />
                  </label>
                  <label className="input-label">
                    Issuer
                    <input
                      type="text"
                      className="text-input"
                      value={registerForm.issuer}
                      onChange={(e) =>
                        setRegisterForm({
                          ...registerForm,
                          issuer: e.target.value,
                        })
                      }
                      placeholder="Optional issuer"
                    />
                  </label>
                </>
              )}

              <button
                className="primary-button form-submit"
                disabled={!file || loading}
                onClick={() => submitArtifact(page)}
              >
                {loading
                  ? "WORKING…"
                  : page === "verify"
                    ? "VERIFY ARTIFACT"
                    : "REGISTER ARTIFACT"}{" "}
                ↗
              </button>
              {message && <p className="notice">{message}</p>}
            </div>

            <div className="info-panel">
              <div className="info-panel-art">M</div>
              <span className="form-kicker">HOW IT WORKS</span>
              <h3>
                {page === "verify"
                  ? "Verify the origin."
                  : "Record the origin."}
              </h3>
              <p>
                {page === "verify"
                  ? "The system compares the current file SHA-256 and C2PA evidence against the provenance registry. A match alone does not prove an AI model was the creator."
                  : "Manual metadata is only accepted as self-asserted unless C2PA evidence is present and trusted."}
              </p>
              <div className="info-step">
                <span>01</span>
                <p>Upload your digital artifact</p>
              </div>
              <div className="info-step">
                <span>02</span>
                <p>Compute SHA-256 and inspect C2PA</p>
              </div>
              <div className="info-step">
                <span>03</span>
                <p>
                  {page === "verify"
                    ? "Compare against registered provenance evidence"
                    : "Store a verifiable provenance record"}
                </p>
              </div>
            </div>
          </div>

          {result && renderArtifactSummary(result.artifact || result)}
        </section>
      )}

      {page === "provenance" && (
        <section className="content-page workspace-page">
          <div className="page-heading">
            <div>
              <div className="eyebrow">WORKSPACE / 04</div>
              <h1>
                Provenance<span className="heading-period">.</span>
              </h1>
              <p>Explore the origin and transformation history of artifacts.</p>
            </div>
          </div>

          <div className="workspace-card provenance-card">
            <div className="form-kicker">PROVENANCE TIMELINE</div>
            <h2>Artifact history</h2>
            {history.length ? (
              <div style={{ display: "grid", gap: 12 }}>
                {history.map((item) => (
                  <div key={item.id} className="selected-file">
                    <span>↗</span>
                    <div>
                      <strong>{item.filename}</strong>
                      <small>
                        {item.status} · {item.issuer || "Unknown issuer"}
                      </small>
                    </div>
                    <button
                      onClick={() => {
                        setResult({ artifact: item });
                        setPage("verify");
                      }}
                    >
                      View
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">↗</div>
                <h3>No history available</h3>
                <p>
                  Provenance records will appear here once artifacts are
                  registered and their history is recorded.
                </p>
                <button
                  className="secondary-button"
                  onClick={() => navigate("register")}
                >
                  REGISTER ARTIFACT →
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      <footer className="site-footer">
        <span>© 2026 MODELLEDGER</span>
        <span>TRACE THE ORIGIN. VERIFY THE STORY.</span>
        <button onClick={() => navigate("home")}>BACK TO TOP ↑</button>
      </footer>
    </main>
  );
}

export default App;