import { DashboardLayout } from './DashboardLayout'

const SUPPLIER_NAV = [
  { to: '/supplier', label: 'Dashboard', end: true },
  { to: '/supplier/orders?view=incoming', label: 'Incoming orders' },
  { to: '/supplier/orders?view=active', label: 'Active deliveries' },
  { to: '/supplier/orders?view=completed', label: 'Completed' },
  { to: '/supplier/plants', label: 'Plants & Pricing' },
]

export function SupplierLayout({ title, subtitle, children, actions }) {
  return (
    <DashboardLayout
      title={title}
      subtitle={subtitle}
      navLinks={SUPPLIER_NAV}
      headerActions={actions}
    >
      {children}
    </DashboardLayout>
  )
}
