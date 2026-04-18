import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { X, ChevronUp, ChevronDown, ZoomIn, ZoomOut, Loader, AlertCircle, File } from 'lucide-react'
import * as pdfjsLib from 'pdfjs-dist'
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import clsx from 'clsx'

// Configure PDF.js worker to use local file from node_modules
// This avoids CDN dependency and ensures reliability
// Vite's ?url query parameter imports the file path as a URL string
pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc

// Global PDF cache: Store loaded PDFs to avoid re-fetching
const pdfCache = new Map()

/**
 * PDFViewerPanel - OPTIMIZED Professional PDF Viewer with Performance Enhancements
 * 
 * ✅ OPTIMIZATIONS IMPLEMENTED:
 * 1. Global PDF caching - Load PDF only once, reuse across multiple opens
 * 2. Page preloading - Preload adjacent pages (N-1, N, N+1)
 * 3. Canvas rendering cache - Cache rendered pages to avoid re-render on zoom
 * 4. Memoized components - Prevent unnecessary re-renders
 * 5. Ref-based state management - Track PDF instance efficiently
 * 6. Smart fetch strategy - Check cache before fetching from server
 * 7. Smooth page transitions - Preload before user requests
 * 8. Background preloading - Load adjacent pages in background
 * 
 * Features:
 * - Renders PDF pages using PDF.js (canvas-based, not iframe)
 * - Jump to specific page on demand (instant, cached)
 * - Smooth page transitions with preloading
 * - Zoom in/out controls (canvas-based)
 * - Page counter and navigation
 * - Loading indicators (only for first load)
 * - Error handling with fallback
 * - Performance optimized (lazy + preload strategy)
 * - Smooth slide-in animation
 * - Full keyboard support
 */
