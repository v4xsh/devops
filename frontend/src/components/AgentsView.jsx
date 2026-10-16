import { useState } from 'react'
import { initials } from '../api.js'

export default function AgentsView({ agents, tickets, loading, onCreate }) {
  const [form, setForm] = useState({ name: '', email: '', team: 'Tier 1' })
  const [saving, setSaving] = useState(false)

  const load = (id) => tickets.filter((t) => t.assignee_id === id && ['open', 'in_progress'].includes(t.status)).length

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await onCreate(form)
      setForm({ name: '', email: '', team: 'Tier 1' })
    } catch {
      /* toast already shown */
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="grid agents-grid">
      <section className="card">
        <div className="card-head">
          <h2>Team</h2>
          <span className="muted">{agents.length} agents</span>
        </div>
        {loading && agents.length === 0 ? (
          [0, 1, 2].map((i) => <div key={i} className="skeleton row" />)
        ) : (
          <ul className="agent-list">
            {agents.map((a) => (
              <li key={a.id}>
                <span className="avatar">{initials(a.name)}</span>
                <div className="agent-info">
                  <div className="agent-name">{a.name}</div>
                  <div className="muted">{a.email}</div>
                </div>
                <span className="badge team">{a.team}</span>
                <span className="agent-load" title="Active tickets">
                  {load(a.id)} active
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <form className="card agent-form" onSubmit={submit}>
        <h2>Add agent</h2>
        <label className="field">
          <span>Name</span>
          <input required minLength={2} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </label>
        <label className="field">
          <span>Email</span>
          <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </label>
        <label className="field">
          <span>Team</span>
          <input required minLength={2} value={form.team} onChange={(e) => setForm({ ...form, team: e.target.value })} />
        </label>
        <button className="btn btn-primary" disabled={saving}>
          {saving ? 'Adding…' : 'Add agent'}
        </button>
      </form>
    </div>
  )
}
