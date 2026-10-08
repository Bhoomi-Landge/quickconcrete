import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function DashboardLayout({ title, subtitle, children, navLinks = [], headerActions }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">QC</span>
          <div>
            <strong>QuickConcrete</strong>
            <p className="brand-tag">RMC delivery</p>
          </div>
        </div>
        <nav className="sidebar-nav">
          <span className="nav-label">Workspace</span>
          {navLinks.length > 0 ? (
            navLinks.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                {item.label}
              </NavLink>
            ))
          ) : (
            <span className="nav-link active">Dashboard</span>
          )}
        </nav>
        <div className="sidebar-footer">
          <p className="user-name">{user?.name}</p>
          <p className="user-role">{user?.role}</p>
          <button type="button" className="btn btn-ghost btn-block" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </aside>
      <main className="main-content">
        <header className="page-header page-header-row">
          <div>
            <h1>{title}</h1>
            {subtitle && <p className="subtitle">{subtitle}</p>}
          </div>
          {headerActions && <div className="header-actions">{headerActions}</div>}
        </header>
        {children}
      </main>
    </div>
  )
}
