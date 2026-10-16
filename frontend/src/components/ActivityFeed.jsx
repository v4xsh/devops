import { timeAgo } from '../api.js'
import Icon from './Icon.jsx'

export default function ActivityFeed({ items, loading }) {
  return (
    <section className="card feed">
      <div className="card-head">
        <h2>
          <Icon name="activity" size={16} /> Activity
        </h2>
      </div>
      {loading && items.length === 0 ? (
        [0, 1, 2].map((i) => <div key={i} className="skeleton row small" />)
      ) : items.length === 0 ? (
        <p className="muted">No activity yet.</p>
      ) : (
        <ol className="feed-list">
          {items.map((e) => (
            <li key={e.id} className={`feed-item action-${e.action}`}>
              <span className="feed-dot" />
              <div>
                <div className="feed-msg">{e.message}</div>
                <div className="feed-time">{timeAgo(e.created_at)}</div>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
