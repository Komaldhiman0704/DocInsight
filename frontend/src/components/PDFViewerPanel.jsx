import React, { useState, useEffect, useRef, useCallback } from 'react'
import { X, ChevronUp, ChevronDown, ZoomIn, ZoomOut, Loader, AlertCircle, File } from 'lucide-react'
import * as pdfjsLib from 'pdfjs-dist'
import clsx from 'clsx'

// Set up PDF.js worker with proper HTTPS protocol
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`

/**
 * PDFViewerPanel - Professional PDF Viewer with Page Jump (Citation-based Navigation)
 * 
 * Features:
 * - Renders PDF pages using PDF.js
 * - Jump to specific page on demand
 * - Smooth page transitions
 * - Zoom in/out controls
 * - Page counter and navigation
 * - Loading indicators
 * - Error handling with fallback
 * - Performance optimized (lazy page rendering)
 * - Smooth slide-in animation
 * - Full keyboard support
 */
export default function PDFViewerPanel({ 
  filename, 
  docPath, 
  targetPage = 1, 
  onClose 
}) {
  // State: Document and rendering
  const [pdfDoc, setPdfDoc] = useState(null)
  const [currentPage, setCurrentPage] = useState(targetPage)
  const [totalPages, setTotalPages] = useState(0)
  const [scale, setScale] = useState(100)
  const [loading, setLoading] = useState(true)
  const [rendering, setRendering] = useState(false)
  const [error, setError] = useState(null)
  
  // Refs: Canvas and PDF document
  const canvasRef = useRef(null)
  const containerRef = useRef(null)

  // ──────────────────────────────────────────────────────────────────
  // Load PDF document on mount or when docPath changes
  // ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    const loadPDF = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // Fetch PDF as ArrayBuffer
        const response = await fetch(docPath)
        if (!response.ok) throw new Error(`HTTP ${response.status}: Failed to fetch PDF`)
        
        const arrayBuffer = await response.arrayBuffer()
        
        // Load document with PDF.js
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
        setPdfDoc(pdf)
        setTotalPages(pdf.numPages)
        
        // Jump to target page if specified
        if (targetPage > 0 && targetPage <= pdf.numPages) {
          setCurrentPage(targetPage)
        } else {
          setCurrentPage(1)
        }
      } catch (err) {
        console.error('PDF load error:', err)
        setError(err.message || 'Failed to load PDF')
        setPdfDoc(null)
      } finally {
        setLoading(false)
      }
    }

    loadPDF()
  }, [docPath, targetPage])

  // ──────────────────────────────────────────────────────────────────
  // Render the current page on canvas
  // ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    const renderPage = async () => {
      if (!pdfDoc || !canvasRef.current) return

      try {
        setRendering(true)
        
        // Validate page number
        const pageNum = Math.max(1, Math.min(currentPage, totalPages))
        setCurrentPage(pageNum)
        
        // Get page
        const page = await pdfDoc.getPage(pageNum)
        
        // Calculate rendering dimensions
        const viewport = page.getViewport({ scale: scale / 100 })
        const canvas = canvasRef.current
        const context = canvas.getContext('2d')
        
        // Set canvas size
        canvas.width = viewport.width
        canvas.height = viewport.height
        
        // Render page to canvas
        await page.render({
          canvasContext: context,
          viewport: viewport,
        }).promise
        
        setError(null)
      } catch (err) {
        console.error('Page render error:', err)
        setError(`Failed to render page ${currentPage}`)
      } finally {
        setRendering(false)
      }
    }

    renderPage()
  }, [pdfDoc, currentPage, scale, totalPages])

  // ──────────────────────────────────────────────────────────────────
  // Navigation handlers
  // ──────────────────────────────────────────────────────────────────
  const goToPage = useCallback((pageNum) => {
    const newPage = Math.max(1, Math.min(pageNum, totalPages))
    setCurrentPage(newPage)
  }, [totalPages])

  const nextPage = useCallback(() => {
    goToPage(currentPage + 1)
  }, [currentPage, goToPage])

  const prevPage = useCallback(() => {
    goToPage(currentPage - 1)
  }, [currentPage, goToPage])

  // ──────────────────────────────────────────────────────────────────
  // Zoom handlers
  // ──────────────────────────────────────────────────────────────────
  const zoomIn = () => {
    setScale(prev => Math.min(prev + 10, 200))
  }

  const zoomOut = () => {
    setScale(prev => Math.max(prev - 10, 50))
  }

  // ──────────────────────────────────────────────────────────────────
  // Keyboard navigation
  // ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault()
        nextPage()
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault()
        prevPage()
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      } else if (e.key === '+' || e.key === '=') {
        e.preventDefault()
        zoomIn()
      } else if (e.key === '-') {
        e.preventDefault()
        zoomOut()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [nextPage, prevPage, onClose])

  // ──────────────────────────────────────────────────────────────────
  // Render: Main UI
  // ──────────────────────────────────────────────────────────────────
  return (
    <>
      {/* Backdrop - dismisses on click */}
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel - Slides in from right */}
      <div
        ref={containerRef}
        className={clsx(
          'fixed inset-y-0 right-0 w-full max-w-2xl bg-[var(--bg-primary)] shadow-2xl z-50',
          'flex flex-col animate-slide-in-right',
          'border-l border-[var(--border)]'
        )}
      >
        {/* ── Header ────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-secondary)] shrink-0">
          {/* Document info */}
          <div className="flex-1 min-w-0 flex items-center gap-2">
            <File size={18} className="text-[var(--accent)] shrink-0" />
            <h2 className="text-sm font-semibold text-[var(--text-primary)] truncate">
              {filename}
            </h2>
          </div>

          {/* Page counter */}
          <div className="flex items-center gap-3 px-3 py-1 rounded-lg bg-[var(--bg-primary)] text-xs font-medium text-[var(--text-muted)]">
            <span>{currentPage}</span>
            <span className="text-[10px]">/</span>
            <span>{totalPages}</span>
          </div>

          {/* Close button */}
          <button
            onClick={onClose}
            className="ml-2 p-1.5 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
            title="Close (Esc)"
            aria-label="Close PDF viewer"
          >
            <X size={18} className="text-[var(--text-secondary)]" />
          </button>
        </div>

        {/* ── Controls ──────────────────────────────────────────────── */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border)] bg-[var(--bg-secondary)] shrink-0">
          {/* Navigation buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={prevPage}
              disabled={currentPage <= 1 || loading || rendering}
              className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              title="Previous page (←)"
              aria-label="Previous page"
            >
              <ChevronUp size={16} className="text-[var(--text-secondary)]" />
            </button>
            <button
              onClick={nextPage}
              disabled={currentPage >= totalPages || loading || rendering}
              className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              title="Next page (→)"
              aria-label="Next page"
            >
              <ChevronDown size={16} className="text-[var(--text-secondary)]" />
            </button>
          </div>

          {/* Zoom controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={zoomOut}
              disabled={scale <= 50 || loading || rendering}
              className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              title="Zoom out (−)"
              aria-label="Zoom out"
            >
              <ZoomOut size={16} className="text-[var(--text-secondary)]" />
            </button>
            <span className="text-xs text-[var(--text-muted)] w-12 text-center font-mono">
              {scale}%
            </span>
            <button
              onClick={zoomIn}
              disabled={scale >= 200 || loading || rendering}
              className="p-1.5 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              title="Zoom in (+)"
              aria-label="Zoom in"
            >
              <ZoomIn size={16} className="text-[var(--text-secondary)]" />
            </button>
          </div>

          {/* Status indicator */}
          {rendering && (
            <div className="flex items-center gap-1.5 text-[var(--text-muted)] text-xs">
              <Loader size={12} className="animate-spin" />
              <span>Rendering...</span>
            </div>
          )}
        </div>

        {/* ── Content Area ──────────────────────────────────────────── */}
        <div className="flex-1 overflow-auto bg-[var(--bg-primary)] flex items-center justify-center p-4">
          {/* Loading state */}
          {loading && (
            <div className="flex flex-col items-center gap-3 text-[var(--text-muted)]">
              <Loader size={28} className="animate-spin text-[var(--accent)]" />
              <p className="text-sm font-medium">Loading PDF...</p>
              <p className="text-xs opacity-70">Preparing {filename}</p>
            </div>
          )}

          {/* Error state */}
          {error && !loading && (
            <div className="flex flex-col items-center gap-2 text-center max-w-sm">
              <div className="p-3 rounded-lg bg-red-500/10 text-red-500 dark:text-red-400">
                <AlertCircle size={24} />
              </div>
              <p className="font-semibold text-sm text-red-500 dark:text-red-400">
                Failed to display PDF
              </p>
              <p className="text-xs text-[var(--text-muted)] break-all">
                {error}
              </p>
              <p className="text-xs text-[var(--text-muted)] opacity-70 mt-2">
                Path: {docPath}
              </p>
            </div>
          )}

          {/* Canvas: PDF page rendering */}
          {pdfDoc && !error && (
            <div className="flex flex-col items-center justify-center">
              <canvas
                ref={canvasRef}
                className={clsx(
                  'max-w-full max-h-full rounded-sm shadow-lg',
                  'border border-[var(--border)]',
                  rendering && 'opacity-50 transition-opacity'
                )}
                style={{
                  transition: 'opacity 0.2s ease-in-out',
                }}
              />
              
              {/* Page highlight animation (brief flash when jumping) */}
              {rendering && (
                <div className="fixed inset-0 pointer-events-none z-50">
                  <div className="absolute inset-0 bg-yellow-300/5 animate-pulse-fade" />
                </div>
              )}
            </div>
          )}

          {/* Empty state (shouldn't happen) */}
          {!pdfDoc && !loading && !error && (
            <div className="text-center text-[var(--text-muted)]">
              <p className="text-sm">No PDF loaded</p>
            </div>
          )}
        </div>

        {/* ── Footer: Keyboard Shortcuts ────────────────────────────── */}
        <div className="px-4 py-2 border-t border-[var(--border)] bg-[var(--bg-secondary)] text-[10px] text-[var(--text-muted)] shrink-0">
          <p className="text-[9px] opacity-60">
            💡 Keyboard: ← → (navigate) | + − (zoom) | Esc (close)
          </p>
        </div>
      </div>

      {/* Global style: slide-in animation */}
      <style>{`
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
        @keyframes pulse-fade {
          0%, 100% { opacity: 0; }
          50% { opacity: 1; }
        }
        .animate-pulse-fade {
          animation: pulse-fade 0.6s ease-in-out;
        }
      `}</style>
    </>
  )
}
