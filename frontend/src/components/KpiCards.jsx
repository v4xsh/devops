import Icon from './Icon.jsx'

export default function KpiCards({ stats, loading }) {
  const cards = stats
    ? [
        { label: 'Open tickets', value: stats.by_status.open, hint: `${stats.total} total`, icon: 'inbox', tone: 'indigo' },
        { label: 'In progress', value: stats.by_status.in_progress, hint: `${stats.unassigned} unassigned`, icon: 'clock', tone: 'amber' },
        { label: 'Urgent & active', value: stats.open_urgent, hint: 'needs attention now', icon: 'alert', tone: 'rose' },
        { label: 'Resolution rate', value: `${stats.resolution_rate}%`, hint: `${stats.by_status.resolved + stats.by_status.closed} resolved or closed`, icon: 'check', tone: 'emerald' },
      ]
    : []

  if (loading && !stats) {
    return (
      <section className="kpis">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="card kpi skeleton-card">
            <div className="skeleton w-40" />
            <div className="skeleton w-20 tall" />
            <div className="skeleton w-60" />
          </div>
        ))}
      </section>
    )
  }

  return (
    <section className="kpis">
      {cards.map((c) => (
        <div key={c.label} className={`card kpi tone-${c.tone}`}>
          <div className="kpi-top">
            <span className="kpi-label">{c.label}</span>
            <span className="kpi-icon">
              <Icon name={c.icon} size={16} />
            </span>
          </div>
          <div className="kpi-value">{c.value}</div>
          <div className="kpi-hint">{c.hint}</div>
        </div>
      ))}
    </section>
  )
}
