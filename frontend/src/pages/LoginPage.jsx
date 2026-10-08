import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { AuthFooterLink, AuthLayout } from '../components/AuthLayout'
import { useAuth } from '../context/AuthContext'

function dashboardPathForRole(role) {
  if (role === 'SUPPLIER') return '/supplier'
  if (role === 'ADMIN') return '/admin'
  return '/contractor'
}

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const user = await login(email, password)
      navigate(dashboardPathForRole(user.role))
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Access your QuickConcrete workspace"
      footer={
        <AuthFooterLink text="New here?" linkText="Create an account" to="/register" />
      }
    >
      <form className="form" onSubmit={handleSubmit}>
        {error && <div className="alert alert-error">{error}</div>}
        <label className="field">
          <span>Email</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            placeholder="you@company.com"
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            placeholder="••••••••"
          />
        </label>
        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="demo-hint">
          Demo admin: <code>admin@quickconcrete.local</code> / <code>admin123</code>
        </p>
      </form>
    </AuthLayout>
  )
}
