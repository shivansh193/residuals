import { NavLink, Route, Routes, Link } from 'react-router-dom'
import Home from './pages/Home.jsx'
import Preclear from './pages/Preclear.jsx'
import Owner from './pages/Owner.jsx'
import Enrol from './pages/Enrol.jsx'
import Developers from './pages/Developers.jsx'

export default function App() {
  return (
    <div className="shell">
      <header className="top">
        <Link to="/" className="brand" aria-label="Residuals home">
          <span className="meter" aria-hidden><i /><i /><i /></span>
          <b>Residuals</b>
        </Link>
        <nav className="nav">
          <NavLink to="/" end>How it works</NavLink>
          <NavLink to="/preclear">Pre-clear audio</NavLink>
          <NavLink to="/owner">Voice owner</NavLink>
          <NavLink to="/enrol">Enrol a voice</NavLink>
          <NavLink to="/developers">API</NavLink>
        </nav>
        <span className="sandbox" title="All payments use the PayPal sandbox. No real money moves.">PayPal SANDBOX</span>
      </header>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/preclear" element={<Preclear />} />
        <Route path="/owner" element={<Owner />} />
        <Route path="/owner/:voiceId" element={<Owner />} />
        <Route path="/enrol" element={<Enrol />} />
        <Route path="/developers" element={<Developers />} />
      </Routes>
      <footer className="muted small" style={{ marginTop: 60, borderTop: '1px solid var(--rule)', paddingTop: 16 }}>
        Consent first: only voices enrolled by their owners can be registered. Every demo voice here is a fictional,
        fully synthetic persona. Payments run in the PayPal sandbox. <a href="https://github.com/shivansh193/residuals">Source (MIT)</a>
      </footer>
    </div>
  )
}
