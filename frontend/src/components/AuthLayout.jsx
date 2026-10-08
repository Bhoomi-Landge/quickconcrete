import { Link } from 'react-router-dom'

export function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="auth-page">
      <div className="auth-panel">
        <div className="auth-brand">
          <span className="brand-mark lg">QC</span>
          <div>
            <h1>QuickConcrete</h1>
            <p>On-demand ready-mix concrete for construction sites</p>
          </div>
        </div>
        <div className="auth-card">
          <h2>{title}</h2>
          {subtitle && <p className="auth-subtitle">{subtitle}</p>}
          {children}
          {footer}
        </div>
      </div>
    </div>
  )
}

export function AuthFooterLink({ text, linkText, to }) {
  return (
    <p className="auth-footer">
      {text}{' '}
      <Link to={to} className="link">
        {linkText}
      </Link>
    </p>
  )
}
