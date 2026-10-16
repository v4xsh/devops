// All calls are relative: Nginx (compose) or the Ingress (Kubernetes)
// routes /api to the backend, so the browser never needs its hostname.
async function request(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body.detail) {
        detail = Array.isArray(body.detail)
          ? body.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join(', ')
          : body.detail
      }
    } catch {
      /* response had no JSON body */
    }
    throw new Error(detail)
  }
  return res.status === 204 ? null : res.json()
}

export const api = {
  tickets: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString()
    return request(`/api/tickets${qs ? `?${qs}` : ''}`)
  },
  stats: () => request('/api/tickets/stats'),
  activity: () => request('/api/activity?limit=12'),
  agents: () => request('/api/agents'),
  createTicket: (data) => request('/api/tickets', { method: 'POST', body: JSON.stringify(data) }),
  updateTicket: (id, data) => request(`/api/tickets/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteTicket: (id) => request(`/api/tickets/${id}`, { method: 'DELETE' }),
  createAgent: (data) => request('/api/agents', { method: 'POST', body: JSON.stringify(data) }),
}

export const STATUSES = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
]

export const PRIORITIES = ['low', 'medium', 'high', 'urgent']

export function timeAgo(iso) {
  const then = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
  const s = Math.max(0, Math.round((Date.now() - then.getTime()) / 1000))
  if (s < 60) return 'just now'
  const m = Math.round(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.round(h / 24)}d ago`
}

export function initials(name = '') {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join('')
}
