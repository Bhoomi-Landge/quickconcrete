import { DashboardLayout } from '../components/DashboardLayout'

export function AdminDashboard() {
  return (
    <DashboardLayout
      title="Admin dashboard"
      subtitle="Platform overview — full admin tools arrive in Phase 6."
    >
      <div className="stats-row">
        <div className="stat-card">
          <p className="eyebrow">Contractors</p>
          <p className="stat-value">—</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Suppliers</p>
          <p className="stat-value">—</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Orders</p>
          <p className="stat-value">—</p>
        </div>
        <div className="stat-card">
          <p className="eyebrow">Active deliveries</p>
          <p className="stat-value">—</p>
        </div>
      </div>
      <section className="card">
        <h3>Platform activity</h3>
        <p className="muted empty-state">
          Admin listings and statistics will be wired in Phase 6.
        </p>
      </section>
    </DashboardLayout>
  )
}
