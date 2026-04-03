// ── API utility — all calls to FastAPI backend ─────────────────────────────
const BASE = '/api'

// ── Upload PDF ────────────────────────────────────────────────────────────────
export async function uploadPDF(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)

  const xhr = new XMLHttpRequest()

  return new Promise((resolve, reject) => {
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        try {
          const err = JSON.parse(xhr.responseText)
          reject(new Error(err.detail || 'Upload failed'))
        } catch {
          reject(new Error('Upload failed: ' + xhr.statusText))
        }
      }
    }
    xhr.onerror = () => reject(new Error('Network error — is the backend running?'))
    xhr.open('POST', `${BASE}/upload`)
    xhr.send(formData)
  })
}

// ── List Documents ────────────────────────────────────────────────────────────
export async function listDocuments() {
  const res = await fetch(`${BASE}/documents`)
  if (!res.ok) throw new Error('Failed to fetch documents')
  return res.json()
}

// ── Delete Document ───────────────────────────────────────────────────────────
export async function deleteDocument(docId) {
  const res = await fetch(`${BASE}/documents/${docId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete document')
  return res.json()
}

// ── Stream Chat (SSE) ─────────────────────────────────────────────────────────
// Yields { type: 'sources', sources: [...] } then { type: 'token', token: '...' }
export async function* streamChat({ question, chatHistory, docIds }) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      chat_history: chatHistory,
      doc_ids: docIds?.length ? docIds : null,
    }),
  })

  if (!res.ok) {
    let errMsg = 'Chat request failed'
    try {
      const err = await res.json()
      errMsg = err.detail || errMsg
    } catch {}
    throw new Error(errMsg)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? '' // Keep incomplete last line

    let i = 0
    while (i < lines.length) {
      const line = lines[i]

      // SSE event type line
      if (line.startsWith('event: ')) {
        const eventType = line.slice(7).trim()
        // Next line should be the data
        const dataLine = lines[i + 1] ?? ''
        const rawData = dataLine.startsWith('data: ') ? dataLine.slice(6) : dataLine

        if (eventType === 'sources') {
          try {
            const sources = JSON.parse(rawData)
            yield { type: 'sources', sources }
          } catch {}
          i += 2
          continue
        }
        if (eventType === 'done') {
          return
        }
        if (eventType === 'error') {
          try {
            const errData = JSON.parse(rawData)
            throw new Error(errData.error || 'Stream error')
          } catch (e) {
            throw e
          }
        }
        i += 2
        continue
      }

      // Plain data line (token)
      if (line.startsWith('data: ')) {
        const raw = line.slice(6)
        if (!raw || raw === '{}') { i++; continue }
        try {
          const parsed = JSON.parse(raw)
          if (parsed.token !== undefined) {
            yield { type: 'token', token: parsed.token }
          }
        } catch {}
      }

      i++
    }
  }
}

// ── Regular (non-streaming) Chat ──────────────────────────────────────────────
export async function sendChat({ question, chatHistory, docIds }) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      chat_history: chatHistory,
      doc_ids: docIds?.length ? docIds : null,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Chat failed')
  }
  return res.json()
}
