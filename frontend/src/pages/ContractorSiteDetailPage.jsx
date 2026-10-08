import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ContractorLayout } from '../components/ContractorLayout'
import { sitesApi } from '../services/api'

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return iso
  }
}

export function ContractorSiteDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [site, setSite] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let cancelled = false
    sitesApi
      .get(id)
      .then((data) => {
        if (!cancelled) setSite(data.site)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${site?.site_name}"? This cannot be undone.`)) return
    setDeleting(true)
    setError('')
    try {
      await sitesApi.remove(id)
      navigate('/contractor/sites')
    } catch (err) {
      setError(err.message)
      setDeleting(false)
    }
  }

  return (
    <ContractorLayout
      title={site?.site_name || 'Site details'}
      subtitle="Delivery location for RMC orders."
      actions={
        site && (
          <>
            <Link to={`/contractor/sites/${id}/edit`} className="btn btn-secondary">
              Edit
            </Link>
            <button
              type="button"
              className="btn btn-danger"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting…' : 'Delete'}
            </button>
          </>
        )
      }
    >
      <p className="breadcrumb">
        <Link to="/contractor/sites" className="link">
          Sites
        </Link>
        <span className="muted"> / Details</span>
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p className="muted">Loading site…</p>
      ) : !site ? (
        <p className="muted">Site not found.</p>
      ) : (
        <section className="card detail-card">
          <dl className="detail-list">
            <div>
              <dt>Site name</dt>
              <dd>{site.site_name}</dd>
            </div>
            <div>
              <dt>Address</dt>
              <dd>{site.address}</dd>
            </div>
            <div>
              <dt>City</dt>
              <dd>{site.city}</dd>
            </div>
            <div>
              <dt>Pincode</dt>
              <dd>{site.pincode}</dd>
            </div>
            <div>
              <dt>Added on</dt>
              <dd>{formatDate(site.created_at)}</dd>
            </div>
          </dl>
        </section>
      )}
    </ContractorLayout>
  )
}
