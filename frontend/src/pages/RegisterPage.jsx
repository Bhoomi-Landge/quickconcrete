import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { AuthFooterLink, AuthLayout } from '../components/AuthLayout'
import { useAuth } from '../context/AuthContext'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    role: 'CONTRACTOR',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }))

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const user = await register(form)
      navigate(user.role === 'SUPPLIER' ? '/supplier' : '/contractor')
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Create account"
      subtitle="Register as a contractor or RMC supplier"
      footer={
        <AuthFooterLink text="Already have an account?" linkText="Sign in" to="/login" />
      }
    >
      <form className="form" onSubmit={handleSubmit}>
        {error && <div className="alert alert-error">{error}</div>}
        <label className="field">
          <span>Full name</span>
          <input
            value={form.name}
            onChange={(e) => update('name', e.target.value)}
            required
            placeholder="Rajesh Kumar"
          />
        </label>
        <label className="field">
          <span>Email</span>
          <input
            type="email"
            value={form.email}
            onChange={(e) => update('email', e.target.value)}
            required
            placeholder="you@company.com"
          />
        </label>
        <label className="field">
          <span>Phone (optional)</span>
          <input
            value={form.phone}
            onChange={(e) => update('phone', e.target.value)}
            placeholder="+91 98765 43210"
          />
        </label>
        <label className="field">
          <span>I am a</span>
          <select value={form.role} onChange={(e) => update('role', e.target.value)}>
            <option value="CONTRACTOR">Contractor</option>
            <option value="SUPPLIER">RMC Supplier</option>
          </select>
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={form.password}
            onChange={(e) => update('password', e.target.value)}
            required
            minLength={6}
            placeholder="At least 6 characters"
          />
        </label>
        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create account'}
        </button>
      </form>
    </AuthLayout>
  )
}
