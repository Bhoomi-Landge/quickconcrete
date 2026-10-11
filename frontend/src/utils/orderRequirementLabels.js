export const PUMP_OPTIONS = [
  { value: 'true', label: 'With pump' },
  { value: 'false', label: 'Without pump' },
]

export const PUMP_TYPE_OPTIONS = [
  { value: 'BOOM', label: 'Boom pump' },
  { value: 'LINE', label: 'Line pump' },
  { value: 'OTHER', label: 'Other' },
]

export const PLACEMENT_METHOD_OPTIONS = [
  { value: 'PUMP', label: 'Pump' },
  { value: 'BUCKET_CRANE', label: 'Bucket / Crane bucket' },
  { value: 'CHUTE', label: 'Chute' },
  { value: 'DIRECT_DISCHARGE', label: 'Direct discharge from transit mixer' },
  { value: 'OTHER', label: 'Other' },
]

export const WORKABILITY_OPTIONS = [
  { value: 'SLUMP', label: 'Slump' },
  { value: 'SLUMP_FLOW', label: 'Slump flow' },
]

export const SPECIAL_CONCRETE_OPTIONS = [
  { value: 'NORMAL', label: 'Normal concrete' },
  { value: 'FREE_FLOW', label: 'Free-flow concrete (FF)' },
  { value: 'SCC', label: 'Self-compacting concrete (SCC)' },
  { value: 'TEMPERATURE_CONTROLLED', label: 'Temperature-controlled / chilled concrete' },
  { value: 'OTHER', label: 'Other' },
]

const LABEL_MAPS = {
  pump_type: Object.fromEntries(PUMP_TYPE_OPTIONS.map((o) => [o.value, o.label])),
  placement_method: Object.fromEntries(PLACEMENT_METHOD_OPTIONS.map((o) => [o.value, o.label])),
  workability_test_type: Object.fromEntries(WORKABILITY_OPTIONS.map((o) => [o.value, o.label])),
  special_concrete_type: Object.fromEntries(SPECIAL_CONCRETE_OPTIONS.map((o) => [o.value, o.label])),
}

export function labelFor(field, value) {
  if (value == null || value === '') return '—'
  if (field === 'pump_required') {
    if (value === true) return 'With pump'
    if (value === false) return 'Without pump'
    return '—'
  }
  const map = LABEL_MAPS[field]
  return map?.[value] || value
}

export function formatWorkability(order) {
  if (!order?.workability_test_type && order?.target_slump_mm == null) return null
  const testLabel = labelFor('workability_test_type', order.workability_test_type)
  const parts = [`${testLabel}: ${order.target_slump_mm} mm target`]
  if (order.minimum_slump_mm != null || order.maximum_slump_mm != null) {
    const min = order.minimum_slump_mm ?? '—'
    const max = order.maximum_slump_mm ?? '—'
    parts.push(`range ${min}–${max} mm`)
  }
  return parts.join(' · ')
}

export function buildRequirementsPayload(form) {
  const pumpRequired = form.pumpRequired === 'true'
  const payload = {
    pump_required: pumpRequired,
    placement_method: form.placementMethod,
    placement_method_other:
      form.placementMethod === 'OTHER' ? form.placementMethodOther.trim() || undefined : undefined,
    workability_test_type: form.workabilityTestType,
    target_slump_mm: Number(form.targetSlumpMm),
    minimum_slump_mm: form.minimumSlumpMm ? Number(form.minimumSlumpMm) : null,
    maximum_slump_mm: form.maximumSlumpMm ? Number(form.maximumSlumpMm) : null,
    special_concrete_type: form.specialConcreteType,
    special_concrete_notes: form.specialConcreteNotes.trim() || undefined,
  }

  if (pumpRequired) {
    if (form.pumpType) payload.pump_type = form.pumpType
    if (form.pumpBoomReachM) payload.pump_boom_reach_m = Number(form.pumpBoomReachM)
    if (form.pumpPipelineLengthM) payload.pump_pipeline_length_m = Number(form.pumpPipelineLengthM)
    if (form.pumpInstructions.trim()) payload.pump_instructions = form.pumpInstructions.trim()
  }

  if (form.specialConcreteType === 'TEMPERATURE_CONTROLLED' && form.requestedConcreteTempC) {
    payload.requested_concrete_temp_c = Number(form.requestedConcreteTempC)
  }

  return payload
}

