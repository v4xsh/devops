import { useEffect, useState } from 'react'

const STAGES = ['Test', 'Build', 'Scan', 'Push', 'Deploy']
const VERSION = import.meta.env.VITE_APP_VERSION || 'local'

export default function PipelineIndicator() {
  const [ready, setReady] = useState(null)

  useEffect(() => {
    let cancelled = false
    const check = () =>
      fetch('/ready')
        .then((r) => !cancelled && setReady(r.ok))
        .catch(() => !cancelled && setReady(false))
    check()
    const id = setInterval(check, 10000)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [])

  return (
    <section className="card pipeline">
      <div className="card-head">
        <h2>Delivery pipeline</h2>
        <span className={`pill ${ready === null ? '' : ready ? 'pill-ok' : 'pill-bad'}`}>
          {ready === null ? 'checking' : ready ? 'API ready' : 'API down'}
        </span>
      </div>
      <ol className="stages">
        {STAGES.map((s) => (
          <li key={s} className="stage done">
            <span className="stage-dot" />
            <span>{s}</span>
          </li>
        ))}
      </ol>
      <div className="build-meta">
        build <code>{VERSION.slice(0, 7)}</code>
      </div>
    </section>
  )
}
