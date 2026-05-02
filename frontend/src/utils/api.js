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

// ── Get Document Summary ───────────────────────────────────────────────────────
export async function getDocumentSummary(docId) {
  const res = await fetch(`${BASE}/documents/${docId}/summary`)
  if (!res.ok) throw new Error('Failed to fetch summary')
  return res.json()
}

// ── Stream Chat (SSE) ─────────────────────────────────────────────────────────
// Yields { type: 'sources', sources: [...] } then { type: 'token', token: '...' }
export async function* streamChat({ question, chatHistory, docIds, sessionId }) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      chat_history: chatHistory,
      doc_ids: docIds?.length ? docIds : null,
      session_id: sessionId || null,
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
            const sourcesData = JSON.parse(rawData)
            // Handle both old format (array) and new format (object)
            if (Array.isArray(sourcesData)) {
              yield { type: 'sources', sources: sourcesData }
            } else {
              yield { 
                type: 'sources', 
                sources: sourcesData.sources || [],
                confidence: sourcesData.confidence,
                relevance_score: sourcesData.relevance_score,
                source_count: sourcesData.source_count,
              }
            }
          } catch {}
          i += 2
          continue
        }

        // ✅ PHASE 3-4: Handle semantically enhanced sources (improve after answer generation)
        if (eventType === 'sources_enhanced') {
          try {
            const enhancedData = JSON.parse(rawData)
            // Pass enhanced sources to frontend
            if (enhancedData.sources) {
              yield { 
                type: 'sources_enhanced',
                sources: enhancedData.sources,
              }
            }
          } catch (e) {
            console.debug('Failed to parse enhanced sources', e)
          }
          i += 2
          continue
        }

        if (eventType === 'suggestions') {
          try {
            const suggestions = JSON.parse(rawData)
            yield { type: 'suggestions', suggestions }
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

// ── Chat Sessions ─────────────────────────────────────────────────────────────
export async function listSessions() {
  const res = await fetch(`${BASE}/sessions`)
  if (!res.ok) throw new Error('Failed to fetch sessions')
  return res.json()
}

export async function createSession(docIds = []) {
  const res = await fetch(`${BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ doc_ids: docIds }),
  })
  if (!res.ok) throw new Error('Failed to create session')
  return res.json()
}

export async function getSession(sessionId) {
  const res = await fetch(`${BASE}/sessions/${sessionId}`)
  if (!res.ok) throw new Error('Failed to fetch session')
  return res.json()
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${BASE}/sessions/${sessionId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete session')
  return res.json()
}

export async function renameSession(sessionId, title) {
  const res = await fetch(`${BASE}/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  })
  if (!res.ok) throw new Error('Failed to rename session')
  return res.json()
}

// ── Export Chat as PDF ─────────────────────────────────────────────────────────
export async function exportChatAsPDF(sessionId) {
  const res = await fetch(`${BASE}/chat/export?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  })
  
  if (!res.ok) {
    throw new Error('Failed to export chat')
  }
  
  // Get filename from Content-Disposition header
  const contentDisposition = res.headers.get('content-disposition')
  let filename = `chat_export_${sessionId}.pdf`
  if (contentDisposition && contentDisposition.includes('filename=')) {
    filename = contentDisposition.split('filename=')[1].replace(/"/g, '')
  }
  
  // Get PDF blob and trigger download
  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
