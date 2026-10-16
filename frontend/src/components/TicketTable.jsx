import { STATUSES, initials, timeAgo } from '../api.js'
import Icon from './Icon.jsx'

export function StatusBadge({ status }) {
  const label = STATUSES.find((s) => s.value === status)?.label ?? status
  return <span className={`badge status-${status}`}>{label}</span>
}

export function PriorityBadge({ priority }) {
  return (
    <span className={`priority priority-${priority}`}>
      <span className="dot" />
      {priority}
    </span>
  )
}

export default function TicketTable({ tickets, agents, stats, loading, statusFilter, onFilter, onUpdate, onDelete }) {
  const filters = [{ value: '', label: 'All', count: stats?.total }].concat(
    STATUSES.map((s) => ({ ...s, count: stats?.by_status[s.value] })),
  )

  return (
    <section className="card table-card">
      <div className="card-head">
        <h2>Tickets</h2>
        <div className="filters" role="tablist" aria-label="Filter by status">
          {filters.map((f) => (
            <button
              key={f.value || 'all'}
              role="tab"
              aria-selected={statusFilter === f.value}
              className={`chip ${statusFilter === f.value ? 'active' : ''}`}
              onClick={() => onFilter(f.value)}
            >
              {f.label}
              {f.count !== undefined && <span className="chip-count">{f.count}</span>}
            </button>
          ))}
        </div>
      </div>

      {loading && tickets.length === 0 ? (
        <div className="table-skeleton">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton row" />
          ))}
        </div>
      ) : tickets.length === 0 ? (
        <div className="empty">
          <Icon name="inbox" size={28} />
          <p>No tickets match this view.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="tickets">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Assignee</th>
                <th>Updated</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {tickets.map((t) => (
                <tr key={t.id}>
                  <td data-label="Ticket">
                    <div className="t-title">
                      <span className="t-id">#{t.id}</span> {t.title}
                    </div>
                    <div className="t-customer">{t.customer}</div>
                  </td>
                  <td data-label="Status">
                    <select
                      className={`status-select status-${t.status}`}
                      value={t.status}
                      onChange={(e) => onUpdate(t.id, { status: e.target.value }).catch(() => {})}
                      aria-label={`Status of ticket ${t.id}`}
                    >
                      {STATUSES.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td data-label="Priority">
                    <PriorityBadge priority={t.priority} />
                  </td>
                  <td data-label="Assignee">
                    <div className="assignee-cell">
                    <span className={`avatar avatar-sm ${t.assignee_name ? '' : 'avatar-empty'}`}>
                      {t.assignee_name ? initials(t.assignee_name) : '–'}
                    </span>
                    <select
                      className="assignee-select"
                      value={t.assignee_id ?? ''}
                      onChange={(e) =>
                        onUpdate(t.id, { assignee_id: e.target.value ? Number(e.target.value) : null }).catch(() => {})
                      }
                      aria-label={`Assignee of ticket ${t.id}`}
                    >
                      <option value="">Unassigned</option>
                      {agents.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.name}
                        </option>
                      ))}
                    </select>
                    </div>
                  </td>
                  <td data-label="Updated" className="muted nowrap">
                    {timeAgo(t.updated_at)}
                  </td>
                  <td className="actions">
                    <button
                      className="icon-btn danger"
                      onClick={() => {
                        if (window.confirm(`Delete ticket #${t.id}?`)) onDelete(t.id).catch(() => {})
                      }}
                      aria-label={`Delete ticket ${t.id}`}
                    >
                      <Icon name="trash" size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
