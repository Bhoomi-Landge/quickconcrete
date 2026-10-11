const EMPTY = {
  plant_name: '',
  address: '',
  city: '',
  pincode: '',
  contact_phone: '',
  operating_hours: '',
  pump_charge_inr: '',
  transport_charge_per_m3: '',
  other_charge_inr: '',
  other_charge_label: '',
  gst_rate_percent: '',
  estimated_lead_time_hours: '',
  quotation_valid_days: '',
}

export function emptyPlantForm() {
  return { ...EMPTY }
}

export function plantToForm(plant) {
  if (!plant) return emptyPlantForm()
  return {
    plant_name: plant.plant_name || '',
    address: plant.address || '',
    city: plant.city || '',
    pincode: plant.pincode || '',
    contact_phone: plant.contact_phone || '',
    operating_hours: plant.operating_hours || '',
    pump_charge_inr: plant.pump_charge_inr != null ? String(plant.pump_charge_inr) : '',
    transport_charge_per_m3:
      plant.transport_charge_per_m3 != null ? String(plant.transport_charge_per_m3) : '',
    other_charge_inr: plant.other_charge_inr != null ? String(plant.other_charge_inr) : '',
    other_charge_label: plant.other_charge_label || '',
    gst_rate_percent: plant.gst_rate_percent != null ? String(plant.gst_rate_percent) : '',
    estimated_lead_time_hours:
      plant.estimated_lead_time_hours != null ? String(plant.estimated_lead_time_hours) : '',
    quotation_valid_days:
      plant.quotation_valid_days != null ? String(plant.quotation_valid_days) : '',
  }
}

export function PlantForm({ form, onChange, onSubmit, submitting, error, submitLabel }) {
  const update = (key, value) => onChange({ ...form, [key]: value })

  return (
    <form className="form form-card" onSubmit={onSubmit}>
      {error && <div className="alert alert-error">{error}</div>}
      <label className="field">
        <span>Plant name</span>
        <input
          value={form.plant_name}
          onChange={(e) => update('plant_name', e.target.value)}
          required
          placeholder="Andheri Batch Plant"
        />
      </label>
      <label className="field">
        <span>Address</span>
        <input
          value={form.address}
          onChange={(e) => update('address', e.target.value)}
          required
          placeholder="Plot 12, MIDC"
        />
      </label>
      <div className="form-row">
        <label className="field">
          <span>City</span>
          <input value={form.city} onChange={(e) => update('city', e.target.value)} required />
        </label>
        <label className="field">
          <span>Pincode</span>
          <input
            value={form.pincode}
            onChange={(e) => update('pincode', e.target.value)}
            required
            inputMode="numeric"
            pattern="[0-9]{6}"
            maxLength={6}
          />
        </label>
      </div>
      <label className="field">
        <span>Contact number</span>
        <input
          value={form.contact_phone}
          onChange={(e) => update('contact_phone', e.target.value)}
          placeholder="+91 98765 43210"
        />
      </label>
      <label className="field">
        <span>Operating hours</span>
        <input
          value={form.operating_hours}
          onChange={(e) => update('operating_hours', e.target.value)}
          placeholder="Mon–Sat 6:00 AM – 8:00 PM"
        />
      </label>

      <h3 className="form-section-title">Cost estimate charges (optional)</h3>
      <p className="field-hint">
        Published rates help contractors compare total estimated cost. Leave blank if not applicable.
      </p>
      <div className="form-row">
        <label className="field">
          <span>Pump charge (₹ flat per order)</span>
          <input
            type="number"
            min="0"
            step="1"
            value={form.pump_charge_inr}
            onChange={(e) => update('pump_charge_inr', e.target.value)}
            placeholder="e.g. 4500"
          />
        </label>
        <label className="field">
          <span>Transport (₹ per m³)</span>
          <input
            type="number"
            min="0"
            step="1"
            value={form.transport_charge_per_m3}
            onChange={(e) => update('transport_charge_per_m3', e.target.value)}
            placeholder="e.g. 120"
          />
        </label>
      </div>
      <div className="form-row">
        <label className="field">
          <span>Other charge (₹ flat)</span>
          <input
            type="number"
            min="0"
            step="1"
            value={form.other_charge_inr}
            onChange={(e) => update('other_charge_inr', e.target.value)}
          />
        </label>
        <label className="field">
          <span>Other charge label</span>
          <input
            value={form.other_charge_label}
            onChange={(e) => update('other_charge_label', e.target.value)}
            placeholder="e.g. Night delivery surcharge"
          />
        </label>
      </div>
      <div className="form-row">
        <label className="field">
          <span>GST rate (%)</span>
          <input
            type="number"
            min="0"
            max="28"
            step="0.1"
            value={form.gst_rate_percent}
            onChange={(e) => update('gst_rate_percent', e.target.value)}
            placeholder="e.g. 18"
          />
        </label>
        <label className="field">
          <span>Est. lead time (hours)</span>
          <input
            type="number"
            min="0"
            value={form.estimated_lead_time_hours}
            onChange={(e) => update('estimated_lead_time_hours', e.target.value)}
          />
        </label>
        <label className="field">
          <span>Quote validity (days)</span>
          <input
            type="number"
            min="0"
            value={form.quotation_valid_days}
            onChange={(e) => update('quotation_valid_days', e.target.value)}
          />
        </label>
      </div>

      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Saving…' : submitLabel}
        </button>
      </div>
    </form>
  )
}
