import { DashboardLayout } from './DashboardLayout'

const CONTRACTOR_NAV = [
  { to: '/contractor', label: 'Dashboard', end: true },
  { to: '/contractor/marketplace', label: 'Browse RMC plants' },
  { to: '/contractor/orders/new', label: 'Order concrete' },
  { to: '/contractor/sites', label: 'Construction sites' },
]

export function ContractorLayout({ title, subtitle, children, actions }) {
  return (
    <DashboardLayout
      title={title}
      subtitle={subtitle}
      navLinks={CONTRACTOR_NAV}
      headerActions={actions}
    >
      {children}
    </DashboardLayout>
  )
}
