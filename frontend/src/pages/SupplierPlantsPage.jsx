import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { SupplierLayout } from '../components/SupplierLayout'
import { supplierApi } from '../services/api'

export function SupplierPlantsPage() {
  const [plants, setPlants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = () => {
    setLoading(true)
    supplierApi
      .listPlants()
      .then((data) => setPlants(data.plants || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const handleDeletePlant = async (plant) => {
    if (
      !window.confirm(
        `Delete plant "${plant.plant_name}" and all its grades/prices? This cannot be undone.`,
      )
    ) {
      return
    }
    setError('')
    try {
      await supplierApi.deletePlant(plant.id)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <SupplierLayout
      title="Plants & Pricing"
      subtitle="Manage your RMC plants and concrete rates."
      actions={
        <Link to="/supplier/plants/new" className="btn btn-primary">
          + Add Plant
        </Link>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <p className="muted">Loading plants…</p>
      ) : plants.length === 0 ? (
        <section className="card">
          <p className="muted empty-state">
            No plants yet.{' '}
            <Link to="/supplier/plants/new" className="link">
              Add your first plant
            </Link>
          </p>
        </section>
      ) : (
        <div className="card-grid">
          {plants.map((plant) => (
            <section className="card plant-card" key={plant.id}>
              <div className="plant-card-body">
                <h3>{plant.plant_name}</h3>
                <p className="muted">
                  {plant.address}
                  <span className="block-text">
                    {plant.city} · {plant.pincode}
                  </span>
                </p>
                <dl className="summary-lines">
                  <div>
                    <dt>Products</dt>
                    <dd>{plant.product_count ?? 0}</dd>
                  </div>
                  <div>
                    <dt>Active grades</dt>
                    <dd className="grades-summary">{plant.grades_summary || '—'}</dd>
                  </div>
                </dl>
              </div>
              <div className="plant-card-actions">
                <Link to={`/supplier/plants/${plant.id}`} className="btn btn-primary btn-sm">
                  Manage
                </Link>
                <Link to={`/supplier/plants/${plant.id}/edit`} className="btn btn-secondary btn-sm">
                  Edit
                </Link>
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDeletePlant(plant)}
                >
                  Delete
                </button>
              </div>
            </section>
          ))}
        </div>
      )}
    </SupplierLayout>
  )
}
