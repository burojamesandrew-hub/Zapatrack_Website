import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import jsQR from 'jsqr';
import { api } from '../api';
import './Home.css';

export default function Home() {
  const [input, setInput]     = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState('');
  const [scanStatus, setScanStatus] = useState('');
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const scanIntervalRef = useRef(null);
  const navigate = useNavigate();

  async function handleTrack(e) {
    e.preventDefault();
    const id = input.trim();
    if (!id) {
      setError('Please enter a Request ID.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await api.getRequest(id);
      navigate(`/track/${id}`);
    } catch (err) {
      const msg = err.message || 'Request not found. Please check your Request ID.';
      setError(msg);
      console.error('[Track Error]', msg);
    } finally {
      setLoading(false);
    }
  }

  async function startScan() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setScanError('Camera access is not supported by this browser.');
      return;
    }
    setScanError('');
    setScanStatus('Requesting camera access...');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) throw new Error('Video element not found');
      video.srcObject = stream;
      await video.play();
      setScanning(true);
      setScanStatus('Scanning for QR code...');
      scanIntervalRef.current = window.setInterval(scanFrame, 250);
    } catch (err) {
      setScanError(err?.message || 'Unable to access camera.');
      setScanning(false);
      stopScan();
    }
  }

  function stopScan() {
    setScanning(false);
    setScanStatus('');
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    const stream = streamRef.current;
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }

  function scanFrame() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState !== video.HAVE_ENOUGH_DATA) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height);
    if (code?.data) {
      setScanStatus(`QR detected: ${code.data}`);
      stopScan();
      navigate(`/track/${encodeURIComponent(code.data)}`);
    }
  }

  function handleFileUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setScanError('');
    setScanStatus('Reading QR image...');
    const reader = new FileReader();
    reader.onload = () => {
      const image = new Image();
      image.onload = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        canvas.width = image.width;
        canvas.height = image.height;
        ctx.drawImage(image, 0, 0);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, imageData.width, imageData.height);
        if (!code?.data) {
          setScanError('No QR code found in uploaded image.');
          setScanStatus('');
          return;
        }
        setScanStatus(`QR detected: ${code.data}`);
        navigate(`/track/${encodeURIComponent(code.data)}`);
      };
      image.onerror = () => {
        setScanError('Unable to read the selected image.');
        setScanStatus('');
      };
      image.src = reader.result;
    };
    reader.readAsDataURL(file);
    event.target.value = '';
  }

  return (
    <div className="home">
      {/* Hero */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-badge">Barangay Zapatera · Cebu City</div>
          <h1>Track Your Certificate Request</h1>
          <p>Enter your Request ID to check the status of your barangay certificate request.</p>

          <div className="hero-panel">
            <form className="track-form" onSubmit={handleTrack}>
              <input
                className="track-input"
                type="text"
                placeholder="Enter your Request ID (UUID)…"
                value={input}
                onChange={e => { setInput(e.target.value); setError(''); }}
                autoFocus
              />
              <button className="btn-primary track-btn" type="submit" disabled={loading || !input.trim()}>
                {loading ? 'Searching…' : 'Track Request'}
              </button>
            </form>

            <div className="qr-home-panel">
            <div className="qr-actions">
              <button className="btn-secondary" type="button" onClick={startScan} disabled={scanning}>
                {scanning ? 'Scanning…' : 'Scan QR Code'}
              </button>
              <label className="btn-secondary btn-upload">
                Upload QR Image
                <input type="file" accept="image/*" onChange={handleFileUpload} hidden />
              </label>
            </div>
            {(scanError || scanStatus) && (
              <div className="scan-status">
                {scanError ? <span className="scan-error">{scanError}</span> : <span>{scanStatus}</span>}
              </div>
            )}
            <div className="scan-preview" style={{ display: scanning ? 'flex' : 'none' }}>
              <video ref={videoRef} muted playsInline />
              <button className="btn-secondary btn-cancel" type="button" onClick={stopScan}>
                Cancel Scan
              </button>
            </div>
            <canvas ref={canvasRef} hidden />
          </div>
          </div>

          {error && <div className="error-box" style={{ marginTop: 12 }}>{error}</div>}

          <p className="hero-hint">
            You received your Request ID when staff encoded your request at the barangay hall.
          </p>
        </div>
      </section>

      <section className="how-section">
        <div className="how-inner">
          <h2>Track what matters to you</h2>
          <div className="steps-grid">
            {[
              { n: '1', title: 'Get your Request ID', desc: 'Ask the barangay staff for your encoded request details and QR code.' },
              { n: '2', title: 'Scan or enter your code', desc: 'Use the QR scanner or enter your Request ID directly to view status.' },
              { n: '3', title: 'Check status instantly', desc: 'See if your certificate is pending, ready for pickup, or claimed.' },
              { n: '4', title: 'Claim when ready', desc: 'Bring your QR or Request ID to collect your certificate.' },
            ].map(s => (
              <div key={s.n} className="step-card card">
                <div className="step-num">{s.n}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <p>Barangay Zapatera · Cebu City, Philippines</p>
        <p>Office hours: Mon–Fri, 8:00 AM – 5:00 PM</p>
      </footer>
    </div>
  );
}
