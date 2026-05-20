import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: '80px 24px', flex: 1 }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
      <h1 style={{ fontSize: 28, color: '#0F2D5E', marginBottom: 10 }}>Page Not Found</h1>
      <p style={{ color: '#64748B', marginBottom: 24 }}>
        The page you're looking for doesn't exist.
      </p>
      <Link to="/">
        <button className="btn-primary">← Back to Home</button>
      </Link>
    </div>
  );
}
