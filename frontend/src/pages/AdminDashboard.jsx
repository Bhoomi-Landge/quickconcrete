import { useEffect, useState } from 'react'

import { DashboardLayout } from '../components/DashboardLayout'
import { adminApi } from '../services/api'

export function AdminDashboard() {
  const [overview, setOverview] = useState(null)
  const [recentUsers, setRecentUsers] = useState([])
  const [dbHint, setDbHint] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    adminApi
      .overview()
      .then((data) => {
        setOverview(data.overview)
        setRecentUsers(data.recent_users || [])
        setDbHint(data.database_uri || '')
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const stat = (value) => (loading ? '…' : value ?? '0')

  return (
    <DashboardLayout
      title="Admin dashboard"
      subtitle="Live production data from the hosted database."
    >
      {error && <div className="alert alert-error">{error}</div>}

      <div className="stats-row">
        <div className="stat-card">
          <p className="eyebrow">Contractors</p>
          <p className="stat-value">{stat(overview?.contractors)}</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Suppliers</p>
          <p className="stat-value">{stat(overview?.suppliers)}</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Orders</p>
          <p className="stat-value">{stat(overview?.orders)}</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Active deliveries</p>
          <p className="stat-value">{stat(overview?.active_deliveries)}</p>
        </div>
      </div>

      <section className="card">
        <h3>Registered users (live DB)</h3>
        {loading ? (
          <p className="muted">Loading…</p>
        ) : recentUsers.length === 0 ? (
          <p className="muted empty-state">
            No users in this database yet. Registrations on{' '}
            <strong>quickconcrete.onrender.com</strong> appear here.
          </p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Joined</th>
                </tr>
              </thead>
              <tbody>
                {recentUsers.map((u) => (
                  <tr key={u.id}>
                    <td>{u.name}</td>
                    <td>{u.email}</td>
                    <td>{u.role}</td>
                    <td>{u.created_at ? new Date(u.created_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {dbHint && (
          <p className="muted table-sub" style={{ marginTop: '1rem', fontSize: '0.8rem' }}>
            DB: {dbHint.includes('sqlite') ? 'SQLite on server' : 'Hosted database'} — free Render
            resets this on redeploy unless you add a persistent disk or Postgres.
          </p>
        )}
      </section>
    </DashboardLayout>
  )
}
