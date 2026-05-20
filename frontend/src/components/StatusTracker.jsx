import './StatusTracker.css';

const STEPS = ['Pending', 'Approved', 'Ready for Pickup', 'Claimed'];

export default function StatusTracker({ status }) {
  if (!STEPS.includes(status)) {
    return (
      <div className="tracker tracker-special">
        <div className="tracker-special-text">
          Current status: <strong>{status}</strong>
        </div>
      </div>
    );
  }

  const idx = STEPS.indexOf(status);
  return (
    <div className="tracker">
      {STEPS.map((step, i) => {
        const done    = i < idx;
        const current = i === idx;
        return (
          <div key={step} className="tracker-step">
            <div className={`tracker-dot ${done ? 'done' : current ? 'current' : 'future'}`}>
              {done ? '✓' : i + 1}
            </div>
            <div className={`tracker-label ${current ? 'tracker-label-active' : ''}`}>{step}</div>
            {i < STEPS.length - 1 && (
              <div className={`tracker-line ${done ? 'tracker-line-done' : ''}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
