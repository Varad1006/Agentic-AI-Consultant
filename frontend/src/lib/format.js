const compact = (value) => Math.abs(value) >= 10_000

export function formatCurrency(value) {
  if (value == null) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: compact(value) ? 'compact' : 'standard',
    maximumFractionDigits: compact(value) ? 1 : 0,
  }).format(value)
}

export function formatNumber(value, maximumFractionDigits = 1) {
  if (value == null) return '—'
  return new Intl.NumberFormat('en-US', {
    notation: compact(value) ? 'compact' : 'standard',
    maximumFractionDigits,
  }).format(value)
}

export function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export function formatDateTime(iso) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function formatDuration(totalSeconds) {
  const seconds = Math.max(0, Math.floor(totalSeconds))
  const minutes = Math.floor(seconds / 60)
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
}
