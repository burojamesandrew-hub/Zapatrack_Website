export default function StatusBadge({ status }) {
  const key = status?.replace(/\s+/g, '-') || '';
  const styles = {
    'Pending':          { bg: '#FEF3C7', color: '#92400E' },
    'Approved':         { bg: '#D1FAE5', color: '#065F46' },
    'Ready-for-Pickup': { bg: '#DBEAFE', color: '#1E3A8A' },
    'Claimed':          { bg: '#EDE9FE', color: '#4C1D95' },
    'Rejected':         { bg: '#FEE2E2', color: '#991B1B' },
    'Cancelled':        { bg: '#F1F5F9', color: '#64748B' },
  };
  const s = styles[key] || { bg: '#F1F5F9', color: '#334155' };
  return (
    <span style={{
      background: s.bg, color: s.color,
      borderRadius: 20, padding: '3px 10px',
      fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap',
    }}>
      {status}
    </span>
  );
}
