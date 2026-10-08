import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'

import { ContractorLayout } from '../components/ContractorLayout'
import { ordersApi } from '../services/api'

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function ContractorOrderConfirmationPage() {
  const { id } = useParams()
  const location = useLocation()
  const [order, setOrder] = useState(location.state?.order || null)
  const [loading, setLoading] = useState(!location.state?.order)
  const [error, setError] = useState('')

  useEffect(() => {
    if (location.state?.order) return undefined
    let cancelled = false
    ordersApi
      .get(id)
      .then((data) => {
        if (!cancelled) setOrder(data.order)
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
  }, [id, location.state?.order])

  return (
    <ContractorLayout
      title="Order confirmed"
      subtitle="Your RMC request has been placed with the supplier."
      actions={
        <Link to="/contractor/orders/new" className="btn btn-secondary">
          New order
        </Link>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <p className="muted">Loading confirmation…</p>
      ) : !order ? (
        <p className="muted">Order not found.</p>
      ) : (
        <section className="card confirmation-card">
          <div className="confirmation-header">
            <span className="status-badge status-placed">{order.status.replace(/_/g, ' ')}</span>
            <h2>{order.order_number}</h2>
            <p className="muted">Placed successfully — supplier will review your request.</p>
          </div>

          <dl className="detail-list">
            <div>
              <dt>Site</dt>
              <dd>
                {order.site_name}
                <span className="muted block-text">
                  {order.site_address}
                  {(order.site_city || order.site_pincode) && (
                    <>
                      <br />
                      {[order.site_city, order.site_pincode].filter(Boolean).join(' · ')}
                    </>
                  )}
                </span>
              </dd>
            </div>
            <div>
              <dt>Concrete</dt>
              <dd>
                {order.concrete_grade} · {order.quantity_m3} m³
              </dd>
            </div>
            <div>
              <dt>Delivery</dt>
              <dd>
                {formatDate(order.delivery_date)} at {order.delivery_time}
              </dd>
            </div>
            <div>
              <dt>Supplier</dt>
              <dd>{order.supplier_name}</dd>
            </div>
            <div>
              <dt>Estimated total</dt>
              <dd className="summary-total inline-total">{formatCurrency(order.total_amount)}</dd>
            </div>
            {order.special_instructions && (
              <div>
                <dt>Instructions</dt>
                <dd>{order.special_instructions}</dd>
              </div>
            )}
          </dl>

          <div className="confirmation-actions">
            <Link to="/contractor" className="btn btn-primary">
              Back to dashboard
            </Link>
            <Link to={`/contractor/orders/${order.id}`} className="btn btn-secondary">
              View order details
            </Link>
          </div>
        </section>
      )}
    </ContractorLayout>
  )
}
