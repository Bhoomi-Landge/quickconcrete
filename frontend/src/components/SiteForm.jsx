const EMPTY = {
  site_name: '',
  address: '',
  city: '',
  pincode: '',
}

export function emptySiteForm() {
  return { ...EMPTY }
}

export function siteToForm(site) {
  if (!site) return emptySiteForm()
  return {
    site_name: site.site_name || '',
    address: site.address || '',
    city: site.city || '',
    pincode: site.pincode || '',
  }
}

export function SiteForm({ form, onChange, onSubmit, submitting, error, submitLabel }) {
  const update = (key, value) => onChange({ ...form, [key]: value })

  return (
    <form className="form form-card" onSubmit={onSubmit}>
      {error && <div className="alert alert-error">{error}</div>}
      <label className="field">
        <span>Site name</span>
        <input
          value={form.site_name}
          onChange={(e) => update('site_name', e.target.value)}
          required
          placeholder="Skyline Tower — Block A"
        />
      </label>
      <label className="field">
        <span>Address</span>
        <input
          value={form.address}
          onChange={(e) => update('address', e.target.value)}
          required
          placeholder="Plot 12, Industrial Area"
        />
      </label>
      <div className="form-row">
        <label className="field">
          <span>City</span>
          <input
            value={form.city}
            onChange={(e) => update('city', e.target.value)}
            required
            placeholder="Mumbai"
          />
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
            placeholder="400053"
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
