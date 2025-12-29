export default function Summary() {
  return (
    <div className="main-content">
      <div className="section-header">
        <h2 className="section-title">📊 Summary</h2>
        <p className="section-subtitle">Statistics and insights coming soon</p>
      </div>

      <div style={{ 
        textAlign: 'center', 
        padding: '4rem 2rem',
        color: 'var(--text-secondary)'
      }}>
        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🚧</div>
        <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
          Coming Soon
        </h3>
        <p>
          This page will show statistics about your property reviews,<br />
          price trends, and other insights.
        </p>
      </div>
    </div>
  );
}