import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { SupplierLayout } from '../components/SupplierLayout'
import { supplierApi } from '../services/api'
import { NEXT_STATUS_LABELS, formatInr, formatStatus, statusClass } from '../utils/orderHelpers'

export function SupplierOrderDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [acting, setActing] = useState(false)

  const loadOrder = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await supplierApi.getOrder(id)
      setOrder(data.order)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    loadOrder()
  }, [loadOrder])

  const runAction = async (action) => {
    setActing(true)
    setError('')
    try {
      let data
      if (action === 'accept') data = await supplierApi.acceptOrder(id)
      else if (action === 'reject') data = await supplierApi.rejectOrder(id)
      else if (action === 'advance') data = await supplierApi.updateStatus(id, order.next_status)
      setOrder(data.order)
    } catch (err) {
      setError(err.message)
    } finally {
      setActing(false)
    }
  }

  const handleReject = async () => {
    if (!window.confirm('Reject this order? It will be marked CANCELLED.')) return
    await runAction('reject')
  }

  const nextLabel = order?.next_status ? NEXT_STATUS_LABELS[order.next_status] : null

  return (
    <SupplierLayout
      title={order?.order_number || 'Order details'}
      subtitle="Review request and update delivery status."
      actions={
        order?.status === 'PLACED' ? (
          <>
            <button type="button" className="btn btn-primary" disabled={acting} onClick={() => runAction('accept')}>
              Accept order
            </button>
            <button type="button" className="btn btn-danger" disabled={acting} onClick={handleReject}>
              Reject
            </button>
          </>
        ) : nextLabel ? (
          <button type="button" className="btn btn-primary" disabled={acting} onClick={() => runAction('advance')}>
            {acting ? 'Updating…' : nextLabel}
          </button>
        ) : null
      }
    >
      <p className="breadcrumb">
        <Link to="/supplier/orders?view=incoming" className="link">
          Orders
        </Link>
        <span className="muted"> / Details</span>
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p className="muted">Loading order…</p>
      ) : !order ? (
        <p className="muted">Order not found.</p>
      ) : (
        <section className="card detail-card">
          <span className={statusClass(order.status)}>{formatStatus(order.status)}</span>

          <dl className="detail-list">
            <div>
              <dt>Contractor</dt>
              <dd>
                {order.contractor_name}
                {order.contractor_phone && <span className="muted block-text">{order.contractor_phone}</span>}
              </dd>
            </div>
            <div>
              <dt>Delivery site</dt>
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
                {order.concrete_grade} · {order.quantity_m3} m³ @ {formatInr(order.price_per_m3)}/m³
              </dd>
            </div>
            <div>
              <dt>Delivery</dt>
              <dd>
                {order.delivery_date} · {order.delivery_time}
              </dd>
            </div>
            <div>
              <dt>Order total</dt>
              <dd>{formatInr(order.total_amount)}</dd>
            </div>
            {order.special_instructions && (
              <div>
                <dt>Instructions</dt>
                <dd>{order.special_instructions}</dd>
              </div>
            )}
          </dl>

          {order.status === 'DELIVERED' && (
            <p className="muted">This order is complete and included in revenue summary.</p>
          )}
          {order.status === 'CANCELLED' && (
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/supplier/orders?view=incoming')}>
              Back to orders
            </button>
          )}
        </section>
      )}
    </SupplierLayout>
  )
}
