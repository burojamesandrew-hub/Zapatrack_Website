import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import jsQR from 'jsqr';
import { QRCodeCanvas } from 'qrcode.react';
import { api } from '../api';
import StatusBadge from '../components/StatusBadge';
import StatusTracker from '../components/StatusTracker';
import StatusLog from '../components/StatusLog';
import './TrackRequest.css';

export default function TrackRequest() {
  const { id }           = useParams();
  const navigate         = useNavigate();
  const [data, setData]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [searchId, setSearchId] = useState(id || '');
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState('');
  const [scanStatus, setScanStatus] = useState('');
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const scanIntervalRef = useRef(null);

  useEffect(() => {
    if (id) fetchRequest(id);
    return () => stopScan();
  }, [id]);

  async function fetchRequest(rid) {
    setLoading(true); setError(''); setData(null);
    try {
      const res = await api.getRequest(rid.trim());
      if (!res) {
        throw new Error('No request data received from server.');
      }
      setData(res);
    } catch (e) {
      const msg = e.message || 'Unable to retrieve request. Please check your Request ID or contact the barangay office.';
      setError(msg);
      console.error('[Fetch Request Error]', msg);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e) {
    e.preventDefault();
    const rid = searchId.trim();
    if (!rid) return;
    stopScan();
    navigate(`/track/${rid}`);
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
      setSearchId(code.data);
      fetchRequest(code.data);
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
        setSearchId(code.data);
        fetchRequest(code.data);
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
    <div className="track-page">
      <div className="track-inner">
        <div className="track-hero">
          <div>
            <div className="track-hero-label">Track Request</div>
            <h1>Use your Request ID or QR code to check status</h1>
            <p>Residents can scan a QR code or enter the request ID to view certificate progress.</p>
          </div>
        </div>

        {/* Search bar and QR input controls */}
        <div className="track-scan-panel">
          <form className="track-search-form" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Enter Request ID…"
              value={searchId}
              onChange={e => setSearchId(e.target.value)}
              style={{ fontFamily: 'Courier New, monospace' }}
            />
            <button className="btn-primary" type="submit">Search</button>
          </form>

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

        {loading && <div className="spinner" />}
        {error   && <div className="error-box">{error}</div>}

        {data && (
          <div className="track-content">

            {/* Status header card */}
            <div className="card status-header">
              <div className="status-header-top">
                <div>
                  <div className="section-label">Request ID</div>
                  <div className="req-id">{data.request_id_text}</div>
                </div>
                <StatusBadge status={data.status} />
              </div>
              <div className="status-header-meta">
                <span><b>Resident:</b> {data.resident_name}</span>
                <span><b>Certificate:</b> {data.cert_type}</span>
                <span><b>Date Filed:</b> {data.date_requested}</span>
              </div>
              <hr className="divider" />
              <StatusTracker status={data.status} />
            </div>

            <div className="track-cols">
              {/* Left — details */}
              <div className="track-left">

                {/* Request details */}
                <div className="card">
                  <div className="section-label">Request Details</div>
                  <table className="detail-table">
                    <tbody>
                      <DetailRow label="Certificate Type" value={data.cert_type} />
                      <DetailRow label="Purpose"          value={data.purpose || '—'} />
                      <DetailRow label="Date Requested"   value={data.date_requested} />
                      <DetailRow label="O.R. Number"      value={data.or_number || '—'} />
                      <DetailRow label="Encoded By"       value={data.encoded_by} />
                      <DetailRow label="Status"           value={<StatusBadge status={data.status} />} />
                    </tbody>
                  </table>
                </div>

                {/* Cert-type specific */}
                {data.detail && (
                  <div className="card">
                    <div className="section-label">{data.cert_type} — Specific Details</div>
                    <table className="detail-table">
                      <tbody>
                        <CertDetail cert={data.cert_type} detail={data.detail} />
                      </tbody>
                    </table>
                  </div>
                )}

              </div>

              {/* Right — status log and QR code */}
              <div className="track-right">
                <StatusLog logs={data.status_log || []} />

                {/* QR Code Display with UUID generation */}
                <div className="card qr-card">
                  <div className="section-label">QR Code</div>
                  <div className="qr-display-container">
                    <div className="qr-code-wrapper">
                      {data.request_id && (
                        <QRCodeCanvas
                          value={data.request_id}
                          size={200}
                          level="H"
                          includeMargin={true}
                        />
                      )}
                    </div>
                  </div>
                  <div className="qr-note">
                    Scan this QR code or show it at the counter to identify your request.
                  </div>
                  <div className="qr-uuid">
                    <small>Request UUID: <code>{data.request_id}</code></small>
                  </div>
                </div>

                {/* Instructions card */}
                <div className="card instructions-card">
                  <div className="section-label">Claiming Instructions</div>
                  <ol className="instructions-list">
                    <li>Bring a valid government-issued ID (PhilSys, Voter's ID, etc.)</li>
                    <li>Present your Request ID or QR code at the counter</li>
                    <li>Office hours: Mon–Fri, 8:00 AM – 5:00 PM</li>
                  </ol>
                  <div className="contact-info">
                    <b>Barangay Hall Address:</b><br />
                    Brgy. Zapatera, Cebu City
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function DetailRow({ label, value }) {
  return (
    <tr>
      <td className="detail-key">{label}</td>
      <td className="detail-val">{value}</td>
    </tr>
  );
}

function CertDetail({ cert, detail }) {
  if (!detail) return null;
  if (cert === 'Barangay Clearance') return <>
    <DetailRow label="Purpose"       value={detail.purpose || '—'} />
    <DetailRow label="ID Presented"  value={detail.id_type_presented || '—'} />
    <DetailRow label="ID Number"     value={detail.id_number || '—'} />
    <DetailRow label="With Cedula"   value={detail.with_community_tax ? 'Yes' : 'No'} />
    <DetailRow label="Fee"           value={detail.fee_amount ? `₱${detail.fee_amount}` : '—'} />
  </>;
  if (cert === 'Certificate of Indigency') return <>
    <DetailRow label="Reason"        value={detail.reason || '—'} />
    <DetailRow label="Monthly Income" value={detail.monthly_income || '—'} />
    <DetailRow label="Dependents"    value={detail.num_dependents ?? '—'} />
    <DetailRow label="For Medical"   value={detail.for_medical ? 'Yes' : 'No'} />
    <DetailRow label="For Scholarship" value={detail.for_scholarship ? 'Yes' : 'No'} />
    <DetailRow label="For Burial"    value={detail.for_burial ? 'Yes' : 'No'} />
    <DetailRow label="Beneficiary"   value={detail.beneficiary_name || 'Self'} />
    <DetailRow label="Institution"   value={detail.requesting_institution || '—'} />
  </>;
  if (cert === 'Certificate of Residency') return <>
    <DetailRow label="Purpose"       value={detail.purpose || '—'} />
    <DetailRow label="Years Here"    value={`${detail.years_of_residency ?? 0} yr(s), ${detail.months_of_residency ?? 0} mo(s)`} />
    <DetailRow label="Born Here"     value={detail.born_in_barangay ? 'Yes' : 'No'} />
    <DetailRow label="Requested For" value={detail.requested_for || 'Self'} />
    <DetailRow label="Institution"   value={detail.requesting_institution || '—'} />
  </>;
  if (['BUS. PERMIT', 'BUS. CLEARANCE NEW', 'BUS. CLEARANCE RENEWAL'].includes(cert)) return <>
    <DetailRow label="Purpose"          value={detail.purpose || '—'} />
    <DetailRow label="Business Name"    value={detail.business_name || '—'} />
    <DetailRow label="Nature of Biz"    value={detail.nature_of_business || '—'} />
    <DetailRow label="Contact Number"   value={detail.business_contact_number || '—'} />
    <DetailRow label="Capital Invested" value={detail.capital_invested || '—'} />
    <DetailRow label="Gross Sales"      value={detail.gross_sales || '—'} />
    <DetailRow label="Fee"              value={detail.fee_amount ? `₱${detail.fee_amount}` : '—'} />
    <DetailRow label="Doc Stamps"       value={detail.doc_stamps ? `₱${detail.doc_stamps}` : '—'} />
  </>;
  return null;
}
