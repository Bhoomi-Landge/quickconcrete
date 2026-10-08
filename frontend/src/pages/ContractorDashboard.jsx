import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ContractorLayout } from '../components/ContractorLayout'
import { useAuth } from '../context/AuthContext'
import { ordersApi, sitesApi } from '../services/api'

const ACTIVE_STATUSES = ['PLACED', 'ACCEPTED', 'PREPARING', 'DISPATCHED', 'OUT_FOR_DELIVERY']

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function ContractorDashboard() {
  const { user } = useAuth()
  const [sites, setSites] = useState([])
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    Promise.all([sitesApi.list(), ordersApi.list()])
      .then(([sitesRes, ordersRes]) => {
        if (!cancelled) {
          setSites(sitesRes.sites || [])
          setOrders(ordersRes.orders || [])
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

  const greeting = user?.name?.split(' ')[0] || 'there'
  const activeOrders = orders.filter((o) => ACTIVE_STATUSES.includes(o.status))
  const recentOrders = orders.slice(0, 5)

  return (
    <ContractorLayout
      title={`Good morning, ${greeting}`}
      subtitle="Manage sites and order ready-mix concrete."
      actions={
        <Link to="/contractor/orders/new" className="btn btn-primary">
          + Order Concrete
        </Link>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card-grid">
        <section className="card card-highlight">
          <p className="eyebrow">Primary action</p>
          <h2>Order concrete</h2>
          <p className="muted">Choose grade, quantity, and delivery slot from your saved sites.</p>
          <Link to="/contractor/orders/new" className="btn btn-primary">
            + Order Concrete
          </Link>
        </section>

        <section className="card">
          <h3>Active orders</h3>
          {loading ? (
            <p className="muted empty-state">Loading…</p>
          ) : activeOrders.length === 0 ? (
            <p className="muted empty-state">No active orders yet.</p>
          ) : (
            <ul className="mini-list">
              {activeOrders.slice(0, 3).map((order) => (
                <li key={order.id}>
                  <Link to={`/contractor/orders/${order.id}`} className="mini-list-link">
                    <strong>
                      {order.order_number} · {order.concrete_grade} · {order.quantity_m3} m³
                    </strong>
                    <span className="muted">
                      Site: {order.site_name} · {order.status.replace(/_/g, ' ')}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <div className="card-title-row">
            <h3>Recent orders</h3>
          </div>
          {loading ? (
            <p className="muted empty-state">Loading…</p>
          ) : recentOrders.length === 0 ? (
            <p className="muted empty-state">No orders placed yet.</p>
          ) : (
            <ul className="mini-list">
              {recentOrders.map((order) => (
                <li key={order.id}>
                  <Link to={`/contractor/orders/${order.id}`} className="mini-list-link">
                    <strong>{order.order_number}</strong>
                    <span className="muted">
                      {order.concrete_grade} · {formatCurrency(order.total_amount)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <div className="card-title-row">
            <h3>Construction sites</h3>
            <Link to="/contractor/sites" className="link">
              View all
            </Link>
          </div>
          {loading ? (
            <p className="muted empty-state">Loading sites…</p>
          ) : sites.length === 0 ? (
            <p className="muted empty-state">
              No sites saved.{' '}
              <Link to="/contractor/sites/new" className="link">
                Add your first site
              </Link>
            </p>
          ) : (
            <ul className="mini-list">
              {sites.slice(0, 3).map((site) => (
                <li key={site.id}>
                  <Link to={`/contractor/sites/${site.id}`} className="mini-list-link">
                    <strong>{site.site_name}</strong>
                    <span className="muted">
                      {site.city} · {site.pincode}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </ContractorLayout>
  )
}
