import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

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
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function ContractorOrderDetailPage() {
  const { id } = useParams()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
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
  }, [id])

  return (
    <ContractorLayout title={order?.order_number || 'Order details'} subtitle="Order summary and delivery info.">
      <p className="breadcrumb">
        <Link to="/contractor" className="link">
          Dashboard
        </Link>
        <span className="muted"> / Order</span>
      </p>

      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <p className="muted">Loading order…</p>
      ) : !order ? (
        <p className="muted">Order not found.</p>
      ) : (
        <section className="card detail-card">
          <span className={`status-badge status-${order.status.toLowerCase()}`}>
            {order.status.replace(/_/g, ' ')}
          </span>
          <dl className="detail-list">
            <div>
              <dt>Site</dt>
              <dd>
                {order.site_name}
                {(order.site_address || order.site_city) && (
                  <span className="muted block-text">
                    {order.site_address}
                    {order.site_city && (
                      <>
                        <br />
                        {order.site_city}
                        {order.site_pincode ? ` · ${order.site_pincode}` : ''}
                      </>
                    )}
                  </span>
                )}
              </dd>
            </div>
            <div>
              <dt>Grade & quantity</dt>
              <dd>
                {order.concrete_grade} · {order.quantity_m3} m³
              </dd>
            </div>
            <div>
              <dt>Delivery</dt>
              <dd>
                {formatDate(order.delivery_date)} · {order.delivery_time}
              </dd>
            </div>
            <div>
              <dt>Rate</dt>
              <dd>{formatCurrency(order.price_per_m3)}/m³</dd>
            </div>
            <div>
              <dt>Total</dt>
              <dd>{formatCurrency(order.total_amount)}</dd>
            </div>
            <div>
              <dt>Supplier</dt>
              <dd>{order.supplier_name}</dd>
            </div>
            {order.special_instructions && (
              <div>
                <dt>Instructions</dt>
                <dd>{order.special_instructions}</dd>
              </div>
            )}
          </dl>
        </section>
      )}
    </ContractorLayout>
  )
}
