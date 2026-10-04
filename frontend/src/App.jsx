
import { useState } from 'react'
import './App.css'

function App() {
  const [page, setPage] = useState('home')
  const [menuOpen, setMenuOpen] = useState(false)
  const [authMode, setAuthMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [file, setFile] = useState(null)
  const [message, setMessage] = useState('')

  const navigate = (nextPage) => {
    setPage(nextPage)
    setMenuOpen(false)
    setMessage('')
  }

  const handleAuth = (e) => {
    e.preventDefault()
    setMessage('UI prototype only. Connect authentication to your backend.')
  }

  const handleFile = (e) => {
    setFile(e.target.files?.[0] || null)
    setMessage('')
  }

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '▦' },
    { id: 'verify', label: 'Verify Artifact', icon: '◈' },
    { id: 'register', label: 'Register Artifact', icon: '+' },
    { id: 'provenance', label: 'Provenance History', icon: '↗' },
  ]

  return (
    <main className="app-shell">
      <div className="background-shape shape-one" />
      <div className="background-shape shape-two" />
      <div className="background-shape shape-three" />

      <header className="topbar">
        <button className="brand" onClick={() => navigate('home')}>
          <span className="brand-symbol">M</span>
          <span>MODEL<span className="brand-light">LEDGER</span></span>
        </button>

        <span className="top-caption">DIGITAL PROVENANCE / WEB 3.0</span>

        <button
          className="mobile-menu"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle navigation"
        >
          ☰
        </button>

        <nav className={`top-links ${menuOpen ? 'show-menu' : ''}`}>
          {page === 'home' ? (
            <>
              <button onClick={() => navigate('home')}>Home</button>
              <button onClick={() => navigate('dashboard')}>Explore</button>
              <button onClick={() => navigate('provenance')}>About</button>
              <button className="nav-login" onClick={() => {
                setAuthMode('login')
                navigate('auth')
              }}>Login ↗</button>
              <button className="nav-signup" onClick={() => {
                setAuthMode('signup')
                navigate('auth')
              }}>Get Started</button>
            </>
          ) : (
            <>
              <button onClick={() => navigate('dashboard')}>Dashboard</button>
              <button onClick={() => navigate('verify')}>Verification</button>
              <button onClick={() => navigate('provenance')}>Provenance</button>
              <button className="nav-signup" onClick={() => navigate('home')}>Home ↗</button>
            </>
          )}
        </nav>
      </header>

      {page !== 'home' && page !== 'auth' && (
        <aside className={`sidebar ${menuOpen ? 'sidebar-open' : ''}`}>
          <div className="side-label">WORKSPACE</div>
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`side-link ${page === item.id ? 'active' : ''}`}
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

      {page === 'home' && (
        <section className="hero-section">
          <div className="hero-sidebar">
            <span className="vertical-text">TRACE · VERIFY · PROVE</span>
            <span className="sidebar-dash" />
            <span className="vertical-small">DIGITAL CONTENT PROVENANCE</span>
          </div>

          <div className="hero-content">
            <div className="eyebrow">
              <span className="eyebrow-dot" />
              TRUST THE ORIGIN. VERIFY THE STORY.
            </div>

            <h1>
              PROVE
              <br />
              <span>WHAT</span>
              <br />
              <span className="outlined-text">CREATED IT.</span>
            </h1>

            <p className="hero-description">
              Every digital creation has a story.
              ModelLedger helps you register, verify and
              trace the origin of AI-generated content
              with a verifiable digital fingerprint.
            </p>

            <div className="hero-actions">
              <button
                className="primary-button"
                onClick={() => {
                  setAuthMode('signup')
                  navigate('auth')
                }}
              >
                GET STARTED <span>↗</span>
              </button>
              <button
                className="secondary-button"
                onClick={() => navigate('verify')}
              >
                VERIFY AN ARTIFACT <span>→</span>
              </button>
            </div>

            <div className="hero-footnote">
              <span className="foot-line" />
              BLOCKCHAIN-BACKED PROVENANCE
            </div>
          </div>

          <div className="hero-visual">
            <div className="visual-number">01</div>
            <div className="visual-number second-number">02</div>
            <div className="visual-card">
              <div className="visual-card-top">
                <span className="visual-dot" />
                <span>MODELLEDGER / PROTOCOL</span>
                <span>↗</span>
              </div>
              <div className="fingerprint">
                <div className="fingerprint-ring ring-one" />
                <div className="fingerprint-ring ring-two" />
                <div className="fingerprint-ring ring-three" />
                <div className="fingerprint-center">M</div>
              </div>
              <div className="visual-card-bottom">
                <div>
                  <small>ARTIFACT STATUS</small>
                  <strong>Ready to verify</strong>
                </div>
                <div className="visual-status">●</div>
              </div>
            </div>
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

      {page === 'auth' && (
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
              <h2>{authMode === 'login' ? 'Welcome back.' : 'Create account.'}</h2>
              <p className="form-description">
                {authMode === 'login'
                  ? 'Sign in to access your provenance workspace.'
                  : 'Start registering and verifying your digital artifacts.'}
              </p>

              <form onSubmit={handleAuth}>
                {authMode === 'signup' && (
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
                  {authMode === 'login' ? 'SIGN IN' : 'CREATE ACCOUNT'} ↗
                </button>
              </form>

              {message && <p className="notice">{message}</p>}

              <div className="form-switch">
                {authMode === 'login'
                  ? "Don't have an account?"
                  : 'Already have an account?'}
                <button onClick={() => {
                  setAuthMode(authMode === 'login' ? 'signup' : 'login')
                  setMessage('')
                }}>
                  {authMode === 'login' ? 'Sign up' : 'Log in'}
                </button>
              </div>
              <button className="back-home" onClick={() => navigate('home')}>
                ← Back to home
              </button>
            </div>
          </div>
        </section>
      )}

      {page === 'dashboard' && (
        <section className="content-page workspace-page">
          <div className="page-heading">
            <div>
              <div className="eyebrow">YOUR WORKSPACE / 01</div>
              <h1>Dashboard<span className="heading-period">.</span></h1>
              <p>Manage your digital artifacts and their provenance.</p>
            </div>
            <button className="primary-button" onClick={() => navigate('register')}>
              + REGISTER ARTIFACT
            </button>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <span>TOTAL ARTIFACTS</span>
              <strong>—</strong>
              <small>Registered artifacts</small>
            </div>
            <div className="stat-card">
              <span>VERIFICATIONS</span>
              <strong>—</strong>
              <small>Verification requests</small>
            </div>
            <div className="stat-card">
              <span>PROVENANCE RECORDS</span>
              <strong>—</strong>
              <small>Recorded history</small>
            </div>
          </div>

          <div className="workspace-card">
            <div className="workspace-card-header">
              <div>
                <span className="form-kicker">ARTIFACT MANAGEMENT</span>
                <h2>Your recent artifacts</h2>
              </div>
              <button className="text-button" onClick={() => navigate('provenance')}>
                VIEW HISTORY ↗
              </button>
            </div>
            <div className="empty-state">
              <div className="empty-icon">◈</div>
              <h3>No artifacts yet</h3>
              <p>Register a digital creation to start building its provenance record.</p>
              <button className="secondary-button" onClick={() => navigate('register')}>
                REGISTER YOUR FIRST ARTIFACT →
              </button>
            </div>
          </div>
        </section>
      )}

      {(page === 'verify' || page === 'register') && (
        <section className="content-page workspace-page">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                WORKSPACE / {page === 'verify' ? '02' : '03'}
              </div>
              <h1>
                {page === 'verify' ? 'Verify Artifact' : 'Register Artifact'}
                <span className="heading-period">.</span>
              </h1>
              <p>
                {page === 'verify'
                  ? 'Check an artifact against existing provenance records.'
                  : 'Create a fingerprint and submit the artifact for provenance registration.'}
              </p>
            </div>
          </div>

          <div className="upload-layout">
            <div className="workspace-card upload-card">
              <div className="form-kicker">
                {page === 'verify' ? 'ARTIFACT VERIFICATION' : 'NEW REGISTRATION'}
              </div>
              <h2>{page === 'verify' ? 'Upload your file.' : 'Register your creation.'}</h2>
              <p className="form-description">
                {page === 'verify'
                  ? 'Select the digital artifact you want to verify.'
                  : 'Select the file you created to start the registration process.'}
              </p>

              <label className="upload-zone">
                <input
                  type="file"
                  accept="image/*,video/*,audio/*,.pdf,.txt"
                  onChange={handleFile}
                />
                <span className="upload-icon">↑</span>
                <strong>{file ? file.name : 'Drop your file here'}</strong>
                <span>{file ? 'File selected' : 'or click to browse your device'}</span>
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

              {page === 'register' && (
                <>
                  <label className="input-label">
                    Creation tool / AI model
                    <input
                      type="text"
                      placeholder="e.g. Gemini, GPT, Adobe..."
                      className="text-input"
                    />
                  </label>
                  <label className="input-label">
                    Description
                    <textarea
                      className="text-input description-input"
                      placeholder="Describe your artifact (optional)"
                    />
                  </label>
                </>
              )}

              <button
                className="primary-button form-submit"
                disabled={!file}
                onClick={() => setMessage(
                  page === 'verify'
                    ? 'File selected. Connect the verification API to check its fingerprint and provenance.'
                    : 'File selected. Connect the registration API to create its fingerprint and provenance record.'
                )}
              >
                {page === 'verify' ? 'VERIFY ARTIFACT' : 'REGISTER ARTIFACT'} ↗
              </button>
              {message && <p className="notice">{message}</p>}
            </div>

            <div className="info-panel">
              <div className="info-panel-art">M</div>
              <span className="form-kicker">HOW IT WORKS</span>
              <h3>{page === 'verify' ? 'Verify the origin.' : 'Record the origin.'}</h3>
              <p>
                {page === 'verify'
                  ? 'The system can compare your file fingerprint with previously registered artifacts. A match alone does not prove which AI model originally generated it.'
                  : 'The registration flow can generate a cryptographic fingerprint, record the provided metadata and store a provenance reference.'}
              </p>
              <div className="info-step">
                <span>01</span>
                <p>Upload your digital artifact</p>
              </div>
              <div className="info-step">
                <span>02</span>
                <p>Generate a fingerprint</p>
              </div>
              <div className="info-step">
                <span>03</span>
                <p>{page === 'verify' ? 'Compare against registered records' : 'Store a verifiable provenance record'}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {page === 'provenance' && (
        <section className="content-page workspace-page">
          <div className="page-heading">
            <div>
              <div className="eyebrow">WORKSPACE / 04</div>
              <h1>Provenance<span className="heading-period">.</span></h1>
              <p>Explore the origin and transformation history of artifacts.</p>
            </div>
          </div>

          <div className="workspace-card provenance-card">
            <div className="form-kicker">PROVENANCE TIMELINE</div>
            <h2>Artifact history</h2>
            <div className="empty-state">
              <div className="empty-icon">↗</div>
              <h3>No history available</h3>
              <p>Provenance records will appear here once artifacts are registered and their history is recorded.</p>
              <button className="secondary-button" onClick={() => navigate('register')}>
                REGISTER ARTIFACT →
              </button>
            </div>
          </div>
        </section>
      )}

      <footer className="site-footer">
        <span>© 2026 MODELLEDGER</span>
        <span>TRACE THE ORIGIN. VERIFY THE STORY.</span>
        <button onClick={() => navigate('home')}>BACK TO TOP ↑</button>
      </footer>
    </main>
  )
}

export default App 