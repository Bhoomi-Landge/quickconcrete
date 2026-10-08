import { Navigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function HomeRedirect() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="page-center">
        <p className="muted">Loading…</p>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (user.role === 'SUPPLIER') return <Navigate to="/supplier" replace />
  if (user.role === 'ADMIN') return <Navigate to="/admin" replace />
  return <Navigate to="/contractor" replace />
}
