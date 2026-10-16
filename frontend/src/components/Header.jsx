import Icon from './Icon.jsx'

export default function Header({ title, search, onSearch, onNew, onMenu }) {
  const today = new Date().toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })
  return (
    <header className="header">
      <button className="icon-btn menu-btn" onClick={onMenu} aria-label="Toggle navigation">
        <Icon name="menu" />
      </button>
      <div className="header-title">
        <h1>{title}</h1>
        <p>{today}</p>
      </div>
      <div className="header-actions">
        <label className="search">
          <Icon name="search" size={16} />
          <input
            type="search"
            placeholder="Search title or customer"
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            aria-label="Search tickets"
          />
        </label>
        <button className="btn btn-primary" onClick={onNew}>
          <Icon name="plus" size={16} />
          <span>New ticket</span>
        </button>
      </div>
    </header>
  )
}
