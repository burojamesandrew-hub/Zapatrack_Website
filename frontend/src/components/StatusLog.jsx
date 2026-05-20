import React, { useMemo } from 'react';
import './StatusLog.css';

export default function StatusLog({ logs = [] }) {
  // Deduplicate logs: group by status transition and keep only entries with notes, or the first one if no notes
  const deduplicatedLogs = useMemo(() => {
    if (!logs || logs.length === 0) return [];

    // Group by status transition
    const grouped = {};
    logs.forEach((log, index) => {
      const key = `${log.old_status || 'initial'}_to_${log.new_status}`;
      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key].push(log);
    });

    // For each group, merge all notes so encoder feedback is preserved on every status change
    const deduped = Object.values(grouped).map(group => {
      if (group.length === 1) return group[0];
      // Use first entry as base
      const base = group[0];
      // Collect all unique notes from all entries in the group
      const notesList = Array.from(
        new Set(
          group
            .map(l => (l.notes || '').trim())
            .filter(s => s)
        )
      );
      // Merge notes if any exist
      if (notesList.length > 0) {
        base.notes = notesList.join('\n\n');
      }
      return base;
    });

    return deduped;
  }, [logs]);

  if (!deduplicatedLogs || deduplicatedLogs.length === 0) {
    return (
      <div className="card status-log-card">
        <div className="section-label">Status History</div>
        <div className="no-logs">
          <p>No status changes recorded yet.</p>
        </div>
      </div>
    );
  }

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status) => {
    if (!status) return 'neutral';
    const statusMap = {
      'submitted': 'info',
      'pending': 'warning',
      'processing': 'warning',
      'approved': 'success',
      'ready for pickup': 'success',
      'completed': 'success',
      'rejected': 'error',
      'cancelled': 'error'
    };
    return statusMap[status?.toLowerCase()] || 'neutral';
  };

  return (
    <div className="card status-log-card">
      <div className="section-label">Status History</div>
      <div className="status-log-timeline">
        {deduplicatedLogs.map((log, index) => (
          <div key={index} className="status-log-entry">
            <div className="timeline-marker"></div>
            <div className="log-content">
              <div className="log-header">
                {log.old_status ? (
                  <div className="status-transition">
                    <span className={`status-badge status-${getStatusColor(log.old_status)}`}>
                      {log.old_status}
                    </span>
                    <span className="arrow">→</span>
                    <span className={`status-badge status-${getStatusColor(log.new_status)}`}>
                      {log.new_status}
                    </span>
                  </div>
                ) : (
                  <div className="status-creation">
                    <span className="label">Request Created</span>
                    <span className={`status-badge status-${getStatusColor(log.new_status)}`}>
                      {log.new_status}
                    </span>
                  </div>
                )}
              </div>
              <div className="log-meta">
                <span className="changed-by">by {log.changed_by}</span>
                <span className="changed-at">{formatDate(log.changed_at)}</span>
              </div>
              {log.notes && log.notes.trim() && (
                <div className="log-notes">
                  <span className="notes-label">Notes:</span>
                  <p>{log.notes}</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
