export function formatInr(amount) {
  if (amount == null || Number.isNaN(amount)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatStatus(status) {
  return (status || '').replace(/_/g, ' ')
}

export function statusClass(status) {
  return `status-badge status-${(status || 'placed').toLowerCase()}`
}

export const NEXT_STATUS_LABELS = {
  PREPARING: 'Mark preparing',
  DISPATCHED: 'Mark dispatched',
  OUT_FOR_DELIVERY: 'Out for delivery',
  DELIVERED: 'Mark delivered',
}
