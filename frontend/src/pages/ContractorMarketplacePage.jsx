import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ContractorLayout } from '../components/ContractorLayout'
import { ordersApi } from '../services/api'
import { formatInr } from '../utils/orderHelpers'

export function ContractorMarketplacePage() {
  const [plants, setPlants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    ordersApi
      .marketplace()
      .then((data) => setPlants(data.plants || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <ContractorLayout
      title="Browse RMC plants"
      subtitle="All supplier plants and location-based concrete rates."
      actions={
        <Link to="/contractor/orders/new" className="btn btn-primary">
          + Order concrete
        </Link>
      }
    >
      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <p className="muted">Loading plants…</p>
      ) : plants.length === 0 ? (
        <section className="card">
          <p className="muted empty-state">No supplier plants listed yet.</p>
        </section>
      ) : (
        <div className="marketplace-list">
          {plants.map((plant) => (
            <section className="card" key={plant.id}>
              <div className="card-title-row">
                <div>
                  <h3>{plant.plant_name}</h3>
                  <p className="muted">
                    {plant.supplier_name} · {plant.city} · {plant.pincode}
                  </p>
                  <p className="table-sub muted">{plant.address}</p>
                </div>
                <Link
                  to={`/contractor/orders/new?plant_id=${plant.id}`}
                  className="btn btn-primary btn-sm"
                >
                  Order from this plant
                </Link>
              </div>
              {plant.products?.length ? (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Grade</th>
                        <th>Price / m³</th>
                        <th>Min order</th>
                      </tr>
                    </thead>
                    <tbody>
                      {plant.products.map((p) => (
                        <tr key={p.id}>
                          <td>{p.grade}</td>
                          <td>{formatInr(p.price_per_m3)}</td>
                          <td>{p.minimum_order_m3 ?? 1} m³</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="muted empty-state">No rates published for this plant yet.</p>
              )}
            </section>
          ))}
        </div>
      )}
    </ContractorLayout>
  )
}