export function validateRequirementsForm(form) {
  const errors = {}
  if (!form.pumpRequired) errors.pumpRequired = 'Select whether a pump is required.'
  if (!form.placementMethod) errors.placementMethod = 'Select a placing method.'
  if (form.placementMethod === 'OTHER' && !form.placementMethodOther.trim()) {
    errors.placementMethodOther = 'Describe the placing method.'
  }
  if (!form.workabilityTestType) errors.workabilityTestType = 'Select slump or slump flow.'
  if (!form.targetSlumpMm) errors.targetSlumpMm = 'Enter a target value in mm.'
  if (!form.specialConcreteType) errors.specialConcreteType = 'Select a special concrete type.'
  if (form.specialConcreteType === 'OTHER' && !form.specialConcreteNotes.trim()) {
    errors.specialConcreteNotes = 'Describe the special concrete requirement.'
  }

  const pumpRequired = form.pumpRequired === 'true'
  if (form.placementMethod === 'PUMP' && form.pumpRequired === 'false') {
    errors.placementMethod =
      'Placing method is Pump but pump requirement is Without pump. Update one of these fields.'
  }

  if (pumpRequired && form.pumpBoomReachM && Number(form.pumpBoomReachM) <= 0) {
    errors.pumpBoomReachM = 'Enter a positive reach in metres.'
  }

  const min = form.minimumSlumpMm ? Number(form.minimumSlumpMm) : null
  const max = form.maximumSlumpMm ? Number(form.maximumSlumpMm) : null
  const target = form.targetSlumpMm ? Number(form.targetSlumpMm) : null
  if (min != null && max != null && min > max) {
    errors.workabilityRange = 'Minimum cannot be greater than maximum.'
  }
  if (target != null && min != null && target < min) {
    errors.workabilityRange = 'Target must be at least the minimum (mm).'
  }
  if (target != null && max != null && target > max) {
    errors.workabilityRange = 'Target must not exceed the maximum (mm).'
  }

  return errors
}

/** Human-readable reasons the Place order button stays disabled. */
export function getOrderSubmitBlockers({
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
  deliveryTimeValue,
}) {
  const blockers = []
  if (!siteId) blockers.push('Select a delivery site.')
  if (!plantId) blockers.push('Select an RMC plant.')
  if (!concreteGrade) blockers.push('Select a concrete grade.')
  if (!quantityNumber || quantityNumber <= 0) blockers.push('Enter a valid quantity (m³).')
  if (!deliveryDate) blockers.push('Choose a delivery date.')
  if (!deliveryTimeValue) blockers.push('Choose a delivery time.')
  if (minDeliveryTime && deliveryTimeValue && deliveryTimeValue < minDeliveryTime) {
    blockers.push('Delivery time must be later today (see minimum on the time picker).')
  }
  if (estimateLoading) blockers.push('Waiting for price estimate…')
  else if (!estimate) {
    blockers.push(
      estimateError
        ? `Price estimate failed: ${estimateError}`
        : 'Complete site, plant, grade and quantity to get a price estimate.',
    )
  }
  if (!requirements.pumpRequired) {
    blockers.push('Select With pump or Without pump (Pump requirement section).')
  }
  if (!requirements.placementMethod) {
    blockers.push('Select a method of concrete placing.')
  }
  if (!requirements.workabilityTestType) {
    blockers.push('Select slump or slump flow.')
  }
  if (!requirements.targetSlumpMm) {
    blockers.push('Enter a target workability value (mm).')
  }
  if (!requirements.specialConcreteType) {
    blockers.push('Select a special concrete type.')
  }
  const reqErrors = validateRequirementsForm(requirements)
  Object.values(reqErrors).forEach((msg) => {
    if (msg && !blockers.includes(msg)) blockers.push(msg)
  })
  return blockers
}

export function requirementsFormFromOrder(order) {
  if (!order) return { ...DEFAULT_REQUIREMENTS_FORM }
  const pumpRequired =
    order.pump_required === true ? 'true' : order.pump_required === false ? 'false' : ''
  return {
    pumpRequired,
    pumpType: order.pump_type || '',
    pumpBoomReachM: order.pump_boom_reach_m != null ? String(order.pump_boom_reach_m) : '',
    pumpPipelineLengthM:
      order.pump_pipeline_length_m != null ? String(order.pump_pipeline_length_m) : '',
    pumpInstructions: order.pump_instructions || '',
    placementMethod: order.placement_method || '',
    placementMethodOther: order.placement_method_other || '',
    workabilityTestType: order.workability_test_type || '',
    targetSlumpMm: order.target_slump_mm != null ? String(order.target_slump_mm) : '',
    minimumSlumpMm: order.minimum_slump_mm != null ? String(order.minimum_slump_mm) : '',
    maximumSlumpMm: order.maximum_slump_mm != null ? String(order.maximum_slump_mm) : '',
    specialConcreteType: order.special_concrete_type || 'NORMAL',
    specialConcreteNotes: order.special_concrete_notes || '',
    requestedConcreteTempC:
      order.requested_concrete_temp_c != null ? String(order.requested_concrete_temp_c) : '',
  }
}

export const DEFAULT_REQUIREMENTS_FORM = {
  pumpRequired: '',
  pumpType: '',
  pumpBoomReachM: '',
  pumpPipelineLengthM: '',
  pumpInstructions: '',
  placementMethod: '',
  placementMethodOther: '',
  workabilityTestType: '',
  targetSlumpMm: '',
  minimumSlumpMm: '',
  maximumSlumpMm: '',
  specialConcreteType: 'NORMAL',
  specialConcreteNotes: '',
  requestedConcreteTempC: '',
}
