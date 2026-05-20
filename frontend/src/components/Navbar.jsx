import { Link, useLocation } from 'react-router-dom';
import './Navbar.css';
import zapateraLogo from '../assets/zapatera-logo.png';

export default function Navbar() {
  const { pathname } = useLocation();
  const nav = [
    { to: '/',      label: 'Home' },
    { to: '/track', label: 'Track Request' },
  ];
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-brand">
          <img src={zapateraLogo} alt="Zapatera Logo" className="logo-icon" />
          <span>
            <div className="brand-title">Brgy. Zapatera</div>
            <div className="brand-sub">CertTrack Portal</div>
          </span>
        </Link>
        <nav className="navbar-links">
          {nav.map(n => (
            <Link
              key={n.to}
              to={n.to}
              className={`nav-link ${pathname === n.to ? 'active' : ''}`}
            >
              {n.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
