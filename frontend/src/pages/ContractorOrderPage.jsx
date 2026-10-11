import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { QuotationBreakdown } from '../components/QuotationBreakdown'
import { ContractorLayout } from '../components/ContractorLayout'
import { ordersApi, sitesApi } from '../services/api'
import {
  defaultDeliveryTimeForDate,
  isTimeBeforeMin,
  minTimeForDate,
  normalizeTimeForInput,
  todayIsoDate,
} from '../utils/deliveryTime'
import {
  DEFAULT_REQUIREMENTS_FORM,
  PLACEMENT_METHOD_OPTIONS,
  PUMP_OPTIONS,
  PUMP_TYPE_OPTIONS,
  SPECIAL_CONCRETE_OPTIONS,
  WORKABILITY_OPTIONS,
  buildRequirementsPayload,
  getOrderSubmitBlockers,
  requirementsFormFromOrder,
  validateRequirementsForm,
} from '../utils/orderRequirementLabels'

function formatCurrency(amount) {
  if (amount == null || Number.isNaN(amount)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function ContractorOrderPage({ mode = 'create' }) {
  const navigate = useNavigate()
  const { id: editOrderId } = useParams()
  const isEdit = mode === 'edit' && editOrderId
  const [searchParams] = useSearchParams()
  const preselectedPlant = searchParams.get('plant_id') || ''

  const [existingOrder, setExistingOrder] = useState(null)
  const [sites, setSites] = useState([])
  const [plants, setPlants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [siteId, setSiteId] = useState('')
  const [plantId, setPlantId] = useState(preselectedPlant)
  const [concreteGrade, setConcreteGrade] = useState('')
  const [quantityM3, setQuantityM3] = useState('')
  const [deliveryDate, setDeliveryDate] = useState(todayIsoDate())
  const [deliveryTime, setDeliveryTime] = useState(() => defaultDeliveryTimeForDate(todayIsoDate()))
  const [specialInstructions, setSpecialInstructions] = useState('')
  const [requirements, setRequirements] = useState({ ...DEFAULT_REQUIREMENTS_FORM })
  const [fieldErrors, setFieldErrors] = useState({})

  const [estimate, setEstimate] = useState(null)
  const [estimateLoading, setEstimateLoading] = useState(false)
  const [estimateError, setEstimateError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false
    const loads = [sitesApi.list(), ordersApi.marketplace()]
    if (isEdit) loads.push(ordersApi.get(editOrderId))

    Promise.all(loads)
      .then(([sitesRes, marketRes, orderRes]) => {
        if (cancelled) return
        const siteList = sitesRes.sites || []
        const plantList = marketRes.plants || []
        setSites(siteList)
        setPlants(plantList)

        if (isEdit && orderRes?.order) {
          const order = orderRes.order
          setExistingOrder(order)
          if (!order.editable) return
          setSiteId(String(order.site_id))
          setPlantId(String(order.plant_id))
          setConcreteGrade(order.concrete_grade)
          setQuantityM3(String(order.quantity_m3))
          setDeliveryDate(order.delivery_date)
          setDeliveryTime(normalizeTimeForInput(order.delivery_time))
          setSpecialInstructions(order.special_instructions || '')
          setRequirements(requirementsFormFromOrder(order))
          return
        }

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
  }, [preselectedPlant, isEdit, editOrderId])

  const minDeliveryTime = useMemo(() => minTimeForDate(deliveryDate), [deliveryDate])

  useEffect(() => {
    if (minDeliveryTime && isTimeBeforeMin(deliveryTime, minDeliveryTime)) {
      setDeliveryTime(minDeliveryTime)
    }
  }, [deliveryDate, minDeliveryTime, deliveryTime])

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
        pump_required: requirements.pumpRequired === 'true',
      })
      setEstimate(data.estimate)
    } catch (err) {
      setEstimate(null)
      setEstimateError(err.message)
    } finally {
      setEstimateLoading(false)
    }
  }, [siteId, plantId, concreteGrade, quantityNumber, requirements.pumpRequired])

  useEffect(() => {
    const timer = setTimeout(fetchEstimate, 350)
    return () => clearTimeout(timer)
  }, [fetchEstimate])

  const updateRequirement = (key, value) => {
    setRequirements((prev) => {
      const next = { ...prev, [key]: value }
      if (key === 'pumpRequired' && value === 'false') {
        next.pumpType = ''
        next.pumpBoomReachM = ''
        next.pumpPipelineLengthM = ''
        next.pumpInstructions = ''
      }
      if (key === 'placementMethod' && value !== 'OTHER') {
        next.placementMethodOther = ''
      }
      if (key === 'specialConcreteType' && value !== 'TEMPERATURE_CONTROLLED') {
        next.requestedConcreteTempC = ''
      }
      return next
    })
    setFieldErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    const clientErrors = validateRequirementsForm(requirements)
    if (Object.keys(clientErrors).length > 0) {
      setFieldErrors(clientErrors)
      return
    }
    setFieldErrors({})
    if (minDeliveryTime && isTimeBeforeMin(deliveryTime, minDeliveryTime)) {
      setFieldErrors((prev) => ({
        ...prev,
        deliveryTime: 'Choose a delivery time later today.',
      }))
      return
    }

    setSubmitting(true)
    const payload = {
      site_id: Number(siteId),
      plant_id: Number(plantId),
      concrete_grade: concreteGrade,
      quantity_m3: quantityNumber,
      delivery_date: deliveryDate,
      delivery_time: deliveryTime,
      special_instructions: specialInstructions,
      ...buildRequirementsPayload(requirements),
    }
    try {
      if (isEdit) {
        const data = await ordersApi.update(editOrderId, payload)
        navigate(`/contractor/orders/${editOrderId}`, { state: { saved: true, order: data.order } })
      } else {
        const data = await ordersApi.create(payload)
        navigate(`/contractor/orders/${data.order.id}/confirmation`, { state: { order: data.order } })
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const submitBlockers = useMemo(
    () =>
      getOrderSubmitBlockers({
        siteId,
        plantId,
        concreteGrade,
        quantityNumber,
        deliveryDate,
        deliveryTime,
        estimate,
        estimateLoading,
        estimateError,
        requirements,
        minDeliveryTime,
        deliveryTimeValue: deliveryTime,
      }),
    [
      siteId,
      plantId,
      concreteGrade,
      quantityNumber,
      deliveryDate,
      deliveryTime,
      estimate,
      estimateLoading,
      estimateError,
      requirements,
      minDeliveryTime,
    ],
  )

  const canSubmit = submitBlockers.length === 0 && !submitting

  const notEditable = isEdit && existingOrder && !existingOrder.editable

  return (
    <ContractorLayout
      title={isEdit ? `Edit ${existingOrder?.order_number || 'order'}` : 'Order concrete'}
      subtitle={
        isEdit
          ? 'Update your request before the supplier accepts it.'
          : 'Choose supplier plant, grade, and delivery window.'
      }
      actions={
        isEdit ? (
          <Link to={`/contractor/orders/${editOrderId}`} className="btn btn-secondary">
            Back to order
          </Link>
        ) : (
          <Link to="/contractor/marketplace" className="btn btn-secondary">
            Browse all plants
          </Link>
        )
      }
    >
      {notEditable ? (
        <section className="card">
          <p className="alert alert-error">
            This order is <strong>{existingOrder.status.replace(/_/g, ' ')}</strong> and can no
            longer be edited. Only PLACED orders (before supplier acceptance) can be changed.
          </p>
          <Link to={`/contractor/orders/${editOrderId}`} className="btn btn-secondary">
            View order details
          </Link>
        </section>
      ) : loading ? (
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

            <section className="form-section">
              <h3 className="form-section-title">Pump requirement</h3>
              <fieldset className="radio-fieldset">
                <legend className="sr-only">Pump requirement</legend>
                {PUMP_OPTIONS.map((opt) => (
                  <label key={opt.value} className="radio-option">
                    <input
                      type="radio"
                      name="pumpRequired"
                      value={opt.value}
                      checked={requirements.pumpRequired === opt.value}
                      onChange={(e) => updateRequirement('pumpRequired', e.target.value)}
                    />
                    {opt.label}
                  </label>
                ))}
              </fieldset>
              {fieldErrors.pumpRequired && <p className="field-error">{fieldErrors.pumpRequired}</p>}

              {requirements.pumpRequired === 'true' && (
                <div className="conditional-fields">
                  <label className="field">
                    <span>Pump type (optional)</span>
                    <select
                      value={requirements.pumpType}
                      onChange={(e) => updateRequirement('pumpType', e.target.value)}
                    >
                      <option value="">Select type</option>
                      {PUMP_TYPE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="form-row">
                    <label className="field">
                      <span>Boom reach (m, if applicable)</span>
                      <input
                        type="number"
                        min="0"
                        step="0.5"
                        value={requirements.pumpBoomReachM}
                        onChange={(e) => updateRequirement('pumpBoomReachM', e.target.value)}
                        placeholder="e.g. 32"
                      />
                      {fieldErrors.pumpBoomReachM && (
                        <p className="field-error">{fieldErrors.pumpBoomReachM}</p>
                      )}
                    </label>
                    <label className="field">
                      <span>Pipeline length (m, if applicable)</span>
                      <input
                        type="number"
                        min="0"
                        step="0.5"
                        value={requirements.pumpPipelineLengthM}
                        onChange={(e) => updateRequirement('pumpPipelineLengthM', e.target.value)}
                        placeholder="e.g. 80"
                      />
                    </label>
                  </div>
                  <label className="field">
                    <span>Additional pump instructions (optional)</span>
                    <textarea
                      rows={2}
                      value={requirements.pumpInstructions}
                      onChange={(e) => updateRequirement('pumpInstructions', e.target.value)}
                    />
                  </label>
                </div>
              )}
            </section>

            <section className="form-section">
              <h3 className="form-section-title">Method of concrete placing</h3>
              <label className="field">
                <span>Placing method</span>
                <select
                  value={requirements.placementMethod}
                  onChange={(e) => updateRequirement('placementMethod', e.target.value)}
                  required
                >
                  <option value="">Select method</option>
                  {PLACEMENT_METHOD_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.placementMethod && (
                  <p className="field-error">{fieldErrors.placementMethod}</p>
                )}
              </label>
              {requirements.placementMethod === 'OTHER' && (
                <label className="field">
                  <span>Describe placing method</span>
                  <input
                    type="text"
                    value={requirements.placementMethodOther}
                    onChange={(e) => updateRequirement('placementMethodOther', e.target.value)}
                  />
                  {fieldErrors.placementMethodOther && (
                    <p className="field-error">{fieldErrors.placementMethodOther}</p>
                  )}
                </label>
              )}
            </section>

            <section className="form-section">
              <h3 className="form-section-title">Slump / flow requirements</h3>
              <p className="field-hint">
                Slump (conventional concrete) and slump flow (SCC) are different tests — specify the
                test type that matches your requirement.
              </p>
              <label className="field">
                <span>Measurement type</span>
                <select
                  value={requirements.workabilityTestType}
                  onChange={(e) => updateRequirement('workabilityTestType', e.target.value)}
                  required
                >
                  <option value="">Select type</option>
                  {WORKABILITY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.workabilityTestType && (
                  <p className="field-error">{fieldErrors.workabilityTestType}</p>
                )}
              </label>
              <label className="field">
                <span>Target value (mm)</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={requirements.targetSlumpMm}
                  onChange={(e) => updateRequirement('targetSlumpMm', e.target.value)}
                  required
                  placeholder="e.g. 100"
                />
                {fieldErrors.targetSlumpMm && <p className="field-error">{fieldErrors.targetSlumpMm}</p>}
              </label>
              {fieldErrors.workabilityRange && (
                <p className="field-error">{fieldErrors.workabilityRange}</p>
              )}
              <div className="form-row">
                <label className="field">
                  <span>Minimum (mm, optional)</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={requirements.minimumSlumpMm}
                    onChange={(e) => updateRequirement('minimumSlumpMm', e.target.value)}
                  />
                </label>
                <label className="field">
                  <span>Maximum (mm, optional)</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={requirements.maximumSlumpMm}
                    onChange={(e) => updateRequirement('maximumSlumpMm', e.target.value)}
                  />
                </label>
              </div>
            </section>

            <section className="form-section">
              <h3 className="form-section-title">Special concrete requirements</h3>
              <label className="field">
                <span>Concrete type</span>
                <select
                  value={requirements.specialConcreteType}
                  onChange={(e) => updateRequirement('specialConcreteType', e.target.value)}
                  required
                >
                  {SPECIAL_CONCRETE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.specialConcreteType && (
                  <p className="field-error">{fieldErrors.specialConcreteType}</p>
                )}
              </label>
              {requirements.specialConcreteType === 'TEMPERATURE_CONTROLLED' && (
                <label className="field">
                  <span>Requested concrete temperature (°C, optional)</span>
                  <input
                    type="number"
                    step="0.5"
                    value={requirements.requestedConcreteTempC}
                    onChange={(e) => updateRequirement('requestedConcreteTempC', e.target.value)}
                    placeholder="e.g. 18"
                  />
                </label>
              )}
              <label className="field">
                <span>
                  {requirements.specialConcreteType === 'OTHER'
                    ? 'Describe requirement'
                    : 'Additional notes (optional)'}
                </span>
                <textarea
                  rows={2}
                  value={requirements.specialConcreteNotes}
                  onChange={(e) => updateRequirement('specialConcreteNotes', e.target.value)}
                />
                {fieldErrors.specialConcreteNotes && (
                  <p className="field-error">{fieldErrors.specialConcreteNotes}</p>
                )}
              </label>
            </section>

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
                <input
                  type="time"
                  value={deliveryTime}
                  min={minDeliveryTime || undefined}
                  step={900}
                  onChange={(e) => setDeliveryTime(e.target.value)}
                  required
                />
                <p className="field-hint">
                  Choose any time in 15-minute steps. Past times are hidden when delivery is today.
                </p>
                {fieldErrors.deliveryTime && (
                  <p className="field-error">{fieldErrors.deliveryTime}</p>
                )}
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
              {submitting
                ? isEdit
                  ? 'Saving changes…'
                  : 'Placing order…'
                : isEdit
                  ? 'Save changes'
                  : 'Place order'}
            </button>
            {!canSubmit && !submitting && submitBlockers.length > 0 && (
              <div className="submit-blockers" role="status">
                <p className="submit-blockers-title">Complete these to place your order:</p>
                <ul>
                  {submitBlockers.map((msg) => (
                    <li key={msg}>{msg}</li>
                  ))}
                </ul>
              </div>
            )}
          </form>

          <aside className="card order-summary">
            <p className="eyebrow">Estimated price</p>
            {estimateLoading ? (
              <p className="muted">Calculating…</p>
            ) : estimateError ? (
              <p className="alert alert-error">{estimateError}</p>
            ) : estimate ? (
              <>
                <p className="eyebrow">Concrete subtotal</p>
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
                </dl>
                {estimate.quotation && (
                  <QuotationBreakdown quotation={estimate.quotation} compact />
                )}
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
