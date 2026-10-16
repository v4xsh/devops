import { useEffect, useState } from 'react'
import { PRIORITIES, STATUSES } from '../api.js'
import Icon from './Icon.jsx'

const EMPTY = { title: '', customer: '', description: '', priority: 'medium', status: 'open', assignee_id: '' }

export default function CreateTicketModal({ agents, onClose, onSubmit }) {
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSubmit({ ...form, assignee_id: form.assignee_id ? Number(form.assignee_id) : null })
      onClose()
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form className="modal" onSubmit={submit} role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-head">
          <h2 id="modal-title">New support ticket</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            <Icon name="x" />
          </button>
        </div>

        <label className="field">
          <span>Title</span>
          <input required minLength={3} maxLength={200} value={form.title} onChange={set('title')} placeholder="Short summary of the issue" autoFocus />
        </label>
        <label className="field">
          <span>Customer</span>
          <input required minLength={2} maxLength={160} value={form.customer} onChange={set('customer')} placeholder="Company or contact name" />
        </label>
        <label className="field">
          <span>Description</span>
          <textarea rows={3} value={form.description} onChange={set('description')} placeholder="What happened, steps to reproduce, impact…" />
        </label>
        <div className="field-row">
          <label className="field">
            <span>Priority</span>
            <select value={form.priority} onChange={set('priority')}>
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p[0].toUpperCase() + p.slice(1)}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Status</span>
            <select value={form.status} onChange={set('status')}>
              {STATUSES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="field">
          <span>Assignee</span>
          <select value={form.assignee_id} onChange={set('assignee_id')}>
            <option value="">Unassigned</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} · {a.team}
              </option>
            ))}
          </select>
        </label>

        {error && <div className="form-error">{error}</div>}

        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Creating…' : 'Create ticket'}
          </button>
        </div>
      </form>
    </div>
  )
}
