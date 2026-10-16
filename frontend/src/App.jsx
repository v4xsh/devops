import { useCallback, useEffect, useState } from 'react'
import { api } from './api.js'
import Sidebar from './components/Sidebar.jsx'
import Header from './components/Header.jsx'
import KpiCards from './components/KpiCards.jsx'
import TicketTable from './components/TicketTable.jsx'
import ActivityFeed from './components/ActivityFeed.jsx'
import PipelineIndicator from './components/PipelineIndicator.jsx'
import CreateTicketModal from './components/CreateTicketModal.jsx'
import AgentsView from './components/AgentsView.jsx'

export default function App() {
  const [view, setView] = useState('dashboard')
  const [tickets, setTickets] = useState([])
  const [stats, setStats] = useState(null)
  const [activity, setActivity] = useState([])
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [navOpen, setNavOpen] = useState(false)
  const [toast, setToast] = useState(null)

  const load = useCallback(async () => {
    try {
      const [t, s, a, ag] = await Promise.all([
        api.tickets({ status: statusFilter, q: search }),
        api.stats(),
        api.activity(),
        api.agents(),
      ])
      setTickets(t)
      setStats(s)
      setActivity(a)
      setAgents(ag)
      setError(null)
    } catch (err) {
      setError(err.message || 'Backend unreachable')
    } finally {
      setLoading(false)
    }
  }, [statusFilter, search])

  useEffect(() => {
    const id = setTimeout(load, search ? 250 : 0)
    return () => clearTimeout(id)
  }, [load, search])

  useEffect(() => {
    const id = setInterval(load, 15000)
    return () => clearInterval(id)
  }, [load])

  const notify = (message, kind = 'ok') => {
    setToast({ message, kind })
    setTimeout(() => setToast(null), 3000)
  }

  const run = async (fn, okMessage) => {
    try {
      await fn()
      notify(okMessage)
      await load()
    } catch (err) {
      notify(err.message, 'error')
      throw err
    }
  }

  const handleCreate = (data) => run(() => api.createTicket(data), 'Ticket created')
  const handleUpdate = (id, data) => run(() => api.updateTicket(id, data), `Ticket #${id} updated`)
  const handleDelete = (id) => run(() => api.deleteTicket(id), `Ticket #${id} deleted`)
  const handleCreateAgent = (data) => run(() => api.createAgent(data), 'Agent added')

  return (
    <div className={`shell ${navOpen ? 'nav-open' : ''}`}>
      <Sidebar
        view={view}
        onNavigate={(v) => {
          setView(v)
          setNavOpen(false)
        }}
        stats={stats}
      />
      <div className="scrim" onClick={() => setNavOpen(false)} />
      <main className="main">
        <Header
          title={view === 'agents' ? 'Agents' : 'Support overview'}
          search={search}
          onSearch={setSearch}
          onNew={() => setModalOpen(true)}
          onMenu={() => setNavOpen((o) => !o)}
        />

        {error && (
          <div className="banner banner-error" role="alert">
            <div>
              <strong>Backend unavailable.</strong> {error}. Check that the API is running and that{' '}
              <code>/api</code> is routed to it.
            </div>
            <button className="btn btn-ghost" onClick={load}>
              Retry
            </button>
          </div>
        )}

        {view === 'dashboard' ? (
          <>
            <KpiCards stats={stats} loading={loading} />
            <div className="grid">
              <TicketTable
                tickets={tickets}
                agents={agents}
                stats={stats}
                loading={loading}
                statusFilter={statusFilter}
                onFilter={setStatusFilter}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
              />
              <aside className="side-col">
                <PipelineIndicator />
                <ActivityFeed items={activity} loading={loading} />
              </aside>
            </div>
          </>
        ) : (
          <AgentsView agents={agents} tickets={tickets} loading={loading} onCreate={handleCreateAgent} />
        )}
      </main>

      {modalOpen && (
        <CreateTicketModal agents={agents} onClose={() => setModalOpen(false)} onSubmit={handleCreate} />
      )}
      {toast && <div className={`toast toast-${toast.kind}`}>{toast.message}</div>}
    </div>
  )
}
