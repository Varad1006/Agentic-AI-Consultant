export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

function describeDetail(detail) {
  if (!detail) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ')
  return JSON.stringify(detail)
}

async function request(path, options) {
  let response
  try {
    response = await fetch(`${API_URL}${path}`, options)
  } catch {
    throw new ApiError(`Can't reach the API at ${API_URL}. Is the backend running?`, 0)
  }
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new ApiError(describeDetail(body.detail) || `Request failed (${response.status})`, response.status)
  }
  return body
}

const postJson = (path, payload) =>
  request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

export const api = {
  health: () => request('/api/v1/health'),
  uploadDocument: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/api/v1/upload', { method: 'POST', body: form })
  },
  submitText: (text) => postJson('/api/v1/consult', { document_text: text }),
  getJob: (jobId) => request(`/api/v1/consult/${jobId}`),
  getReportMarkdown: (jobId) => request(`/api/v1/consult/${jobId}/report`),
  ask: (jobId, question) => postJson(`/api/v1/consult/${jobId}/chat`, { question }),
}
