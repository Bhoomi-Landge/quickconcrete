/** Local-date helpers for delivery scheduling (browser local timezone). */

export function todayIsoDate() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

/** Normalize API time "10:00" or "10:00 AM" to HH:MM for <input type="time"> */
export function normalizeTimeForInput(value) {
  if (!value) return ''
  const trimmed = String(value).trim()
  const match24 = trimmed.match(/^(\d{1,2}):(\d{2})$/)
  if (match24) {
    const h = Number(match24[1])
    const m = match24[2]
    if (h >= 0 && h <= 23) return `${String(h).padStart(2, '0')}:${m}`
  }
  return trimmed.slice(0, 5)
}

/** Minimum selectable time (HH:MM) when delivery is today — next 15-minute slot after now. */
export function minTimeForDate(isoDate) {
  if (isoDate !== todayIsoDate()) return ''
  const now = new Date()
  const minutes = now.getHours() * 60 + now.getMinutes() + 15
  const h = Math.floor(minutes / 60) % 24
  const m = Math.floor((minutes % 60) / 15) * 15
  if (h >= 24) return '23:45'
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

export function isTimeBeforeMin(timeValue, minTime) {
  if (!minTime || !timeValue) return false
  const [th, tm] = timeValue.split(':').map(Number)
  const [mh, mm] = minTime.split(':').map(Number)
  return th * 60 + tm < mh * 60 + mm
}

export function defaultDeliveryTimeForDate(isoDate) {
  const min = minTimeForDate(isoDate)
  if (min) return min
  return '08:00'
}

export function formatTimeLabel(hhmm) {
  if (!hhmm) return ''
  const [h, m] = hhmm.split(':').map(Number)
  const period = h >= 12 ? 'PM' : 'AM'
  const hour12 = h % 12 === 0 ? 12 : h % 12
  return `${hour12}:${String(m).padStart(2, '0')} ${period}`
}
