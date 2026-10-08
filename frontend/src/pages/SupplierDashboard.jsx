import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { SupplierLayout } from '../components/SupplierLayout'
import { supplierApi } from '../services/api'
import { formatInr, formatStatus } from '../utils/orderHelpers'

export function SupplierDashboard() {
  const [summary, setSummary] = useState(null)
  const [incoming, setIncoming] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    Promise.all([supplierApi.summary(), supplierApi.listOrders('incoming')])
      .then(([summaryRes, ordersRes]) => {
        if (!cancelled) {
          setSummary(summaryRes.summary)
          setIncoming(ordersRes.orders || [])
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <SupplierLayout
      title="Supplier dashboard"
      subtitle="Review incoming RMC orders and track deliveries."
    >
      {error && <div className="alert alert-error">{error}</div>}

      <div className="stats-row">
        <div className="stat-card">
          <p className="eyebrow">Incoming</p>
          <p className="stat-value">{loading ? '—' : summary?.incoming_count ?? 0}</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Active</p>
          <p className="stat-value">{loading ? '—' : summary?.active_count ?? 0}</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Completed</p>
          <p className="stat-value">{loading ? '—' : summary?.completed_count ?? 0}</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Revenue (delivered)</p>
          <p className="stat-value">{loading ? '—' : formatInr(summary?.total_revenue ?? 0)}</p>
          <p className="muted">Pending pipeline: {formatInr(summary?.pending_value ?? 0)}</p>
        </div>
      </div>

      <div className="card-grid">
        <section className="card">
          <div className="card-title-row">
            <h3>Incoming orders (PLACED)</h3>
            <Link to="/supplier/orders?view=incoming" className="link">
              View all
            </Link>
          </div>
          {loading ? (
            <p className="muted empty-state">Loading…</p>
          ) : incoming.length === 0 ? (
            <p className="muted empty-state">No new orders to review.</p>
          ) : (
            <ul className="mini-list">
              {incoming.slice(0, 5).map((order) => (
                <li key={order.id}>
                  <Link to={`/supplier/orders/${order.id}`} className="mini-list-link">
                    <strong>
                      {order.order_number} · {order.concrete_grade} · {order.quantity_m3} m³
                    </strong>
                    <span className="muted">
                      {order.site_name} · {formatStatus(order.status)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h3>Quick links</h3>
          <div className="link-stack">
            <Link to="/supplier/orders?view=active" className="btn btn-secondary btn-block">
              Active deliveries
            </Link>
            <Link to="/supplier/orders?view=completed" className="btn btn-secondary btn-block">
              Completed orders
            </Link>
          </div>
        </section>
      </div>
    </SupplierLayout>
  )
}