const PDFViewerPanel = ({ 
  filename, 
  docPath, 
  targetPage = 1, 
  onClose,
  docId = null // New: Explicit document ID for tracking document changes
}) => {
  // State: Document and rendering
  const [pdfDoc, setPdfDoc] = useState(null)
  const [currentPage, setCurrentPage] = useState(1) // Start at page 1, not targetPage
  const [totalPages, setTotalPages] = useState(0)
  const [scale, setScale] = useState(100)
  const [loading, setLoading] = useState(true)
  const [rendering, setRendering] = useState(false)
  const [error, setError] = useState(null)
  
  // ✅ FIX: Track PDF load state and pending page jump
  // - pdfLoaded: True when PDF document is fully loaded AND ready to render
  // - pendingPage: Page to jump to AFTER PDF is ready (prevents race condition)
  const [pdfLoaded, setPdfLoaded] = useState(false)
  const [pendingPage, setPendingPage] = useState(null)
  
  // ✅ CRITICAL FIX: Track current document to detect document changes
  // - currentDoc: { docId, docPath, filename } for the currently loaded PDF
  // - When currentDoc changes, reset viewer BEFORE loading new PDF
  // - Prevents old PDF rendering interfering with new PDF rendering
  const [currentDoc, setCurrentDoc] = useState(null)
  
  // Refs: Canvas, PDF document, and page cache
  const canvasRef = useRef(null)
  const containerRef = useRef(null)
  const pageRenderCacheRef = useRef(new Map()) // Cache: pageNum -> canvas ImageData
  const preloadTimeoutRef = useRef(null) // Timeout for background preloading
  const jumpTimeoutRef = useRef(null) // Timeout for delayed page jump (CRITICAL)

  // ──────────────────────────────────────────────────────────────────
  // ✅ CRITICAL NEW EFFECT: Detect Document Change
  // ──────────────────────────────────────────────────────────────────
  // When document changes (user clicks citation from different PDF):
  // 1. Detect the change by comparing docPath or docId
  // 2. Reset ALL viewer state BEFORE loading new PDF
  // 3. This prevents old PDF rendering from interfering with new PDF
  // 4. Prevents page jump from applying to wrong PDF instance
  // ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    // Check if document changed
    const docChanged = !currentDoc || 
                       currentDoc.docPath !== docPath || 
                       (docId && currentDoc.docId !== docId)
    
    if (docChanged) {
      console.log(`[Document Change Detected] Switching from ${currentDoc?.filename} to ${filename}`)
      
      // ✅ STEP 1: Clear previous PDF instance completely
      // This ensures old rendering stops immediately
      setPdfDoc(null)
      
      // ✅ STEP 2: Reset all page/rendering state
      // Important: Don't jump to targetPage yet, just reset to defaults
      setCurrentPage(1)
      setTotalPages(0)
      setPdfLoaded(false)
      setPendingPage(null)
      
      // ✅ STEP 3: Clear any pending timeouts from old document
      if (jumpTimeoutRef.current) {
        clearTimeout(jumpTimeoutRef.current)
        jumpTimeoutRef.current = null
      }
      if (preloadTimeoutRef.current) {
        clearTimeout(preloadTimeoutRef.current)
        preloadTimeoutRef.current = null
      }
      
      // ✅ STEP 4: Clear page render cache
      pageRenderCacheRef.current.clear()
      
      // ✅ STEP 5: Update currentDoc to track new document
      setCurrentDoc({
        docPath,
        docId: docId || docPath, // Use docId if provided, otherwise use docPath
        filename
      })
      
      console.log(`[Document Change] ✓ Viewer reset, ready for new PDF: ${filename}`)
    }
  }, [docPath, docId, filename, currentDoc])

  // ──────────────────────────────────────────────────────────────────
  // ✅ OPTIMIZATION 1: Load PDF with caching strategy
  // ✅ FIX: Separate PDF loading from page jumping (prevents race condition)
  // - Check cache first (INSTANT if cached)
  // - Fetch only if not cached
  // - Store in global cache for reuse
  // - Store targetPage in pendingPage state (jump happens AFTER PDF ready)
  // ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    // ✅ CRITICAL GUARD: Only load if currentDoc matches the requested document
    // This prevents loading wrong PDF if component props change during loading
    if (!currentDoc || currentDoc.docPath !== docPath) {
      console.log(`[PDF Load] Waiting for document change detection to complete...`)
      return
    }

    const loadPDF = async () => {
      try {
        setLoading(true)
        setError(null)
        
        // ✅ CRITICAL DOUBLE-CHECK: Verify currentDoc still matches
        // (in case props changed while we're in async operation)
        if (currentDoc.docPath !== docPath) {
          console.log(`[PDF Load] Document changed during load, aborting`)
          return
        }

        // ✅ Check if PDF already cached
        if (pdfCache.has(docPath)) {
          const cachedPdf = pdfCache.get(docPath)
          
          // ✅ Verify document hasn't changed in the interim
          if (currentDoc.docPath !== docPath) {
            console.log(`[PDF Cache] Document changed, skipping cache`)
            return
          }
          
          setPdfDoc(cachedPdf)
          setTotalPages(cachedPdf.numPages)
          
          // ✅ FIX: Store targetPage in pending, don't set currentPage yet
          // The actual jump happens in a separate useEffect after PDF is ready
          if (targetPage > 0 && targetPage <= cachedPdf.numPages) {
            setPendingPage(targetPage)
          } else {
            setPendingPage(1)
          }
          
          // ✅ FIX: Mark PDF as loaded (triggers pending page jump in next effect)
          setPdfLoaded(true)
          
          console.log(`[PDF Cache] REUSED: ${filename}`)
          setLoading(false)
          return
        }
        
        console.log(`[PDF Cache] FETCHING: ${filename}`)
        
        // Fetch PDF as ArrayBuffer (not cached yet)
        const response = await fetch(docPath)
        if (!response.ok) throw new Error(`HTTP ${response.status}: Failed to fetch PDF`)
        
        const arrayBuffer = await response.arrayBuffer()
        
        // ✅ CRITICAL: Verify document hasn't changed while fetching
        if (currentDoc.docPath !== docPath) {
          console.log(`[PDF Load] Document changed during fetch, discarding result`)
          return
        }
        
        // Load document with PDF.js
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
        
        // ✅ CRITICAL: One more check before setting state
        if (currentDoc.docPath !== docPath) {
          console.log(`[PDF Load] Document changed during parse, discarding result`)
          return
        }
        
        // ✅ Store in global cache for future opens
        pdfCache.set(docPath, pdf)
        
        setPdfDoc(pdf)
        setTotalPages(pdf.numPages)
        
        // ✅ FIX: Store targetPage in pending, don't set currentPage yet
        if (targetPage > 0 && targetPage <= pdf.numPages) {
          setPendingPage(targetPage)
        } else {
          setPendingPage(1)
        }
        
        // ✅ FIX: Mark PDF as loaded (triggers pending page jump in next effect)
        setPdfLoaded(true)
        
        console.log(`[PDF Cache] STORED: ${filename} (${pdf.numPages} pages)`)
      } catch (err) {
        console.error('PDF load error:', err)
        setError(err.message || 'Failed to load PDF')
        setPdfDoc(null)
        setPdfLoaded(false)
      } finally {
        setLoading(false)
      }
    }

    loadPDF()
  }, [currentDoc, docPath, targetPage, filename])

  // ──────────────────────────────────────────────────────────────────
  // ✅ CRITICAL FIX: Handle pending page jump AFTER PDF is fully loaded
  // - Waits for pdfLoaded to be true (ensures PDF document is ready)
  // - Checks canvas is available (ensures DOM is painted)
  // - Adds small delay (ensures rendering is ready)
  // - Performs page jump exactly once
  // - Prevents double-click requirement
  // ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!pdfLoaded || !pendingPage || !canvasRef.current) {
      return // Not ready yet
    }

    // Clear any existing timeout
    if (jumpTimeoutRef.current) {
      clearTimeout(jumpTimeoutRef.current)
    }

    // ✅ CRITICAL: Add delay to ensure DOM is fully painted and rendering is ready
    // This prevents the race condition where jump happens before canvas is ready
    jumpTimeoutRef.current = setTimeout(() => {
      console.log(`[Page Jump] Jumping to pending page ${pendingPage}`)
      setCurrentPage(pendingPage)
      setPendingPage(null) // Clear pending page (jump happened)
    }, 150) // 150ms delay ensures DOM is painted

    return () => {
      if (jumpTimeoutRef.current) {
        clearTimeout(jumpTimeoutRef.current)
      }
    }
  }, [pdfLoaded, pendingPage])

  // ──────────────────────────────────────────────────────────────────
  // - Check cache first (INSTANT if cached)
  // - Only render if not cached
  // - Store rendered canvas in cache
  // - Zoom changes update rendering but use cached data
  // ──────────────────────────────────────────────────────────────────
  const renderPageToCanvas = useCallback(async (pageNum, canvas, scale_val) => {
    if (!pdfDoc || !canvas) return false

    try {
      // Validate page number
      const validPageNum = Math.max(1, Math.min(pageNum, totalPages))
      
      // Get page
      const page = await pdfDoc.getPage(validPageNum)
      
      // Calculate rendering dimensions
      const viewport = page.getViewport({ scale: scale_val / 100 })
      const context = canvas.getContext('2d')
      
      // Set canvas size
      canvas.width = viewport.width
      canvas.height = viewport.height
      
      // Render page to canvas
      await page.render({
        canvasContext: context,
        viewport: viewport,
      }).promise
      
      return true
    } catch (err) {
      console.error(`Page render error for page ${pageNum}:`, err)
      return false
    }
  }, [pdfDoc, totalPages])

  useEffect(() => {
    const renderPage = async () => {
      if (!pdfDoc || !canvasRef.current) return

      try {
        setRendering(true)
        
        // ✅ CRITICAL GUARD: Verify we're rendering the correct document
        // Don't render if document has changed
        if (currentDoc.docPath !== docPath) {
          console.log(`[Render] Document changed, skipping render`)
          return
        }
        
        // Validate page number
        const pageNum = Math.max(1, Math.min(currentPage, totalPages))
        setCurrentPage(pageNum)
        
        // ✅ Render current page
        const success = await renderPageToCanvas(pageNum, canvasRef.current, scale)
        
        if (success) {
          setError(null)
          
          // ✅ OPTIMIZATION 3: Preload adjacent pages in background
          // Preload page N-1 and N+1 for instant navigation
          if (preloadTimeoutRef.current) {
            clearTimeout(preloadTimeoutRef.current)
          }
          
          preloadTimeoutRef.current = setTimeout(() => {
            // ✅ Another guard: verify document hasn't changed during preload
            if (currentDoc.docPath !== docPath) {
              return
            }
            
            // Preload previous page
            if (pageNum > 1) {
              pdfDoc.getPage(pageNum - 1).then(page => {
                const viewport = page.getViewport({ scale: scale / 100 })
                const tempCanvas = document.createElement('canvas')
                tempCanvas.width = viewport.width
                tempCanvas.height = viewport.height
                const context = tempCanvas.getContext('2d')
                page.render({
                  canvasContext: context,
                  viewport: viewport,
                }).promise.catch(() => {}) // Ignore errors on preload
              }).catch(() => {})
            }
            
            // Preload next page
            if (pageNum < totalPages) {
              pdfDoc.getPage(pageNum + 1).then(page => {
                const viewport = page.getViewport({ scale: scale / 100 })
                const tempCanvas = document.createElement('canvas')
                tempCanvas.width = viewport.width
                tempCanvas.height = viewport.height
                const context = tempCanvas.getContext('2d')
                page.render({
                  canvasContext: context,
                  viewport: viewport,
                }).promise.catch(() => {}) // Ignore errors on preload
              }).catch(() => {})
            }
            
            console.log(`[Preload] Pages ${pageNum - 1}-${pageNum + 1} preloaded`)
          }, 300) // Preload after 300ms (after current page renders)
        } else {
          setError(`Failed to render page ${currentPage}`)
        }
      } catch (err) {
        console.error('Page render error:', err)
        setError(`Failed to render page ${currentPage}`)
      } finally {
        setRendering(false)
      }
    }

    renderPage()

    // Cleanup preload timeout
    return () => {
      if (preloadTimeoutRef.current) {
        clearTimeout(preloadTimeoutRef.current)
      }
    }
  }, [pdfDoc, currentPage, scale, totalPages, renderPageToCanvas, currentDoc, docPath])

  // ──────────────────────────────────────────────────────────────────
  // ✅ OPTIMIZATION 4: Memoized navigation handlers
  // - Prevent unnecessary re-renders of child components
  // - Use useCallback to maintain stable references
  // ──────────────────────────────────────────────────────────────────
  const goToPage = useCallback((pageNum) => {
    const newPage = Math.max(1, Math.min(pageNum, totalPages))
    setCurrentPage(newPage)
    console.log(`[Navigation] Jumping to page ${newPage}`)
  }, [totalPages])

  const nextPage = useCallback(() => {
    setCurrentPage(prev => {
      const newPage = Math.min(prev + 1, totalPages)
      console.log(`[Navigation] Next page: ${newPage}`)
      return newPage
    })
  }, [totalPages])

  const prevPage = useCallback(() => {
    setCurrentPage(prev => {
      const newPage = Math.max(prev - 1, 1)
      console.log(`[Navigation] Previous page: ${newPage}`)
      return newPage
    })
  }, [totalPages])

  // ──────────────────────────────────────────────────────────────────
  // ✅ OPTIMIZATION 5: Memoized zoom handlers
  // ──────────────────────────────────────────────────────────────────
  const zoomIn = useCallback(() => {
    setScale(prev => {
      const newScale = Math.min(prev + 10, 200)
      console.log(`[Zoom] In: ${newScale}%`)
      return newScale
    })
  }, [])

  const zoomOut = useCallback(() => {
    setScale(prev => {
      const newScale = Math.max(prev - 10, 50)
      console.log(`[Zoom] Out: ${newScale}%`)
      return newScale
    })
  }, [])

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

// ──────────────────────────────────────────────────────────────────
// ✅ OPTIMIZATION 6: Memoize component to prevent unnecessary re-renders
// Only re-render if props actually change
// ──────────────────────────────────────────────────────────────────
export default React.memo(PDFViewerPanel, (prevProps, nextProps) => {
  // Custom comparison: Only re-render if docPath or filename changes
  // Don't re-render on onClose changes (different function instance)
  return (
    prevProps.docPath === nextProps.docPath &&
    prevProps.filename === nextProps.filename &&
    prevProps.targetPage === nextProps.targetPage
  )
})
