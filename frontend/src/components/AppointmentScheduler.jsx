import { useState, useEffect } from 'react';
import { api } from '../api';
import './AppointmentScheduler.css';

export default function AppointmentScheduler({ requestId, status, onScheduled }) {
  const [appt, setAppt]       = useState(null);
  const [slots, setSlots]     = useState([]);
  const [date, setDate]       = useState('');
  const [slot, setSlot]       = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [success, setSuccess] = useState(false);

  const canSchedule = status === 'Ready for Pickup';

  useEffect(() => {
    // Load available timeslots
    api.getTimeslots()
      .then(r => setSlots(r.slots))
      .catch(err => {
        console.warn('Failed to load timeslots:', err.message);
        setSlots([
          '8:00 AM – 9:00 AM',
          '9:00 AM – 10:00 AM',
          '10:00 AM – 11:00 AM',
          '1:00 PM – 2:00 PM',
          '2:00 PM – 3:00 PM',
          '3:00 PM – 4:00 PM',
        ]);
      });
    
    // Load existing appointment
    if (requestId) {
      api.getAppointment(requestId)
        .then(r => {
          if (r?.appointment) setAppt(r.appointment);
        })
        .catch(err => {
          console.warn('Could not load appointment details:', err.message);
        });
    }
  }, [requestId]);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!date || !slot) { setError('Please select both a date and time slot.'); return; }
    setLoading(true); setError('');
    try {
      await api.createAppointment({
        request_id: requestId,
        pickup_date: date,
        pickup_time_slot: slot,
      });
      setSuccess(true);
      onScheduled && onScheduled();
      api.getAppointment(requestId).then(r => setAppt(r.appointment)).catch(() => {});
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Today's date string for min
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="card appt-card">
      <div className="section-label">Pickup Appointment</div>

      {/* Existing appointment */}
      {appt && (
        <div className="appt-existing">
          <div className="appt-existing-title">✓ Appointment Scheduled</div>
          <div className="appt-row"><span>Date</span><b>{appt.pickup_date}</b></div>
          <div className="appt-row"><span>Time</span><b>{appt.pickup_time_slot}</b></div>
          <div className="appt-row"><span>Status</span><b>{appt.pickup_status}</b></div>
        </div>
      )}

      {/* Schedule form */}
      {!appt && canSchedule && !success && (
        <form onSubmit={handleSubmit} className="appt-form">
          <p className="appt-info">
            Your certificate is ready! Schedule a pickup appointment below.
          </p>
          <div className="form-group">
            <label>Preferred Date</label>
            <input type="date" value={date} min={today}
              onChange={e => { setDate(e.target.value); setError(''); }} />
          </div>
          <div className="form-group">
            <label>Preferred Time Slot</label>
            <select value={slot} onChange={e => { setSlot(e.target.value); setError(''); }}>
              <option value="">— Select time slot —</option>
              {slots.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          {error && <div className="error-box" style={{ marginBottom: 10 }}>{error}</div>}
          <button className="btn-primary" type="submit" disabled={loading} style={{ width: '100%' }}>
            {loading ? 'Scheduling…' : 'Confirm Appointment'}
          </button>
        </form>
      )}

      {/* Not ready yet */}
      {!appt && !canSchedule && (
        <div className="appt-not-ready">
          <div className="appt-status-icon">🕐</div>
          <p>Appointment scheduling is available once your certificate status is <b>Ready for Pickup</b>.</p>
          <p>Current status: <b>{status}</b></p>
        </div>
      )}

      {/* Success */}
      {success && (
        <div className="appt-success">
          ✓ Appointment confirmed! See you at the barangay hall on <b>{date}</b> at <b>{slot}</b>.
        </div>
      )}
    </div>
  );
}
