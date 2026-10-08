import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { ContractorLayout } from '../components/ContractorLayout'
import { ordersApi, sitesApi } from '../services/api'

const DELIVERY_TIMES = [
  { value: '08:00', label: '8:00 AM' },
  { value: '10:00', label: '10:00 AM' },
  { value: '12:00', label: '12:00 PM' },
  { value: '14:00', label: '2:00 PM' },
  { value: '16:00', label: '4:00 PM' },
  { value: '18:00', label: '6:00 PM' },
]

function todayIsoDate() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function formatCurrency(amount) {
  if (amount == null || Number.isNaN(amount)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function ContractorOrderPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const preselectedPlant = searchParams.get('plant_id') || ''

  const [sites, setSites] = useState([])
  const [plants, setPlants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [siteId, setSiteId] = useState('')
  const [plantId, setPlantId] = useState(preselectedPlant)
  const [concreteGrade, setConcreteGrade] = useState('')
  const [quantityM3, setQuantityM3] = useState('')
  const [deliveryDate, setDeliveryDate] = useState(todayIsoDate())
  const [deliveryTime, setDeliveryTime] = useState('10:00')
  const [specialInstructions, setSpecialInstructions] = useState('')

  const [estimate, setEstimate] = useState(null)
  const [estimateLoading, setEstimateLoading] = useState(false)
  const [estimateError, setEstimateError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false
    Promise.all([sitesApi.list(), ordersApi.marketplace()])
      .then(([sitesRes, marketRes]) => {
        if (cancelled) return
        const siteList = sitesRes.sites || []
        const plantList = marketRes.plants || []
        setSites(siteList)
        setPlants(plantList)
        if (siteList.length > 0) setSiteId(String(siteList[0].id))
        const initialPlant =
          preselectedPlant && plantList.some((p) => String(p.id) === preselectedPlant)
            ? preselectedPlant
            : plantList[0]
              ? String(plantList[0].id)
              : ''
        setPlantId(initialPlant)
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
  }, [preselectedPlant])

  const selectedPlant = plants.find((p) => String(p.id) === String(plantId))
  const plantProducts = selectedPlant?.products || []

  useEffect(() => {
    if (plantProducts.length === 0) {
      setConcreteGrade('')
      return
    }
    if (!plantProducts.some((p) => p.grade === concreteGrade)) {
      setConcreteGrade(plantProducts[0].grade)
    }
  }, [plantId, plantProducts, concreteGrade])

  const quantityNumber = useMemo(() => {
    const n = parseFloat(quantityM3)
    return Number.isFinite(n) ? n : null
  }, [quantityM3])

  const fetchEstimate = useCallback(async () => {
    if (!siteId || !plantId || !concreteGrade || !quantityNumber || quantityNumber <= 0) {
      setEstimate(null)
      setEstimateError('')
      return
    }
    setEstimateLoading(true)
    setEstimateError('')
    try {
      const data = await ordersApi.estimate({
        site_id: Number(siteId),
        plant_id: Number(plantId),
        concrete_grade: concreteGrade,
        quantity_m3: quantityNumber,
      })
      setEstimate(data.estimate)
    } catch (err) {
      setEstimate(null)
      setEstimateError(err.message)
    } finally {
      setEstimateLoading(false)
    }
  }, [siteId, plantId, concreteGrade, quantityNumber])

  useEffect(() => {
    const timer = setTimeout(fetchEstimate, 350)
    return () => clearTimeout(timer)
  }, [fetchEstimate])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const data = await ordersApi.create({
        site_id: Number(siteId),
        plant_id: Number(plantId),
        concrete_grade: concreteGrade,
        quantity_m3: quantityNumber,
        delivery_date: deliveryDate,
        delivery_time: deliveryTime,
        special_instructions: specialInstructions,
      })
      navigate(`/contractor/orders/${data.order.id}/confirmation`, { state: { order: data.order } })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const canSubmit =
    siteId &&
    plantId &&
    concreteGrade &&
    quantityNumber > 0 &&
    deliveryDate &&
    deliveryTime &&
    estimate &&
    !submitting

  return (
    <ContractorLayout
      title="Order concrete"
      subtitle="Choose supplier plant, grade, and delivery window."
      actions={
        <Link to="/contractor/marketplace" className="btn btn-secondary">
          Browse all plants
        </Link>
      }
    >
      {loading ? (
        <p className="muted">Loading order form…</p>
      ) : sites.length === 0 ? (
        <section className="card">
          <p className="muted">
            Add a construction site before placing an order.{' '}
            <Link to="/contractor/sites/new" className="link">
              Add site
            </Link>
          </p>
        </section>
      ) : plants.length === 0 ? (
        <section className="card">
          <p className="muted">No supplier plants available yet.</p>
        </section>
      ) : (
        <div className="order-layout">
          <form className="card order-form" onSubmit={handleSubmit}>
            {error && <div className="alert alert-error">{error}</div>}

            <label className="field">
              <span>RMC plant (supplier location)</span>
              <select value={plantId} onChange={(e) => setPlantId(e.target.value)} required>
                {plants.map((plant) => (
                  <option key={plant.id} value={plant.id}>
                    {plant.supplier_name} — {plant.plant_name} ({plant.city})
                  </option>
                ))}
              </select>
              {selectedPlant && (
                <p className="field-hint muted">
                  {selectedPlant.address} · {selectedPlant.pincode}
                </p>
              )}
            </label>

            <label className="field">
              <span>Your delivery site</span>
              <select value={siteId} onChange={(e) => setSiteId(e.target.value)} required>
                {sites.map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.site_name} — {site.city}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Concrete grade</span>
              <select
                value={concreteGrade}
                onChange={(e) => setConcreteGrade(e.target.value)}
                required
                disabled={plantProducts.length === 0}
              >
                {plantProducts.map((item) => (
                  <option key={item.id} value={item.grade}>
                    {item.grade} · {formatCurrency(item.price_per_m3)}/m³
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Quantity (m³)</span>
              <input
                type="number"
                min="0.5"
                step="0.5"
                value={quantityM3}
                onChange={(e) => setQuantityM3(e.target.value)}
                required
                placeholder="e.g. 5"
              />
            </label>

            <div className="form-row">
              <label className="field">
                <span>Delivery date</span>
                <input
                  type="date"
                  value={deliveryDate}
                  min={todayIsoDate()}
                  onChange={(e) => setDeliveryDate(e.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>Delivery time</span>
                <select value={deliveryTime} onChange={(e) => setDeliveryTime(e.target.value)} required>
                  {DELIVERY_TIMES.map((slot) => (
                    <option key={slot.value} value={slot.value}>
                      {slot.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="field">
              <span>Special instructions (optional)</span>
              <textarea
                rows={3}
                value={specialInstructions}
                onChange={(e) => setSpecialInstructions(e.target.value)}
                placeholder="Pump access, gate pass, contact on site…"
              />
            </label>

            <button type="submit" className="btn btn-primary btn-block" disabled={!canSubmit}>
              {submitting ? 'Placing order…' : 'Place order'}
            </button>
          </form>

          <aside className="card order-summary">
            <p className="eyebrow">Estimated price</p>
            {estimateLoading ? (
              <p className="muted">Calculating…</p>
            ) : estimateError ? (
              <p className="alert alert-error">{estimateError}</p>
            ) : estimate ? (
              <>
                <p className="summary-total">{formatCurrency(estimate.total_amount)}</p>
                <dl className="summary-lines">
                  <div>
                    <dt>Plant</dt>
                    <dd>{estimate.plant_name}</dd>
                  </div>
                  <div>
                    <dt>Supplier</dt>
                    <dd>{estimate.supplier_name}</dd>
                  </div>
                  <div>
                    <dt>Grade</dt>
                    <dd>{estimate.concrete_grade}</dd>
                  </div>
                  <div>
                    <dt>Quantity</dt>
                    <dd>{estimate.quantity_m3} m³</dd>
                  </div>
                  <div>
                    <dt>Rate</dt>
                    <dd>{formatCurrency(estimate.price_per_m3)}/m³</dd>
                  </div>
                </dl>
              </>
            ) : (
              <p className="muted">Select plant, grade, and quantity.</p>
            )}
          </aside>
        </div>
      )}
    </ContractorLayout>
  )
}
