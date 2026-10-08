import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { SupplierLayout } from '../components/SupplierLayout'
import { supplierApi } from '../services/api'
import { formatInr, formatStatus, statusClass } from '../utils/orderHelpers'

const VIEWS = [
  { key: 'incoming', label: 'Incoming' },
  { key: 'active', label: 'Active' },
  { key: 'completed', label: 'Completed' },
  { key: 'all', label: 'All' },
]

const VIEW_TITLES = {
  incoming: 'Incoming orders',
  active: 'Active deliveries',
  completed: 'Completed orders',
  all: 'All orders',
}

export function SupplierOrdersPage() {
  const [searchParams] = useSearchParams()
  const view = searchParams.get('view') || 'incoming'
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const validView = useMemo(() => (VIEWS.some((v) => v.key === view) ? view : 'incoming'), [view])

  const loadOrders = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await supplierApi.listOrders(validView)
      setOrders(data.orders || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [validView])

  useEffect(() => {
    loadOrders()
  }, [loadOrders])

  return (
    <SupplierLayout
      title={VIEW_TITLES[validView] || 'Orders'}
      subtitle="Manage order acceptance and delivery status updates."
    >
      <div className="filter-tabs">
        {VIEWS.map((item) => (
          <Link
            key={item.key}
            to={`/supplier/orders?view=${item.key}`}
            className={validView === item.key ? 'filter-tab active' : 'filter-tab'}
          >
            {item.label}
          </Link>
        ))}
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <section className="card">
        {loading ? (
          <p className="muted empty-state">Loading orders…</p>
        ) : orders.length === 0 ? (
          <p className="muted empty-state">No orders in this list.</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Site</th>
                  <th>Delivery</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {orders.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <Link to={`/supplier/orders/${order.id}`} className="link table-link">
                        {order.order_number}
                      </Link>
                      <p className="table-sub muted">
                        {order.concrete_grade} · {order.quantity_m3} m³
                      </p>
                    </td>
                    <td>
                      {order.site_name}
                      <p className="table-sub muted">{order.site_city}</p>
                    </td>
                    <td>
                      {order.delivery_date}
                      <p className="table-sub muted">{order.delivery_time}</p>
                    </td>
                    <td>{formatInr(order.total_amount)}</td>
                    <td>
                      <span className={statusClass(order.status)}>{formatStatus(order.status)}</span>
                    </td>
                    <td className="table-actions">
                      <Link to={`/supplier/orders/${order.id}`} className="btn btn-secondary btn-sm">
                        Open
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </SupplierLayout>
  )
}
