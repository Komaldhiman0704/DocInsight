import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Moon, Sun, Trash2, ChevronLeft, ChevronRight, Download, ChevronDown } from 'lucide-react'
import { Toaster } from 'react-hot-toast'
import toast from 'react-hot-toast'

import { useDarkMode } from './hooks/useDarkMode'
import { listDocuments, streamChat, listSessions, createSession, getSession, deleteSession, renameSession, getDocumentSummary, exportChatAsPDF } from './utils/api'

import UploadZone from './components/UploadZone'
import DocumentList from './components/DocumentList'
import SessionList from './components/SessionList'
import DocumentSummaryCard from './components/DocumentSummaryCard'
import ChatMessage from './components/ChatMessage'
import ChatInput from './components/ChatInput'
import PDFViewer from './components/PDFViewer'
import PDFViewerPanel from './components/PDFViewerPanel'
import Logo from './components/Logo'

const SUGGESTIONS = [
  'Generate comprehensive summary',
  'Extract key findings',
  'Identify main topics',
  'Analyze document structure',
]

export default function App() {
  const [dark, setDark] = useDarkMode()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [sessionsExpanded, setSessionsExpanded] = useState(true)
  const [documentsExpanded, setDocumentsExpanded] = useState(true)

  const [documents, setDocuments] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [docsLoading, setDocsLoading] = useState(true)

  const [sessions, setSessions] = useState([])
  const [currentSessionId, setCurrentSessionId] = useState(null)
  const [sessionsLoading, setSessionsLoading] = useState(true)

  const [messages, setMessages] = useState([])
  const [chatting, setChatting] = useState(false)
  const messagesEndRef = useRef(null)

  const [documentSummary, setDocumentSummary] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  const [pdfOpen, setPdfOpen] = useState(false)
  const [pdfDoc, setPdfDoc] = useState(null)
  
  // New: PDF Viewer Panel with page jump support
  const [pdfPanelOpen, setPdfPanelOpen] = useState(false)
  const [pdfPanelDoc, setPdfPanelDoc] = useState(null)
  const [pdfTargetPage, setPdfTargetPage] = useState(1)

  useEffect(() => {
    loadDocuments()
    loadSessions()
  }, [])

  useEffect(() => {
    const scrollToBottom = () => {
      const timeout = setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' })
      }, 50)
      return () => clearTimeout(timeout)
    }
    
    scrollToBottom()
  }, [messages])

  // Fetch summary when exactly one document is selected
  useEffect(() => {
    async function fetchSummary() {
      if (selectedIds.length !== 1) {
        setDocumentSummary(null)
        return
      }

      setSummaryLoading(true)
      try {
        const data = await getDocumentSummary(selectedIds[0])
        setDocumentSummary(data)
      } catch (e) {
        console.warn('Could not fetch summary:', e)
        setDocumentSummary(null)
      } finally {
        setSummaryLoading(false)
      }
    }

    fetchSummary()
  }, [selectedIds])

  async function loadDocuments() {
    setDocsLoading(true)
    try {
      const data = await listDocuments()
      setDocuments(data.documents || [])
      setSelectedIds((data.documents || []).map(d => d.id))
    } catch {
      toast.error('Could not reach backend. Is it running?')
    } finally {
      setDocsLoading(false)
    }
  }

  async function loadSessions() {
    setSessionsLoading(true)
    try {
      const data = await listSessions()
      setSessions(data || [])
    } catch (e) {
      console.warn('Could not load sessions:', e)
    } finally {
      setSessionsLoading(false)
    }
  }

  async function handleNewSession() {
    try {
      const session = await createSession(selectedIds)
      setCurrentSessionId(session.id)
      setMessages([])
      await loadSessions()
    } catch (e) {
      toast.error(`Failed to create session: ${e.message}`)
    }
  }

  async function handleSelectSession(sessionId) {
    try {
      const session = await getSession(sessionId)
      setCurrentSessionId(sessionId)
      
      // Convert stored messages to chat format
      const chatMessages = session.messages.map((msg, i) => ({
        id: i,
        role: msg.role,
        content: msg.content,
        sources: msg.sources || [],
        suggestions: msg.suggestions || [],
        confidence: msg.confidence || null,
        relevance_score: msg.relevance_score || 0,
        source_count: msg.sources?.length || 0,
        status: 'done',
        timestamp: msg.timestamp,
      }))
      setMessages(chatMessages)
    } catch (e) {
      toast.error(`Failed to load session: ${e.message}`)
    }
  }

  async function handleDeleteSession(sessionId) {
    try {
      await deleteSession(sessionId)
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null)
        setMessages([])
      }
      await loadSessions()
    } catch (e) {
      throw e
    }
  }

  async function handleRenameSession(sessionId, newTitle) {
    try {
      await renameSession(sessionId, newTitle)
      await loadSessions()
    } catch (e) {
      throw e
    }
  }

  function handleDocumentUploaded(doc) {
    setDocuments(prev => [doc, ...prev])
    setSelectedIds(prev => [doc.id, ...prev])
    toast.success(`"${doc.filename}" ready!`, { icon: '📄' })
  }

  function handleDocumentDeleted(docId) {
    setDocuments(prev => prev.filter(d => d.id !== docId))
    setSelectedIds(prev => prev.filter(id => id !== docId))
  }

  function toggleDocument(docId) {
    setSelectedIds(prev =>
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    )
  }

  function clearChat() {
    if (messages.length === 0) return
    if (!confirm('Clear chat history?')) return
    setMessages([])
  }

  function buildHistory() {
    return messages
      .filter(m => m.status === 'done' || m.role === 'user')
      .slice(-10)
      .map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content }))
  }

  async function handleExportChat() {
    if (!currentSessionId) {
      toast.error('No active session to export')
      return
    }

    try {
      toast.loading('Generating PDF...', { id: 'pdf-export' })
      await exportChatAsPDF(currentSessionId)
      toast.success('Chat exported successfully!', { id: 'pdf-export' })
    } catch (err) {
      toast.error(`Export failed: ${err.message}`, { id: 'pdf-export' })
    }
  }

  function handleOpenPDF(doc) {
    // New: Use PDFViewerPanel for page jump support
    // doc can be: { id, filename } or { id, filename, page }
    const targetPage = doc.page || 1
    
    setPdfPanelDoc({
      filename: doc.filename,
      docPath: `http://localhost:8000/api/documents/${doc.id}/pdf`,
      id: doc.id,
    })
    setPdfTargetPage(targetPage)
    setPdfPanelOpen(true)
    
    // Legacy: Keep old PDFViewer working for backward compatibility
    setPdfDoc({
      filename: doc.filename,
      docPath: `http://localhost:8000/api/documents/${doc.id}/pdf`
    })
    // Don't open old viewer: setPdfOpen(true)
  }

  const handleSend = useCallback(async (question) => {
    if (chatting) return

    // Create a session if this is the first message
    let sessionId = currentSessionId
    if (!sessionId) {
      try {
        const session = await createSession(selectedIds)
        sessionId = session.id
        setCurrentSessionId(sessionId)
        await loadSessions()
      } catch (e) {
        toast.error(`Failed to create session: ${e.message}`)
        return
      }
    }

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: question,
      status: 'done',
      timestamp: new Date().toISOString(),
    }

    const aiMsgId = Date.now() + 1
    const aiMsg = {
      id: aiMsgId,
      role: 'assistant',
      content: '',
      sources: [],
      suggestions: [],
      confidence: null,
      relevance_score: 0,
      source_count: 0,
      ocr_sources: false,
      status: 'thinking',
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMsg, aiMsg])
    setChatting(true)

    try {
      const history = buildHistory()
      let fullContent = ''

      for await (const chunk of streamChat({
        question,
        chatHistory: history,
        docIds: selectedIds,
        sessionId,
      })) {
        if (chunk.type === 'sources') {
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId
              ? { 
                  ...m, 
                  sources: chunk.sources,
                  confidence: chunk.confidence || null,
                  relevance_score: chunk.relevance_score || 0,
                  source_count: chunk.source_count || 0,
                  ocr_sources: chunk.ocr_sources || false,
                  status: 'streaming' 
                }
              : m
          ))
        } else if (chunk.type === 'token') {
          fullContent += chunk.token
          const captured = fullContent
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId
              ? { ...m, content: captured, status: 'streaming' }
              : m
          ))
        } 
        // ✅ PHASE 3-4: Handle semantically enhanced sources (improve after answer generation)
        else if (chunk.type === 'sources_enhanced') {
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId
              ? { 
                  ...m, 
                  sources: chunk.sources,  // Replace with semantically ranked sources
                  status: 'streaming'
                }
              : m
          ))
        } 
        else if (chunk.type === 'suggestions') {
          setMessages(prev => prev.map(m =>
            m.id === aiMsgId
              ? { ...m, suggestions: chunk.suggestions }
              : m
          ))
        }
      }

      setMessages(prev => prev.map(m =>
        m.id === aiMsgId ? { ...m, status: 'done' } : m
      ))
      
      // Refresh sessions to update message count
      await loadSessions()
    } catch (err) {
      setMessages(prev => prev.map(m =>
        m.id === aiMsgId
          ? { ...m, content: `⚠️ Error: ${err.message}`, status: 'done' }
          : m
      ))
      toast.error(err.message)
    } finally {
      setChatting(false)
    }
  }, [chatting, selectedIds, messages, currentSessionId])

  const hasDocuments = documents.length > 0
  const hasSelected = selectedIds.length > 0

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-primary)]">
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            border: '1px solid var(--border)',
            fontSize: '13px',
          }
        }}
      />

      {/* ── Sidebar ── */}
      <aside
        className="flex flex-col shrink-0 border-r border-[var(--border)] bg-[var(--bg-secondary)] transition-all duration-300 overflow-hidden"
        style={{ width: sidebarOpen ? '288px' : '0px', minWidth: sidebarOpen ? '288px' : '0px' }}
      >
        <div className="flex flex-col h-full" style={{ minWidth: '288px' }}>
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[var(--border)]">
            {/* Premium Logo Container */}
            <div className="relative group">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl opacity-0 group-hover:opacity-20 blur-md transition-all duration-300" />
              <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/60 dark:to-blue-800/40 flex items-center justify-center shrink-0 shadow-lg shadow-blue-500/20 border border-blue-200 dark:border-blue-700/30 hover:shadow-blue-500/30 transition-all duration-300">
                <Logo size={22} animated={true} />
              </div>
            </div>
            
            {/* Title */}
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight text-[var(--text-primary)]">DocInsight</span>
              <span className="text-xs text-[var(--text-muted)] font-medium">AI Document Assistant</span>
            </div>
          </div>

          {/* Upload */}
          <div className="p-3 border-b border-[var(--border)]">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2 px-1">
              Upload Documents
            </p>
            <UploadZone onUploadSuccess={handleDocumentUploaded} />
          </div>

          {/* Documents & Sessions */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {/* 📄 Documents Section (Now First - Higher Priority) */}
            <div>
              <button
                onClick={() => setDocumentsExpanded(!documentsExpanded)}
                className="w-full flex items-center justify-between px-1 mb-2 hover:opacity-80 transition-opacity"
              >
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Your Documents
                </p>
                <div className="flex items-center gap-1">
                  {documents.length > 0 && (
                    <span className="px-1.5 py-0.5 rounded-md bg-[var(--bg-tertiary)] text-[var(--text-muted)] font-mono text-[10px]">
                      {selectedIds.length}/{documents.length}
                    </span>
                  )}
                  <ChevronDown 
                    size={14} 
                    className={`text-[var(--text-muted)] transition-transform duration-200 ${documentsExpanded ? '' : '-rotate-90'}`}
                  />
                </div>
              </button>

              {documentsExpanded && (
                <>
                  {docsLoading ? (
                    <div className="space-y-2">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="h-14 rounded-lg shimmer" />
                      ))}
                    </div>
                  ) : (
                    <DocumentList
                      documents={documents}
                      selectedIds={selectedIds}
                      onToggle={toggleDocument}
                      onDeleted={handleDocumentDeleted}
                    />
                  )}
                </>
              )}
            </div>

            {/* Divider */}
            {documents.length > 0 && sessions.length > 0 && (
              <div className="h-px bg-[var(--border)] my-2" />
            )}

            {/* 💬 Chat History Section (Now Second - Collapsible) */}
            <div>
              <button
                onClick={() => setSessionsExpanded(!sessionsExpanded)}
                className="w-full flex items-center justify-between px-1 mb-2 hover:opacity-80 transition-opacity"
              >
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Chat History
                </p>
                <ChevronDown 
                  size={14} 
                  className={`text-[var(--text-muted)] transition-transform duration-200 ${sessionsExpanded ? '' : '-rotate-90'}`}
                />
              </button>

              {sessionsExpanded && (
                <>
                  {sessionsLoading ? (
                    <div className="space-y-2">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="h-10 rounded-lg shimmer" />
                      ))}
                    </div>
                  ) : (
                    <SessionList
                      sessions={sessions}
                      onSessionSelect={handleSelectSession}
                      onSessionCreate={handleNewSession}
                      onSessionDelete={handleDeleteSession}
                      onSessionRename={handleRenameSession}
                      currentSessionId={currentSessionId}
                    />
                  )}
                </>
              )}
            </div>
          </div>

          {/* Warning */}
          {!hasSelected && hasDocuments && (
            <div className="px-3 py-2 border-t border-[var(--border)]">
              <p className="text-xs text-amber-600 dark:text-amber-400 text-center">
                ⚠ Select at least one document to chat
              </p>
            </div>
          )}
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex flex-col flex-1 min-w-0">
        {/* Topbar */}
        <header className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-primary)] shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
          >
            {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
          </button>

          <div className="flex-1 text-sm text-[var(--text-secondary)]">
            {!hasDocuments
              ? <span className="text-[var(--text-muted)]">Upload documents to get started</span>
              : !hasSelected
                ? <span className="text-amber-600 dark:text-amber-400">Select at least one document</span>
                : <span>Querying <strong className="text-[var(--text-primary)]">{selectedIds.length}</strong> document{selectedIds.length > 1 ? 's' : ''}</span>
            }
          </div>

          <div className="flex items-center gap-1">
            {messages.length > 0 && (
              <>
                <button
                  onClick={handleExportChat}
                  className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-green-600 dark:hover:text-green-400 transition-colors"
                  title="Export chat as PDF"
                >
                  <Download size={16} />
                </button>
                <button
                  onClick={clearChat}
                  className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-red-500 transition-colors"
                  title="Clear chat"
                >
                  <Trash2 size={16} />
                </button>
              </>
            )}
            <button
              onClick={() => setDark(!dark)}
              className="p-1.5 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              title="Toggle dark mode"
            >
              {dark ? <Sun size={17} /> : <Moon size={17} />}
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6" style={{ overflowAnchor: 'auto' }}>
          {/* Document Summary - Show when single doc selected */}
          {selectedIds.length === 1 && documentSummary && (
            <DocumentSummaryCard
              summary={documentSummary.summary}
              filename={documentSummary.filename}
              isGenerating={summaryLoading}
            />
          )}

          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center select-none">
              <div className="relative group mb-6">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-600 rounded-3xl opacity-0 group-hover:opacity-30 blur-xl transition-all duration-300" />
                <div className="relative w-16 h-16 rounded-3xl bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-900/60 dark:to-blue-800/40 flex items-center justify-center shadow-2xl shadow-blue-300/30 dark:shadow-blue-900/50 border border-blue-200 dark:border-blue-700/40 hover:shadow-blue-400/40 transition-all duration-300">
                  <Logo size={36} animated={true} />
                </div>
              </div>
              <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-1">
                Ask your documents anything
              </h2>
              <p className="text-sm text-[var(--text-muted)] max-w-sm mb-6 leading-relaxed">
                Upload PDFs, DOCX, or TXT files and chat with them using AI.
                Get answers with exact citations.
              </p>
              {hasSelected && (
                <div className="flex flex-wrap gap-2 justify-center max-w-md">
                  {SUGGESTIONS.map(s => (
                    <button
                      key={s}
                      onClick={() => handleSend(s)}
                      className="px-3 py-1.5 text-xs rounded-full border border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--accent)] hover:text-[var(--accent)] hover:bg-blue-50 dark:hover:bg-blue-950/20 transition-all"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            messages.map(msg => <ChatMessage key={msg.id} message={msg} onSuggestionClick={handleSend} onViewPDF={handleOpenPDF} />)
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-4 pb-4 shrink-0">
          <ChatInput
            onSubmit={handleSend}
            disabled={chatting}
            hasDocuments={hasSelected}
          />
          <p className="text-center text-[10px] text-[var(--text-muted)] mt-2">
            AI may make mistakes · Always verify answers with source documents
          </p>
        </div>
      </main>

      {/* PDF Viewer Modal - Legacy (for backward compatibility) */}
      {pdfOpen && pdfDoc && (
        <PDFViewer
          filename={pdfDoc.filename}
          docPath={pdfDoc.docPath}
          onClose={() => setPdfOpen(false)}
        />
      )}

      {/* PDF Viewer Panel - New (with page jump support) */}
      {pdfPanelOpen && pdfPanelDoc && (
        <PDFViewerPanel
          filename={pdfPanelDoc.filename}
          docPath={pdfPanelDoc.docPath}
          docId={pdfPanelDoc.id}
          targetPage={pdfTargetPage}
          onClose={() => setPdfPanelOpen(false)}
        />
      )}

      <Toaster position="top-center" />
    </div>
  )
}
