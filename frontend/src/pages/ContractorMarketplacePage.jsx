import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { ContractorLayout } from '../components/ContractorLayout'
import { ordersApi } from '../services/api'
import { formatInr } from '../utils/orderHelpers'

const GRADES = ['M20', 'M25', 'M30', 'M35', 'M40']

export function ContractorMarketplacePage() {
  const [plants, setPlants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [compareGrade, setCompareGrade] = useState('M25')
  const [compareQty, setCompareQty] = useState('3')
  const [comparePump, setComparePump] = useState('false')
  const [compareResult, setCompareResult] = useState(null)
  const [compareLoading, setCompareLoading] = useState(false)
  const [compareError, setCompareError] = useState('')

  useEffect(() => {
    ordersApi
      .marketplace()
      .then((data) => setPlants(data.plants || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const gradeOptions = useMemo(() => {
    const fromPlants = new Set()
    plants.forEach((p) => p.products?.forEach((pr) => fromPlants.add(pr.grade)))
    const list = [...fromPlants].sort()
    return list.length ? list : GRADES
  }, [plants])

  const runCompare = async () => {
    const qty = parseFloat(compareQty)
    if (!qty || qty <= 0) {
      setCompareError('Enter a valid quantity to compare.')
      return
    }
    setCompareLoading(true)
    setCompareError('')
    try {
      const data = await ordersApi.compare({
        concrete_grade: compareGrade,
        quantity_m3: qty,
        pump_required: comparePump === 'true',
      })
      setCompareResult(data)
    } catch (err) {
      setCompareError(err.message)
      setCompareResult(null)
    } finally {
      setCompareLoading(false)
    }
  }

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

      <section className="card compare-card">
        <h2>Compare estimated total cost</h2>
        <p className="muted">
          Same grade and quantity across plants. Totals include supplier-published charges only;
          unknown pump/transport/tax lines are excluded — not treated as free.
        </p>
        <div className="compare-form form-row">
          <label className="field">
            <span>Grade</span>
            <select value={compareGrade} onChange={(e) => setCompareGrade(e.target.value)}>
              {gradeOptions.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Quantity (m³)</span>
            <input
              type="number"
              min="0.5"
              step="0.5"
              value={compareQty}
              onChange={(e) => setCompareQty(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Pump required</span>
            <select value={comparePump} onChange={(e) => setComparePump(e.target.value)}>
              <option value="false">Without pump</option>
              <option value="true">With pump</option>
            </select>
          </label>
          <button
            type="button"
            className="btn btn-secondary"
            disabled={compareLoading}
            onClick={runCompare}
          >
            {compareLoading ? 'Comparing…' : 'Compare offers'}
          </button>
        </div>
        {compareError && <p className="field-error">{compareError}</p>}
        {compareResult?.offers?.length > 0 && (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Plant</th>
                  <th>Concrete</th>
                  <th>Est. total</th>
                  <th>Notes</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {compareResult.offers.map((offer) => (
                  <tr key={offer.plant_id}>
                    <td>
                      <strong>{offer.plant_name}</strong>
                      <span className="block-text muted">
                        {offer.supplier_name} · {offer.plant_city}
                      </span>
                    </td>
                    <td>{formatInr(offer.quotation.concrete_subtotal_inr)}</td>
                    <td>
                      {formatInr(offer.quotation.estimated_total_inr)}
                      {offer.quotation.has_unknown_charges && (
                        <span className="block-text muted">partial</span>
                      )}
                    </td>
                    <td className="muted compare-notes">
                      {offer.quotation.has_unknown_charges
                        ? `Excludes: ${offer.quotation.unknown_charge_codes.join(', ')}`
                        : 'All published charges included'}
                    </td>
                    <td>
                      <Link
                        to={`/contractor/orders/new?plant_id=${offer.plant_id}`}
                        className="btn btn-primary btn-sm"
                      >
                        Order
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {compareResult && compareResult.offers?.length === 0 && (
          <p className="muted">No plants meet min order/stock for this grade and quantity.</p>
        )}
      </section>

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
