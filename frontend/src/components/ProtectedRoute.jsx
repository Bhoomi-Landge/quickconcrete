import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

export function ProtectedRoute({ allowedRoles }) {
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

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    const fallback =
      user.role === 'CONTRACTOR'
        ? '/contractor'
        : user.role === 'SUPPLIER'
          ? '/supplier'
          : '/admin'
    return <Navigate to={fallback} replace />
  }

  return <Outlet />
}
