const EMPTY = {
  plant_name: '',
  address: '',
  city: '',
  pincode: '',
  contact_phone: '',
  operating_hours: '',
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
      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Saving…' : submitLabel}
        </button>
      </div>
    </form>
  )
}
