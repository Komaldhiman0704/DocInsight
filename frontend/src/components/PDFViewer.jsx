import React, { useState, useEffect } from 'react'
import { X, ZoomIn, ZoomOut, Loader } from 'lucide-react'

// ── PDF Blob Cache (global across all component instances) ──────────────────
// Significantly speeds up re-opening the same PDF
const pdfBlobCache = new Map()

export default function PDFViewer({ filename, docPath, onClose }) {
  const [scale, setScale] = useState(100)
  const [error, setError] = useState(null)
  const [blobUrl, setBlobUrl] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch PDF as blob to avoid Chrome cross-origin iframe blocking
    const fetchPDF = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Check cache first (instant load if cached)
        const cacheKey = docPath
        if (pdfBlobCache.has(cacheKey)) {
          console.log('📦 PDF loaded from cache:', filename)
          setBlobUrl(pdfBlobCache.get(cacheKey))
          setLoading(false)
          return
        }
        
        // Not in cache, fetch from server
        const response = await fetch(docPath)
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const blob = await response.blob()
        
        // Verify it's actually a PDF
        if (!blob.type.includes('pdf') && !blob.type.includes('application')) {
          throw new Error('Invalid file type: not a PDF')
        }
        
        const url = URL.createObjectURL(blob)
        
        // Cache the blob URL for future opens
        pdfBlobCache.set(cacheKey, url)
        console.log('💾 PDF cached for future opens:', filename)
        
        setBlobUrl(url)
      } catch (err) {
        console.error('PDF fetch error:', err)
        setError(err.message || 'Failed to load PDF')
      } finally {
        setLoading(false)
      }
    }

    fetchPDF()

    // Note: Don't revoke cached URLs on unmount
    // They'll be reused when the same PDF is opened again
    // This dramatically improves UX for re-opening PDFs
  }, [docPath, filename])

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 10, 200))
  }

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 10, 50))
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[var(--bg-primary)] rounded-lg shadow-2xl w-full h-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
          <div className="flex-1 min-w-0">
            <h2 className="text-sm font-semibold text-[var(--text-primary)] truncate">
              {filename}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleZoomOut}
              disabled={loading}
              className="p-1.5 hover:bg-[var(--bg-secondary)] rounded-lg transition-colors disabled:opacity-50"
              title="Zoom out"
            >
              <ZoomOut size={16} className="text-[var(--text-secondary)]" />
            </button>
            <span className="text-xs text-[var(--text-muted)] w-12 text-center">{scale}%</span>
            <button
              onClick={handleZoomIn}
              disabled={loading}
              className="p-1.5 hover:bg-[var(--bg-secondary)] rounded-lg transition-colors disabled:opacity-50"
              title="Zoom in"
            >
              <ZoomIn size={16} className="text-[var(--text-secondary)]" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-[var(--bg-secondary)] rounded-lg transition-colors ml-2"
              title="Close"
            >
              <X size={18} className="text-[var(--text-secondary)]" />
            </button>
          </div>
        </div>

        {/* PDF Container */}
        <div className="flex-1 overflow-auto flex items-center justify-center bg-[var(--bg-secondary)] p-4">
          {loading && (
            <div className="flex flex-col items-center gap-2 text-[var(--text-muted)]">
              <Loader size={24} className="animate-spin" />
              <p className="text-sm">Loading PDF...</p>
            </div>
          )}
          
          {error && !loading && (
            <div className="text-red-500 text-sm dark:text-red-400 max-w-sm text-center">
              <p className="font-semibold mb-1">⚠️ PDF Failed to Load</p>
              <p className="text-xs opacity-80">{error}</p>
              <p className="text-xs opacity-60 mt-2 break-all font-mono text-[11px]">{docPath}</p>
            </div>
          )}
          
          {blobUrl && !error && (
            <iframe
              src={`${blobUrl}#zoom=${scale}&toolbar=0&navpanes=0`}
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                borderRadius: '0.5rem',
              }}
              onError={() => setError('Failed to display PDF in iframe')}
              title={filename}
            />
          )}
        </div>
      </div>
    </div>
  )
}
