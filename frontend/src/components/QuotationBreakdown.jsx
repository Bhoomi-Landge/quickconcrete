import { formatInr } from '../utils/orderHelpers'

function lineAmount(line) {
  if (line.status === 'unknown' || line.amount_inr == null) {
    return 'Not published'
  }
  return formatInr(line.amount_inr)
}

export function QuotationBreakdown({ quotation, compact = false }) {
  if (!quotation) return null

  const { lines, tax, estimated_total_inr, has_unknown_charges, disclaimer } = quotation

  return (
    <div className={`quotation-breakdown ${compact ? 'quotation-breakdown--compact' : ''}`}>
      {!compact && (
        <p className="quotation-disclaimer muted">{disclaimer}</p>
      )}
      <table className="quotation-table">
        <tbody>
          {lines.map((line) => (
            <tr key={line.code} className={line.status === 'unknown' ? 'quotation-unknown' : ''}>
              <td>
                {line.label}
                {line.note && <span className="block-text muted">{line.note}</span>}
                <span className="quotation-source muted">
                  {line.source === 'supplier' ? 'Supplier rate' : 'Calculated'}
                </span>
              </td>
              <td className="quotation-amount">{lineAmount(line)}</td>
            </tr>
          ))}
          {tax && (
            <tr className={tax.status === 'unknown' ? 'quotation-unknown' : ''}>
              <td>
                GST
                {tax.gst_rate_percent != null && ` (${tax.gst_rate_percent}%)`}
                {tax.note && <span className="block-text muted">{tax.note}</span>}
              </td>
              <td className="quotation-amount">
                {tax.gst_amount_inr != null ? formatInr(tax.gst_amount_inr) : 'Not included'}
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div className="quotation-total-row">
        <span>Estimated total{has_unknown_charges ? ' (partial)' : ''}</span>
        <strong>{formatInr(estimated_total_inr)}</strong>
      </div>
      {has_unknown_charges && (
        <p className="field-hint">
          Total excludes unpublished pump, transport or tax charges — final cost may be higher.
        </p>
      )}
      {quotation.estimated_lead_time_hours != null && (
        <p className="muted field-hint">
          Est. lead time: {quotation.estimated_lead_time_hours} hours
          {quotation.quotation_valid_days != null &&
            ` · Quote validity: ${quotation.quotation_valid_days} days`}
        </p>
      )}
    </div>
  )
}
