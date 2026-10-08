import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ContractorLayout } from '../components/ContractorLayout'
import { sitesApi } from '../services/api'

export function ContractorSitesPage() {
  const [sites, setSites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadSites = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await sitesApi.list()
      setSites(data.sites || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSites()
  }, [loadSites])

  return (
    <ContractorLayout
      title="Construction sites"
      subtitle="Saved delivery locations for your RMC orders."
      actions={
        <Link to="/contractor/sites/new" className="btn btn-primary">
          + Add site
        </Link>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}

      <section className="card">
        {loading ? (
          <p className="muted empty-state">Loading sites…</p>
        ) : sites.length === 0 ? (
          <p className="muted empty-state">
            No sites yet.{' '}
            <Link to="/contractor/sites/new" className="link">
              Add a construction site
            </Link>
          </p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Site</th>
                  <th>City</th>
                  <th>Pincode</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {sites.map((site) => (
                  <tr key={site.id}>
                    <td>
                      <Link to={`/contractor/sites/${site.id}`} className="link table-link">
                        {site.site_name}
                      </Link>
                      <p className="table-sub muted">{site.address}</p>
                    </td>
                    <td>{site.city}</td>
                    <td>{site.pincode}</td>
                    <td className="table-actions">
                      <Link to={`/contractor/sites/${site.id}/edit`} className="btn btn-secondary btn-sm">
                        Edit
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </ContractorLayout>
  )
}
