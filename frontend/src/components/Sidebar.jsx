import Icon from './Icon.jsx'

const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: 'grid' },
  { id: 'agents', label: 'Agents', icon: 'users' },
]

export default function Sidebar({ view, onNavigate, stats }) {
  const openCount = stats ? stats.by_status.open + stats.by_status.in_progress : null
  return (
    <nav className="sidebar" aria-label="Main navigation">
      <div className="brand">
        <div className="brand-mark">D</div>
        <div>
          <div className="brand-name">DeskFlow</div>
          <div className="brand-sub">Support workspace</div>
        </div>
      </div>

      <div className="nav-section">Workspace</div>
      {NAV.map((item) => (
        <button
          key={item.id}
          className={`nav-item ${view === item.id ? 'active' : ''}`}
          onClick={() => onNavigate(item.id)}
        >
          <Icon name={item.icon} />
          <span>{item.label}</span>
          {item.id === 'dashboard' && openCount !== null && <span className="nav-count">{openCount}</span>}
        </button>
      ))}

      <div className="sidebar-footer">
        <div className="avatar avatar-lg">VD</div>
        <div>
          <div className="author">Vansh Dobhal</div>
          <div className="author-sub">Roll No. 10099</div>
        </div>
      </div>
    </nav>
  )
}
